"""Public-audio loaders for TriGuard evaluation track T4.

Two small, reproducible, streamed samples for the *real* audio wrapper:

    - LibriSpeech test-clean (ASR / Whisper WER). Licence CC BY 4.0, ungated.
      `openslr/librispeech_asr`, config ``clean``, split ``test``. Fields:
      ``audio`` + ``text`` (UPPERCASE reference).
    - ESC-50 (environmental-sound tagging / YAMNet). Licence CC BY-NC 3.0
      (non-commercial; academic use only). Piczak (2015), "ESC: Dataset for
      Environmental Sound Classification". `ashraq/esc50`, split ``train``.
      Fields: ``audio`` + ``category`` + ``target``.

Design mirrors ``triguard.data.datasets`` (track T2): lazy ``datasets`` import,
seeded buffered-shuffle streaming, small cap, and an offline persisted sample.
Each sampled clip is written as a 16 kHz mono ``.wav`` under the gitignored
``data/t4_samples/`` with a ``manifest.json``; reruns on the same machine are
offline. A fresh clone re-streams (dataset revisions are not pinned) — the
committed evidence of a run is its ``outputs/evaluation/<ts>/t4/results.json``.

Nothing here downloads model weights; only dataset rows.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, cast

from pydantic import BaseModel, Field

_log = logging.getLogger("triguard.data.audio_datasets")

_DATA_DIR = Path("data")
_HF_CACHE_DIR = _DATA_DIR / "hf_cache"
_SAMPLE_DIR = _DATA_DIR / "t4_samples"

_SR = 16000               # Whisper + YAMNet expect 16 kHz mono
_SHUFFLE_BUFFER = 2000


class AsrSample(BaseModel):
    """One LibriSpeech clip: persisted 16 kHz wav + its reference transcript."""

    wav_path: str
    reference: str = Field(min_length=1)


class EventSample(BaseModel):
    """One ESC-50 clip: persisted 16 kHz wav + its ground-truth category."""

    wav_path: str
    category: str
    target: int = Field(ge=0)


# ---------------------------------------------------------------------------
# Approximate ESC-50 category -> YAMNet (AudioSet) display-name map.
# Hand-built and DELIBERATELY partial: only ESC-50 categories with a reasonably
# direct AudioSet equivalent are included, so the YAMNet sample is drawn from
# these categories only. The mapping is APPROXIMATE (AudioSet's ontology is finer
# and overlapping) and is recorded verbatim in results.json as a stated
# limitation, not hidden. A hit = any mapped name appears in YAMNet's top-k.
# ---------------------------------------------------------------------------

ESC50_TO_YAMNET: dict[str, list[str]] = {
    "dog": ["Dog", "Bark", "Bow-wow"],
    "cat": ["Cat", "Meow"],
    "rooster": ["Crowing, cock-a-doodle-doo", "Chicken, rooster", "Fowl"],
    "pig": ["Pig", "Oink"],
    "cow": ["Cattle, bovinae", "Moo"],
    "sheep": ["Sheep", "Bleat"],
    "frog": ["Frog", "Croak"],
    "crow": ["Crow", "Caw"],
    "rain": ["Rain", "Raindrop", "Rain on surface"],
    "sea_waves": ["Ocean", "Waves, surf"],
    "crackling_fire": ["Fire", "Crackle"],
    "crickets": ["Cricket", "Insect"],
    "chirping_birds": ["Bird", "Bird vocalization, bird call, bird song", "Chirp, tweet"],
    "water_drops": ["Drip", "Water"],
    "wind": ["Wind", "Wind noise (microphone)"],
    "thunderstorm": ["Thunderstorm", "Thunder"],
    "crying_baby": ["Baby cry, infant cry", "Crying, sobbing"],
    "sneezing": ["Sneeze"],
    "clapping": ["Clapping", "Hands"],
    "breathing": ["Breathing"],
    "coughing": ["Cough"],
    "footsteps": ["Walk, footsteps"],
    "laughing": ["Laughter"],
    "snoring": ["Snoring"],
    "drinking_sipping": ["Gulp, swallow", "Slurp"],
    "door_wood_knock": ["Knock"],
    "mouse_click": ["Mouse", "Click"],
    "keyboard_typing": ["Typing", "Computer keyboard"],
    "door_wood_creaks": ["Creak"],
    "clock_alarm": ["Alarm", "Alarm clock"],
    "clock_tick": ["Tick", "Tick-tock", "Clock"],
    "glass_breaking": ["Glass", "Shatter"],
    "helicopter": ["Helicopter"],
    "chainsaw": ["Chainsaw"],
    "siren": ["Siren", "Emergency vehicle"],
    "car_horn": ["Vehicle horn, car horn, honking", "Honk"],
    "engine": ["Engine", "Engine starting"],
    "train": ["Train", "Rail transport"],
    "church_bells": ["Church bell", "Bell"],
    "airplane": ["Aircraft", "Fixed-wing aircraft, airplane"],
    "fireworks": ["Fireworks", "Firecracker"],
    "hand_saw": ["Sawing"],
}


def _sample_dir(source: str) -> Path:
    return _SAMPLE_DIR / source


def _manifest_path(source: str, split: str, sample_size: int, seed: int) -> Path:
    return _SAMPLE_DIR / f"{source}_{split}_n{sample_size}_seed{seed}.json"


def _write_wav(array, sr: int, out_path: Path) -> None:
    """Resample to 16 kHz mono and write a wav (lazy soundfile/librosa/numpy)."""
    import librosa
    import numpy as np
    import soundfile as sf

    data = np.asarray(array, dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != _SR:
        data = librosa.resample(data, orig_sr=sr, target_sr=_SR)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), data, _SR)


def _load_manifest(path: Path, model: type[BaseModel]) -> Optional[list]:
    if not path.exists():
        return None
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        samples = [model(**r) for r in rows]
        # a cached manifest is only usable if its wav files still exist
        if all(Path(s.wav_path).exists() for s in samples):  # type: ignore[attr-defined]
            _log.info("loaded %d cached T4 samples from %s", len(samples), path)
            return samples
        _log.warning("cached wavs missing for %s; re-streaming", path)
        return None
    except Exception as e:  # corrupt cache -> re-stream rather than crash
        _log.warning("ignoring unreadable T4 manifest %s (%s)", path, e)
        return None


def _write_manifest(path: Path, samples: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [s.model_dump() for s in samples]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    _log.info("cached %d T4 samples to %s", len(samples), path)


def load_librispeech_sample(
    *,
    split: str = "test",
    config: str = "clean",
    sample_size: int = 50,
    seed: int = 42,
    force_download: bool = False,
) -> list[AsrSample]:
    """Stream a small LibriSpeech test-clean sample for Whisper WER (CC BY 4.0)."""
    manifest = _manifest_path("librispeech", f"{config}_{split}", sample_size, seed)
    if not force_download:
        cached = _load_manifest(manifest, AsrSample)
        if cached is not None:
            return cast(list[AsrSample], cached)

    from datasets import IterableDataset, load_dataset

    _log.info("streaming openslr/librispeech_asr (%s, %s) ...", config, split)
    ds = load_dataset(
        "openslr/librispeech_asr", config, split=split,
        streaming=True, cache_dir=str(_HF_CACHE_DIR),
    )
    ds = cast(IterableDataset, ds).shuffle(seed=seed, buffer_size=_SHUFFLE_BUFFER)

    out_dir = _sample_dir("librispeech")
    samples: list[AsrSample] = []
    for i, row in enumerate(ds):
        ref = (row.get("text") or "").strip()
        audio = row.get("audio") or {}
        if not ref or "array" not in audio:
            continue
        wav = out_dir / f"clip_{len(samples):03d}.wav"
        _write_wav(audio["array"], int(audio["sampling_rate"]), wav)
        samples.append(AsrSample(wav_path=str(wav), reference=ref))
        if len(samples) >= sample_size:
            break

    _write_manifest(manifest, samples)
    return samples


def load_esc50_sample(
    *,
    split: str = "train",
    sample_size: int = 50,
    seed: int = 42,
    force_download: bool = False,
) -> list[EventSample]:
    """Stream a small ESC-50 sample (mapped categories only) for YAMNet tagging.

    ESC-50: Piczak (2015), CC BY-NC 3.0 (non-commercial; academic use only).
    Only clips whose category is in ``ESC50_TO_YAMNET`` are kept, so every clip
    has a documented (approximate) reference AudioSet name.
    """
    manifest = _manifest_path("esc50", split, sample_size, seed)
    if not force_download:
        cached = _load_manifest(manifest, EventSample)
        if cached is not None:
            return cast(list[EventSample], cached)

    from datasets import IterableDataset, load_dataset

    _log.info("streaming ashraq/esc50 (%s) ...", split)
    ds = load_dataset(
        "ashraq/esc50", split=split, streaming=True, cache_dir=str(_HF_CACHE_DIR),
    )
    ds = cast(IterableDataset, ds).shuffle(seed=seed, buffer_size=_SHUFFLE_BUFFER)

    out_dir = _sample_dir("esc50")
    samples: list[EventSample] = []
    for row in ds:
        category = str(row.get("category") or "")
        if category not in ESC50_TO_YAMNET:
            continue  # keep only categories with a documented YAMNet mapping
        audio = row.get("audio") or {}
        if "array" not in audio:
            continue
        wav = out_dir / f"clip_{len(samples):03d}.wav"
        _write_wav(audio["array"], int(audio["sampling_rate"]), wav)
        samples.append(EventSample(
            wav_path=str(wav), category=category, target=int(row.get("target", -1)),
        ))
        if len(samples) >= sample_size:
            break

    _write_manifest(manifest, samples)
    return samples
