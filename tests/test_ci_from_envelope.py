"""Unit test for scripts/ci_from_envelope.py (Wilson score interval, stdlib only).

The expected values below are worked by hand for a small matrix so the test
does not merely re-run the function under test.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO / "scripts" / "ci_from_envelope.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("ci_from_envelope", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


# Small matrix (rows = truth): TP=3, FP=1, FN=1, TN=5  -> n=10.
#   accuracy        k=8,  n=10  (p=0.8)
#   toxic precision k=3,  n=4   (p=0.75)
#   toxic recall    k=3,  n=4   (p=0.75)
#
# Wilson with z=1.959964, z^2=3.841459:
#   accuracy: denom = 1 + 3.841459/10 = 1.3841459
#             centre = (0.8 + 3.841459/20) / 1.3841459 = 0.99207295 / 1.3841459 = 0.7167402
#             half   = 1.959964 * sqrt(0.8*0.2/10 + 3.841459/400) / 1.3841459
#                    = 1.959964 * sqrt(0.016 + 0.0096036) / 1.3841459
#                    = 1.959964 * 0.1600117 / 1.3841459 = 0.2265777
#             -> [0.4902, 0.9433]
#   precision/recall: denom = 1 + 3.841459/4 = 1.9603647
#             centre = (0.75 + 3.841459/8) / 1.9603647 = 1.2301824 / 1.9603647 = 0.6275273
#             half   = 1.959964 * sqrt(0.75*0.25/4 + 3.841459/64) / 1.9603647
#                    = 1.959964 * sqrt(0.046875 + 0.0600228) / 1.9603647
#                    = 1.959964 * 0.3269523 / 1.9603647 = 0.3268854
#             -> [0.3006, 0.9544]
_MATRIX = {"non-toxic": {"non-toxic": 5, "toxic": 1},
           "toxic": {"non-toxic": 1, "toxic": 3}}


def test_wilson_matches_hand_arithmetic():
    mod = _load_module()
    lo, hi = mod.wilson(8, 10)
    assert lo == pytest.approx(0.4902, abs=5e-4)
    assert hi == pytest.approx(0.9433, abs=5e-4)
    lo, hi = mod.wilson(3, 4)
    assert lo == pytest.approx(0.3006, abs=5e-4)
    assert hi == pytest.approx(0.9544, abs=5e-4)


def test_intervals_from_matrix_and_write(tmp_path: Path):
    mod = _load_module()
    res = mod.intervals(_MATRIX)
    assert res["counts"] == {"tp": 3, "fp": 1, "fn": 1, "tn": 5, "n": 10}
    v = res["values"]
    assert (v["accuracy"]["k"], v["accuracy"]["n"]) == (8, 10)
    assert (v["toxic_precision"]["k"], v["toxic_precision"]["n"]) == (3, 4)
    assert (v["toxic_recall"]["k"], v["toxic_recall"]["n"]) == (3, 4)
    assert v["accuracy"]["ci95_low"] == pytest.approx(0.4902, abs=5e-4)
    assert v["toxic_recall"]["ci95_high"] == pytest.approx(0.9544, abs=5e-4)

    # --write puts derived_intervals.json next to the envelope and names its source
    env = tmp_path / "t2" / "results.json"
    env.parent.mkdir()
    env.write_text(json.dumps({"confusion_matrix": _MATRIX, "accuracy": 0.8}), encoding="utf-8")
    assert mod.main([str(env), "--write"]) == 0
    derived = json.loads((env.parent / "derived_intervals.json").read_text(encoding="utf-8"))
    assert derived["method"] == "Wilson score interval, z=1.959964"
    assert derived["derived_from"].endswith("t2/results.json")
    assert derived["values"]["accuracy"]["point"] == 0.8
