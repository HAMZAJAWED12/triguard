"""
TriGuard CLI.

Usage:
    python -m triguard.cli run <sample.json>
    python -m triguard.cli analyse --text "your text here"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .orchestrator.pipeline import run as run_pipeline


def _effective_judge(args: argparse.Namespace) -> str:
    """Subcommand-level --judge wins over the top-level flag."""
    return getattr(args, "judge_sub", None) or args.judge


def _cmd_run(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.path).read_text(encoding="utf-8"))
    result = run_pipeline(
        text=payload.get("text"),
        image=payload.get("image"),
        audio=payload.get("audio"),
        judge_mode=_effective_judge(args),
    )
    print(json.dumps(result.model_dump(), indent=2))
    return 0


def _cmd_analyse(args: argparse.Namespace) -> int:
    result = run_pipeline(
        text=args.text, image=args.image, audio=args.audio,
        judge_mode=_effective_judge(args),
    )
    print(json.dumps(result.model_dump(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="triguard")
    # --judge works both before AND after the subcommand (the after-form is the
    # one people type live; the subparser default of None defers to the parent).
    p.add_argument("--judge", choices=["rule", "ollama"], default="rule",
                   help="judge backend (default: rule)")
    sub = p.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="run a JSON sample through the pipeline")
    run_p.add_argument("path", help="path to a JSON file with text/image/audio")
    run_p.add_argument("--judge", dest="judge_sub",
                       choices=["rule", "ollama"], default=None)
    run_p.set_defaults(func=_cmd_run)

    a_p = sub.add_parser("analyse", help="analyse a single input")
    a_p.add_argument("--text", default=None)
    a_p.add_argument("--image", default=None)
    a_p.add_argument("--audio", default=None)
    a_p.add_argument("--judge", dest="judge_sub",
                     choices=["rule", "ollama"], default=None)
    a_p.set_defaults(func=_cmd_analyse)

    ns = p.parse_args(argv)
    try:
        return ns.func(ns)
    except FileNotFoundError as e:
        print(f"error: file not found: {e.filename or e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON in sample file: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
