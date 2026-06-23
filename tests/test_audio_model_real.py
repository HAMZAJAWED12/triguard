"""
Slow / model test for the real audio tier (Whisper + YAMNet).

Marked @pytest.mark.slow, skipped by default (see tests/conftest.py). Run with:

    PYTHONPATH=src python -m pytest -q --run-slow tests/test_audio_model_real.py

Needs a committed short public-domain speech clip at
data/sample_inputs/audio_test.wav; the test SKIPS if it is absent (drop one in
to enable). Requires the py3.12 ~/.venv-triguard-audio (Whisper + TensorFlow/YAMNet) — see
scripts/run_wsl_sprint3.sh. Asserts shape only — no hardcoded transcript.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from triguard.models import audio_model

_WAV = Path("data/sample_inputs/audio_test.wav")


@pytest.mark.slow
def test_real_audio_shape():
    if not _WAV.exists():
        pytest.skip(f"no test clip at {_WAV} — drop a public-domain .wav to enable")

    e = audio_model.analyse(str(_WAV), force_mode="real")

    assert e.raw["mode"] in {"real-audio", "real-audio-partial"}
    assert isinstance(e.transcript, str) and e.transcript.strip()
    assert 0.0 <= e.transcript_confidence <= 1.0
    assert isinstance(e.yamnet_tags, list)
    for tag, score in e.yamnet_tags:
        assert isinstance(tag, str) and 0.0 <= score <= 1.0
