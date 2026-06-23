"""
Tier-A evaluation harness.

Runs a small hand-built tri-modal evaluation set through the pipeline and
saves per-sample outputs + aggregate metrics under outputs/evaluation/<ts>/.

Metrics (per CLAUDE.md §17 + design Ch10):
    - exact-label accuracy
    - per-class precision/recall/F1 (computed without sklearn to keep the eval
      harness self-contained)
    - confusion matrix
    - p50/p95 latency
    - schema-validity rate (always 100% by construction — Pydantic enforces it)

Usage:
    python -m triguard.evaluation.run_eval
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from ..orchestrator.pipeline import run as run_pipeline
from ..orchestrator.schemas import TriGuardResult

# ---------------------------------------------------------------------------
# Hand-built tri-modal evaluation set
# Labels: safe | borderline | harmful
# ---------------------------------------------------------------------------

EVAL_SET: list[dict] = [
    # ---- safe (text-only) ----
    {"id": "S1", "label": "safe", "text": "Thanks for the help organising the picnic"},
    {"id": "S2", "label": "safe", "text": "The weather was lovely on the hike this morning"},
    {"id": "S3", "label": "safe", "text": "I respectfully disagree but appreciate the input"},
    # ---- safe (multimodal) ----
    {"id": "S4", "label": "safe",
     "text": "Lovely day at the lake",
     "image": "/data/calm_lake_photo.jpg",
     "audio": "/data/calm_speech_lakeside.wav"},
    {"id": "S5", "label": "safe",
     "text": "Studying at the library is so peaceful",
     "image": "/data/quiet_library_books.jpg"},

    # ---- borderline (low-confidence or single-modality risk) ----
    {"id": "B1", "label": "borderline",
     "text": "The food at that place was disgusting"},
    {"id": "B2", "label": "borderline",
     "text": "This service is awful and a waste of money"},
    {"id": "B3", "label": "borderline",
     "image": "/data/photo_with_knife_kitchen.jpg",
     "text": "Nice new kitchen setup"},
    {"id": "B4", "label": "borderline",
     "audio": "/data/loud_speech_argument.wav",
     "text": "We had a heated debate at dinner"},

    # ---- harmful (text-only) ----
    {"id": "H1", "label": "harmful",
     "text": "You are a worthless idiot and nobody likes you"},
    {"id": "H2", "label": "harmful",
     "text": "I hope you suffer for being so pathetic"},
    {"id": "H3", "label": "harmful",
     "text": "Stupid people like you should disappear"},

    # ---- harmful (multimodal) ----
    {"id": "H4", "label": "harmful",
     "text": "You should be afraid to leave your house",
     "image": "/data/scary_gun_photo.jpg",
     "audio": "/data/violent_shout_clip.wav"},
    {"id": "H5", "label": "harmful",
     "text": "I hate everyone like you",
     "image": "/data/photo_with_swastika.jpg"},
]

LABELS = ["safe", "borderline", "harmful"]


def _confusion_matrix(true: list[str], pred: list[str]) -> dict[str, dict[str, int]]:
    m: dict[str, dict[str, int]] = {a: {b: 0 for b in LABELS} for a in LABELS}
    for t, p in zip(true, pred):
        m[t][p] += 1
    return m


def _per_class_metrics(matrix: dict[str, dict[str, int]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for cls in LABELS:
        tp = matrix[cls][cls]
        fn = sum(matrix[cls][c] for c in LABELS if c != cls)
        fp = sum(matrix[c2][cls] for c2 in LABELS if c2 != cls)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        out[cls] = {"precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1": round(f1, 4)}
    return out


def main() -> Path:
    started = datetime.now(timezone.utc)
    results: list[dict] = []
    latencies: list[int] = []
    true_labels: list[str] = []
    pred_labels: list[str] = []

    for item in EVAL_SET:
        r: TriGuardResult = run_pipeline(
            text=item.get("text"),
            image=item.get("image"),
            audio=item.get("audio"),
            judge_mode="rule",
        )
        results.append({
            "id": item["id"],
            "true_label": item["label"],
            "pred_label": r.risk_label,
            "risk_score": r.risk_score,
            "flagged_modalities": r.flagged_modalities,
            "recommended_action": r.recommended_action,
            "rationale": r.rationale,
            "uncertainties": r.uncertainties,
            "latency_ms": r.latency_ms,
        })
        true_labels.append(item["label"])
        pred_labels.append(r.risk_label)
        latencies.append(r.latency_ms)

    correct = sum(1 for t, p in zip(true_labels, pred_labels) if t == p)
    n = len(EVAL_SET)
    accuracy = correct / n
    matrix = _confusion_matrix(true_labels, pred_labels)
    per_class = _per_class_metrics(matrix)
    macro_f1 = round(sum(v["f1"] for v in per_class.values()) / len(per_class), 4)

    p50 = int(statistics.median(latencies))
    p95 = int(sorted(latencies)[int(0.95 * (n - 1))])

    summary = {
        "run_at": started.isoformat(),
        "n_samples": n,
        "judge_mode": "rule",
        "accuracy": round(accuracy, 4),
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion_matrix": matrix,
        "latency_ms": {"p50": p50, "p95": p95,
                       "min": min(latencies), "max": max(latencies)},
        "schema_validity_rate": 1.0,  # enforced by Pydantic
        "limitations": [
            "evaluation set is small (15 hand-built items) and English-only",
            "image and audio wrappers are mocks; image cues are derived from filenames",
            "judge is rule-based; Ollama path is implemented but not measured here",
            "labels reflect the author's judgement; no inter-rater agreement available",
        ],
        "results": results,
    }

    out_dir = Path("outputs") / "evaluation" / started.strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # short console summary
    print(f"\nTriGuard Tier-A evaluation — {n} samples")
    print(f"Accuracy:  {accuracy:.3f}    Macro-F1: {macro_f1:.3f}")
    print(f"Latency:   p50={p50}ms  p95={p95}ms")
    print("Per-class:")
    for cls, m in per_class.items():
        print(f"  {cls:<11} P={m['precision']:.2f}  R={m['recall']:.2f}  F1={m['f1']:.2f}")
    print(f"Saved to: {out_path}\n")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    main()
