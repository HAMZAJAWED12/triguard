"""Per-request failures must NOT latch the real tiers off (demo-breaker fix).

A corrupt upload or missing file is a this-request problem; only import/model-
load failures may set the module-level *_BROKEN latches. All offline: the
loaders are monkeypatched, no weights or network involved.
"""
from __future__ import annotations

import numpy as np
import pytest

from triguard.models import audio_model, image_model


def test_image_decode_failure_does_not_latch_blip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(image_model, "_BLIP_BROKEN", False)
    monkeypatch.setattr(image_model, "_blip", lambda: (object(), object()))

    def bad_open(image):
        raise OSError("cannot identify image file")

    monkeypatch.setattr(image_model, "_open_image", bad_open)
    ev = image_model._blip_analyse("data/local_demo/corrupt.png")
    assert ev.raw["mode"] == "mock"
    assert "decode_error" in ev.raw
    assert image_model._BLIP_BROKEN is False  # model stays live


def test_image_model_load_failure_still_latches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(image_model, "_BLIP_BROKEN", False)

    def broken_loader():
        raise ImportError("no transformers")

    monkeypatch.setattr(image_model, "_blip", broken_loader)
    ev = image_model._blip_analyse("data/sample_inputs/blip_test.png")
    assert ev.raw["mode"] == "mock"
    assert image_model._BLIP_BROKEN is True


def test_whisper_clip_failure_does_not_latch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audio_model, "_WHISPER_BROKEN", False)

    class BadModel:
        def transcribe(self, clip, fp16=False):
            raise RuntimeError("weird clip")

    monkeypatch.setattr(audio_model, "_whisper", lambda name: BadModel())
    assert audio_model._transcribe(np.zeros(16000, dtype=np.float32)) is None
    assert audio_model._WHISPER_BROKEN is False


def test_yamnet_clip_failure_does_not_latch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audio_model, "_YAMNET_BROKEN", False)

    def bad_model(chunk):
        raise RuntimeError("bad tensor")

    monkeypatch.setattr(audio_model, "_yamnet", lambda: (bad_model, ["Speech"]))
    assert audio_model._tag(np.zeros(16000, dtype=np.float32)) is None
    assert audio_model._YAMNET_BROKEN is False
