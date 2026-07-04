"""Evaluation track T4 — real audio wrapper against public ground truth.

Two honest sub-metrics, computed with the *real* audio wrapper
(``triguard.models.audio_model.analyse(..., force_mode="real")``):

  1. **Whisper WER** on LibriSpeech test-clean (CC BY 4.0). Corpus word error
     rate via ``jiwer`` after a documented normalisation (LibriSpeech references
     are UPPERCASE and unpunctuated; Whisper adds case + punctuation).
  2. **YAMNet event accuracy** on ESC-50 (Piczak 2015, CC BY-NC 3.0, academic
     non-commercial). top-1 and top-5 hit rate against an APPROXIMATE, hand-built
     ESC-50 -> AudioSet display-name map (``ESC50_TO_YAMNET``), recorded verbatim
     in the output as a stated limitation.

NEVER invent numbers — only what this run computed is written to disk.

Usage (WSL, ~/.venv-tri, USE_TF=0):
    PYTHONPATH=src python -m triguard.evaluation.run_t4
    PYTHONPATH=src python -m triguard.evaluation.run_t4 --sample-size 50 --seed 42
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..data.audio_datasets import (
    ESC50_TO_YAMNET,
    load_esc50_sample,
    load_librispeech_sample,
)
from ..models import audio_model

_DATASETS = {
    "librispeech": {
        "hub_id": "openslr/librispeech_asr",
        "config": "clean",
        "split": "test",
        "licence": "CC BY 4.0",
    },
    "esc50": {
        "hub_id": "ashraq/esc50",
        "config": None,
        "split": "train",
        "licence": "CC BY-NC 3.0 (Piczak 2015; non-commercial, academic use)",
    },
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TriGuard T4 audio-track evaluation")
    p.add_argument("--sample-size", type=int, default=50,
                   help="max clips per sub-metric (default: 50)")
    p.add_argument("--seed", type=int, default=42,
                   help="shuffle seed for reproducible sampling (default: 42)")
    return p.parse_args(argv)


def _wer(refs: list[str], hyps: list[str]) -> float:
    """Corpus WER after normalisation (lazy jiwer import)."""
    import jiwer

    tr = jiwer.Compose([
        jiwer.ToLowerCase(),
        jiwer.RemovePunctuation(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.Strip(),
        jiwer.ReduceToListOfListOfWords(),
    ])
    return float(jiwer.wer(refs, hyps,
                           reference_transform=tr, hypothesis_transform=tr))


def _per_clip_wer(ref: str, hyp: str) -> float:
    import jiwer

    tr = jiwer.Compose([
        jiwer.ToLowerCase(),
        jiwer.RemovePunctuation(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.Strip(),
        jiwer.ReduceToListOfListOfWords(),
    ])
    return float(jiwer.wer(ref, hyp,
                           reference_transform=tr, hypothesis_transform=tr))


def _eval_asr(sample_size: int, seed: int) -> dict:
    samples = load_librispeech_sample(sample_size=sample_size, seed=seed)
    refs: list[str] = []
    hyps: list[str] = []
    modes: set[str] = set()
    whisper_model: str | None = None
    per_clip: list[dict] = []

    for s in samples:
        ev = audio_model.analyse(s.wav_path, force_mode="real")
        modes.add(str(ev.raw.get("mode")))
        whisper_model = whisper_model or ev.raw.get("whisper_model")
        hyp = ev.transcript
        refs.append(s.reference)
        hyps.append(hyp)
        per_clip.append({
            "reference": s.reference[:200],
            "hypothesis": hyp[:200],
            "wer": round(_per_clip_wer(s.reference, hyp), 4),
            "mode": ev.raw.get("mode"),
        })

    corpus_wer = round(_wer(refs, hyps), 4) if refs else None
    mean_wer = (round(sum(c["wer"] for c in per_clip) / len(per_clip), 4)
                if per_clip else None)
    worst = sorted(per_clip, key=lambda c: c["wer"], reverse=True)[:10]
    return {
        "n": len(samples),
        "wer_corpus": corpus_wer,
        "wer_mean_per_clip": mean_wer,
        "whisper_model": whisper_model,
        "wrapper_modes": sorted(modes),
        "failures_worst_wer": worst,
    }


def _eval_events(sample_size: int, seed: int) -> dict:
    samples = load_esc50_sample(sample_size=sample_size, seed=seed)
    modes: set[str] = set()
    yamnet_ref: str | None = None
    top1_hits = 0
    top5_hits = 0
    mismatches: list[dict] = []

    for s in samples:
        ev = audio_model.analyse(s.wav_path, force_mode="real")
        modes.add(str(ev.raw.get("mode")))
        yamnet_ref = yamnet_ref or ev.raw.get("yamnet")
        tags = [t for t, _ in ev.yamnet_tags]
        expected = ESC50_TO_YAMNET.get(s.category, [])
        top1 = bool(tags) and tags[0] in expected
        top5 = any(t in expected for t in tags[:5])
        top1_hits += int(top1)
        top5_hits += int(top5)
        if not top5:
            mismatches.append({
                "category": s.category,
                "expected_any_of": expected,
                "yamnet_top5": tags[:5],
            })

    n = len(samples)
    return {
        "n": n,
        "yamnet_top1_rate": round(top1_hits / n, 4) if n else None,
        "yamnet_top5_rate": round(top5_hits / n, 4) if n else None,
        "yamnet_ref": yamnet_ref,
        "wrapper_modes": sorted(modes),
        "categories_used": sorted({s.category for s in samples}),
        "failures_mismatched": mismatches[:10],
    }


def main(argv: list[str] | None = None) -> Path:
    args = _parse_args(argv)
    started = datetime.now(timezone.utc)

    asr = _eval_asr(args.sample_size, args.seed)
    events = _eval_events(args.sample_size, args.seed)

    limitations = [
        "small samples (<= %d clips each); indicative, not a benchmark claim"
        % args.sample_size,
        "evaluation-protocol T4 named an AudioSet subset; AudioSet ships only "
        "YouTube ids (no hosted audio), so LibriSpeech test-clean (WER) and "
        "ESC-50 (event tagging) are used as public, ungated proxies",
        "ESC-50 -> AudioSet label map is APPROXIMATE and hand-built (see "
        "'yamnet_label_map'); only mapped categories are sampled, so top-1 is a "
        "strict lower bound and top-5 is the fairer headline",
        "ESC-50 is CC BY-NC 3.0 (Piczak 2015) — academic non-commercial use only",
        "LibriSpeech is clean read speech; WER here is a best case, not "
        "representative of noisy/adversarial moderation audio",
        "dataset revisions are not pinned; committed evidence is this results.json",
    ]
    if any(m != "real-audio" for m in asr["wrapper_modes"] + events["wrapper_modes"]):
        limitations.append(
            "one or more clips fell back from the real tier (see wrapper_modes); "
            "those rows do not reflect the real model"
        )

    summary = {
        "track": "T4",
        "run_at": started.isoformat(),
        "datasets": _DATASETS,
        "config": {
            "sample_size": args.sample_size,
            "seed": args.seed,
            "run_env": os.getenv("TRIGUARD_RUN_ENV") or sys.platform,
        },
        "model_versions": {
            "whisper_model": asr.get("whisper_model"),
            "yamnet": events.get("yamnet_ref"),
        },
        "whisper_wer": {
            "n": asr["n"],
            "wer_corpus": asr["wer_corpus"],
            "wer_mean_per_clip": asr["wer_mean_per_clip"],
            "wrapper_modes": asr["wrapper_modes"],
        },
        "yamnet_events": {
            "n": events["n"],
            "top1_rate": events["yamnet_top1_rate"],
            "top5_rate": events["yamnet_top5_rate"],
            "categories_used": events["categories_used"],
            "wrapper_modes": events["wrapper_modes"],
        },
        "yamnet_label_map": ESC50_TO_YAMNET,
        "failures": {
            "asr_worst_wer": asr["failures_worst_wer"],
            "yamnet_mismatched": events["failures_mismatched"],
        },
        "limitations": limitations,
    }

    out_dir = Path("outputs") / "evaluation" / started.strftime("%Y%m%d-%H%M%S") / "t4"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    print(f"\nTriGuard T4 audio evaluation")
    print(f"Whisper WER  (LibriSpeech test-clean, n={asr['n']}): "
          f"corpus={asr['wer_corpus']}  mean/clip={asr['wer_mean_per_clip']}  "
          f"({asr['whisper_model']})")
    print(f"YAMNet events (ESC-50, n={events['n']}): "
          f"top1={events['yamnet_top1_rate']}  top5={events['yamnet_top5_rate']}")
    print(f"Saved to: {out_path}\n")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    main()
