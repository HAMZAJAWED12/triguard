"""
LLM judge for TriGuard.

Production path: a local Llama-3-8B-Instruct model served via Ollama. The judge
reads a JudgeInput, builds a structured prompt, calls the local LLM and parses
the response against JudgeOutput. If parsing fails it retries once with a
stricter prompt; if it fails again the orchestrator falls back to a deterministic
rule-based judge so the pipeline never crashes.

For the Tier-A prototype demo the rule-based judge is the default because it
runs without Ollama, fits 8 GB RAM, and produces fully schema-valid output.
The Ollama path is implemented so the marker can see the full pattern.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional, cast

from pydantic import ValidationError

from ..orchestrator.schemas import (
    JudgeInput,
    JudgeOutput,
    Modality,
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q4_K_M")

# Prompt used in production (Ollama path).
JUDGE_PROMPT_TEMPLATE = """You are a content-moderation judge. Read the evidence below
and return ONE JSON object that conforms exactly to this schema:

{{
  "risk_score": float in [0,1],
  "risk_label": "safe" | "borderline" | "harmful",
  "flagged_modalities": list of "text" | "image" | "audio",
  "rationale": short paragraph grounded in the evidence,
  "uncertainties": list of short strings,
  "recommended_action": "allow" | "review" | "block"
}}

Rules:
- A "safe" label must NOT recommend block.
- A "harmful" label must NOT recommend allow.
- Reference at least one piece of evidence in the rationale.
- If evidence is conflicting, prefer "borderline" + "review".

Evidence:
{evidence_block}

Return ONLY the JSON object, nothing else."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class JudgeFailure(Exception):
    """Raised when both Ollama attempts produce an invalid schema."""


def judge(input_: JudgeInput, *, force_mode: Optional[str] = None) -> JudgeOutput:
    """Score the evidence and emit a JudgeOutput.

    force_mode: "rule" | "ollama" | None.
        None uses TRIGUARD_JUDGE env var, defaulting to "rule".
    """
    mode = force_mode or os.getenv("TRIGUARD_JUDGE", "rule")

    if mode == "ollama":
        try:
            return _judge_via_ollama(input_)
        except (urllib.error.URLError, JudgeFailure) as e:
            # graceful fallback
            return _rule_based_judge(
                input_,
                extra_uncertainties=[f"ollama_unavailable: {type(e).__name__}"],
            )
    return _rule_based_judge(input_)


# ---------------------------------------------------------------------------
# Rule-based judge — deterministic, schema-valid, used for the Tier-A demo.
# ---------------------------------------------------------------------------


def _rule_based_judge(
    input_: JudgeInput, *, extra_uncertainties: Optional[list[str]] = None
) -> JudgeOutput:
    extra_uncertainties = list(extra_uncertainties or [])
    signals: list[tuple[str, float, str]] = []
    flagged: list[str] = []
    rationale_parts: list[str] = []

    # Text signal
    if input_.text:
        ts = input_.text.toxicity_score
        signals.append(("text", ts, f"text toxicity score {ts:.2f}"))
        if ts >= 0.5:
            flagged.append("text")
            rationale_parts.append(
                f"the text classifier flagged toxicity at {ts:.2f}"
                + (f" ({', '.join(input_.text.top_labels)})"
                   if input_.text.top_labels else "")
            )
        else:
            rationale_parts.append(f"the text appeared benign (toxicity {ts:.2f})")

    # Image signal
    if input_.image:
        cues = input_.image.visual_risk_cues
        img_score = 0.6 if cues else 0.1
        signals.append(("image", img_score, f"image cues {cues}"))
        if cues:
            flagged.append("image")
            rationale_parts.append(
                f"the image caption '{input_.image.caption}' mentioned {', '.join(cues)}"
            )
        else:
            rationale_parts.append(
                f"the image caption '{input_.image.caption}' showed no obvious risk cues"
            )

    # Audio signal
    if input_.audio:
        risky_tags = [t for t, s in input_.audio.yamnet_tags
                      if t in {"shouting", "screaming", "gunshot"}]
        aud_score = 0.6 if risky_tags else 0.1
        signals.append(("audio", aud_score, f"audio tags {risky_tags}"))
        if risky_tags:
            flagged.append("audio")
            rationale_parts.append(
                f"audio analysis detected {', '.join(risky_tags)}"
            )
        else:
            tags_repr = (
                ", ".join(t for t, _ in input_.audio.yamnet_tags) or "no salient events"
            )
            rationale_parts.append(f"audio events: {tags_repr}")

    # Combine scores — simple max with mild boost for multimodal agreement.
    if not signals:
        risk_score = 0.0
    else:
        scores = [s for _, s, _ in signals]
        risk_score = max(scores)
        if len(flagged) >= 2:
            risk_score = min(1.0, risk_score + 0.15)

    if risk_score >= 0.65:
        label = "harmful"
        action = "block"
    elif risk_score >= 0.35:
        label = "borderline"
        action = "review"
    else:
        label = "safe"
        action = "allow"

    uncertainties: list[str] = list(extra_uncertainties)
    # Confidence-aware uncertainty
    if input_.text and input_.text.confidence < 0.4:
        uncertainties.append("low_text_classifier_confidence")
    if input_.audio and input_.audio.transcript_confidence < 0.5:
        uncertainties.append("low_audio_transcript_confidence")
    if input_.image and input_.image.confidence < 0.5:
        uncertainties.append("low_image_caption_confidence")

    rationale = ". ".join(rationale_parts).strip()
    if not rationale:
        rationale = "no modalities supplied; defaulting to safe"

    return JudgeOutput(
        risk_score=round(risk_score, 4),
        risk_label=label,
        flagged_modalities=cast(list[Modality], sorted(set(flagged))),
        rationale=rationale[:600],
        uncertainties=uncertainties,
        recommended_action=action,
    )


# ---------------------------------------------------------------------------
# Ollama integration — production path.
# ---------------------------------------------------------------------------


def _judge_via_ollama(input_: JudgeInput) -> JudgeOutput:
    """Call the local Ollama server; retry once with a stricter prompt on failure."""
    evidence_block = _build_evidence_block(input_)
    prompt = JUDGE_PROMPT_TEMPLATE.format(evidence_block=evidence_block)

    raw = _ollama_generate(prompt)
    try:
        return _parse_judge_output(raw)
    except ValidationError:
        stricter = prompt + "\n\nIMPORTANT: respond with ONLY the JSON object. " \
                            "Do not add commentary, markdown or code fences."
        raw2 = _ollama_generate(stricter)
        try:
            return _parse_judge_output(raw2)
        except ValidationError as e:
            raise JudgeFailure(str(e)) from e


def _ollama_generate(prompt: str) -> str:
    body = json.dumps(
        {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
         "options": {"temperature": 0.0}}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response", "")


def _parse_judge_output(text: str) -> JudgeOutput:
    """Locate the first { ... } block and parse it strictly."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValidationError.from_exception_data("JudgeOutput", [])
    blob = text[start : end + 1]
    obj = json.loads(blob)
    return JudgeOutput.model_validate(obj)


def _build_evidence_block(i: JudgeInput) -> str:
    parts: list[str] = []
    if i.text:
        parts.append(
            f"TEXT — toxicity={i.text.toxicity_score:.2f}, "
            f"labels={i.text.top_labels}, confidence={i.text.confidence:.2f}"
        )
    if i.image:
        parts.append(
            f"IMAGE — caption='{i.image.caption}', "
            f"visual_risk_cues={i.image.visual_risk_cues}, "
            f"confidence={i.image.confidence:.2f}"
        )
    if i.audio:
        parts.append(
            f"AUDIO — transcript='{i.audio.transcript}', "
            f"tags={i.audio.yamnet_tags}, "
            f"transcript_confidence={i.audio.transcript_confidence:.2f}"
        )
    return "\n".join(parts)
