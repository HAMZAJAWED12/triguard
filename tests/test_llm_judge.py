import pytest

from triguard.models import llm_judge
from triguard.orchestrator.schemas import (
    AudioEvidence,
    ImageEvidence,
    JudgeInput,
    TextEvidence,
)


def _benign() -> JudgeInput:
    return JudgeInput(
        text=TextEvidence(toxicity_score=0.05, top_labels=[], confidence=0.9),
        image=ImageEvidence(caption="a photo of a sunset", visual_risk_cues=[], confidence=0.6),
    )


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


def test_rule_judge_benign_returns_safe() -> None:
    out = llm_judge.judge(_benign(), force_mode="rule")
    assert out.risk_label == "safe"
    assert out.recommended_action == "allow"


def test_rule_judge_harmful_returns_block() -> None:
    out = llm_judge.judge(_harmful(), force_mode="rule")
    assert out.risk_label == "harmful"
    assert out.recommended_action == "block"
    # rationale must reference at least one piece of evidence
    assert any(k in out.rationale.lower()
               for k in ["text", "image", "audio", "weapon", "shouting"])


def test_rule_judge_flags_all_three_modalities_on_harmful() -> None:
    out = llm_judge.judge(_harmful(), force_mode="rule")
    assert set(out.flagged_modalities) == {"text", "image", "audio"}


def test_rule_judge_borderline_when_only_one_modality_flagged() -> None:
    j = JudgeInput(
        text=TextEvidence(toxicity_score=0.5, top_labels=["toxic"], confidence=0.3),
    )
    out = llm_judge.judge(j, force_mode="rule")
    assert out.risk_label in {"borderline", "harmful"}


def test_ollama_unavailable_falls_back_to_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When Ollama is not running, the judge must not crash; it should fall
    back to the rule-based path and tag the uncertainty."""
    # this points at a closed port so urlopen will fail fast
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:1")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")  # defeat sys proxy
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    out = llm_judge.judge(_benign(), force_mode="ollama")
    assert any("ollama_unavailable" in u for u in out.uncertainties)
