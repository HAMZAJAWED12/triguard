"""Failure-case analysis (evaluation Prompt 7).

Reads any TriGuard results.json, extracts the misclassified rows (from a
per-sample `results` list or a `failures` list), ranks them by severity, and
writes a top-N markdown table with a failure-class taxonomy:

    * false-positive-harmful : benign item predicted harmful/toxic
    * missed-harmful         : harmful/toxic item predicted safe
    * borderline-drift       : one side is borderline

Usage:
    python -m triguard.evaluation.failure_analysis <results.json> [--top 10]
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

# severity order for label strings (higher = more harmful)
_ORDER = {
    "safe": 0, "non-toxic": 0, "non_toxic": 0, "0": 0,
    "borderline": 1,
    "harmful": 2, "toxic": 2, "1": 2,
}


def _order(label: object) -> int:
    return _ORDER.get(str(label).strip().lower(), 1)


def _taxonomy(true: object, pred: object) -> str:
    t, p = _order(true), _order(pred)
    if t == 1 or p == 1:
        return "borderline-drift"
    if p > t:
        return "false-positive-harmful"
    if p < t:
        return "missed-harmful"
    return "other"


def _rows(data: dict) -> list[dict]:
    """Normalise a results envelope into failure rows (only misclassified)."""
    out: list[dict] = []
    if isinstance(data.get("results"), list):        # run_eval-style per-sample
        for r in data["results"]:
            true = r.get("true_label")
            pred = r.get("pred_label")
            if true is None or pred is None or str(true) == str(pred):
                continue
            out.append({
                "id": r.get("id", ""), "true": true, "pred": pred,
                "risk_score": r.get("risk_score"),
                "flagged": r.get("flagged_modalities"),
                "rationale": r.get("rationale", ""),
                "uncertainties": r.get("uncertainties"),
                "detail": "",
            })
    elif isinstance(data.get("failures"), list):     # T2/T3-style failures list
        for r in data["failures"]:
            true = r.get("true", r.get("label"))
            pred = r.get("pred")
            out.append({
                "id": r.get("id", ""), "true": true, "pred": pred,
                "risk_score": r.get("risk_score", r.get("score")),
                "flagged": None,
                "rationale": "",
                "uncertainties": None,
                "detail": str(r.get("caption") or r.get("text") or "")[:160],
            })
    for r in out:
        r["gap"] = abs(_order(r["true"]) - _order(r["pred"]))
        r["class"] = _taxonomy(r["true"], r["pred"])
    out.sort(key=lambda r: r["gap"], reverse=True)
    return out


def _md(cell: object) -> str:
    return str(cell if cell is not None else "").replace("|", "\\|").replace("\n", " ")


def main(argv: list[str] | None = None) -> Path:
    p = argparse.ArgumentParser(description="TriGuard failure-case analysis")
    p.add_argument("results_json")
    p.add_argument("--top", type=int, default=10)
    args = p.parse_args(argv)

    data = json.loads(Path(args.results_json).read_text(encoding="utf-8"))
    rows = _rows(data)
    started = datetime.now(timezone.utc)
    out_dir = (Path("outputs") / "evaluation"
               / started.strftime("%Y%m%d-%H%M%S") / "failures")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "top10.md"

    lines = [
        f"# Failure-case analysis — {data.get('track', 'results')}",
        "",
        f"Source: `{args.results_json}`  ·  total failures: {len(rows)}",
        "",
        "Taxonomy: **false-positive-harmful** (benign flagged), **missed-harmful** "
        "(harmful missed), **borderline-drift** (a borderline label involved).",
        "",
    ]
    if not rows:
        lines.append("No failures found.")
    else:
        counts: dict[str, int] = {}
        for r in rows:
            counts[r["class"]] = counts.get(r["class"], 0) + 1
        lines.append("Counts: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        lines += ["", "| id | true | pred | class | risk | detail / rationale |",
                  "|---|---|---|---|---|---|"]
        for r in rows[: args.top]:
            detail = r["rationale"] or r["detail"]
            lines.append(
                f"| {_md(r['id'])} | {_md(r['true'])} | {_md(r['pred'])} | "
                f"{_md(r['class'])} | {_md(r['risk_score'])} | {_md(detail)[:180]} |"
            )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"failure analysis: {len(rows)} failures -> {out_path}")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    main()
