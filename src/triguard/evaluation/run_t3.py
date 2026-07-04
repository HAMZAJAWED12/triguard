"""Evaluation track T3 — image-text moderation, flag-vs-label.

Runs the real pipeline (image = BLIP caption + keyword risk-cues; text =
toxic-bert on the dataset's OCR text; rule judge) over a small public Memotion
sample and compares the pipeline's decision to the item's binary offence label.

HONEST FRAMING (also in `limitations`): BLIP is a CAPTIONER, not a hate
classifier, and does NOT OCR the text baked into a meme — so the image track
rarely fires on offensive memes (they are offensive via the words, not by
depicting weapons/blood). The text signal here comes from the DATASET's OCR
field, not from BLIP. So T3 measures how the pipeline's downstream decision flags
labelled positive vs negative items — NOT a trained classifier's F1. Expect
modest numbers with most signal from the text track; that is a real finding,
documented, not hidden.

Decision rule: predicted-positive = `risk_label in {borderline, harmful}`.
Metrics: precision / recall / F1 (positive = offensive), confusion matrix,
accuracy, AUROC over `risk_score`, plus a text-only baseline (image omitted).
Rule judge (deterministic, offline) for reproducibility. NEVER invent numbers.

Usage (WSL, ~/.venv-tri, USE_TF=0):
    TRIGUARD_TEXT_BACKEND=hf TRIGUARD_IMAGE_BACKEND=blip \
    PYTHONPATH=src python -m triguard.evaluation.run_t3 --sample-size 50 --seed 42
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..data.image_datasets import _SOURCE, load_memotion_sample
from ..orchestrator.pipeline import run as run_pipeline

LABELS = ["not_offensive", "offensive"]  # index encodes the 0/1 label


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TriGuard T3 image-text evaluation")
    p.add_argument("--sample-size", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args(argv)


def _confusion(true: list[int], pred: list[int]) -> dict[str, dict[str, int]]:
    m = {a: {b: 0 for b in LABELS} for a in LABELS}
    for t, p in zip(true, pred):
        m[LABELS[t]][LABELS[p]] += 1
    return m


def _prf(true: list[int], pred: list[int]) -> dict[str, float]:
    tp = sum(1 for t, p in zip(true, pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(true, pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(true, pred) if t == 1 and p == 0)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    acc = sum(1 for t, p in zip(true, pred) if t == p) / len(true) if true else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4), "accuracy": round(acc, 4)}


def _auroc(scores: list[float], labels: list[int]) -> float | None:
    """Rank-based AUROC (Mann-Whitney U) with tie-averaged ranks."""
    n = len(scores)
    n_pos = sum(1 for x in labels if x == 1)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    order = sorted(range(n), key=lambda k: scores[k])
    ranks = [0.0] * n
    j = 0
    while j < n:
        k = j
        while k + 1 < n and scores[order[k + 1]] == scores[order[j]]:
            k += 1
        avg = (j + k) / 2.0 + 1.0  # 1-based average rank
        for m in range(j, k + 1):
            ranks[order[m]] = avg
        j = k + 1
    sum_pos = sum(ranks[i] for i in range(n) if labels[i] == 1)
    return round((sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg), 4)


def _predict_positive(label_str: str) -> int:
    return 1 if label_str in {"borderline", "harmful"} else 0


def main(argv: list[str] | None = None) -> Path:
    args = _parse_args(argv)
    started = datetime.now(timezone.utc)

    samples = load_memotion_sample(sample_size=args.sample_size, seed=args.seed)

    true: list[int] = []
    pred: list[int] = []            # full pipeline (image + text)
    scores: list[float] = []
    base_pred: list[int] = []       # text-only baseline
    text_mode: str | None = None
    image_mode: str | None = None
    failures: list[dict] = []

    for s in samples:
        txt = s.text if s.text.strip() else None

        full = run_pipeline(text=txt, image=s.image_path, judge_mode="rule")
        if text_mode is None and full.text_evidence:
            text_mode = full.text_evidence.raw.get("mode")
        if image_mode is None and full.image_evidence:
            image_mode = full.image_evidence.raw.get("mode")
        p = _predict_positive(full.risk_label)

        # text-only baseline (image omitted); no-text items default to negative
        if txt is None:
            bp = 0
        else:
            base = run_pipeline(text=txt, judge_mode="rule")
            bp = _predict_positive(base.risk_label)

        true.append(s.label)
        pred.append(p)
        scores.append(full.risk_score)
        base_pred.append(bp)

        if p != s.label and len(failures) < 10:
            failures.append({
                "label": LABELS[s.label],
                "pred": full.risk_label,
                "risk_score": full.risk_score,
                "caption": (full.image_evidence.caption if full.image_evidence else ""),
                "text": s.text[:160],
            })

    n = len(samples)
    metrics = _prf(true, pred)
    baseline = _prf(true, base_pred)
    summary = {
        "track": "T3",
        "run_at": started.isoformat(),
        "dataset": _SOURCE,
        "config": {
            "sample_size": args.sample_size,
            "seed": args.seed,
            "decision_rule": "predicted_positive = risk_label in {borderline, harmful}",
            "judge": "rule",
            "text_backend": os.getenv("TRIGUARD_TEXT_BACKEND", "sklearn"),
            "image_backend": os.getenv("TRIGUARD_IMAGE_BACKEND", "mock"),
            "run_env": os.getenv("TRIGUARD_RUN_ENV") or sys.platform,
        },
        "model_versions": {"text_mode": text_mode, "image_mode": image_mode},
        "n_samples": n,
        "class_balance": {LABELS[0]: true.count(0), LABELS[1]: true.count(1)},
        "metrics_pipeline": {**metrics, "auroc": _auroc(scores, true)},
        "metrics_text_only_baseline": baseline,
        "confusion_matrix_pipeline": _confusion(true, pred),
        "failures": failures,
        "limitations": [
            "BLIP is a captioner, not a hate classifier, and does not OCR meme "
            "text; the image track rarely fires on offensive memes",
            "text signal comes from the dataset's OCR field (text_corrected/"
            "text_ocr), not from the pipeline's own OCR",
            "this is a flag-vs-label decision measure, NOT a trained-classifier F1",
            "small sample (<= %d); indicative, not a benchmark claim" % args.sample_size,
            "Memotion 'offensive' is graded and crowd-annotated; binarised as "
            "not_offensive -> 0 else 1 (near-threshold items are ambiguous)",
            "meme images are third-party copyright — streamed + persisted to a "
            "gitignored cache, never committed; dataset revision not pinned",
        ],
    }
    if text_mode != "real-hf" or image_mode != "real-blip":
        summary["limitations"].append(
            f"a backend was not the real tier (text_mode={text_mode}, "
            f"image_mode={image_mode}); results do not reflect the real model"
        )

    out_dir = Path("outputs") / "evaluation" / started.strftime("%Y%m%d-%H%M%S") / "t3"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    print(f"\nTriGuard T3 image-text evaluation — Memotion, n={n}")
    print(f"Backends: text={text_mode}  image={image_mode}   judge=rule")
    print(f"Pipeline : P={metrics['precision']}  R={metrics['recall']}  "
          f"F1={metrics['f1']}  acc={metrics['accuracy']}  "
          f"AUROC={summary['metrics_pipeline']['auroc']}")
    print(f"Text-only: P={baseline['precision']}  R={baseline['recall']}  "
          f"F1={baseline['f1']}  acc={baseline['accuracy']}")
    print(f"Saved to: {out_path}\n")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    main()
