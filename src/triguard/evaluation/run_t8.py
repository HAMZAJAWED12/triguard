"""Evaluation track T8 — hardware viability.

Runs the T6 set through the pipeline (multimodal, rule judge) and records
p50/p95 latency, cold-start (first-call) latency, and peak resident memory. Run
it once per backend config to compare mock vs real:

    # mock (offline)
    TRIGUARD_MOCK=1 PYTHONPATH=src python -m triguard.evaluation.run_t8
    # real (WSL ~/.venv-tri)
    USE_TF=0 TRIGUARD_TEXT_BACKEND=hf TRIGUARD_IMAGE_BACKEND=blip \
    TRIGUARD_AUDIO_BACKEND=real PYTHONPATH=src python -m triguard.evaluation.run_t8
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ..orchestrator.pipeline import run as run_pipeline
from .run_t6 import _MANIFEST, _inputs_for, _load_items


def main(argv: list[str] | None = None) -> Path:
    p = argparse.ArgumentParser(description="TriGuard T8 latency + RAM eval")
    p.add_argument("--manifest", default=str(_MANIFEST))
    args = p.parse_args(argv)
    import psutil  # lazy

    started = datetime.now(timezone.utc)
    proc = psutil.Process()
    items = _load_items(Path(args.manifest))

    latencies: list[float] = []
    cold_start_ms: float | None = None
    peak_rss = proc.memory_info().rss
    for item in items:
        kwargs = _inputs_for(item, "multimodal")
        if kwargs is None:
            continue
        t0 = time.perf_counter()
        run_pipeline(judge_mode="rule", **kwargs)
        dt = (time.perf_counter() - t0) * 1000.0
        if cold_start_ms is None:
            cold_start_ms = round(dt, 1)
        latencies.append(dt)
        peak_rss = max(peak_rss, proc.memory_info().rss)

    n = len(latencies)
    lat: dict = {}
    if n:
        ordered = sorted(latencies)
        lat = {
            "p50": round(statistics.median(latencies), 1),
            "p95": round(ordered[int(0.95 * (n - 1))], 1),
            "min": round(min(latencies), 1),
            "max": round(max(latencies), 1),
            "cold_start_ms": cold_start_ms,
        }

    summary = {
        "track": "T8",
        "run_at": started.isoformat(),
        "n": n,
        "config": {
            "judge": "rule",
            "mock": os.getenv("TRIGUARD_MOCK", "") in {"1", "true", "yes"},
            "text_backend": os.getenv("TRIGUARD_TEXT_BACKEND", "sklearn"),
            "image_backend": os.getenv("TRIGUARD_IMAGE_BACKEND", "mock"),
            "audio_backend": os.getenv("TRIGUARD_AUDIO_BACKEND", "mock"),
            "run_env": os.getenv("TRIGUARD_RUN_ENV") or sys.platform,
        },
        "latency_ms": lat,
        "peak_rss_mb": round(peak_rss / (1024 * 1024), 1),
        "note": ("cold_start_ms is the first-call latency (includes model load for "
                 "real backends). Run once per backend config to compare mock vs real."),
    }

    out_dir = Path("outputs") / "evaluation" / started.strftime("%Y%m%d-%H%M%S") / "t8"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\nTriGuard T8 hardware viability — n={n}")
    print(f"latency_ms: {lat}")
    print(f"peak_rss_mb: {summary['peak_rss_mb']}")
    print(f"Saved to: {out_path}\n")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    main()
