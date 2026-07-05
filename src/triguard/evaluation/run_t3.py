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
from ..models import image_model
from ..orchestrator.pipeline import run as run_pipeline

LABELS = ["not_offensive", "offensive"]  # index encodes the 0/1 label


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TriGuard T3 image-text evaluation")
    p.add_argument("--sample-size", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ocr", action="store_true",
                   help="also run the image-only +/-OCR ablation (needs the blip tier + easyocr)")
    return p.parse_args(argv)


def _image_only(samples: list, ocr: bool) -> dict:
    """Image-track-alone pass with OCR on/off.

    The dataset `text` field is deliberately DROPPED here so the metric isolates
    OCR's contribution to the IMAGE track. (Feeding OCR to the text track would be
    redundant on Memotion, whose text field already carries the overlay text.)
    """
    os.environ["TRIGUARD_IMAGE_OCR"] = "1" if ocr else "0"
    true: list[int] = []
    pred: list[int] = []
    scores: list[float] = []
    n_ocr_text = 0
    for s in samples:
        r = run_pipeline(image=s.image_path, judge_mode="rule")
        true.append(s.label)
        pred.append(_predict_positive(r.risk_label))
        scores.append(r.risk_score)
        if r.image_evidence and r.image_evidence.raw.get("ocr_text"):
            n_ocr_text += 1
    m = _prf(true, pred)
    m["auroc"] = _auroc(scores, true)
    m["n_with_ocr_text"] = n_ocr_text
    return m


def _ocr_to_text(samples: list) -> dict:
    """Deployment-real route: OCR the image, feed the extracted text to the TEXT
    track (toxic-bert), no image cues, no dataset text. This is what OCR is *for* —
    reading overlaid words and classifying them, not matching a keyword vocab."""
    os.environ["TRIGUARD_IMAGE_OCR"] = "1"
    true: list[int] = []
    pred: list[int] = []
    scores: list[float] = []
    n_ocr_text = 0
    for s in samples:
        ev = image_model.analyse(s.image_path, force_mode="blip")
        ocr = (ev.raw.get("ocr_text") or "").strip()
        if ocr:
            n_ocr_text += 1
            r = run_pipeline(text=ocr, judge_mode="rule")
            pred.append(_predict_positive(r.risk_label))
            scores.append(r.risk_score)
        else:
            pred.append(0)      # no readable text -> negative
            scores.append(0.0)
        true.append(s.label)
    m = _prf(true, pred)
    m["auroc"] = _auroc(scores, true)
    m["n_with_ocr_text"] = n_ocr_text
    return m


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

    if args.ocr:
        os.environ.setdefault("TRIGUARD_IMAGE_BACKEND", "blip")  # OCR runs in the blip tier
        m_no = _image_only(samples, ocr=False)     # BLIP-caption cues only
        m_cues = _image_only(samples, ocr=True)    # OCR folded into keyword cues
        m_text = _ocr_to_text(samples)             # OCR -> toxic-bert text track
        os.environ.pop("TRIGUARD_IMAGE_OCR", None)
        summary["ocr_ablation"] = {
            "measured_on": "image track alone (dataset text dropped)",
            "image_only_noocr": m_no,
            "image_only_ocr_cues": m_cues,
            "image_only_ocr_to_text": m_text,
            "delta_f1_ocr_to_cues": round(m_cues["f1"] - m_no["f1"], 4),
            "delta_f1_ocr_to_text": round(m_text["f1"] - m_no["f1"], 4),
            "headline": "ocr_to_text",
            "note": ("Two OCR routes vs BLIP-caption-only. Routing OCR text into the "
                     "keyword cues adds ~0 (the vocab rarely matches meme language) — "
                     "a sub-finding. Routing OCR text to the toxic-bert TEXT track is "
                     "the deployment-real path and is the headline. The full-pipeline "
                     "+/-OCR delta is ~0 because Memotion already supplies the overlay "
                     "text in its `text` field."),
        }

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
    if "ocr_ablation" in summary:
        a = summary["ocr_ablation"]
        print("Image-only OCR ablation (dataset text dropped):")
        print(f"  BLIP-caption only    : F1={a['image_only_noocr']['f1']}")
        print(f"  +OCR -> keyword cues : F1={a['image_only_ocr_cues']['f1']}  "
              f"(delta {a['delta_f1_ocr_to_cues']})")
        print(f"  +OCR -> text track   : F1={a['image_only_ocr_to_text']['f1']}  "
              f"(delta {a['delta_f1_ocr_to_text']})  "
              f"[ocr_text on {a['image_only_ocr_to_text']['n_with_ocr_text']}/{n}]")
    print(f"Saved to: {out_path}\n")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    main()
