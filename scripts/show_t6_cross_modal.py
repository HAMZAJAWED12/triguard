"""Print the cross-modal ablation block of T6 runs (the thesis metric).

    python scripts/show_t6_cross_modal.py           # newest T6 run
    python scripts/show_t6_cross_modal.py --all     # every T6 run, oldest first
    python scripts/show_t6_cross_modal.py <run_id>  # one specific run

Reads only committed evidence; computes nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_EVAL = _REPO / "outputs" / "evaluation"


def _runs() -> list[Path]:
    return sorted(_EVAL.glob("*/t6/results.json"))


def _show(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    cfg = data.get("config", {})
    print("=" * 70)
    print(f"run:    {path.parent.parent.name}")
    print(f"file:   {path.relative_to(_REPO).as_posix()}")
    print(f"judge:  {cfg.get('judge')}   backends: text={cfg.get('text_backend')} "
          f"image={cfg.get('image_backend')} audio={cfg.get('audio_backend')}")
    print(f"n_items: {data.get('n_items')}   balance: {data.get('class_balance')}")
    print("-- overall (accuracy / macro-F1) --")
    for cond, res in (data.get("conditions") or {}).items():
        print(f"   {cond:<12} n={res.get('n'):<3} "
              f"acc={res.get('accuracy')}  macroF1={res.get('macro_f1')}")
    print("-- cross_modal_ablation --")
    print(json.dumps(data.get("cross_modal_ablation", {}), indent=2))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("run", nargs="?", help="run id (timestamp dir) — default newest")
    p.add_argument("--all", action="store_true", help="show every T6 run")
    args = p.parse_args(argv)

    runs = _runs()
    if not runs:
        print("no T6 results found under outputs/evaluation/", file=sys.stderr)
        return 1
    if args.all:
        for r in runs:
            _show(r)
        return 0
    if args.run:
        match = [r for r in runs if r.parent.parent.name == args.run]
        if not match:
            print(f"no T6 run named {args.run}", file=sys.stderr)
            return 1
        _show(match[0])
        return 0
    _show(runs[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
