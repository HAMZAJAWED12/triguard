import pytest

from triguard.orchestrator import pipeline


def test_orchestrator_text_only() -> None:
    r = pipeline.run(text="Thanks for the kind feedback")
    assert r.risk_label in {"safe", "borderline"}
    assert r.text_evidence is not None
    assert r.image_evidence is None and r.audio_evidence is None
    assert r.latency_ms >= 0


def test_orchestrator_three_modalities_harmful() -> None:
    r = pipeline.run(
        text="I hope you suffer for being so worthless",
        image="/tmp/scary_gun_photo.jpg",
        audio="/tmp/violent_shout.wav",
    )
    assert r.risk_label == "harmful"
    assert r.recommended_action == "block"
    assert set(r.flagged_modalities) == {"text", "image", "audio"}


def test_orchestrator_missing_inputs_raises() -> None:
    with pytest.raises(ValueError):
        pipeline.run()


def test_orchestrator_attaches_versions_and_latency() -> None:
    r = pipeline.run(text="Hello world")
    assert "orchestrator" in r.model_versions
    assert r.latency_ms >= 0


def test_model_versions_agree_with_raw_mode() -> None:
    """model_versions must reflect the backend each evidence actually used."""
    r = pipeline.run(
        text="Hello there friend",
        image="/tmp/calm_photo.jpg",
        audio="/tmp/calm_speech.wav",
    )
    for key, ev in (("text_model", r.text_evidence),
                    ("image_model", r.image_evidence),
                    ("audio_model", r.audio_evidence)):
        assert ev is not None
        token = pipeline.backend_of_mode(ev.raw.get("mode"))
        assert token != "unknown"
        assert r.model_versions[key].split(":")[0] == token
    # offline defaults: text = sklearn tier, image/audio = mock, judge = rule
    assert r.model_versions["text_model"].split(":")[0] == "sklearn"
    assert r.model_versions["image_model"] == "mock"
    assert r.model_versions["audio_model"] == "mock"
    assert r.model_versions["llm_judge"] == "rule"


def test_model_versions_judge_reflects_env_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env-driven ollama (judge_mode=None) must be labelled ollama, not rule."""
    monkeypatch.setenv("TRIGUARD_JUDGE", "ollama")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:1")  # unreachable -> fallback
    r = pipeline.run(text="hello world")  # judge_mode=None honours the env
    assert r.model_versions["llm_judge"] in {"ollama", "ollama->rule"}
    assert r.model_versions["llm_judge"] != "rule"
