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
            versions["text_model"] = "sklearn-tfidf-lr-v1"
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
            versions["image_model"] = "mock-v1"
        except Exception as e:
            log.warning("image wrapper failed: %s", e)
            image_ev = ImageEvidence(
                caption="(error)", visual_risk_cues=[],
                confidence=0.0, raw={"error": str(e)},
            )

    if audio is not None:
        try:
            audio_ev = audio_model.analyse(audio)
            versions["audio_model"] = "mock-v1"
        except Exception as e:
            log.warning("audio wrapper failed: %s", e)
            audio_ev = AudioEvidence(
                transcript="(error)",
                transcript_confidence=0.0,
                yamnet_tags=[],
                raw={"error": str(e)},
            )

    # 2. Judge
    judge_input = JudgeInput(text=text_ev, image=image_ev, audio=audio_ev)
    judge_out = llm_judge.judge(judge_input, force_mode=judge_mode)
    versions["llm_judge"] = "rule-based-v1" if (judge_mode or "rule") == "rule" else "ollama"

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
