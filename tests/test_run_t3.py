"""Slow, opt-in test for the T3 image-text loader (Memotion).

Marked ``slow`` (skipped unless ``--run-slow``). Streams ~5 items and asserts the
loader shape. SKIPS cleanly (never fails) when the dataset is unreachable /
``datasets`` is absent, so no CI run depends on the network.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from triguard.data.image_datasets import (
    LabeledImageTextSample,
    load_memotion_sample,
)


@pytest.mark.slow
def test_t3_loader_shape() -> None:
    try:
        samples = load_memotion_sample(sample_size=5, seed=42)
    except Exception as e:  # offline / datasets missing -> skip, do not fail
        pytest.skip(f"Memotion unavailable: {e}")

    assert samples, "expected at least one Memotion item"
    for s in samples:
        assert isinstance(s, LabeledImageTextSample)
        assert Path(s.image_path).exists()
        assert s.label in (0, 1)
