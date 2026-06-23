"""
Slow / network test for the T2 public-dataset loader.

Marked ``@pytest.mark.slow`` and skipped by default (see tests/conftest.py).
Run explicitly with:

    PYTHONPATH=src python -m pytest -q --run-slow tests/test_t2_dataset.py

It streams ~10 rows of the CC0 civil_comments dataset (the default source) and
asserts the loader's output shape — not specific numbers. ``force_download=True``
bypasses the persisted sample cache so the test always exercises the real
streaming/network path (a cache hit must not masquerade as a passing network
test).
"""
from __future__ import annotations

import pytest

from triguard.data.datasets import LabeledTextSample, load_toxicity_sample


@pytest.mark.slow
def test_load_toxicity_sample_shape():
    samples = load_toxicity_sample(
        source="civil_comments", split="test", sample_size=10, seed=42,
        force_download=True,
    )

    assert isinstance(samples, list)
    assert 1 <= len(samples) <= 10

    for s in samples:
        assert isinstance(s, LabeledTextSample)
        assert isinstance(s.text, str) and s.text.strip()
        assert s.label in {0, 1}
        assert s.source == "civil_comments"
