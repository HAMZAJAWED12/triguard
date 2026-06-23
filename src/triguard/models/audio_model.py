"""
Audio wrapper for TriGuard.

Two tiers:
    - "mock" (default, offline): deterministic transcript + YAMNet-style tags
      derived from the file name. Lets the orchestrator run without weights.
    - "real" (opt-in): OpenAI Whisper transcription + YAMNet (TF-Hub) audio-event
      tagging. Each component degrades to the mock independently, so a missing
      backend never crashes the pipeline (e.g. Whisper real + YAMNet mock).

force_mode accepts "mock" | "real" | None. None uses TRIGUARD_MOCK=1 (-> mock),
else TRIGUARD_AUDIO_BACKEND in {mock,real}, defaulting to "mock" so the fast
test suite stays offline. Whisper variant via TRIGUARD_WHISPER_MODEL (default
"tiny"; e.g. "small"). Whisper needs ffmpeg on PATH for file decoding.

Real audio needs Python <= 3.12 (TensorFlow / numba have no 3.14 wheels); see
scripts/run_wsl_sprint3.sh which provisions a py3.12 ~/.venv-triguard-audio via uv.
"""
from __future__ import annotations

import io
import logging
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

from ..orchestrator.schemas import AudioEvidence

_log = logging.getLogger("triguard.audio_model")
_WHISPER_BROKEN = False
_YAMNET_BROKEN = False

_YAMNET_URL = "https://tfhub.dev/google/yamnet/1"
_SR = 16000              # YAMNet + Whisper expect 16 kHz mono
_MAX_SECONDS = 60        # clip / chunk window
_TAG_THRESHOLD = 0.2     # YAMNet class score floor
_TOP_K = 5

AudioInput = Union[str, Path, bytes, bytearray]

# Mock vocabulary: filename token -> (yamnet-style label, score).
_AUDIO_TAGS = {
    "shout": ("shouting", 0.7),
    "scream": ("screaming", 0.8),
    "gun": ("gunshot", 0.75),
    "siren": ("siren", 0.6),
    "calm": ("speech", 0.6),
    "speech": ("speech", 0.7),
}


def _resolve_backend(force_mode: Optional[str]) -> str:
    if force_mode:
        return force_mode
    if os.getenv("TRIGUARD_MOCK", "").strip() in {"1", "true", "yes"}:
        return "mock"
    env = os.getenv("TRIGUARD_AUDIO_BACKEND", "").strip().lower()
    return env if env in {"mock", "real"} else "mock"


def _mock_analyse(audio: AudioInput) -> AudioEvidence:
    if isinstance(audio, (bytes, bytearray)):
        return AudioEvidence(
            transcript="(audio provided as raw bytes)",
            transcript_confidence=0.4,
            yamnet_tags=[],
            raw={"mode": "mock", "source": "bytes"},
        )
    path = Path(audio)
    name = path.stem.lower().replace("-", " ").replace("_", " ")
    tags: list[tuple[str, float]] = []
    for token, (label, conf) in _AUDIO_TAGS.items():
        if token in name:
            tags.append((label, conf))
    if "shout" in name or "scream" in name:
        transcript, transcript_conf = "(loud distressed vocalisation)", 0.35
    elif "speech" in name or "calm" in name:
        transcript, transcript_conf = f"sample speech about {name}", 0.6
    else:
        transcript, transcript_conf = f"unclear audio with hints of {name}", 0.45
    return AudioEvidence(
        transcript=transcript,
        transcript_confidence=transcript_conf,
        yamnet_tags=tags,
        raw={"mode": "mock", "path": str(path)},
    )


def _load_waveform(audio: AudioInput):
    """Decode to mono float32 at 16 kHz."""
    import librosa  # lazy
    import numpy as np

    if isinstance(audio, (bytes, bytearray)):
        import soundfile as sf

        data, sr = sf.read(io.BytesIO(bytes(audio)))
        data = data.astype("float32")
        if data.ndim > 1:
            data = data.mean(axis=1)
        if sr != _SR:
            data = librosa.resample(data, orig_sr=sr, target_sr=_SR)
        return data
    wav, _ = librosa.load(str(Path(audio)), sr=_SR, mono=True)
    return wav.astype(np.float32)


@lru_cache(maxsize=2)
def _whisper(model_name: str):
    import whisper  # lazy

    return whisper.load_model(model_name)


def _transcribe(wav):
    """-> (text, confidence, model_name) or None on failure."""
    global _WHISPER_BROKEN
    if _WHISPER_BROKEN:
        return None
    model_name = os.getenv("TRIGUARD_WHISPER_MODEL", "tiny")
    try:
        model = _whisper(model_name)
        clip = wav[: _SR * _MAX_SECONDS]
        result = model.transcribe(clip, fp16=False)
    except Exception as e:  # whisper/numba/ffmpeg missing or failed
        _WHISPER_BROKEN = True
        _log.warning("whisper unavailable (%s); falling back to mock transcript", e)
        return None
    text = (result.get("text") or "").strip()
    segments = result.get("segments") or []
    if segments:
        conf = sum(math.exp(s.get("avg_logprob", -5.0)) for s in segments) / len(segments)
    else:
        conf = 0.0
    return text, max(0.0, min(1.0, round(conf, 4))), model_name


@lru_cache(maxsize=1)
def _yamnet():
    import csv

    import tensorflow as tf  # lazy
    import tensorflow_hub as hub

    model = hub.load(_YAMNET_URL)
    names: list[str] = []
    with tf.io.gfile.GFile(model.class_map_path().numpy()) as f:
        for row in csv.DictReader(f):
            names.append(row["display_name"])
    return model, names


def _tag(wav):
    """-> list[(label, score)] (top-5 > 0.2) or None on failure."""
    global _YAMNET_BROKEN
    if _YAMNET_BROKEN:
        return None
    try:
        import numpy as np

        model, names = _yamnet()
        if len(wav) == 0:
            return []
        win = _SR * _MAX_SECONDS
        chunks = [wav[i:i + win] for i in range(0, len(wav), win)] or [wav]
        agg = None
        for c in chunks:
            scores, _, _ = model(c)
            mean_c = np.mean(scores.numpy(), axis=0)
            agg = mean_c if agg is None else agg + mean_c
        mean = agg / len(chunks)
        order = mean.argsort()[::-1]
        return [
            (names[i], float(round(float(mean[i]), 4)))
            for i in order
            if mean[i] > _TAG_THRESHOLD
        ][:_TOP_K]
    except Exception as e:  # tensorflow/tf-hub missing or failed
        _YAMNET_BROKEN = True
        _log.warning("yamnet unavailable (%s); falling back to mock tags", e)
        return None


def _real_analyse(audio: AudioInput) -> AudioEvidence:
    try:
        wav = _load_waveform(audio)
    except Exception as e:
        _log.warning("audio decode failed (%s); falling back to mock", e)
        return _mock_analyse(audio)

    transcription = _transcribe(wav)
    tags = _tag(wav)
    raw: dict = {"mode": "real-audio"}

    if transcription is None:
        m = _mock_analyse(audio)
        transcript, transcript_conf = m.transcript, m.transcript_confidence
        raw["whisper_fallback"] = True
    else:
        transcript, transcript_conf, wmodel = transcription
        raw["whisper_model"] = wmodel

    if tags is None:
        tags = _mock_analyse(audio).yamnet_tags
        raw["yamnet_fallback"] = True
    else:
        raw["yamnet"] = "yamnet/1"

    if raw.get("whisper_fallback") or raw.get("yamnet_fallback"):
        raw["mode"] = "real-audio-partial"

    return AudioEvidence(
        transcript=transcript or "(no speech detected)",
        transcript_confidence=transcript_conf,
        yamnet_tags=tags,
        raw=raw,
    )


def analyse(audio: AudioInput, *, force_mode: Optional[str] = None) -> AudioEvidence:
    """Transcribe + tag an audio clip.

    force_mode: "mock" | "real" | None. None uses TRIGUARD_MOCK, then
    TRIGUARD_AUDIO_BACKEND, defaulting to "mock" (offline).
    """
    if _resolve_backend(force_mode) == "real":
        return _real_analyse(audio)
    return _mock_analyse(audio)
