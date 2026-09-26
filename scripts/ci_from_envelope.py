"""Wilson 95% intervals for a committed T2 envelope's confusion matrix.

    python scripts/ci_from_envelope.py outputs/evaluation/<run>/t2/results.json
    python scripts/ci_from_envelope.py <results.json> --write   # also writes
        outputs/evaluation/<run>/t2/derived_intervals.json next to the envelope

Reads ONLY `confusion_matrix` (rows = truth, columns = prediction; labels
`non-toxic` / `toxic`) and derives accuracy, toxic precision and toxic recall
with a Wilson score interval (z = 1.959964). Stdlib `math` only. The
envelope itself is never modified; the derived file records where it came
from and how it was computed.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Optional

Z_95 = 1.959964
METHOD = "Wilson score interval, z=1.959964"
_POS = "toxic"
_NEG = "non-toxic"
_REPO = Path(__file__).resolve().parents[1]


def wilson(k: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials.

    centre = (p + z^2/2n) / (1 + z^2/n)
    half   = z * sqrt(p(1-p)/n + z^2/4n^2) / (1 + z^2/n)
    """
    if n <= 0:
        raise ValueError("n must be positive")
    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    return centre - half, centre + half


def counts_from_matrix(matrix: dict) -> dict:
    """TP/FP/FN/TN for the positive class ``toxic`` from a rows=truth matrix."""
    tp = int(matrix[_POS][_POS])
    fn = int(matrix[_POS][_NEG])
    fp = int(matrix[_NEG][_POS])
    tn = int(matrix[_NEG][_NEG])
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "n": tp + fp + fn + tn}


def intervals(matrix: dict, z: float = Z_95) -> dict:
    c = counts_from_matrix(matrix)
    out = {}
    for name, k, n in (
        ("accuracy", c["tp"] + c["tn"], c["n"]),
        ("toxic_precision", c["tp"], c["tp"] + c["fp"]),
        ("toxic_recall", c["tp"], c["tp"] + c["fn"]),
    ):
        lo, hi = wilson(k, n, z)
        out[name] = {"k": k, "n": n, "point": round(k / n, 4),
                     "ci95_low": round(lo, 4), "ci95_high": round(hi, 4)}
    return {"counts": c, "values": out}


def derive(results_path: Path, z: float = Z_95) -> dict:
    env = json.loads(results_path.read_text(encoding="utf-8"))
    res = intervals(env["confusion_matrix"], z)
    try:
        rel = results_path.resolve().relative_to(_REPO).as_posix()
    except ValueError:
        rel = results_path.as_posix()
    return {
        "derived_from": rel,
        "derived_by": "scripts/ci_from_envelope.py",
        "method": METHOD,
        "z": z,
        "positive_class": _POS,
        "confusion_matrix_copied": env["confusion_matrix"],
        "counts": res["counts"],
        "values": res["values"],
        "point_estimates_in_envelope": {
            "accuracy": env.get("accuracy"),
            "toxic_precision": (env.get("per_class") or {}).get(_POS, {}).get("precision"),
            "toxic_recall": (env.get("per_class") or {}).get(_POS, {}).get("recall"),
        },
    }


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Wilson 95% CIs from a T2 results.json")
    p.add_argument("results", help="path to outputs/evaluation/<run>/t2/results.json")
    p.add_argument("--write", action="store_true",
                   help="write derived_intervals.json next to the envelope")
    args = p.parse_args(argv)
    path = Path(args.results)
    d = derive(path)
    print(f"{d['derived_from']}  ({METHOD})")
    for name, v in d["values"].items():
        print(f"  {name:<16} {v['k']:>4}/{v['n']:<4} point={v['point']:.4f}  "
              f"95% CI [{v['ci95_low']:.4f}, {v['ci95_high']:.4f}]")
    if args.write:
        out = path.parent / "derived_intervals.json"
        out.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
        print(f"  wrote {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
