"""
Evaluation track T2 — text-side moderation accuracy on a real public dataset.

Runs the *real* text wrapper (``triguard.models.text_model.analyse``) over a
small, reproducible sample of a public toxicity dataset and reports binary
classification metrics: accuracy, macro-F1, per-class precision/recall/F1, a
confusion matrix, and a sample of misclassifications.

The decision rule is ``toxicity_score >= threshold`` (default 0.5).
Classes: ``non-toxic`` (0) / ``toxic`` (1). Both supported datasets are binary
at the label level; the wrapper emits a single ``toxicity_score`` per input, so
a 3-bucket scheme does not apply (see DECISIONS.md D-011).

Metrics are computed without ``sklearn.metrics`` to keep the harness
self-contained, matching ``run_eval.py``.

NEVER invent numbers — only what this run computed is written to disk.

Usage:
    python -m triguard.evaluation.run_t2
    python -m triguard.evaluation.run_t2 --source tweet_eval --sample-size 500 --seed 42
    python -m triguard.evaluation.run_t2 --source civil_comments --split test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..data.datasets import _SOURCES, load_toxicity_sample
from ..models import text_model

# Binary class scheme. Index position encodes the integer label (0/1).
LABELS = ["non-toxic", "toxic"]


def _name(label_int: int) -> str:
    return LABELS[label_int]


def _confusion_matrix(true: list[str], pred: list[str],
                      labels: list[str]) -> dict[str, dict[str, int]]:
    m: dict[str, dict[str, int]] = {a: {b: 0 for b in labels} for a in labels}
    for t, p in zip(true, pred):
        m[t][p] += 1
    return m


def _per_class_metrics(matrix: dict[str, dict[str, int]],
                       labels: list[str]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for cls in labels:
        tp = matrix[cls][cls]
        fn = sum(matrix[cls][c] for c in labels if c != cls)
        fp = sum(matrix[c2][cls] for c2 in labels if c2 != cls)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        out[cls] = {"precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1": round(f1, 4)}
    return out


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TriGuard T2 text-track evaluation")
    p.add_argument("--source", default="civil_comments", choices=sorted(_SOURCES),
                   help="public dataset to evaluate against (default: civil_comments, CC0)")
    p.add_argument("--split", default="test",
                   help="dataset split (default: test)")
    p.add_argument("--sample-size", type=int, default=500,
                   help="max rows to sample (default: 500)")
    p.add_argument("--seed", type=int, default=42,
                   help="shuffle seed for reproducible sampling (default: 42)")
    p.add_argument("--threshold", type=float, default=0.5,
                   help="toxicity_score decision threshold (default: 0.5)")
    p.add_argument("--backend", default="sklearn",
                   choices=["sklearn", "hf", "mock"],
                   help="text wrapper tier to evaluate (default: sklearn)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> Path:
    """Run T2 over a public dataset sample; write results.json; return its path."""
    args = _parse_args(argv)
    started = datetime.now(timezone.utc)

    samples = load_toxicity_sample(
        source=args.source,
        split=args.split,
        sample_size=args.sample_size,
        seed=args.seed,
    )

    true_labels: list[str] = []
    pred_labels: list[str] = []
    failures: list[dict] = []
    wrapper_mode: str | None = None
    classifier: str | None = None
    model_revision: str | None = None

    for s in samples:
        ev = text_model.analyse(s.text, force_mode=args.backend)
        if wrapper_mode is None:
            # ev.raw is a dict at runtime (TextEvidence.raw); pylint mis-types it.
            wrapper_mode = ev.raw.get("mode")  # pylint: disable=no-member
            classifier = (ev.raw.get("classifier")  # pylint: disable=no-member
                          or ev.raw.get("model_name"))  # pylint: disable=no-member
            model_revision = ev.raw.get("model_revision")  # pylint: disable=no-member
        pred_int = 1 if ev.toxicity_score >= args.threshold else 0
        t_name, p_name = _name(s.label), _name(pred_int)
        true_labels.append(t_name)
        pred_labels.append(p_name)
        if pred_int != s.label and len(failures) < 10:
            failures.append({
                "text": s.text[:200],
                "true": s.label,
                "pred": pred_int,
                "score": round(ev.toxicity_score, 4),
            })

    n = len(samples)
    correct = sum(1 for t, p in zip(true_labels, pred_labels) if t == p)
    accuracy = round(correct / n, 4) if n else 0.0
    matrix = _confusion_matrix(true_labels, pred_labels, LABELS)
    per_class = _per_class_metrics(matrix, LABELS)
    macro_f1 = round(sum(v["f1"] for v in per_class.values()) / len(per_class), 4)

    class_balance = {
        cls: sum(1 for t in true_labels if t == cls) for cls in LABELS
    }

    meta = _SOURCES[args.source]
    limitations = [
        "binary scheme (non-toxic / toxic); the source labels carry no "
        "'borderline' band",
    ]
    if args.backend == "sklearn":
        limitations.append(
            "text wrapper is a small sklearn TF-IDF + logistic-regression "
            "baseline trained on 30 bundled examples — a sanity floor, not a "
            "tuned production model"
        )
    elif args.backend == "hf":
        limitations.append(
            f"text wrapper is the pretrained multi-label model "
            f"{classifier or 'unitary/toxic-bert'} (real-hf)"
        )
    if args.source == "civil_comments":
        limitations.append(
            "civil_comments toxicity is a continuous 0..1 crowd rating "
            "thresholded at 0.5 to a binary label; near-threshold items are "
            "inherently ambiguous"
        )
    if args.source == "tweet_eval":
        limitations.append(
            "tweet_eval/hate measures hate-speech specifically; the wrapper is "
            "a general-toxicity baseline, so a domain gap is expected"
        )
    if wrapper_mode == "mock":
        limitations.append(
            f"requested backend '{args.backend}' fell back to mock (backend "
            "unavailable); results do NOT reflect the real model"
        )

    summary = {
        "track": "T2",
        "run_at": started.isoformat(),
        "dataset": {
            "source": args.source,
            "hub_id": meta["hub_id"],
            "config": meta["config"],
            "split": args.split,
        },
        "n_samples": n,
        "class_labels": LABELS,
        "class_balance": class_balance,
        "config": {
            "backend": args.backend,
            "sample_size": args.sample_size,
            "seed": args.seed,
            "threshold": args.threshold,
            "wrapper_mode": wrapper_mode,
            "run_env": os.getenv("TRIGUARD_RUN_ENV") or sys.platform,
        },
        "model_versions": {
            "text_model": classifier or wrapper_mode or "unknown",
            "text_model_revision": model_revision,
        },
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion_matrix": matrix,
        "failures": failures,
        "limitations": limitations,
    }

    out_dir = Path("outputs") / "evaluation" / started.strftime("%Y%m%d-%H%M%S") / "t2"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    # short console summary
    print(f"\nTriGuard T2 text evaluation — {args.source} ({args.split}), {n} samples")
    print(f"Wrapper mode: {wrapper_mode}   threshold: {args.threshold}")
    print(f"Class balance: {class_balance}")
    print(f"Accuracy:  {accuracy:.3f}    Macro-F1: {macro_f1:.3f}")
    for cls, m in per_class.items():
        print(f"  {cls:<11} P={m['precision']:.2f}  R={m['recall']:.2f}  F1={m['f1']:.2f}")
    print(f"Saved to: {out_path}\n")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    main()
