"""Public image-text loader for TriGuard evaluation track T3.

Streams a small, reproducible sample from a public, ungated, embedded-image
multimodal set for the image track:

    - `Ahren09/MMSoc_Memotion` — the Memotion (SemEval-2020 Task 8) memes,
      repackaged with images embedded as a Hugging Face `Image` feature (so
      streaming yields image bytes per row — no external zip). Fields used:
      `image` (PIL), `text_corrected`/`text_ocr` (dataset-provided OCR text),
      `offensive` (graded label).

Licence note: Memotion memes are internet memes released for research
(SemEval-2020 Task 8); the images carry third-party copyright, so media is
STREAMED and PERSISTED to a gitignored cache and is NEVER committed. The only
committed evidence is `outputs/evaluation/<ts>/t3/results.json`.

Label rule: binary — `not_offensive` -> 0 (negative), anything else -> 1
(offensive / positive). Design mirrors the T2/T4 loaders: lazy `datasets`/PIL
import, seeded buffered-shuffle streaming, small cap, persisted sample.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, cast

from pydantic import BaseModel, Field

_log = logging.getLogger("triguard.data.image_datasets")

_DATA_DIR = Path("data")
_HF_CACHE_DIR = _DATA_DIR / "hf_cache"
_SAMPLE_DIR = _DATA_DIR / "t3_samples"
_IMG_DIR = _SAMPLE_DIR / "img"

_SHUFFLE_BUFFER = 2000

_SOURCE = {
    "hub_id": "Ahren09/MMSoc_Memotion",
    "config": None,
    "split": "train",
    "licence": "Memotion / SemEval-2020 Task 8 (research use; meme images are "
               "third-party copyright — streamed, never committed)",
}


class LabeledImageTextSample(BaseModel):
    """One Memotion item: persisted image + its OCR text + binary offence label."""

    image_path: str
    text: str = ""            # dataset-provided OCR text; may be empty
    label: int = Field(ge=0, le=1)  # 0 = not_offensive, 1 = offensive


def _binarize_offensive(value: object) -> Optional[int]:
    """not_offensive -> 0; slight/very/hateful_offensive -> 1; unknown -> None."""
    if value is None:
        return None
    s = str(value).strip().lower()
    if not s:
        return None
    return 0 if s.startswith("not") else 1


def _manifest_path(sample_size: int, seed: int) -> Path:
    return _SAMPLE_DIR / f"memotion_train_n{sample_size}_seed{seed}.json"


def _load_manifest(path: Path) -> Optional[list[LabeledImageTextSample]]:
    if not path.exists():
        return None
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        samples = [LabeledImageTextSample(**r) for r in rows]
        if all(Path(s.image_path).exists() for s in samples):
            _log.info("loaded %d cached T3 samples from %s", len(samples), path)
            return samples
        _log.warning("cached images missing for %s; re-streaming", path)
        return None
    except Exception as e:  # corrupt cache -> re-stream rather than crash
        _log.warning("ignoring unreadable T3 manifest %s (%s)", path, e)
        return None


def _write_manifest(path: Path, samples: list[LabeledImageTextSample]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [s.model_dump() for s in samples]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    _log.info("cached %d T3 samples to %s", len(samples), path)


def load_memotion_sample(
    *,
    split: str = "train",
    sample_size: int = 50,
    seed: int = 42,
    force_download: bool = False,
) -> list[LabeledImageTextSample]:
    """Stream a small, reproducible Memotion image-text sample.

    Images are persisted as JPEGs under the gitignored ``data/t3_samples/img/``;
    the manifest holds image path + OCR text + binary label. Reproducible for a
    fixed (sample_size, seed).
    """
    manifest = _manifest_path(sample_size, seed)
    if not force_download:
        cached = _load_manifest(manifest)
        if cached is not None:
            return cached

    from datasets import IterableDataset, load_dataset

    _log.info("streaming %s (%s) ...", _SOURCE["hub_id"], split)
    ds = load_dataset(_SOURCE["hub_id"], split=split, streaming=True,
                      cache_dir=str(_HF_CACHE_DIR))
    ds = cast(IterableDataset, ds).shuffle(seed=seed, buffer_size=_SHUFFLE_BUFFER)

    _IMG_DIR.mkdir(parents=True, exist_ok=True)
    samples: list[LabeledImageTextSample] = []
    for row in ds:
        label = _binarize_offensive(row.get("offensive"))
        img = row.get("image")
        if label is None or img is None:
            continue
        text = (row.get("text_corrected") or row.get("text_ocr") or "").strip()
        img_path = _IMG_DIR / f"clip_{len(samples):03d}.jpg"
        try:
            img.convert("RGB").save(str(img_path), format="JPEG", quality=90)
        except Exception as e:  # undecodable image -> skip
            _log.warning("skipping undecodable image (%s)", e)
            continue
        samples.append(LabeledImageTextSample(
            image_path=str(img_path), text=text, label=label))
        if len(samples) >= sample_size:
            break

    _write_manifest(manifest, samples)
    return samples
