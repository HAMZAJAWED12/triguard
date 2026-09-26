"""Offline regression tests for wrapper-failure shielding in the orchestrator.

``pipeline.run`` wraps each wrapper call in ``try/except Exception`` and, on
failure, substitutes a zero-confidence evidence object carrying
``raw={"error": str(e)}`` so the judge still runs and a ``TriGuardResult`` is
always returned (src/triguard/orchestrator/pipeline.py, modality dispatch).
Each test breaks exactly one wrapper via monkeypatch; the other two run in
mock mode (``TRIGUARD_MOCK=1``) so nothing touches weights or the network.
"""
from __future__ import annotations

import pytest

from triguard.models import audio_model, image_model, text_model
from triguard.orchestrator import pipeline
from triguard.orchestrator.schemas import TriGuardResult

_TEXT = "I hope you suffer for being so worthless"
_IMAGE = "data/local_demo/scary_gun_photo.jpg"
_AUDIO = "data/local_demo/violent_shout_sample.wav"


def _boom(*_args, **_kwargs):
    raise RuntimeError("boom")


@pytest.fixture(autouse=True)
def _mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRIGUARD_MOCK", "1")


def _assert_common(r: TriGuardResult) -> None:
    assert isinstance(r, TriGuardResult)
    assert r.recommended_action in {"allow", "review", "block"}
    assert r.model_versions["orchestrator"] == pipeline.VERSION
    assert r.model_versions["llm_judge"] == "rule"
    assert set(r.model_versions) >= {
        "orchestrator", "text_model", "image_model", "audio_model", "llm_judge",
    }


def test_text_wrapper_failure_is_shielded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(text_model, "analyse", _boom)

    r = pipeline.run(text=_TEXT, image=_IMAGE, audio=_AUDIO, judge_mode="rule")

    _assert_common(r)
    assert r.text_evidence is not None
    assert r.text_evidence.confidence == 0.0
    assert r.text_evidence.toxicity_score == 0.0
    assert r.text_evidence.top_labels == []
    assert r.text_evidence.raw["error"] == "boom"
    # No raw["mode"] on the placeholder -> honest "unknown" backend token.
    assert r.model_versions["text_model"] == "unknown"
    # The other wrappers still ran in mock mode and are labelled as such.
    assert r.model_versions["image_model"].startswith("mock")
    assert r.model_versions["audio_model"].startswith("mock")
    # Text was benign-by-error; image + audio cues still reach the judge.
    assert "text" not in r.flagged_modalities


def test_image_wrapper_failure_is_shielded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(image_model, "analyse", _boom)

    r = pipeline.run(text=_TEXT, image=_IMAGE, audio=_AUDIO, judge_mode="rule")

    _assert_common(r)
    assert r.image_evidence is not None
    assert r.image_evidence.confidence == 0.0
    assert r.image_evidence.caption == "(error)"
    assert r.image_evidence.visual_risk_cues == []
    assert r.image_evidence.raw["error"] == "boom"
    assert r.model_versions["image_model"] == "unknown"
    assert "image" not in r.flagged_modalities
    # Zero image confidence is surfaced as an uncertainty by the rule judge.
    assert "low_image_caption_confidence" in r.uncertainties


def test_audio_wrapper_failure_is_shielded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audio_model, "analyse", _boom)

    r = pipeline.run(text=_TEXT, image=_IMAGE, audio=_AUDIO, judge_mode="rule")

    _assert_common(r)
    assert r.audio_evidence is not None
    assert r.audio_evidence.transcript_confidence == 0.0
    assert r.audio_evidence.transcript == "(error)"
    assert r.audio_evidence.yamnet_tags == []
    assert r.audio_evidence.raw["error"] == "boom"
    assert r.model_versions["audio_model"] == "unknown"
    assert "audio" not in r.flagged_modalities
    assert "low_audio_transcript_confidence" in r.uncertainties


def test_all_three_wrappers_failing_still_returns_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(text_model, "analyse", _boom)
    monkeypatch.setattr(image_model, "analyse", _boom)
    monkeypatch.setattr(audio_model, "analyse", _boom)

    r = pipeline.run(text=_TEXT, image=_IMAGE, audio=_AUDIO, judge_mode="rule")

    _assert_common(r)
    assert r.flagged_modalities == []
    assert r.risk_label == "safe"
    for ev in (r.text_evidence, r.image_evidence, r.audio_evidence):
        assert ev is not None and ev.raw["error"] == "boom"
    assert all(r.model_versions[k] == "unknown"
               for k in ("text_model", "image_model", "audio_model"))
