"""Fast, offline test for the T6 manifest loader.

Parses the committed manifest and checks item shape. No models, no network — runs
in every environment (unlike the slow real-model harness run).
"""
from __future__ import annotations

from pathlib import Path

from triguard.evaluation.run_t6 import LABELS, T6Item, _load_items

_MANIFEST = (Path(__file__).resolve().parents[1]
             / "data" / "sample_inputs" / "triguard_eval_v1" / "manifest.json")


def test_t6_manifest_loads() -> None:
    items = _load_items(_MANIFEST)
    assert items, "expected at least one item"
    for it in items:
        assert isinstance(it, T6Item)
        assert it.label in LABELS
        assert it.text or it.image or it.audio  # at least one modality
