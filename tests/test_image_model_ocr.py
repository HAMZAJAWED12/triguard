"""Slow, opt-in test for the opt-in OCR path (RapidOCR) on the image wrapper.

Skips cleanly where rapidocr / the test image is absent (e.g. the Windows offline
venv). Where present, checks OCR reads the known overlay text from the committed
`ocr_test.png` and populates `ImageEvidence.raw["ocr_text"]`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("rapidocr_onnxruntime")

from triguard.models import image_model  # noqa: E402

_IMG = (Path(__file__).resolve().parents[1]
        / "data" / "sample_inputs" / "ocr_test.png")


@pytest.mark.slow
def test_ocr_reads_overlay_text(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _IMG.exists():
        pytest.skip("ocr_test.png missing (generate it first)")
    monkeypatch.setenv("TRIGUARD_IMAGE_OCR", "1")
    ev = image_model.analyse(str(_IMG), force_mode="blip")
    ocr = (ev.raw.get("ocr_text") or "").lower()
    assert ocr, "expected OCR to read some overlay text"
    # the committed test image draws the words DANGER and WEAPON
    assert "weapon" in ocr or "danger" in ocr
    # and the meme text should drive the image risk cues (weapon vocab)
    assert "weapon" in ev.visual_risk_cues
