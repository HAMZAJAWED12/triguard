# Evaluation Protocol — TriGuard

Eight tracks, each tied to a design question. All outputs saved under `outputs/evaluation/<timestamp>/`.

## Track summary

| ID | Question | Method | Dataset / source | Primary metric |
|---|---|---|---|---|
| T1 | Are wrapper + judge outputs always schema-valid? | pytest with mock + real | synthetic fixtures | % valid JSON, schema-violation count |
| T2 | How accurate is text-side moderation? | offline eval | Civil Comments (public) | macro F1, precision, recall |
| T3 | How accurate is image-text moderation? | offline eval | Hateful Memes (gated access; fallback MMHS150K) | F1, AUROC |
| T4 | How accurate are speech-to-text + audio-event tagging? | offline eval | small AudioSet subset + 20 synthetic clips | WER (Whisper), top-1 (YAMNet) |
| T5 | Does the orchestrator combine evidence correctly? | unit + integration tests with mock wrappers | synthetic fixtures | passing tests; branch coverage > 80 % |
| T6 | How well does the full pipeline behave on tri-modal samples? | run end-to-end | hand-built 50-item set | per-class F1; confusion matrix |
| T7 | Are rationales useful and grounded? | qualitative review (self + 1–2 peers if ethics permits low-risk peer review) | T6 outputs | usefulness rating 1–5; grounding-check % |
| T8 | Is the system viable on consumer hardware? | timed runs | T6 set | p50 / p95 latency (ms); peak RAM; cold-start (s) |

## Per-track detail

### T1 Schema validity
- Run 200 synthetic inputs through both mock and real pipelines.
- Validate each wrapper output against its Pydantic schema; validate each `TriGuardResult` against the result schema.
- Fail the build if validity < 100 %.

### T2 Text component
- Civil Comments (public, English, **CC0 1.0**) — `test` split, sampled.
- **Binary** classification: `non-toxic` (0) / `toxic` (1). The dataset's
  continuous `toxicity` score is thresholded at 0.5 to a label; the text
  wrapper's `toxicity_score` is thresholded at 0.5 to a prediction. (The
  earlier 3-bucket "borderline" framing is dropped — the source labels and the
  wrapper are binary; see DECISIONS.md D-011.)
- Metric: macro F1, plus per-class precision/recall/F1 and a confusion matrix.
- Baseline: the shipped TF-IDF + logistic-regression classifier is the sanity
  floor; a future HF toxicity classifier must beat it.
- Reproducible, capped sample (default 500 rows, seed 42); exact rows cached
  under `data/t2_samples/` for offline reruns.
- `tweet_eval/hate` is available via `--source tweet_eval` but is
  **permission-gated (HatEval)** and not used by default.
- Run:
  `PYTHONPATH=src python -m triguard.evaluation.run_t2 --source civil_comments --sample-size 500 --seed 42`
  → `outputs/evaluation/<timestamp>/t2/results.json`.

### T3 Image-text
- Hateful Memes dev set if access granted.
- Fallback: MMHS150K (Gomez et al. 2020) public split.
- Metric: F1 + AUROC.
- Baseline: text-only on the caption — TriGuard's image-text pipeline must beat caption-only.

### T4 Audio
- AudioSet eval subset: 200 ten-second clips chosen for speech presence.
- Custom synthetic: 20 clips combining clean speech + adversarial audio (shouting, sirens).
- Whisper measured by WER vs ground-truth transcript.
- YAMNet measured by top-1 accuracy against AudioSet ontology.

### T5 Orchestrator logic
- Fixture-driven unit tests:
    - text-only input → only text wrapper called, audio/image fields `None` in `JudgeInput`.
    - all three modalities present + judge returns invalid JSON → orchestrator retries once → if still invalid → `borderline` result with `uncertainties=["judge_output_invalid"]`.
    - one wrapper raises → orchestrator catches and returns evidence with `confidence=0`.
- Coverage measured via `pytest-cov`; target > 80 % branch coverage on `pipeline.py`.

### T6 Full pipeline
- 50-item synthetic set, hand-labelled by me, balanced across:
    - safe / borderline / harmful (≈ 17 each),
    - unimodal vs cross-modal harm,
    - each modality combination (T, I, A, T+I, T+A, I+A, T+I+A).
- Stored under `data/sample_inputs/triguard_eval_v1/`.
- Outputs: confusion matrix per class; per-modality flag accuracy.

### T7 Rationale quality
- Two reviewers (self + one peer, if low-risk peer review is approved under CLAUDE.md §20) score each T6 rationale on:
    - **Usefulness**: 1 (no help) – 5 (decisive help).
    - **Grounding**: % of rationale sentences that cite at least one piece of structured evidence (regex + manual check).
- Inter-rater agreement reported (Cohen's κ) if two reviewers are used.

### T8 Performance
- Hardware reported: CPU model, RAM, GPU (if any), OS.
- Latency measured wall-clock per pipeline call; p50 / p95 over 100 calls on T6 inputs.
- Peak RAM measured via `psutil`.
- Cold-start = time from `python -m triguard.cli run sample.json` to first JSON byte.

## Cross-cutting rules

- **Unimodal baseline comparison**: every multimodal claim is reported alongside its text-only baseline.
- **No fabricated numbers**: each metric in the report links to a JSON in `outputs/evaluation/`.
- **Failure case log**: ≥ 10 representative failures per track, saved under `outputs/evaluation/<ts>/failures/`.
- **Result envelope** stored with every run: `{dataset, n_samples, metrics, timestamp, config, model_versions, limitations, failures}`.
