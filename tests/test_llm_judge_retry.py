"""Offline unit tests for the Ollama judge's retry-once-then-fall-back contract.

``llm_judge._judge_via_ollama`` calls the module-global ``_ollama_generate``
twice at most: once with the base prompt and, if the reply does not parse as
a ``JudgeOutput``, once more with a stricter suffix appended. A second
failure raises ``JudgeFailure`` and ``judge()`` returns the rule judge tagged
``judge_output_invalid``. These tests monkeypatch ``_ollama_generate`` so no
network or Ollama server is involved (same fixture shapes as
tests/test_llm_judge.py).
"""
from __future__ import annotations

import json

import pytest

from triguard.models import llm_judge
from triguard.orchestrator import pipeline
from triguard.orchestrator.schemas import (
    AudioEvidence,
    ImageEvidence,
    JudgeInput,
    JudgeOutput,
    TextEvidence,
    TriGuardResult,
)

# Verbatim from src/triguard/models/llm_judge.py (the ``stricter`` prompt).
_STRICT_SUFFIX = (
    "IMPORTANT: respond with ONLY the JSON object. "
    "Do not add commentary, markdown or code fences."
)

_VALID_JSON = json.dumps(
    {
        "risk_score": 0.85,
        "risk_label": "harmful",
        "flagged_modalities": ["text"],
        "rationale": "the text classifier flagged toxicity at 0.85 (threat)",
        "uncertainties": [],
        "recommended_action": "block",
    }
)


def _three_modalities() -> JudgeInput:
    """All three modalities present (protocol T5 bullet 2, docs/evaluation_protocol.md)."""
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


def _patch_generate(monkeypatch: pytest.MonkeyPatch, replies: list[str]) -> list[str]:
    """Replace ``_ollama_generate`` with a scripted stub; return the prompt log."""
    prompts: list[str] = []
    queue = list(replies)

    def fake_generate(prompt: str) -> str:
        prompts.append(prompt)
        if not queue:
            raise AssertionError("_ollama_generate called more times than scripted")
        return queue.pop(0)

    monkeypatch.setattr(llm_judge, "_ollama_generate", fake_generate)
    return prompts


def test_invalid_twice_falls_back_to_rule_after_exactly_two_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompts = _patch_generate(monkeypatch, ["not json", "not json"])

    out = llm_judge.judge(_three_modalities(), force_mode="ollama")

    assert isinstance(out, JudgeOutput)
    assert len(prompts) == 2, "retry contract is exactly one retry"
    assert "judge_output_invalid" in out.uncertainties
    # The fallback is the rule judge's own verdict on the same evidence.
    expected = llm_judge.judge(_three_modalities(), force_mode="rule")
    assert out.risk_label == expected.risk_label
    assert out.recommended_action == expected.recommended_action
    assert out.rationale == expected.rationale
    # The orchestrator's honesty label sees the fallback tag.
    assert pipeline.judge_label("ollama", out) == "ollama->rule"


def test_retry_prompt_carries_stricter_suffix_and_second_reply_wins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompts = _patch_generate(monkeypatch, ["```garbage```", _VALID_JSON])

    out = llm_judge.judge(_three_modalities(), force_mode="ollama")

    assert len(prompts) == 2
    assert _STRICT_SUFFIX not in prompts[0]
    assert prompts[1].startswith(prompts[0])
    assert prompts[1].endswith(_STRICT_SUFFIX)
    # Second reply parsed: the LLM's answer is returned unchanged, no fallback tag.
    assert out.risk_score == 0.85
    assert out.risk_label == "harmful"
    assert out.recommended_action == "block"
    assert out.uncertainties == []
    assert not any(
        u.startswith(("judge_output_invalid", "ollama_unavailable"))
        for u in out.uncertainties
    )
    assert pipeline.judge_label("ollama", out) == "ollama"


def test_valid_first_reply_makes_exactly_one_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompts = _patch_generate(monkeypatch, [_VALID_JSON])

    out = llm_judge.judge(_three_modalities(), force_mode="ollama")

    assert len(prompts) == 1
    assert _STRICT_SUFFIX not in prompts[0]
    assert out.uncertainties == []
    assert pipeline.judge_label("ollama", out) == "ollama"


def test_orchestrator_labels_invalid_json_fallback_ollama_to_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end through pipeline.run: three modalities, judge_mode=ollama,
    invalid JSON twice -> retry once -> rule fallback tagged judge_output_invalid
    and model_versions["llm_judge"] == "ollama->rule" (protocol T5 bullet 2;
    the label is the rule judge's own, not a forced "borderline" — see
    docs/report_evidence_tables.md Table E9, row "T5 judge failure path")."""
    monkeypatch.setenv("TRIGUARD_MOCK", "1")
    prompts = _patch_generate(monkeypatch, ["nope", "still nope"])

    r = pipeline.run(
        text="I hope you suffer for being so worthless",
        image="data/local_demo/scary_gun_photo.jpg",
        audio="data/local_demo/violent_shout_sample.wav",
        judge_mode="ollama",
    )

    assert isinstance(r, TriGuardResult)
    assert len(prompts) == 2
    assert "judge_output_invalid" in r.uncertainties
    assert r.model_versions["llm_judge"] == "ollama->rule"
    assert r.text_evidence and r.image_evidence and r.audio_evidence
    assert r.risk_label in {"safe", "borderline", "harmful"}
