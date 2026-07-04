"""
Orchestrator: ties the wrappers and judge together.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional, Union

from ..models import audio_model, image_model, llm_judge, text_model
from .schemas import (
    AudioEvidence,
    ImageEvidence,
    JudgeInput,
    TextEvidence,
    TriGuardResult,
)

log = logging.getLogger("triguard.pipeline")

VERSION = "0.1.0-tier-a"

# Single source of truth: evidence raw["mode"] -> canonical backend token.
_MODE_BACKEND = {
    "mock": "mock",
    "real": "sklearn",            # text sklearn tier tags raw["mode"]="real"
    "real-hf": "real-hf",
    "real-blip": "real-blip",
    "real-audio": "real-audio",
    "real-audio-partial": "real-audio-partial",
}
_JUDGE_FALLBACK_TAGS = ("ollama_unavailable", "judge_output_invalid")


def backend_of_mode(mode: Optional[str]) -> str:
    """Canonical backend token for an evidence's raw['mode']."""
    return _MODE_BACKEND.get(mode or "", "unknown")


def _version(ev: Union[TextEvidence, ImageEvidence, AudioEvidence]) -> str:
    """model_versions value reflecting the backend that actually produced ev."""
    raw = ev.raw
    token = backend_of_mode(raw.get("mode"))
    name, rev = raw.get("model_name"), raw.get("model_revision")
    if name and rev:
        return f"{token}:{name}@{str(rev)[:12]}"
    if name:
        return f"{token}:{name}"
    return token


def run(
    *,
    text: Optional[str] = None,
    image: Optional[Union[str, Path]] = None,
    audio: Optional[Union[str, Path]] = None,
    judge_mode: Optional[str] = None,
) -> TriGuardResult:
    """Run the TriGuard pipeline end-to-end.

    All inputs are optional. The orchestrator calls only the wrappers needed.
    """
    if text is None and image is None and audio is None:
        raise ValueError("at least one of text/image/audio must be provided")

    started = time.perf_counter()
    versions: dict[str, str] = {"orchestrator": VERSION}

    # 1. Modality dispatch
    text_ev: Optional[TextEvidence] = None
    image_ev: Optional[ImageEvidence] = None
    audio_ev: Optional[AudioEvidence] = None

    if text is not None:
        try:
            text_ev = text_model.analyse(text)
        except Exception as e:  # never crash the pipeline on a wrapper bug
            log.warning("text wrapper failed: %s", e)
            text_ev = TextEvidence(
                toxicity_score=0.0,
                top_labels=[],
                confidence=0.0,
                raw={"error": str(e)},
            )

    if image is not None:
        try:
            image_ev = image_model.analyse(image)
        except Exception as e:
            log.warning("image wrapper failed: %s", e)
            image_ev = ImageEvidence(
                caption="(error)", visual_risk_cues=[],
                confidence=0.0, raw={"error": str(e)},
            )

    if audio is not None:
        try:
            audio_ev = audio_model.analyse(audio)
        except Exception as e:
            log.warning("audio wrapper failed: %s", e)
            audio_ev = AudioEvidence(
                transcript="(error)",
                transcript_confidence=0.0,
                yamnet_tags=[],
                raw={"error": str(e)},
            )

    # 1b. Record which backend actually produced each evidence (honest versions).
    if text_ev is not None:
        versions["text_model"] = _version(text_ev)
    if image_ev is not None:
        versions["image_model"] = _version(image_ev)
    if audio_ev is not None:
        versions["audio_model"] = _version(audio_ev)

    # 2. Judge
    judge_input = JudgeInput(text=text_ev, image=image_ev, audio=audio_ev)
    judge_out = llm_judge.judge(judge_input, force_mode=judge_mode)
    if (judge_mode or "rule") == "ollama":
        fell_back = any(u.startswith(_JUDGE_FALLBACK_TAGS) for u in judge_out.uncertainties)
        versions["llm_judge"] = "ollama->rule" if fell_back else "ollama"
    else:
        versions["llm_judge"] = "rule"

    # 3. Build final result
    latency_ms = int((time.perf_counter() - started) * 1000)
    return TriGuardResult(
        risk_score=judge_out.risk_score,
        risk_label=judge_out.risk_label,
        flagged_modalities=judge_out.flagged_modalities,
        rationale=judge_out.rationale,
        uncertainties=judge_out.uncertainties,
        recommended_action=judge_out.recommended_action,
        text_evidence=text_ev,
        image_evidence=image_ev,
        audio_evidence=audio_ev,
        latency_ms=latency_ms,
        model_versions=versions,
    )
