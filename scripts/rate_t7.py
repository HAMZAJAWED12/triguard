"""Human usefulness ratings for T7 rationales (the blank column in T7).

Two steps, no terminal interaction — you fill the numbers in a text editor.

  1. python scripts/rate_t7.py --init
     Reads the newest committed T7 run and writes data/t7_ratings.json with
     one entry per rationale and "usefulness_1to5": null.

  2. Open data/t7_ratings.json, rate every rationale 1-5, save.
     1 = useless to a moderator, 3 = partly useful, 5 = directly actionable.
     Rate the RATIONALE's usefulness for a human review decision, not whether
     the verdict was right.

  3. python scripts/rate_t7.py --merge
     Validates every rating, then writes a NEW evidence envelope at
     outputs/evaluation/<timestamp>/t7_human/results.json with the per-item
     ratings plus mean/median/distribution. The original T7 run is never
     modified.

The ratings are the author's own judgement; this script only checks and
aggregates them.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_EVAL = _REPO / "outputs" / "evaluation"
_RATINGS = _REPO / "data" / "t7_ratings.json"


def _newest_t7() -> Path:
    runs = sorted(_EVAL.glob("*/t7/results.json"))
    if not runs:
        print("no T7 run found under outputs/evaluation/", file=sys.stderr)
        sys.exit(1)
    return runs[-1]


def _init() -> int:
    src = _newest_t7()
    data = json.loads(src.read_text(encoding="utf-8"))
    items = data.get("per_item", [])
    if not items:
        print(f"{src} has no per_item list", file=sys.stderr)
        return 1
    if _RATINGS.exists():
        print(f"error: {_RATINGS.relative_to(_REPO)} already exists — "
              "delete it first if you want to start over", file=sys.stderr)
        return 1
    out = {
        "source_run": src.parent.parent.name,
        "source_file": src.relative_to(_REPO).as_posix(),
        "judge": data.get("judge"),
        "scale": "1 = useless to a moderator, 3 = partly useful, "
                 "5 = directly actionable",
        "instructions": "Set usefulness_1to5 for every item (integer 1-5), "
                        "then run: python scripts/rate_t7.py --merge",
        "ratings": [
            {"id": it.get("id"),
             "rationale": it.get("rationale"),
             "usefulness_1to5": None}
            for it in items
        ],
    }
    _RATINGS.parent.mkdir(parents=True, exist_ok=True)
    _RATINGS.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {_RATINGS.relative_to(_REPO)} "
          f"({len(items)} rationales from run {out['source_run']})")
    print("now open it, rate every item 1-5, then run --merge")
    return 0


def _merge() -> int:
    if not _RATINGS.exists():
        print(f"error: {_RATINGS.relative_to(_REPO)} not found — run --init "
              "first", file=sys.stderr)
        return 1
    doc = json.loads(_RATINGS.read_text(encoding="utf-8"))
    rows = doc.get("ratings", [])

    problems = []
    scores: list[int] = []
    for r in rows:
        v = r.get("usefulness_1to5")
        if v is None:
            problems.append(f"{r.get('id')}: not rated")
        elif not isinstance(v, int) or not 1 <= v <= 5:
            problems.append(f"{r.get('id')}: {v!r} is not an integer 1-5")
        else:
            scores.append(v)
    if problems:
        print("cannot merge — fix these first:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    started = datetime.now(timezone.utc)
    dist = {str(k): scores.count(k) for k in range(1, 6)}
    envelope = {
        "track": "T7-human",
        "run_at": started.isoformat(),
        "source_run": doc.get("source_run"),
        "source_file": doc.get("source_file"),
        "judge": doc.get("judge"),
        "n": len(scores),
        "scale": doc.get("scale"),
        "mean_usefulness": round(statistics.mean(scores), 4),
        "median_usefulness": statistics.median(scores),
        "distribution": dist,
        "per_item": [{"id": r["id"], "usefulness_1to5": r["usefulness_1to5"],
                      "rationale": r["rationale"]} for r in rows],
        "limitations": [
            "single rater (the author); no inter-rater agreement available",
            "ratings assess rationale usefulness for a human reviewer, not "
            "verdict correctness",
            f"small sample (n={len(scores)}) from one judge run; indicative, "
            "not a benchmark claim",
        ],
    }
    out_dir = _EVAL / started.strftime("%Y%m%d-%H%M%S") / "t7_human"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")

    print(f"wrote {out_path.relative_to(_REPO).as_posix()}")
    print(f"  n={len(scores)}  mean={envelope['mean_usefulness']}  "
          f"median={envelope['median_usefulness']}")
    print(f"  distribution (1..5): {dist}")
    print("commit this file as evidence; the original T7 run is unchanged")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--init", action="store_true",
                   help="create data/t7_ratings.json from the newest T7 run")
    g.add_argument("--merge", action="store_true",
                   help="validate ratings and write the evidence envelope")
    args = p.parse_args(argv)
    return _init() if args.init else _merge()


if __name__ == "__main__":
    sys.exit(main())
