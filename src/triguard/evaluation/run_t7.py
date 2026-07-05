"""Evaluation track T7 — rationale grounding (and a slot for human usefulness).

For each item in the T6 set, runs the pipeline and checks whether the judge's
rationale is *grounded* — i.e. cites at least one real piece of evidence from the
JudgeInput (score / label / caption word / cue / tag) and invents no modality.

Headline = the **llama3 / ollama** grounding rate (`--judge ollama`, server up):
that is the judge whose explanation quality is genuinely in question. The rule
judge grounds ~100% by construction (it builds the rationale by concatenating the
evidence it saw), so its rate is reported but noted as trivial.

A per-item `usefulness` (1-5) column is left blank for a human rater to fill (T7
is partly a human-judgement metric).

Usage:
    PYTHONPATH=src python -m triguard.evaluation.run_t7 --judge rule
    OLLAMA_TIMEOUT=300 PYTHONPATH=src python -m triguard.evaluation.run_t7 --judge ollama
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..orchestrator.pipeline import run as run_pipeline
from ..orchestrator.schemas import JudgeInput
from .grounding import grounding_report
from .run_t6 import _MANIFEST, _inputs_for, _load_items


def main(argv: list[str] | None = None) -> Path:
    p = argparse.ArgumentParser(description="TriGuard T7 rationale-grounding eval")
    p.add_argument("--judge", default="rule", choices=["rule", "ollama"])
    p.add_argument("--manifest", default=str(_MANIFEST))
    args = p.parse_args(argv)
    started = datetime.now(timezone.utc)

    items = _load_items(Path(args.manifest))
    per_item: list[dict] = []
    grounded = 0
    invented = 0
    for item in items:
        kwargs = _inputs_for(item, "multimodal")
        if kwargs is None:
            continue
        r = run_pipeline(judge_mode=args.judge, **kwargs)
        ji = JudgeInput(text=r.text_evidence, image=r.image_evidence,
                        audio=r.audio_evidence)
        rep = grounding_report(ji, r.rationale)
        grounded += int(rep["grounded"])
        invented += int(bool(rep["invented_modalities"]))
        per_item.append({
            "id": item.id,
            "grounded": rep["grounded"],
            "cited": rep["cited"],
            "invented_modalities": rep["invented_modalities"],
            "rationale": r.rationale[:200],
            "usefulness_1to5": None,   # human rater fills this
        })

    n = len(per_item)
    summary = {
        "track": "T7",
        "run_at": started.isoformat(),
        "judge": args.judge,
        "n": n,
        "grounding_rate": round(grounded / n, 4) if n else None,
        "invented_modality_count": invented,
        "config": {
            "text_backend": os.getenv("TRIGUARD_TEXT_BACKEND", "sklearn"),
            "image_backend": os.getenv("TRIGUARD_IMAGE_BACKEND", "mock"),
            "audio_backend": os.getenv("TRIGUARD_AUDIO_BACKEND", "mock"),
            "run_env": os.getenv("TRIGUARD_RUN_ENV") or sys.platform,
        },
        "note": ("grounding_rate = fraction of rationales citing >=1 evidence token. "
                 "The rule judge grounds ~1.0 by construction (it concatenates the "
                 "evidence), so the meaningful headline is the ollama/llama3 rate. "
                 "usefulness_1to5 is left blank for a human rater."),
        "per_item": per_item,
    }

    out_dir = Path("outputs") / "evaluation" / started.strftime("%Y%m%d-%H%M%S") / "t7"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\nTriGuard T7 grounding — judge={args.judge}, n={n}")
    print(f"grounding_rate={summary['grounding_rate']}  "
          f"invented_modalities={invented}")
    print(f"Saved to: {out_path}\n")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    main()
