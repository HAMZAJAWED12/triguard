"""
Public-dataset loader for TriGuard evaluation (evaluation track T2).

Loads a small, reproducible, binary toxicity sample from a public Hugging Face
dataset for evaluating the text track:

    - Default: ``google/civil_comments`` (CC0 1.0 — public domain). The
      continuous ``toxicity`` score is thresholded at 0.5 to a binary label.
      This is the dataset named in docs/evaluation_protocol.md (T2) and approved
      under the project ethics rules.
    - Optional: ``tweet_eval`` config ``hate`` via ``source="tweet_eval"``.
      NOTE: the hate subset originates from HatEval (SemEval-2019 Task 5) and is
      permission-gated — only use it if you hold that usage agreement. Labels
      are already integers (0 = non-hate, 1 = hate).

Design notes
------------
* The ``datasets`` library is imported lazily inside :func:`load_toxicity_sample`
  so the rest of the package imports cleanly when it is absent, and so plain
  test collection never touches the network (per CLAUDE.md heavy-import rule).
* Loading uses **streaming**: rows are pulled lazily and the iterator stops once
  ``sample_size`` rows are collected, so we never download a whole split. The
  sample is drawn from a seeded buffered shuffle.
* The exact sampled rows are persisted to ``data/t2_samples/*.json``. On the
  machine that produced them (or any checkout that has this file) later runs are
  byte-identical and fully offline. A fresh clone has no cache (the dir is
  gitignored) and re-streams from the Hub; that re-stream is *not* guaranteed
  identical, because the dataset revision is not pinned. The committed evidence
  of a run is its ``outputs/evaluation/<ts>/t2/results.json``.
* Caches (both gitignored, so they do not affect tracked repo size):
  ``data/hf_cache/`` is passed to ``datasets`` as ``cache_dir``; in streaming
  mode the raw shards are fetched via ``huggingface_hub``'s hub cache
  (``~/.cache/huggingface`` or ``$HF_HOME``).
* Nothing here downloads model weights; only dataset rows.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, cast

from pydantic import BaseModel, Field

_log = logging.getLogger("triguard.data.datasets")

# Repo-root-relative locations (gitignored; see .gitignore).
_DATA_DIR = Path("data")
_HF_CACHE_DIR = _DATA_DIR / "hf_cache"
_SAMPLE_CACHE_DIR = _DATA_DIR / "t2_samples"

# Upper bound on rows buffered before the seeded shuffle yields. Larger = more
# representative sample but more rows streamed on the first download. The actual
# buffer scales with sample_size (see below) so small loads stay cheap.
# Reproducible given a fixed seed + sample_size.
_SHUFFLE_BUFFER = 10_000


class LabeledTextSample(BaseModel):
    """One labelled text row from a public toxicity dataset.

    Not part of the protected public schema set (TextEvidence / ImageEvidence /
    AudioEvidence / JudgeInput / JudgeOutput / TriGuardResult); it is internal
    to the evaluation harness.
    """

    text: str = Field(min_length=1)
    label: int = Field(ge=0, le=1)  # 0 = non-toxic, 1 = toxic
    source: str


# ---------------------------------------------------------------------------
# Source registry: how to read each supported dataset.
# ---------------------------------------------------------------------------

_SOURCES: dict[str, dict] = {
    "civil_comments": {
        "hub_id": "google/civil_comments",
        "config": None,
        "text_field": "text",
        "licence": "CC0-1.0",
    },
    "tweet_eval": {
        "hub_id": "tweet_eval",
        "config": "hate",
        "text_field": "text",
        # HatEval (SemEval-2019 Task 5) — permission-gated, not freely public.
        "licence": "permission-required (HatEval)",
    },
}


def _label_from_row(source: str, row: dict) -> int:
    """Map a raw dataset row to a binary 0/1 label.

    Fails loudly if the expected label field is absent — silently defaulting
    would quietly corrupt the evaluation (and its reported numbers) if an
    upstream dataset schema ever changed.
    """
    field = "toxicity" if source == "civil_comments" else "label"
    if row.get(field) is None:
        raise KeyError(
            f"{source}: expected a {field!r} field in the dataset row; "
            f"got keys {sorted(row)}"
        )
    if source == "civil_comments":
        return 1 if float(row["toxicity"]) >= 0.5 else 0
    # tweet_eval/hate (and any source whose label is already an int 0/1)
    return int(row["label"])


def _sample_cache_path(source: str, config: Optional[str], split: str,
                       sample_size: int, seed: int) -> Path:
    cfg = config or "default"
    name = f"{source}_{cfg}_{split}_n{sample_size}_seed{seed}.json"
    return _SAMPLE_CACHE_DIR / name


def _load_cached(path: Path) -> Optional[list[LabeledTextSample]]:
    if not path.exists():
        return None
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        samples = [LabeledTextSample(**r) for r in rows]
        _log.info("loaded %d cached T2 samples from %s", len(samples), path)
        return samples
    except Exception as e:  # corrupt cache -> re-stream rather than crash
        _log.warning("ignoring unreadable sample cache %s (%s)", path, e)
        return None


def _write_cache(path: Path, samples: list[LabeledTextSample]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [s.model_dump() for s in samples]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    _log.info("cached %d T2 samples to %s", len(samples), path)


def load_toxicity_sample(
    *,
    source: str = "civil_comments",
    split: str = "test",
    sample_size: int = 500,
    seed: int = 42,
    cache_dir: Optional[Path] = None,
    force_download: bool = False,
) -> list[LabeledTextSample]:
    """Load a small, reproducible binary toxicity sample.

    Args:
        source: ``"civil_comments"`` (default, CC0) or ``"tweet_eval"``
            (permission-gated HatEval — only with a usage agreement).
        split: dataset split, e.g. ``"test"``, ``"validation"``, ``"train"``.
        sample_size: number of rows to return (fewer if the split is smaller).
        seed: shuffle seed for deterministic sampling.
        cache_dir: passed to ``datasets.load_dataset(cache_dir=...)``
            (default ``data/hf_cache/``, gitignored).
        force_download: ignore the persisted sample cache and re-stream.

    Returns:
        A list of :class:`LabeledTextSample`. Reproducible for fixed
        (source, split, sample_size, seed): the exact rows are persisted under
        ``data/t2_samples/`` and reused offline on subsequent calls.
    """
    if source not in _SOURCES:
        raise ValueError(
            f"unknown source {source!r}; expected one of {sorted(_SOURCES)}"
        )
    meta = _SOURCES[source]

    cache_path = _sample_cache_path(source, meta["config"], split,
                                    sample_size, seed)
    if not force_download:
        cached = _load_cached(cache_path)
        if cached is not None:
            return cached

    if source == "tweet_eval":
        _log.warning(
            "tweet_eval/hate is permission-gated (HatEval); ensure you hold the "
            "usage agreement before using it."
        )

    # Lazy import (CLAUDE.md heavy-import rule): keeps the package importable
    # and test collection offline when `datasets` is not installed.
    from datasets import IterableDataset, load_dataset

    hf_cache = str(cache_dir or _HF_CACHE_DIR)
    _log.info("streaming %s (config=%s, split=%s) ...",
              meta["hub_id"], meta["config"], split)
    if meta["config"]:
        ds = load_dataset(meta["hub_id"], meta["config"], split=split,
                          streaming=True, cache_dir=hf_cache)
    else:
        ds = load_dataset(meta["hub_id"], split=split,
                          streaming=True, cache_dir=hf_cache)

    buffer_size = min(_SHUFFLE_BUFFER, max(sample_size * 20, 1000))
    # streaming=True always yields an IterableDataset (whose .shuffle takes
    # buffer_size); cast so type checkers don't see the load_dataset union.
    ds = cast(IterableDataset, ds).shuffle(seed=seed, buffer_size=buffer_size)

    text_field = meta["text_field"]
    samples: list[LabeledTextSample] = []
    for row in ds:
        text = (row.get(text_field) or "").strip()
        if not text:
            continue  # skip empty rows; LabeledTextSample requires non-empty text
        samples.append(
            LabeledTextSample(
                text=text,
                label=_label_from_row(source, row),
                source=source,
            )
        )
        if len(samples) >= sample_size:
            break

    _write_cache(cache_path, samples)
    return samples
