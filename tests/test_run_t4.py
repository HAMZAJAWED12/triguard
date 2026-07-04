"""Slow, opt-in test for the T4 audio-eval loaders (LibriSpeech + ESC-50).

Marked ``slow`` (skipped unless ``--run-slow``). Streams ~5 clips from each set
and asserts the loader shape. SKIPS cleanly (never fails) when the datasets are
unreachable / ``datasets`` is absent, so no CI run depends on the network.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from triguard.data.audio_datasets import (
    ESC50_TO_YAMNET,
    AsrSample,
    EventSample,
    load_esc50_sample,
    load_librispeech_sample,
)


@pytest.mark.slow
def test_t4_loaders_shape() -> None:
    try:
        asr = load_librispeech_sample(sample_size=5, seed=42)
        events = load_esc50_sample(sample_size=5, seed=42)
    except Exception as e:  # offline / datasets missing -> skip, do not fail
        pytest.skip(f"T4 datasets unavailable: {e}")

    assert asr, "expected at least one LibriSpeech clip"
    for s in asr:
        assert isinstance(s, AsrSample)
        assert Path(s.wav_path).exists()
        assert s.reference.strip()

    assert events, "expected at least one ESC-50 clip"
    for s in events:
        assert isinstance(s, EventSample)
        assert Path(s.wav_path).exists()
        assert s.category in ESC50_TO_YAMNET  # only mapped categories are sampled
