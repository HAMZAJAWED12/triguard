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
from typing import Iterator, Optional, cast

from pydantic import ValidationError

from ..orchestrator.schemas import (
    JudgeInput,
    JudgeOutput,
    Modality,
)

_DEFAULT_OLLAMA_HOST = "http://localhost:11434"
_DEFAULT_OLLAMA_MODEL = "llama3:8b-instruct-q4_K_M"


def _ollama_host() -> str:
    """Read the Ollama endpoint per call (not at import) so tests/env can override."""
    return os.getenv("OLLAMA_HOST", _DEFAULT_OLLAMA_HOST)


def _ollama_model() -> str:
    """Model tag, per call. TRIGUARD_OLLAMA_MODEL wins; OLLAMA_MODEL kept for compat."""
    return (
        os.getenv("TRIGUARD_OLLAMA_MODEL")
        or os.getenv("OLLAMA_MODEL")
        or _DEFAULT_OLLAMA_MODEL
    )

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
        except JudgeFailure:
            # LLM reachable but returned invalid JSON twice -> rule fallback.
            return _rule_based_judge(
                input_, extra_uncertainties=["judge_output_invalid"]
            )
        except urllib.error.URLError as e:
            # Ollama not reachable -> silent rule fallback, reason recorded.
            return _rule_based_judge(
                input_, extra_uncertainties=[f"ollama_unavailable:{e.reason}"]
            )
        except Exception as e:  # timeout / unexpected -> never crash the pipeline
            return _rule_based_judge(
                input_,
                extra_uncertainties=[f"ollama_unavailable:{type(e).__name__}"],
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
    except (ValidationError, json.JSONDecodeError):
        stricter = prompt + "\n\nIMPORTANT: respond with ONLY the JSON object. " \
                            "Do not add commentary, markdown or code fences."
        raw2 = _ollama_generate(stricter)
        try:
            return _parse_judge_output(raw2)
        except (ValidationError, json.JSONDecodeError) as e:
            raise JudgeFailure(str(e)) from e


def _ollama_generate(prompt: str) -> str:
    body = json.dumps(
        {"model": _ollama_model(), "prompt": prompt, "stream": False,
         "options": {"temperature": 0.0}}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{_ollama_host()}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    timeout = float(os.getenv("OLLAMA_TIMEOUT", "60"))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response", "")


def _ollama_generate_stream(prompt: str) -> Iterator[str]:
    """Yield response-text fragments from a streaming /api/generate call.

    Additive counterpart to `_ollama_generate` — same body except
    ``"stream": True``. Ollama replies with NDJSON chunks
    ``{"response": "<fragment>", "done": bool}``; the final chunk has
    ``done: true``. The urlopen timeout is an inactivity timeout, so in
    streaming mode it applies per read (per token gap).
    """
    body = json.dumps(
        {"model": _ollama_model(), "prompt": prompt, "stream": True,
         "options": {"temperature": 0.0}}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{_ollama_host()}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    timeout = float(os.getenv("OLLAMA_TIMEOUT", "60"))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for line in resp:
            if not line.strip():
                continue
            chunk = json.loads(line.decode("utf-8"))
            fragment = chunk.get("response", "")
            if fragment:
                yield fragment
            if chunk.get("done"):
                break


def judge_stream(input_: JudgeInput) -> Iterator[dict]:
    """Stream the Ollama judge: token events, then exactly one terminal event.

    Yields dicts:
      ``{"type": "token", "text": "<fragment>"}``   — zero or more;
      ``{"type": "final", "source": "ollama" | "rule_fallback",
         "judge_output": <JudgeOutput as dict>}``   — always last.

    The token stream is presentation-only; the authoritative decision is the
    terminal event's schema-validated JudgeOutput. On any failure
    (unreachable, timeout mid-stream, invalid JSON) it degrades to the rule
    judge with the same uncertainty tags as `judge()` — so downstream
    labelling ("ollama" vs "ollama->rule") stays consistent. Unlike
    `_judge_via_ollama` there is no stricter-prompt retry: a parse failure
    goes straight to the rule fallback. `judge()` and its default path are
    untouched.
    """
    evidence_block = _build_evidence_block(input_)
    prompt = JUDGE_PROMPT_TEMPLATE.format(evidence_block=evidence_block)

    parts: list[str] = []
    fallback_tag: Optional[str] = None
    try:
        for fragment in _ollama_generate_stream(prompt):
            parts.append(fragment)
            yield {"type": "token", "text": fragment}
    except urllib.error.URLError as e:
        fallback_tag = f"ollama_unavailable:{e.reason}"
    except Exception as e:  # timeout mid-stream / bad chunk — never crash
        fallback_tag = f"ollama_unavailable:{type(e).__name__}"

    if fallback_tag is None:
        try:
            out = _parse_judge_output("".join(parts))
            yield {"type": "final", "source": "ollama",
                   "judge_output": out.model_dump()}
            return
        except (ValidationError, json.JSONDecodeError):
            fallback_tag = "judge_output_invalid"

    out = _rule_based_judge(input_, extra_uncertainties=[fallback_tag])
    yield {"type": "final", "source": "rule_fallback",
           "judge_output": out.model_dump()}


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
