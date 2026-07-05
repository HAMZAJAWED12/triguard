"""Fast unit tests for the T7 grounding check (pure function, no models)."""
from __future__ import annotations

from triguard.evaluation.grounding import grounding_report
from triguard.orchestrator.schemas import JudgeInput, TextEvidence


def test_grounding_cites_evidence() -> None:
    ji = JudgeInput(text=TextEvidence(toxicity_score=0.85, top_labels=["threat"],
                                      confidence=0.8))
    rep = grounding_report(ji, "flagged for threat at toxicity 0.85")
    assert rep["grounded"] is True
    assert "threat" in rep["cited"]
    assert rep["invented_modalities"] == []


def test_grounding_detects_invented_modality() -> None:
    ji = JudgeInput(text=TextEvidence(toxicity_score=0.1, top_labels=[], confidence=0.9))
    rep = grounding_report(ji, "the image clearly shows a weapon")  # no image given
    assert "image" in rep["invented_modalities"]
