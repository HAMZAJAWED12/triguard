"""API tests for the Phase D demo endpoints (presets, compare, stream,
eval summary, dashboard).

Same conventions as tests/test_api.py: skip cleanly where `fastapi`/`httpx`
are absent; otherwise fully offline in mock mode. The compare/stream fast
tests point OLLAMA_HOST at a closed local port so the ollama side falls back
instantly (no network wait); the token-stream test monkeypatches the
low-level generator. One slow test exercises a real Ollama server and skips
cleanly when it is unreachable.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
# fastapi's Form/File routes hard-require the python-multipart package at app
# import; without this guard the client fixture ERRORs instead of skipping.
try:
    import python_multipart  # noqa: F401
except ImportError:
    pytest.importorskip("multipart", reason="python-multipart not installed")

from fastapi.testclient import TestClient  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRIGUARD_MOCK", "1")  # force mock everywhere, offline
    monkeypatch.delenv("TRIGUARD_JUDGE", raising=False)  # rule default
    from triguard.api.main import app
    return TestClient(app)


@pytest.fixture()
def offline_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the ollama path at a closed port: instant, honest fallback."""
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:1")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "2")
    # urllib honours proxy env vars; make sure a system proxy can't turn the
    # closed-port call into a real network request.
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")


def _sse_events(resp) -> list[dict]:
    events = []
    for line in resp.iter_lines():
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: "):]))
    return events


# -- presets ----------------------------------------------------------------


def test_presets_list(client: TestClient) -> None:
    resp = client.get("/presets")
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()["presets"]}
    assert {"safe", "borderline", "harmful", "multimodal_real"} <= names


def test_preset_run_harmful(client: TestClient) -> None:
    resp = client.post("/analyse/preset", json={"name": "harmful"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["preset"] == "harmful"
    assert "text" in body["inputs"]
    result = body["result"]
    assert result["risk_label"] in {"safe", "borderline", "harmful"}
    assert "text_model" in result["model_versions"]


def test_preset_unknown_404(client: TestClient) -> None:
    resp = client.post("/analyse/preset", json={"name": "nope"})
    assert resp.status_code == 404


def test_gather_inputs_cleans_up_on_save_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A failure saving the SECOND upload must not leak the first temp file."""
    from types import SimpleNamespace

    from triguard.api import main as api_main

    saved: list[str] = []

    def fake_save(upload) -> str:
        if upload.filename.endswith(".wav"):
            raise OSError(22, "Invalid argument")
        p = tmp_path / f"leakcheck_{len(saved)}.png"
        p.write_bytes(b"x")
        saved.append(str(p))
        return str(p)

    monkeypatch.setattr(api_main, "_save_upload", fake_save)
    image = SimpleNamespace(filename="a.png")
    audio = SimpleNamespace(filename="b.wav")
    with pytest.raises(OSError):
        api_main._gather_inputs(None, image, audio)  # type: ignore[arg-type]
    assert saved, "image save should have happened first"
    assert not os.path.exists(saved[0]), "first temp file leaked"


# -- compare ----------------------------------------------------------------


def test_compare_offline_falls_back(
    client: TestClient, offline_ollama: None
) -> None:
    resp = client.post("/analyse/compare",
                       data={"text": "you are a worthless idiot"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["rule"]["judge_label"] == "rule"
    assert body["rule"]["output"]["risk_label"] in {
        "safe", "borderline", "harmful"}
    # ollama unreachable -> honestly labelled fallback, tagged uncertainty
    assert body["ollama"]["judge_label"] == "ollama->rule"
    assert any(u.startswith("ollama_unavailable")
               for u in body["ollama"]["output"]["uncertainties"])
    assert body["evidence"]["text"] is not None
    assert "llm_judge" not in body["perception_model_versions"]


# -- stream -----------------------------------------------------------------


def test_stream_offline_falls_back(
    client: TestClient, offline_ollama: None
) -> None:
    with client.stream("POST", "/analyse/stream",
                       data={"text": "you are a worthless idiot"}) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        events = _sse_events(resp)
    assert events[0]["type"] == "evidence"
    assert events[0]["rule"]["output"]["risk_label"] in {
        "safe", "borderline", "harmful"}
    final = events[-1]
    assert final["type"] == "final"
    assert final["source"] == "rule_fallback"
    assert final["judge_label"] == "ollama->rule"


def test_stream_tokens_monkeypatched(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    valid = json.dumps({
        "risk_score": 0.9,
        "risk_label": "harmful",
        "flagged_modalities": ["text"],
        "rationale": "the text toxicity 0.90 with an insult label drives it",
        "uncertainties": [],
        "recommended_action": "block",
    })
    from triguard.models import llm_judge
    monkeypatch.setattr(llm_judge, "_ollama_generate_stream",
                        lambda prompt: iter([valid[:25], valid[25:]]))
    with client.stream("POST", "/analyse/stream",
                       data={"text": "you are a worthless idiot"}) as resp:
        events = _sse_events(resp)
    kinds = [e["type"] for e in events]
    assert kinds[0] == "evidence"
    assert kinds.count("token") == 2
    final = events[-1]
    assert final["source"] == "ollama"
    assert final["judge_label"] == "ollama"
    assert final["judge_output"]["risk_label"] == "harmful"


# -- eval summary + dashboard -----------------------------------------------


def test_eval_summary_matches_committed_files(client: TestClient) -> None:
    resp = client.get("/eval/summary")
    assert resp.status_code == 200
    body = resp.json()
    if not body["available"]:
        pytest.skip("no committed outputs/evaluation on this checkout")
    tracks = body["tracks"]
    # Every number must equal the committed file verbatim — spot-check each
    # track the summary claims, against the very file it names.
    for track, entry in tracks.items():
        if track == "t2":
            candidates = entry["runs_by_backend"].values()
        elif track == "t8":
            candidates = entry["runs_by_config"].values()
        else:
            candidates = [entry]
        for e in candidates:
            committed = json.loads(
                (_REPO_ROOT / e["file"]).read_text(encoding="utf-8"))
            for key, value in e["data"].items():
                if key in ("conditions", "whisper_wer", "yamnet_events"):
                    continue  # trimmed sub-dicts checked below
                assert committed[key] == value, f"{track}:{key} drifted"
    if "t8" in tracks:
        by_cfg = tracks["t8"]["runs_by_config"]
        if "mock" in by_cfg:
            assert by_cfg["mock"]["data"]["config"]["mock"] is True
        if "real" in by_cfg:
            assert by_cfg["real"]["data"]["config"]["mock"] is False
    if "t6" in tracks:
        committed = json.loads(
            (_REPO_ROOT / tracks["t6"]["file"]).read_text(encoding="utf-8"))
        for name, cond in tracks["t6"]["data"]["conditions"].items():
            assert cond["accuracy"] == committed["conditions"][name]["accuracy"]
            assert cond["macro_f1"] == committed["conditions"][name]["macro_f1"]
    if "t4" in tracks:
        committed = json.loads(
            (_REPO_ROOT / tracks["t4"]["file"]).read_text(encoding="utf-8"))
        summary = tracks["t4"]["data"]
        for key, sub in (("whisper_wer", ("n", "wer_corpus",
                                          "wer_mean_per_clip")),
                         ("yamnet_events", ("n", "top1_rate", "top5_rate"))):
            for k in sub:
                assert summary[key][k] == committed[key][k], f"t4:{key}.{k}"


def test_dashboard_page(client: TestClient) -> None:
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "evaluation dashboard" in resp.text


# -- slow: real Ollama ---------------------------------------------------


def _ollama_reachable() -> bool:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=2):
            return True
    except Exception:
        return False


@pytest.mark.slow
def test_compare_real_ollama(client: TestClient) -> None:
    """Real llama3 side-by-side; skips cleanly when Ollama is not running."""
    if not _ollama_reachable():
        pytest.skip("Ollama not reachable")
    resp = client.post("/analyse/compare",
                       data={"text": "I hope you suffer, you worthless fool"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ollama"]["judge_label"] in {"ollama", "ollama->rule"}
    out = body["ollama"]["output"]
    assert out["risk_label"] in {"safe", "borderline", "harmful"}
    assert out["recommended_action"] in {"allow", "review", "block"}
    assert out["rationale"]
