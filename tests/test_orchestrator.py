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
