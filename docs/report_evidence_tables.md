# Draft-report evidence tables (pre-built, numbers VERBATIM)

Every value below is copied unchanged from the named committed
`outputs/evaluation/<run>/.../results.json`. Do not retype numbers into the
report by hand — copy from here, and cite the run id. If a number is not in
this file, it does not go in the report (CLAUDE.md rule 2). A 195-claim
audit (commit 33ade3d) verified doc-vs-evidence consistency.

Word-count note: tables and their captions do NOT count toward the 9,500
budget — lean on them.

---

## Table E1 — Test suite and integration status (facts, not results.json)

| fact | value | source |
|---|---|---|
| fast test lane (full WSL venv) | 45 passed / 10 skipped, offline | pytest run, 2026-07-06 |
| fast test lane (minimal offline venv) | 33 passed / 11 skipped | pytest run, 2026-07-06 |
| fast test lane (full WSL venv), after D-027/D-028 | 49 passed / 10 skipped, offline | pytest run, 2026-09-24 |
| fast test lane (minimal offline venv), after D-027/D-028 | 37 passed / 11 skipped | pytest run, 2026-09-24 |
| slow-marked real-path tests | 10 (hf, BLIP, OCR, audio, ollama, stream, dataset loaders) | `tests/`, `--run-slow` |
| schema validity | enforced by construction (pydantic v2 models + validators) | `src/triguard/orchestrator/schemas.py` |
| graceful degradation chain | real tier -> mock wrapper -> rule judge, each honestly labelled in `model_versions` | D-016, D-019, D-021, D-025 |

## Table E2 — T1/T5 smoke run (historical, mock pipeline; quote ONLY with its limitations)

Source: `outputs/evaluation/20260623-063735/results.json` (judge=rule).

| metric | value |
|---|---|
| n_samples | 14 |
| accuracy | 1.0 |
| macro-F1 | 1.0 |
| schema_validity_rate | 1.0 |
| latency p50 / p95 / max (ms) | 0 / 0 / 959 |

Limitations (verbatim from the file): small 15-item hand-built English-only
set; image/audio wrappers are mocks (filename cues); rule judge only; single
annotator, no inter-rater agreement. NEVER present the 1.0s as headline
accuracy — they demonstrate wiring, not capability ("achieves perfect" is
banned wording).

## Table E3 — T2 text track: sklearn baseline vs toxic-bert (Civil Comments, n=500, seed 42)

Sources: `outputs/evaluation/20260623-074102/t2/results.json` (sklearn),
`outputs/evaluation/20260623-124802/t2/results.json` (hf). Class balance
468 non-toxic / 32 toxic. Binary at toxicity >= 0.5.

| backend | accuracy | macro-F1 | toxic P | toxic R | toxic F1 |
|---|---|---|---|---|---|
| sklearn TF-IDF + LR (offline floor) | 0.542 | 0.4149 | 0.0809 | 0.5938 | 0.1423 |
| unitary/toxic-bert @4d6c22e7 | 0.928 | 0.6476 | 0.4091 | 0.2812 | 0.3333 |

toxic-bert confusion matrix (rows = truth): non-toxic 455 correct / 13
flagged; toxic 23 missed / 9 caught. Discussion hooks: over-flagging cured
(precision 0.08 -> 0.41) at the cost of recall (0.59 -> 0.28); positive class
tiny (32) so toxic-F1 is noisy; near-threshold crowd labels inherently
ambiguous.

## Table E4 — T3 image-text track (Memotion, n=50, seed 42, rule judge; flag-vs-label decision measure)

Source: `outputs/evaluation/20260705-111002/t3/results.json`. Class balance
18 not_offensive / 32 offensive. Predicted-positive = risk_label in
{borderline, harmful}.

| condition | precision | recall | F1 | accuracy | AUROC |
|---|---|---|---|---|---|
| pipeline (BLIP image + dataset text) | 0.6923 | 0.2812 | 0.4 | 0.46 | 0.566 |
| text-only baseline | 0.6667 | 0.25 | 0.3636 | 0.44 | — |

Pipeline confusion (rows = truth): not_offensive 14 correct / 4 flagged;
offensive 23 missed / 9 caught.

### Table E4b — OCR ablation, image track ALONE (dataset text dropped)

| route | precision | recall | F1 |
|---|---|---|---|
| BLIP caption only | 1.0 | 0.0312 | 0.0606 |
| + OCR -> keyword cues | 1.0 | 0.0312 | 0.0606 |
| + OCR -> toxic-bert text track | 0.7143 | 0.3125 | 0.4348 |

delta F1 (OCR->text route) = 0.3742 — the chapter's headline T3 finding.
Keyword-cue route adds 0.0 (vocab mismatch with meme language — sub-finding).
Full-pipeline ±OCR delta is ~0 only because Memotion pre-supplies overlay
text in its `text` field. Caveats: BLIP is a captioner, not a hate
classifier; n=50 indicative, not a benchmark claim; meme images third-party
copyright, streamed and never committed.

## Table E5 — T4 audio track (public proxies, n=50 each, seed 42)

Source: `outputs/evaluation/20260704-153729/t4/results.json`. Whisper `tiny`,
YAMNet `yamnet/1`, both wrapper modes `real-audio`.

| sub-metric | dataset | value |
|---|---|---|
| Whisper WER (corpus) | LibriSpeech test-clean (CC BY 4.0) | 0.0971 |
| Whisper WER (mean per clip) | LibriSpeech test-clean | 0.1314 |
| YAMNet top-1 (strict lower bound) | ESC-50 (CC BY-NC 3.0), 29 mapped categories | 0.32 |
| YAMNet top-5 (fair headline) | ESC-50 | 0.66 |

Caveats: AudioSet (protocol plan) ships only YouTube ids — LibriSpeech/ESC-50
are documented public substitutes (D-017); clean read speech = best case;
ESC-50->AudioSet label map is approximate and hand-built.

## Table E6 — T6 tri-modal ablation, v2 student-owned set (n=24, real hf+blip+real-audio, rule judge)

Source: `outputs/evaluation/20260705-160858/t6/results.json`. Class balance
10 safe / 6 borderline / 8 harmful. Manifest provenance: AI-assisted draft,
reviewed/edited/approved by the author (2026-07-05).

| condition | n | accuracy | macro-F1 | safe F1 | borderline F1 | harmful F1 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|
| text only | 22 | 0.5909 | 0.4786 | 0.6667 | 0.0 | 0.7692 | 60 | 70 |
| image only | 8 | 0.5 | 0.2222 | 0.6667 | 0.0 | 0.0 | 3958 | 5114 |
| audio only | 6 | 0.5 | 0.2222 | 0.6667 | 0.0 | 0.0 | 832 | 1131 |
| multimodal | 24 | 0.625 | 0.4945 | 0.7143 | 0.0 | 0.7692 | 160 | 6436 |

cross_modal_ablation: n_cross_modal_harmful = 0 (no confounder items — the
thesis-metric table is empty; honest future work). Discussion hooks:
multimodal >= every unimodal condition; borderline F1 = 0.0 across ALL
conditions — mild-incivility items score below the rule judge's 0.35
threshold (toxic-bert rates them weakly toxic); harmful recall 0.625 with
precision 1.0 (overt abuse caught, no false harmful).

### Table E6b — T6 v1 AI-drafted starter set (n=18; HISTORICAL — superseded by v2, cite only as method evolution)

Source: `outputs/evaluation/20260704-221056/t6/results.json`. Balance 8/4/6.

| condition | n | accuracy | macro-F1 |
|---|---|---|---|
| text only | 16 | 0.75 | 0.6746 |
| image only | 5 | 0.6 | 0.25 |
| audio only | 4 | 0.5 | 0.2222 |
| multimodal | 18 | 0.7778 | 0.6852 |

v2 scores lower than v1 because v2's borderline items are milder — a finding
about pipeline recall on mild incivility, not a set defect (D-026).

## Table E7 — T7 rationale grounding (llama3 judge, v1 set n=18)

Source: `outputs/evaluation/20260705-113456/t7/results.json`.

| metric | value |
|---|---|
| grounding rate (>=1 real evidence token cited) | 1.0 (18/18) |
| invented (unsupplied) modalities cited | 0 |

Caveats: floor metric (cites >= 1 token; not completeness/quality); rule
judge grounds ~1.0 BY CONSTRUCTION and was not separately measured — the
llama3 rate is the meaningful number; human usefulness_1to5 column still
blank (state as future work, or rate the 18 items before submission).

## Table E8 — T8 latency & memory (T6 set, rule judge, per backend config)

Sources: `outputs/evaluation/20260705-113354/t8/` (mock, win32),
`outputs/evaluation/20260705-113639/t8/` (real, WSL).

| config | p50 ms | p95 ms | cold-start ms | peak RSS MB |
|---|---|---|---|---|
| mock (sklearn/mock/mock) | 0.0 | 0.1 | 0.1 | 34.5 |
| real (hf/blip/real-audio) | 31.1 | 4075.1 | 4075.1 | 2873.7 |

Context numbers for the LLM judge (from D-015/D-025 live runs, not T8):
llama3 judging adds seconds per item (observed 5451 ms warm on one item;
5.3 GB VRAM resident) — motivates SSE streaming + rule-default design.

## Table E9 — protocol-vs-actual deviations (Ch5 needs this honesty table)

| track | protocol plan | actual | why (decision) |
|---|---|---|---|
| T2 | 3-bucket labels; future HF model | binary at 0.5; toxic-bert shipped and beat floor | data + wrapper are binary (D-011, D-012) |
| T3 | Hateful Memes / MMHS150K, classifier F1 | Memotion n=50, flag-vs-label decision measure + OCR ablation | gated / unstreamable datasets (D-018, D-023) |
| T4 | 200 AudioSet clips + 20 adversarial | LibriSpeech n=50 WER + ESC-50 n=50 top-1/top-5 | AudioSet = YouTube ids only (D-017) |
| T6 | 50-item set, ~17/17/17 | v1 18-item starter -> v2 24-item student-owned 10/6/8 | authoring capacity; provenance honesty (D-022, D-026) |
| T7 | 2 raters, kappa, usefulness 1-5 | programmatic grounding only (1.0); usefulness blank | no second rater yet (D-024) |
| T8 | 100 calls | T6 set n=18 per config | set reuse for comparability (D-024) |

Unverified protocol claims — do NOT assert in the report without running
them first: T1 "200 synthetic inputs" count; T5 ">80% branch coverage"
(needs pytest-cov run).
