"""
Slow / download test for the real Hugging Face text tier (unitary/toxic-bert).

Marked @pytest.mark.slow, skipped by default (see tests/conftest.py). Run with:

    PYTHONPATH=src python -m pytest -q --run-slow tests/test_text_model_hf.py

First run downloads ~440 MB of weights to the Hugging Face cache.
"""
from __future__ import annotations

import pytest

from triguard.models import text_model


@pytest.mark.slow
def test_hf_benign_scores_low():
    e = text_model.analyse("Thank you so much, this was a wonderful and kind note", force_mode="hf")
    assert e.raw["mode"] == "real-hf"
    assert e.raw["model_name"] == "unitary/toxic-bert"
    assert e.toxicity_score < 0.3


@pytest.mark.slow
def test_hf_toxic_scores_high():
    e = text_model.analyse("I will kill you, you worthless piece of garbage", force_mode="hf")
    assert e.raw["mode"] == "real-hf"
    assert e.toxicity_score > 0.7
    assert "toxic" in e.top_labels
