"""Shared rationale-grounding check for evaluation track T7.

Heuristic (not proof): does a judge rationale cite real evidence from the
JudgeInput — a toxicity score, a label, a caption word, a visual cue, an audio
tag — and does it avoid claiming a modality that was not supplied? Used by
`run_t7` to score the LLM judge's explanations.
"""
from __future__ import annotations

import re

from ..orchestrator.schemas import JudgeInput


def evidence_tokens(ji: JudgeInput) -> list[str]:
    """Concrete strings a grounded rationale could legitimately cite."""
    toks: list[str] = []
    if ji.text:
        toks.append(f"{ji.text.toxicity_score:.2f}")
        toks += [lbl.lower() for lbl in ji.text.top_labels]
        toks.append("toxicity")
    if ji.image:
        toks += re.findall(r"[a-z]{4,}", ji.image.caption.lower())
        toks += [c.lower() for c in ji.image.visual_risk_cues]
    if ji.audio:
        toks += [t.lower() for t, _ in ji.audio.yamnet_tags]
        toks += re.findall(r"[a-z]{4,}", ji.audio.transcript.lower())
    seen: set[str] = set()
    out: list[str] = []
    for t in toks:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def grounding_report(ji: JudgeInput, rationale: str) -> dict:
    """Grounded (cites >=1 evidence token) + any invented (unsupplied) modality."""
    low = rationale.lower()
    cited = [t for t in evidence_tokens(ji) if t in low]
    present = {m for m, ev in (("text", ji.text), ("image", ji.image),
                               ("audio", ji.audio)) if ev is not None}
    claimed = {m for m in ("text", "image", "audio") if m in low}
    return {
        "grounded": bool(cited),
        "cited": cited,
        "invented_modalities": sorted(claimed - present),
    }
