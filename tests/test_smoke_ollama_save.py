"""Fast, offline tests for ``scripts/smoke_ollama.py --save``.

The Ollama HTTP call (``llm_judge._ollama_generate``) is monkeypatched so no
network is touched; perception runs in mock mode (``TRIGUARD_MOCK=1``). The
tests check the additive ``--save`` envelope: fixed key set, native-vs-fallback
``judge_label``, and that the default (no flag) run writes nothing and leaves
``llm_judge._ollama_generate`` as it found it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from triguard.models import llm_judge

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts"))

import smoke_ollama  # noqa: E402

_EXPECTED_KEYS = {
    "rendered_prompt", "raw_response", "validated_output", "uncertainties",
    "model", "keep_alive", "timeout", "judge_label",
}

_VALID_JSON = json.dumps({
    "risk_score": 0.8,
    "risk_label": "harmful",
    "flagged_modalities": ["text"],
    "rationale": "the text toxicity score is high",
    "uncertainties": [],
    "recommended_action": "block",
})


@pytest.fixture()
def sample_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("TRIGUARD_MOCK", "1")  # offline perception
    monkeypatch.setenv("OLLAMA_TIMEOUT", "7")
    p = tmp_path / "sample.json"
    p.write_text(json.dumps({"text": "you are a worthless idiot"}), encoding="utf-8")
    return p


def test_save_writes_envelope_with_fixed_keys(
    sample_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def fake_generate(prompt: str) -> str:
        calls.append(prompt)
        return _VALID_JSON

    monkeypatch.setattr(llm_judge, "_ollama_generate", fake_generate)
    out = tmp_path / "nested" / "save.json"

    rc = smoke_ollama.main(["smoke_ollama.py", str(sample_path), "--save", str(out)])

    assert rc == 0
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) == _EXPECTED_KEYS
    assert len(calls) == 1  # valid first time -> no stricter retry
    assert data["rendered_prompt"] == calls[0]
    assert data["rendered_prompt"].startswith(
        "You are a content-moderation judge."
    )
    assert "{evidence_block}" not in data["rendered_prompt"]
    assert data["raw_response"] == _VALID_JSON
    assert data["validated_output"]["risk_label"] == "harmful"
    assert data["uncertainties"] == []
    assert data["judge_label"] == "ollama"
    assert data["model"] == llm_judge._ollama_model()
    assert data["keep_alive"] == llm_judge._ollama_keep_alive()
    assert data["timeout"] == 7.0
    # recorder removed again after the run
    assert llm_judge._ollama_generate is fake_generate


def test_save_records_fallback_after_invalid_twice(
    sample_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def garbage(prompt: str) -> str:
        calls.append(prompt)
        return "not json at all"

    monkeypatch.setattr(llm_judge, "_ollama_generate", garbage)
    out = tmp_path / "save.json"

    rc = smoke_ollama.main(["smoke_ollama.py", str(sample_path), "--save", str(out)])

    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) == _EXPECTED_KEYS
    assert len(calls) == 2  # first attempt + stricter retry
    assert calls[1].startswith(calls[0])  # retry = same prompt + suffix
    assert data["rendered_prompt"] == calls[0]
    assert data["raw_response"] == "not json at all"
    assert "judge_output_invalid" in data["uncertainties"]
    assert data["judge_label"] == "ollama->rule"


def test_no_flag_writes_nothing_and_restores_nothing(
    sample_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(llm_judge, "_ollama_generate", lambda prompt: _VALID_JSON)
    before = set(tmp_path.iterdir())

    rc = smoke_ollama.main(["smoke_ollama.py", str(sample_path)])

    assert rc == 0
    assert set(tmp_path.iterdir()) == before  # no envelope written


def test_save_flag_without_path_exits() -> None:
    with pytest.raises(SystemExit):
        smoke_ollama._split_save_flag(["smoke_ollama.py", "--save"])
