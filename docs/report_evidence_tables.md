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
| fast test lane (full WSL venv), after D-030 | 52 passed / 10 skipped, offline (49 + 3 docx-tool tests) | pytest run, 2026-09-24 |
| fast test lane (minimal offline venv), after D-030 | 40 passed / 11 skipped (37 + 3) | pytest run, 2026-09-24 |
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

### Table E6c — T6 v2 two-judge comparison (D-029): rule vs llama3, same v2 set (n=24, real hf+blip+real-audio)

Sources: rule = `outputs/evaluation/20260725-191000/t6/results.json`
(`config.judge` = "rule"); ollama = `outputs/evaluation/20260725-191055/t6/results.json`
(`config.judge` = "ollama"). Both: `n_items` 24, `class_balance`
10 safe / 6 borderline / 8 harmful, `manifest` =
`data/sample_inputs/triguard_eval_v1/manifest.json` (v2), `config.run_env`
`wsl-ubuntu-py312-tri`. Every cell below is `conditions.<condition>.<key>`
from the named file.

| condition | judge (run) | n | accuracy | macro-F1 | safe F1 | borderline F1 | harmful F1 | p50 ms | p95 ms | max ms |
|---|---|---|---|---|---|---|---|---|---|---|
| text_only | rule (20260725-191000) | 22 | 0.5909 | 0.4786 | 0.6667 | 0.0 | 0.7692 | 25 | 31 | 6635 |
| text_only | ollama (20260725-191055) | 22 | 0.5909 | 0.4883 | 0.6957 | 0.0 | 0.7692 | 2123 | 2341 | 6435 |
| image_only | rule (20260725-191000) | 8 | 0.5 | 0.2222 | 0.6667 | 0.0 | 0.0 | 623 | 647 | 3900 |
| image_only | ollama (20260725-191055) | 8 | 0.25 | 0.1333 | 0.0 | 0.4 | 0.0 | 4633 | 6494 | 6700 |
| audio_only | rule (20260725-191000) | 6 | 0.5 | 0.2222 | 0.6667 | 0.0 | 0.0 | 350 | 375 | 7921 |
| audio_only | ollama (20260725-191055) | 6 | 0.1667 | 0.0952 | 0.0 | 0.2857 | 0.0 | 3584 | 3691 | 9621 |
| multimodal | rule (20260725-191000) | 24 | 0.625 | 0.4945 | 0.7143 | 0.0 | 0.7692 | 25 | 1066 | 1108 |
| multimodal | ollama (20260725-191055) | 24 | 0.4583 | 0.4722 | 0.5 | 0.25 | 0.6667 | 2318 | 6866 | 10763 |

Multimodal confusion matrices (`conditions.multimodal.confusion_matrix`;
rows = truth, columns = predicted safe / borderline / harmful):

| truth | rule (20260725-191000) | ollama (20260725-191055) |
|---|---|---|
| safe (10) | 10 / 0 / 0 | 5 / 5 / 0 |
| borderline (6) | 6 / 0 / 0 | 4 / 2 / 0 |
| harmful (8) | 2 / 1 / 5 | 1 / 3 / 4 |

Caveats (facts only):
- Single llama3 run; ollama file `limitations[4]` verbatim: "ollama/llama3
  judge (non-deterministic; falls back to rule when unreachable — check
  model_versions in per-run logs)". Rule file `limitations[4]` verbatim:
  "rule judge (deterministic)". The remaining four limitation strings are
  identical in both files ("ground-truth labels come from the project's
  hand-built manifest; see manifest_provenance for its authorship and review
  status"; "no cross_modal confounder items yet (only two benign committed
  media assets); the cross-modal ablation table is empty until such cases are
  added"; "small set; indicative, not a benchmark claim"; "unimodal
  conditions only score items that have that modality (see each n)").
- `cross_modal_ablation.n_cross_modal_harmful` = 0 in the rule file and 0 in
  the ollama file (both carry the note "no cross_modal harmful items in the
  manifest; add confounder cases to populate this table").
- Rule-judge accuracy / macro-F1 / per-class F1 in this table are identical
  to E6 (run 20260705-160858, same set, same backends, rule judge) but the
  latencies differ: E6 p50/p95 ms = text 60/70, image 3958/5114, audio
  832/1131, multimodal 160/6436 vs this rule run p50/p95 ms = text 25/31,
  image 623/647, audio 350/375, multimodal 25/1066 (warm caches vs cold
  loads are not recorded in either envelope; both are single runs).
- Unimodal image/audio rows: per the confusion matrices in both files the
  rule judge predicts `safe` for all 8 image-only and all 6 audio-only
  items and llama3 predicts `borderline` for all of them (D-029).

## Table E7 — T7 rationale grounding (llama3 judge, v1 set n=18)

Source: `outputs/evaluation/20260705-113456/t7/results.json`
(`judge` = "ollama"; `config` text hf / image blip / audio real; `run_env`
`wsl-ubuntu-py312-tri`; `run_at` 2026-07-05T11:34:56 UTC).

| metric | value |
|---|---|
| grounding rate (>=1 real evidence token cited) | 1.0 (18/18) |
| invented (unsupplied) modalities cited | 0 |

Provenance and caveats (facts, each with its pointer):
- Evaluation set = the v1 18-item manifest, recoverable with
  `git show c8f22a8:data/sample_inputs/triguard_eval_v1/manifest.json`
  (commit c8f22a8, 2026-07-05). Modality mix counted from that file:
  11 text-only, 1 image-only, 1 audio-only, 5 multimodal (2 text+image,
  2 text+image+audio, 1 text+audio). The manifest was replaced by the v2
  24-item set in commit 6bfdfc3; the T7 run predates that replacement.
- Per-item judge provenance is NOT recorded: `run_t7.py` calls
  `run_pipeline(judge_mode=args.judge, ...)` (line 49) and stores only
  id / grounded / cited / invented_modalities / rationale / usefulness_1to5
  per item (lines 55-62); `TriGuardResult.model_versions` (which carries the
  `ollama->rule` fallback label) is not written to the envelope.
- One rationale (MB1, results.json line 202) matches the rule-judge template
  verbatim: "the text classifier flagged toxicity at 0.63 (toxic). the image
  caption 'a house in the middle of a field' showed no obvious risk cues" =
  `llm_judge.py` line 137 (`"the text classifier flagged toxicity at {ts:.2f}"`)
  + line 156 (`"... showed no obvious risk cues"`). Read as: 18/18 grounded,
  of which 17 native llama3 + 1 suspected rule-fallback of unrecorded cause
  (`judge` in `llm_judge.py` lines 99-113 falls back to the rule judge on
  invalid JSON, unreachable server, or timeout, tagging only `uncertainties`
  and `model_versions`, neither of which T7 stores).
- Model tag and temperature are code defaults at c8f22a8, not fields of the
  envelope: `_DEFAULT_OLLAMA_MODEL = "llama3:8b-instruct-q4_K_M"`
  (`git show c8f22a8:src/triguard/models/llm_judge.py` line 31, overridable
  by `TRIGUARD_OLLAMA_MODEL` / `OLLAMA_MODEL`, lines 42-43) and
  `"options": {"temperature": 0.0}` (line 237). The envelope `config` holds
  only text/image/audio backend + run_env.
- Six rationales are stored truncated at 200 characters (`run_t7.py` line 60:
  `"rationale": r.rationale[:200]`) — B2, H3, I1, A1, MS1, MH1 per
  `scripts/show_t7_citations.py`; full rationales were not persisted.
- Floor metric: cites >= 1 token (`grounding.py` lines 37-48); not
  completeness or quality. The rule judge grounds ~1.0 BY CONSTRUCTION and
  was not separately measured. `usefulness_1to5` is `null` for all 18 items
  in this file (the human column lives in a separate `t7_human` envelope
  produced by `scripts/rate_t7.py --merge`, if/when run).
- Dashboard: `/eval/summary` (`src/triguard/api/main.py` line 463) copies
  `run_at, judge, n, grounding_rate, invented_modality_count, config, note`
  verbatim from the newest T7 file (`_TRACK_KEYS["t7"]`, lines 415-416), so
  it displays 1.0 (18/18) without any of the caveats above.

### Table E7b — T7 citation-type summary (mechanical, from the committed file)

Source: `scripts/show_t7_citations.py outputs/evaluation/20260705-113456/t7/results.json`
(default `--manifest-rev c8f22a8`). Token classes follow
`src/triguard/evaluation/grounding.py` lines 15-34; "specific" = score /
label / caption word / cue / tag / transcript word that is not a function
word; rule-template = matches the `_rule_based_judge` strings in
`src/triguard/models/llm_judge.py` lines 136-174.

| row | count (of 18) | items |
|---|---|---|
| cite >= 1 specific token | 15 | S1, S2, S3, B1, B2, B3, H1, H2, H3, H4, I1, A1, MB1, MH1, MH2 |
| cite only generic "toxicity" and/or stopwords | 3 | S4, MS1, MS2 |
| rationale matches rule-judge template | 1 | MB1 |
| rationale stored truncated at 200 chars | 6 | B2, H3, I1, A1, MS1, MH1 |

All 18 are `grounded: true` in the file because the literal "toxicity" is an
admitted token whenever text evidence exists (`grounding.py` line 21); rows 1-2
partition the 18 (15 + 3).

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

| track | protocol plan (docs/evaluation_protocol.md) | actual (pointer) | why (decision) |
|---|---|---|---|
| T1 | 200 synthetic inputs; schema validity measured | n=14 smoke run only (`outputs/evaluation/20260623-063735/results.json`, `n_samples` 14, mock pipeline, rule judge); `schema_validity_rate` is the constant `1.0` written at `src/triguard/evaluation/run_eval.py` line 151 (`# enforced by Pydantic`), not a measured rate | validity enforced by pydantic v2 at construction, so no invalid output can reach the counter (see E1 "schema validity") |
| T2 | 3-bucket labels; future HF model | binary at 0.5; toxic-bert shipped and beat floor | data + wrapper are binary (D-011, D-012) |
| T3 | Hateful Memes / MMHS150K, classifier F1 | Memotion n=50, flag-vs-label decision measure + OCR ablation | gated / unstreamable datasets (D-018, D-023) |
| T4 | 200 AudioSet clips + 20 adversarial | LibriSpeech n=50 WER + ESC-50 n=50 top-1/top-5 | AudioSet = YouTube ids only (D-017) |
| T5 | `pytest-cov`, target > 80 % branch coverage on `pipeline.py` (protocol line 60) | NOT measured: `pytest-cov` is absent from both venvs; no coverage run or report exists in the repo | fixture-driven unit tests exist (E1) but coverage percentage was never produced |
| T5 judge failure path | judge returns invalid JSON -> retry once -> if still invalid -> `borderline` result with `uncertainties=["judge_output_invalid"]` (protocol line 58) | rule-judge output is returned instead, tagged `uncertainties=["judge_output_invalid"]` (`src/triguard/models/llm_judge.py` lines 99-103); unreachable server / timeout -> rule output tagged `ollama_unavailable:<reason>` (lines 104-113); pipeline labels the judge `ollama->rule` in `model_versions` | graceful-degradation design (D-016, D-019, D-021, D-025): the label is whatever the rule judge computes, not a forced `borderline` |
| T6 | 50-item set, ~17/17/17 | v1 18-item starter -> v2 24-item student-owned 10/6/8 | authoring capacity; provenance honesty (D-022, D-026) |
| T7 grounding unit | % of rationale SENTENCES citing >= 1 structured-evidence item, regex + manual check (protocol lines 70-74) | per-RATIONALE binary: >= 1 evidence token anywhere in the rationale (`grounding.py` lines 37-48), automated only, no manual check; 1.0 (18/18) — see E7 / E7b for what "cited" means per item | unit changed from sentence-level to rationale-level; manual pass not done (D-024) |
| T7 raters | two reviewers (self + one peer), Cohen's kappa (protocol lines 71, 74) | 0 raters at run time (`usefulness_1to5` = `null` for all 18 in `outputs/evaluation/20260705-113456/t7/results.json`); human column, if filled, comes from `scripts/rate_t7.py` — single author rater, no second rater, no kappa | no second rater yet (D-024) |
| T7 scale wording | Usefulness 1 (no help) – 5 (decisive help) (protocol line 72) | `scripts/rate_t7.py` line 10: "1 = useless to a moderator, 3 = partly useful, 5 = directly actionable" | anchor wording changed when the rating tool was written |
| T8 | 100 calls | T6 set n=18 per config | set reuse for comparability (D-024) |

T1 and T5 rows above replace the earlier "unverified protocol claims" note:
neither the 200-input count nor the coverage percentage was ever produced,
so neither may be asserted.
