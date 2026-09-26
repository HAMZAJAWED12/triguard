"""Offline test for scripts/build_dataset_cards.py.

Runs the generator into a temp dir and checks that the T2 (Civil Comments)
card's class balance is exactly what the committed toxic-bert envelope
`outputs/evaluation/20260623-124802/t2/results.json` records - the card must
never carry a typed number. Also checks the computed overlap block exists and
that no [STUDENT]-owned field is filled in by the script.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO / "scripts" / "build_dataset_cards.py"
_T2_HF = _REPO / "outputs" / "evaluation" / "20260623-124802" / "t2" / "results.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_dataset_cards", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_t2_card_class_balance_matches_committed_envelope(tmp_path: Path):
    mod = _load_module()
    md_path = mod.main(["--out-dir", str(tmp_path)])
    assert md_path.exists()
    cards = json.loads((tmp_path / "dataset_cards.json").read_text(encoding="utf-8"))["cards"]

    envelope = json.loads(_T2_HF.read_text(encoding="utf-8"))
    t2 = cards["A3"]
    assert t2["hub_id"] == envelope["dataset"]["hub_id"]
    # one distinct class balance across all T2 envelopes, and it equals the committed one
    assert t2["class_balance"] == [envelope["class_balance"]]
    assert t2["n"] == [envelope["n_samples"]]
    assert "20260623-124802" in [e["run_id"] for e in t2["evidence_runs"]]


def test_cards_leave_student_fields_blank_and_compute_overlap(tmp_path: Path):
    mod = _load_module()
    mod.main(["--out-dir", str(tmp_path)])
    payload = json.loads((tmp_path / "dataset_cards.json").read_text(encoding="utf-8"))

    corpus = payload["cards"]["A1"]
    assert corpus["authorship"] is None
    assert corpus["n"] == len(corpus["sentences"]) == 30
    assert corpus["per_label"] == {"non-toxic(0)": 15, "toxic(1)": 15}

    overlap = payload["overlap"]
    names = [b["set"] for b in overlap["vs"]]
    assert names == ["T1 EVAL_SET", "T6 v1 manifest (c8f22a8)", "T6 v2 manifest (HEAD)"]
    for b in overlap["vs"]:
        assert b["exact_lowercase_matches_with_corpus"] == len(b["exact_match_texts"])

    # no --cache-root given -> caches must be reported as not inspected, no path recorded
    assert payload["cache_check"]["status"].startswith("no --cache-root")
    md = (tmp_path / "dataset_cards.md").read_text(encoding="utf-8")
    assert "## For integration" in md and "Table E10" in md and "Table E11" in md
