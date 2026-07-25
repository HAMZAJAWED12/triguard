"""Evaluation track T6 — full tri-modal pipeline + cross-modal ablation.

Runs a hand-built tri-modal set (`data/sample_inputs/triguard_eval_v1/manifest.json`)
through the pipeline in FOUR conditions and compares each prediction to the item's
holistic ground-truth `label`:

    text-only | image-only | audio-only | multimodal

The thesis metric is multimodal performance vs the best single modality, and in
particular recall on `cross_modal: true` + `harmful` items (harm that emerges only
from the combination). Rule judge (deterministic) for reproducibility; perception
backends honour the usual `TRIGUARD_*_BACKEND` env flags.

NEVER invent numbers. The manifest labels are the evaluation's ground truth; see
the manifest `provenance` field for how it was authored.

Usage (WSL, real backends):
    USE_TF=0 TRIGUARD_TEXT_BACKEND=hf TRIGUARD_IMAGE_BACKEND=blip \
    TRIGUARD_AUDIO_BACKEND=real PYTHONPATH=src \
      python -m triguard.evaluation.run_t6
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from ..orchestrator.pipeline import run as run_pipeline

LABELS = ["safe", "borderline", "harmful"]
CONDITIONS = ["text_only", "image_only", "audio_only", "multimodal"]
_MANIFEST = Path("data/sample_inputs/triguard_eval_v1/manifest.json")


class T6Item(BaseModel):
    id: str
    label: str = Field(pattern="^(safe|borderline|harmful)$")
    cross_modal: bool = False
    text: Optional[str] = None
    image: Optional[str] = None
    audio: Optional[str] = None


def _load_items(path: Path) -> list[T6Item]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = [T6Item(**it) for it in raw["items"]]
    for it in items:
        if it.text is None and it.image is None and it.audio is None:
            raise ValueError(f"item {it.id}: needs at least one modality")
    return items


def _confusion(true: list[str], pred: list[str]) -> dict[str, dict[str, int]]:
    m = {a: {b: 0 for b in LABELS} for a in LABELS}
    for t, p in zip(true, pred):
        m[t][p] += 1
    return m


def _per_class(matrix: dict[str, dict[str, int]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for cls in LABELS:
        tp = matrix[cls][cls]
        fn = sum(matrix[cls][c] for c in LABELS if c != cls)
        fp = sum(matrix[c2][cls] for c2 in LABELS if c2 != cls)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        out[cls] = {"precision": round(precision, 4), "recall": round(recall, 4),
                    "f1": round(f1, 4)}
    return out


def _inputs_for(item: T6Item, condition: str) -> Optional[dict]:
    """Kwargs for pipeline.run for a condition, or None if item lacks that modality."""
    if condition == "text_only":
        return {"text": item.text} if item.text else None
    if condition == "image_only":
        return {"image": item.image} if item.image else None
    if condition == "audio_only":
        return {"audio": item.audio} if item.audio else None
    # multimodal: pass every modality the item has
    kwargs = {}
    if item.text:
        kwargs["text"] = item.text
    if item.image:
        kwargs["image"] = item.image
    if item.audio:
        kwargs["audio"] = item.audio
    return kwargs or None


def _eval_condition(items: list[T6Item], condition: str,
                    judge: str = "rule") -> dict:
    true: list[str] = []
    pred: list[str] = []
    latencies: list[int] = []
    per_item: dict[str, str] = {}
    for item in items:
        kwargs = _inputs_for(item, condition)
        if kwargs is None:
            continue  # item has no input for this condition
        result = run_pipeline(judge_mode=judge, **kwargs)
        true.append(item.label)
        pred.append(result.risk_label)
        latencies.append(result.latency_ms)
        per_item[item.id] = result.risk_label

    n = len(true)
    matrix = _confusion(true, pred)
    per_class = _per_class(matrix)
    macro_f1 = round(sum(v["f1"] for v in per_class.values()) / len(LABELS), 4)
    accuracy = round(sum(1 for t, p in zip(true, pred) if t == p) / n, 4) if n else 0.0
    lat = {}
    if latencies:
        lat = {"p50": int(statistics.median(latencies)),
               "p95": int(sorted(latencies)[int(0.95 * (len(latencies) - 1))]),
               "max": max(latencies)}
    return {
        "n": n, "accuracy": accuracy, "macro_f1": macro_f1,
        "per_class": per_class, "confusion_matrix": matrix,
        "latency_ms": lat, "_pred": per_item,
    }


def _cross_modal_recall(items: list[T6Item], results: dict) -> dict:
    """Recall on cross_modal + harmful items, per condition (the thesis metric)."""
    targets = [it for it in items if it.cross_modal and it.label == "harmful"]
    out: dict[str, object] = {"n_cross_modal_harmful": len(targets)}
    if not targets:
        out["note"] = ("no cross_modal harmful items in the manifest; add "
                       "confounder cases to populate this table")
        return out
    per_condition = {}
    for cond in CONDITIONS:
        preds = results[cond]["_pred"]
        caught = sum(1 for it in targets
                     if preds.get(it.id) == "harmful")
        scored = sum(1 for it in targets if it.id in preds)
        per_condition[cond] = {
            "scored": scored,
            "caught_harmful": caught,
            "recall": round(caught / scored, 4) if scored else None,
        }
    out["recall_by_condition"] = per_condition
    return out


def main(argv: list[str] | None = None) -> Path:
    p = argparse.ArgumentParser(description="TriGuard T6 tri-modal + ablation eval")
    p.add_argument("--manifest", default=str(_MANIFEST))
    p.add_argument("--judge", choices=["rule", "ollama"], default="rule",
                   help="judge for every condition (default rule, reproducible; "
                        "ollama needs a running server and is the interesting "
                        "variant for cross-modal confounder items)")
    args = p.parse_args(argv)
    started = datetime.now(timezone.utc)

    items = _load_items(Path(args.manifest))
    results = {cond: _eval_condition(items, cond, args.judge)
               for cond in CONDITIONS}
    cross = _cross_modal_recall(items, results)

    # strip the internal per-item map from the saved envelope
    for cond in CONDITIONS:
        results[cond].pop("_pred", None)

    manifest_raw = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    summary = {
        "track": "T6",
        "run_at": started.isoformat(),
        "manifest": args.manifest,
        "manifest_provenance": manifest_raw.get("provenance"),
        "config": {
            "judge": args.judge,
            "text_backend": os.getenv("TRIGUARD_TEXT_BACKEND", "sklearn"),
            "image_backend": os.getenv("TRIGUARD_IMAGE_BACKEND", "mock"),
            "audio_backend": os.getenv("TRIGUARD_AUDIO_BACKEND", "mock"),
            "run_env": os.getenv("TRIGUARD_RUN_ENV") or sys.platform,
        },
        "n_items": len(items),
        "class_balance": {c: sum(1 for it in items if it.label == c) for c in LABELS},
        "conditions": results,
        "cross_modal_ablation": cross,
        "limitations": [
            "ground-truth labels come from the project's hand-built manifest; see "
            "manifest_provenance for its authorship and review status",
            "no cross_modal confounder items yet (only two benign committed media "
            "assets); the cross-modal ablation table is empty until such cases are added",
            "small set; indicative, not a benchmark claim",
            "unimodal conditions only score items that have that modality (see each n)",
            ("rule judge (deterministic)" if args.judge == "rule"
             else "ollama/llama3 judge (non-deterministic; falls back to rule "
                  "when unreachable — check model_versions in per-run logs)"),
        ],
    }

    out_dir = Path("outputs") / "evaluation" / started.strftime("%Y%m%d-%H%M%S") / "t6"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    print(f"\nTriGuard T6 tri-modal evaluation — {len(items)} items")
    print(f"{'condition':<12} {'n':>3}  {'acc':>6}  {'macroF1':>7}")
    for cond in CONDITIONS:
        r = results[cond]
        print(f"{cond:<12} {r['n']:>3}  {r['accuracy']:>6}  {r['macro_f1']:>7}")
    print(f"cross_modal harmful items: {cross['n_cross_modal_harmful']}")
    print(f"Saved to: {out_path}\n")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    main()
