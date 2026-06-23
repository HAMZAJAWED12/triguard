"""
Slow / download test for the real BLIP image tier.

Marked @pytest.mark.slow, skipped by default (see tests/conftest.py). Run with:

    PYTHONPATH=src python -m pytest -q --run-slow tests/test_image_model_blip.py

First run downloads ~990 MB of BLIP weights. Uses the committed synthetic
public-domain image data/sample_inputs/blip_test.png. Asserts shape only — no
hardcoded caption string (captions are model-dependent).
"""
from __future__ import annotations

import pytest

from triguard.models import image_model


@pytest.mark.slow
def test_blip_caption_shape():
    e = image_model.analyse("data/sample_inputs/blip_test.png", force_mode="blip")

    assert e.raw["mode"] == "real-blip"
    assert e.raw["model_name"] == "Salesforce/blip-image-captioning-base"
    assert isinstance(e.caption, str) and e.caption.strip()
    assert 0.0 <= e.confidence <= 1.0
    assert isinstance(e.visual_risk_cues, list)
