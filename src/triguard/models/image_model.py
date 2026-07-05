"""
Image wrapper for TriGuard.

Two tiers:
    - "mock" (default, offline): deterministic caption + visual risk cues derived
      from the file name. Lets the orchestrator run end-to-end without weights.
    - "blip" (opt-in): real Salesforce/blip-image-captioning-base captioning.
      Downloads ~990 MB weights on first use.

force_mode accepts "mock" | "blip" | None. None uses TRIGUARD_MOCK=1 (-> mock),
else TRIGUARD_IMAGE_BACKEND in {mock,blip}, defaulting to "mock" so the fast
test suite stays offline. The blip tier auto-falls back to mock if transformers/
torch/PIL are missing or loading fails.
"""
from __future__ import annotations

import io
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

from ..orchestrator.schemas import ImageEvidence

_log = logging.getLogger("triguard.image_model")
_BLIP_BROKEN = False

# Pinned BLIP captioning model (Sprint 2).
_BLIP_MODEL = "Salesforce/blip-image-captioning-base"
_BLIP_REVISION = "82a37760796d32b1411fe092ab5d4e227313294b"
_BLIP_CONF_FALLBACK = 0.6   # used only if generation scores are unavailable
_MAX_EDGE = 1024            # downscale long edge before captioning

ImageInput = Union[str, Path, bytes, bytearray]

# Documented keyword vocabulary -> visual_risk_cue category. Scanned as
# substrings of the caption (blip) or the file-name tokens (mock).
_RISK_KEYWORDS: dict[str, str] = {
    "gun": "weapon", "rifle": "weapon", "pistol": "weapon",
    "knife": "weapon", "weapon": "weapon",
    "blood": "violence", "fight": "violence", "punch": "violence",
    "attack": "violence",
    "swastika": "hate_symbol", "nazi": "hate_symbol",
    "syringe": "drug", "needle": "drug", "cocaine": "drug", "drug": "drug",
    "nude": "nudity_warning", "naked": "nudity_warning",
}


def _cues_from_text(text: str) -> list[str]:
    low = text.lower()
    cues: list[str] = []
    for token, cue in _RISK_KEYWORDS.items():
        if token in low and cue not in cues:
            cues.append(cue)
    return cues


def _resolve_backend(force_mode: Optional[str]) -> str:
    if force_mode:
        return force_mode
    if os.getenv("TRIGUARD_MOCK", "").strip() in {"1", "true", "yes"}:
        return "mock"
    env = os.getenv("TRIGUARD_IMAGE_BACKEND", "").strip().lower()
    return env if env in {"mock", "blip"} else "mock"


def _mock_analyse(image: ImageInput) -> ImageEvidence:
    if isinstance(image, (bytes, bytearray)):
        return ImageEvidence(
            caption="an image provided as raw bytes",
            visual_risk_cues=[],
            confidence=0.4,
            raw={"mode": "mock", "source": "bytes"},
        )
    path = Path(image)  # pyright: ignore[reportArgumentType]  # bytes handled above
    name = path.stem.lower().replace("-", " ").replace("_", " ")
    cues = _cues_from_text(name)
    if cues:
        caption = f"an image apparently depicting {', '.join(cues)}"
        confidence = 0.55
    else:
        caption = f"a generic photo described as '{name}'"
        confidence = 0.4
    return ImageEvidence(
        caption=caption,
        visual_risk_cues=cues,
        confidence=confidence,
        raw={"mode": "mock", "path": str(path), "stem_tokens": name.split()},
    )


@lru_cache(maxsize=1)
def _blip():
    """Lazy-import transformers; load BLIP once per process."""
    from transformers import BlipForConditionalGeneration, BlipProcessor

    processor = BlipProcessor.from_pretrained(_BLIP_MODEL, revision=_BLIP_REVISION)
    model = BlipForConditionalGeneration.from_pretrained(
        _BLIP_MODEL, revision=_BLIP_REVISION
    )
    model.eval()
    return processor, model


def _open_image(image: ImageInput):
    from PIL import Image  # lazy

    if isinstance(image, (bytes, bytearray)):
        img = Image.open(io.BytesIO(bytes(image)))
    else:
        img = Image.open(Path(image))
    img = img.convert("RGB")
    img.thumbnail((_MAX_EDGE, _MAX_EDGE))  # in-place, preserves aspect ratio
    return img


def _ocr_enabled() -> bool:
    return os.getenv("TRIGUARD_IMAGE_OCR", "").strip() in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def _ocr_engine():
    """Lazy RapidOCR engine (ONNX runtime; no torch/torchvision, so it cannot
    disturb the pinned torch stack). Downloads small ONNX models on first use."""
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


def _ocr_text(img) -> str:
    """Read overlaid text from a PIL image via RapidOCR; '' on any failure."""
    try:
        import numpy as np

        result, _ = _ocr_engine()(np.array(img))
        if not result:
            return ""
        return " ".join(str(item[1]).strip()
                        for item in result if len(item) > 1 and item[1])
    except Exception as e:  # rapidocr missing / load failed -> no OCR text
        _log.warning("OCR unavailable (%s); skipping", e)
        return ""


def _blip_analyse(image: ImageInput) -> ImageEvidence:
    global _BLIP_BROKEN
    if _BLIP_BROKEN:
        return _mock_analyse(image)
    try:
        processor, model = _blip()
        img = _open_image(image)
    except Exception as e:  # transformers/torch/PIL missing or load failed
        _BLIP_BROKEN = True
        _log.warning("BLIP unavailable (%s); falling back to mock mode", e)
        return _mock_analyse(image)

    import torch  # available once BLIP loaded

    inputs = processor(img, return_tensors="pt")  # pyright: ignore[reportCallIssue]
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=30,
            output_scores=True,
            return_dict_in_generate=True,
        )
    caption = processor.decode(out.sequences[0], skip_special_tokens=True).strip()  # pyright: ignore[reportAttributeAccessIssue]

    # Confidence from generation: mean greedy-token softmax probability.
    confidence = _BLIP_CONF_FALLBACK
    fallback = True
    scores = getattr(out, "scores", None)
    if scores:
        probs = [float(torch.softmax(step[0], dim=-1).max().item()) for step in scores]
        if probs:
            confidence = sum(probs) / len(probs)
            fallback = False
    confidence = max(0.0, min(1.0, round(confidence, 4)))

    # Opt-in OCR (TRIGUARD_IMAGE_OCR=1): read overlaid/meme text and let it drive
    # the image risk cues alongside the caption. Text lands in raw["ocr_text"]
    # (no schema change). Off by default; the orchestrator contract is unchanged.
    ocr = _ocr_text(img) if _ocr_enabled() else ""
    cue_source = f"{caption} {ocr}" if ocr else caption

    raw = {
        "mode": "real-blip",
        "model_name": _BLIP_MODEL,
        "model_revision": _BLIP_REVISION,
        "caption": caption,
    }
    if ocr:
        raw["ocr_text"] = ocr
    if fallback:
        raw["confidence_fallback"] = True

    return ImageEvidence(
        caption=caption or "an unrecognised image",
        visual_risk_cues=_cues_from_text(cue_source),
        confidence=confidence,
        raw=raw,
    )


def analyse(image: ImageInput, *, force_mode: Optional[str] = None) -> ImageEvidence:
    """Caption an image and derive visual risk cues.

    force_mode: "mock" | "blip" | None. None uses TRIGUARD_MOCK, then
    TRIGUARD_IMAGE_BACKEND, defaulting to "mock" (offline).
    """
    backend = _resolve_backend(force_mode)
    if backend == "blip":
        return _blip_analyse(image)
    return _mock_analyse(image)
