"""Slow, opt-in test for the real Ollama judge path (Prompt 4).

Marked ``slow`` so it is skipped unless ``--run-slow`` is passed. Even with
``--run-slow`` it SKIPS cleanly (never fails) when Ollama is not reachable, so no
CI run can depend on Ollama being up. When Ollama IS reachable it checks that the
path returns a schema-valid ``JudgeOutput``.
"""
from __future__ import annotations

import urllib.request

import pytest

from triguard.models import llm_judge
from triguard.orchestrator.schemas import (
    AudioEvidence,
    ImageEvidence,
    JudgeInput,
    JudgeOutput,
    TextEvidence,
)


def _ollama_reachable() -> bool:
    """True only if the Ollama server answers /api/tags quickly."""
    try:
        req = urllib.request.Request(f"{llm_judge._ollama_host()}/api/tags")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _harmful() -> JudgeInput:
    return JudgeInput(
        text=TextEvidence(toxicity_score=0.85, top_labels=["threat"], confidence=0.8),
        image=ImageEvidence(
            caption="an image apparently depicting weapon",
            visual_risk_cues=["weapon"],
            confidence=0.55,
        ),
        audio=AudioEvidence(
            transcript="(loud distressed vocalisation)",
            transcript_confidence=0.4,
            yamnet_tags=[("shouting", 0.7)],
        ),
    )


@pytest.mark.slow
def test_ollama_judge_returns_schema_valid_output() -> None:
    if not _ollama_reachable():
        pytest.skip("Ollama not reachable (needs `ollama serve` + a pulled model)")

    out = llm_judge.judge(_harmful(), force_mode="ollama")

    # Schema-valid by contract, and re-validates cleanly.
    assert isinstance(out, JudgeOutput)
    JudgeOutput.model_validate(out.model_dump())
    assert out.risk_label in {"safe", "borderline", "harmful"}
    assert out.recommended_action in {"allow", "review", "block"}
    assert len(out.rationale) >= 1
