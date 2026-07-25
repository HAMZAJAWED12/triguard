"""Validate the author's filled confounder set BEFORE merging into manifest.json.

    python scripts/check_confounders.py            # checks the template file
    python scripts/check_confounders.py <file>     # or any candidate JSON

Checks structure, media existence, id collisions against manifest.json, and
the confounder property itself (combination harmful/borderline while every
supplied modality alone is labelled safe). Prints PASS/FAIL per item; exit 1
if anything fails or nothing is filled.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_EVAL_DIR = _REPO / "data" / "sample_inputs" / "triguard_eval_v1"
_DEFAULT = _EVAL_DIR / "confounders_TEMPLATE.json"
_MANIFEST = _EVAL_DIR / "manifest.json"

_LABELS = {"safe", "borderline", "harmful"}


def check(path: Path) -> int:
    raw = json.loads(path.read_text(encoding="utf-8"))
    manifest_ids = {it["id"] for it in
                    json.loads(_MANIFEST.read_text(encoding="utf-8"))["items"]}

    filled = 0
    failed = 0
    for it in raw.get("items", []):
        iid = it.get("id", "?")
        problems: list[str] = []

        # untouched template slot -> skip silently
        if it.get("label") is None and not it.get("text") \
                and not it.get("image") and not it.get("audio"):
            continue
        filled += 1

        if it.get("label") not in {"harmful", "borderline"}:
            problems.append(f"label must be harmful/borderline for a "
                            f"confounder (got {it.get('label')!r})")
        if it.get("cross_modal") is not True:
            problems.append("cross_modal must be true")
        if iid in manifest_ids:
            problems.append("id already exists in manifest.json")

        supplied = [m for m in ("text", "image", "audio") if it.get(m)]
        if len(supplied) < 2:
            problems.append("a confounder needs >=2 modalities "
                            f"(got {supplied or 'none'})")

        uni = it.get("unimodal_labels") or {}
        for m in supplied:
            ul = uni.get(m)
            if ul not in _LABELS:
                problems.append(f"unimodal_labels.{m} missing/invalid ({ul!r})")
            elif ul != "safe":
                problems.append(
                    f"unimodal_labels.{m} = {ul!r}: if a single modality is "
                    "already not safe this is not a confounder — either "
                    "relabel or move the item to the non-confounder set")
        for m in ("text", "image", "audio"):
            if m not in supplied and uni.get(m) is not None:
                problems.append(f"unimodal_labels.{m} set but no {m} supplied")

        for m in ("image", "audio"):
            v = it.get(m)
            if v:
                p = Path(v)
                if not (_REPO / p).is_file() and not p.is_file():
                    problems.append(f"{m} file not found: {v}")
                if "local_demo" in str(v) or "t3_samples" in str(v):
                    problems.append(f"{m} must not reference gitignored media")

        if not it.get("design_note"):
            problems.append("design_note missing (one sentence: why is the "
                            "combination harmful while the parts are benign?)")

        if problems:
            failed += 1
            print(f"FAIL {iid}")
            for pr in problems:
                print(f"     - {pr}")
        else:
            print(f"PASS {iid}")

    if filled == 0:
        print("nothing filled yet — edit confounders_TEMPLATE.json first")
        return 1
    print(f"\n{filled - failed}/{filled} filled items pass")
    if failed == 0:
        print("all good: merge the items into manifest.json (drop the "
              "design_note keys or keep them — the loader ignores extras), "
              "update provenance, then re-run T6 with and without --judge ollama")
    return 1 if failed else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT
    sys.exit(check(target))
