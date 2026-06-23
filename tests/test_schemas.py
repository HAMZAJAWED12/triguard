import pytest
from pydantic import ValidationError

from triguard.orchestrator.schemas import (
    JudgeInput,
    JudgeOutput,
    TextEvidence,
    TriGuardResult,
)


def test_text_evidence_bounds() -> None:
    TextEvidence(toxicity_score=0.7, top_labels=["insult"], confidence=0.8)
    with pytest.raises(ValidationError):
        TextEvidence(toxicity_score=1.5, top_labels=[], confidence=0.5)
    with pytest.raises(ValidationError):
        TextEvidence(toxicity_score=0.5, top_labels=[], confidence=-0.1)


def test_judge_input_requires_at_least_one_modality() -> None:
    with pytest.raises(ValidationError):
        JudgeInput()


def test_judge_input_accepts_partial_modalities() -> None:
    j = JudgeInput(text=TextEvidence(toxicity_score=0.1, top_labels=[], confidence=0.5))
    assert j.text is not None and j.image is None and j.audio is None


def test_judge_output_safe_cannot_block() -> None:
    with pytest.raises(ValidationError):
        JudgeOutput(
            risk_score=0.1,
            risk_label="safe",
            flagged_modalities=[],
            rationale="benign content",
            uncertainties=[],
            recommended_action="block",
        )


def test_judge_output_harmful_cannot_allow() -> None:
    with pytest.raises(ValidationError):
        JudgeOutput(
            risk_score=0.9,
            risk_label="harmful",
            flagged_modalities=["text"],
            rationale="threat detected",
            uncertainties=[],
            recommended_action="allow",
        )


def test_triguardresult_inherits_validation() -> None:
    r = TriGuardResult(
        risk_score=0.4,
        risk_label="borderline",
        flagged_modalities=["text"],
        rationale="text leaned toxic",
        uncertainties=[],
        recommended_action="review",
        text_evidence=TextEvidence(toxicity_score=0.5, top_labels=["toxic"], confidence=0.4),
        latency_ms=12,
        model_versions={"orchestrator": "0.1.0"},
    )
    assert r.recommended_action == "review"
