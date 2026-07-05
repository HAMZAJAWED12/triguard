"""Offline unit tests for the additive streaming judge path (Phase D).

No network: the unreachable-host test points at a closed local port (instant
connection refusal) and the token tests monkeypatch the low-level stream
generator. The non-streaming judge path is untouched by these features and
keeps its own tests.
"""
from __future__ import annotations

import json

import pytest

from triguard.models import llm_judge
from triguard.orchestrator.schemas import JudgeInput, JudgeOutput, TextEvidence


def _judge_input() -> JudgeInput:
    return JudgeInput(
        text=TextEvidence(
            toxicity_score=0.9,
            top_labels=["insult"],
            confidence=0.8,
            raw={"mode": "mock"},
        )
    )


_VALID_JSON = json.dumps({
    "risk_score": 0.9,
    "risk_label": "harmful",
    "flagged_modalities": ["text"],
    "rationale": "the text toxicity 0.90 with an insult label drives the risk",
    "uncertainties": [],
    "recommended_action": "block",
})


def test_stream_unreachable_falls_back_to_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:1")  # closed port
    monkeypatch.setenv("OLLAMA_TIMEOUT", "2")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")  # defeat sys proxy
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    events = list(llm_judge.judge_stream(_judge_input()))
    assert len(events) == 1  # no tokens, straight to the terminal event
    final = events[0]
    assert final["type"] == "final"
    assert final["source"] == "rule_fallback"
    out = JudgeOutput.model_validate(final["judge_output"])
    assert any(u.startswith("ollama_unavailable") for u in out.uncertainties)


def test_stream_tokens_then_valid_final(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fragments = [_VALID_JSON[:20], _VALID_JSON[20:60], _VALID_JSON[60:]]
    monkeypatch.setattr(
        llm_judge, "_ollama_generate_stream", lambda prompt: iter(fragments)
    )
    events = list(llm_judge.judge_stream(_judge_input()))
    tokens = [e for e in events if e["type"] == "token"]
    assert [t["text"] for t in tokens] == fragments
    final = events[-1]
    assert final["type"] == "final"
    assert final["source"] == "ollama"
    out = JudgeOutput.model_validate(final["judge_output"])
    assert out.risk_label == "harmful"
    assert out.recommended_action == "block"


def test_stream_dies_mid_stream_falls_back_to_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tokens already emitted, then the stream dies -> rule fallback final."""
    def dying_stream(prompt):
        yield '{"risk_'
        raise TimeoutError("socket timed out mid-stream")

    monkeypatch.setattr(llm_judge, "_ollama_generate_stream", dying_stream)
    events = list(llm_judge.judge_stream(_judge_input()))
    assert [e["type"] for e in events] == ["token", "final"]
    final = events[-1]
    assert final["source"] == "rule_fallback"
    out = JudgeOutput.model_validate(final["judge_output"])
    assert any(u.startswith("ollama_unavailable:TimeoutError")
               for u in out.uncertainties)


def test_stream_invalid_json_falls_back_to_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        llm_judge,
        "_ollama_generate_stream",
        lambda prompt: iter(["this is ", "not json at all"]),
    )
    events = list(llm_judge.judge_stream(_judge_input()))
    assert [e["type"] for e in events] == ["token", "token", "final"]
    final = events[-1]
    assert final["source"] == "rule_fallback"
    out = JudgeOutput.model_validate(final["judge_output"])
    assert "judge_output_invalid" in out.uncertainties
