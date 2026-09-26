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
| fast test lane (full WSL venv), after D-035 | 95 passed / 10 skipped, offline (52 + 43: tests added under D-032/D-034/D-035/D-036 plus the other untracked test files listed in E1a) | pytest run, 2026-09-26 (`USE_TF=0 PYTHONPATH=src ~/.venv-tri/bin/python -m pytest -q`, exit 0) |
| fast test lane (minimal offline venv), after D-035 | 83 passed / 11 skipped (40 + 43) | pytest run, 2026-09-26 (`PYTHONPATH=src <windows-venv>\Scripts\python.exe -m pytest -q`, exit 0) |
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
| T5 | `pytest-cov`, target > 80 % branch coverage on `pipeline.py` (protocol line 60) | NOT measured: `pytest-cov` is absent from both venvs; no coverage run or report exists in the repo; `scripts/coverage_report.sh` (fast lane only, WSL) is ready and refuses cleanly without `pytest_cov` (ran 2026-09-24, exit 2, prints the install line) | fixture-driven unit tests exist (E1) but coverage percentage was never produced; dev dependency needs author approval (CLAUDE.md rule 4; D-035) |
| T5 judge failure path | judge returns invalid JSON -> retry once -> if still invalid -> `borderline` result with `uncertainties=["judge_output_invalid"]` (protocol line 58) | rule-judge output is returned instead, tagged `uncertainties=["judge_output_invalid"]` (`src/triguard/models/llm_judge.py` lines 99-103); unreachable server / timeout -> rule output tagged `ollama_unavailable:<reason>` (lines 104-113); pipeline labels the judge `ollama->rule` in `model_versions` | graceful-degradation design (D-016, D-019, D-021, D-025): the label is whatever the rule judge computes, not a forced `borderline` |
| T6 | 50-item set, ~17/17/17 | v1 18-item starter -> v2 24-item student-owned 10/6/8 | authoring capacity; provenance honesty (D-022, D-026) |
| T7 grounding unit | % of rationale SENTENCES citing >= 1 structured-evidence item, regex + manual check (protocol lines 70-74) | per-RATIONALE binary: >= 1 evidence token anywhere in the rationale (`grounding.py` lines 37-48), automated only, no manual check; 1.0 (18/18) — see E7 / E7b for what "cited" means per item | unit changed from sentence-level to rationale-level; manual pass not done (D-024) |
| T7 raters | two reviewers (self + one peer), Cohen's kappa (protocol lines 71, 74) | 0 raters at run time (`usefulness_1to5` = `null` for all 18 in `outputs/evaluation/20260705-113456/t7/results.json`); human column, if filled, comes from `scripts/rate_t7.py` — single author rater, no second rater, no kappa | no second rater yet (D-024) |
| T7 scale wording | Usefulness 1 (no help) – 5 (decisive help) (protocol line 72) | `scripts/rate_t7.py` line 10: "1 = useless to a moderator, 3 = partly useful, 5 = directly actionable" | anchor wording changed when the rating tool was written |
| T8 | 100 calls | T6 set n=18 per config | set reuse for comparability (D-024) |

T1 and T5 rows above replace the earlier "unverified protocol claims" note:
neither the 200-input count nor the coverage percentage was ever produced,
so neither may be asserted.

---

# Tables added by the Integrate stage (2026-09-24) — bodies copied verbatim from their source docs

Each section below names its source doc and the scripts / runs behind it.
The bodies were extracted by line range and checked to be byte-identical
substrings of the source doc (scratchpad `integrate.py`). Edit the source doc
and re-copy; do not hand-edit here. `[STUDENT]` slots are the author's.

## Table E3a — T2 sampling & run parameters (Ch5.3)

Source doc: `docs/t2_sampling_factsheet.md` '## For integration' > '### Table E3a'. Envelopes: `outputs/evaluation/20260623-074102/t2/results.json`, `outputs/evaluation/20260623-124802/t2/results.json` (row cells cite envelope line numbers). Loader: `src/triguard/data/datasets.py`. Derived Wilson CIs: `scripts/ci_from_envelope.py <results.json> --write` -> `outputs/evaluation/<run>/t2/derived_intervals.json` (D-032).

| row | 074102 (sklearn tier) | 124802 (toxic-bert tier) | source |
|---|---|---|---|
| hub_id | `google/civil_comments` | `google/civil_comments` | `dataset.hub_id` (074102:6, 124802:6) |
| split | `test` | `test` | `dataset.split` (074102:8, 124802:8) |
| label rule | `toxicity >= 0.5 → toxic` | same | `datasets.py:107` |
| sampling | seeded buffered shuffle, seed 42, buffer 10,000, first 500 non-empty rows (~10,500 rows of the shard-shuffled stream; not a uniform draw over the split) | same | `datasets.py:56,199,202,206-218` |
| n | 500 | 500 | `n_samples` |
| class_balance | 468 non-toxic / 32 toxic | 468 / 32 | `class_balance` (074102:15-18, 124802:15-18) |
| threshold | 0.5 | 0.5 | `config.threshold` |
| backend / wrapper_mode | backend key absent / `real` | `hf` / `real-hf` | `config` (074102:19-24, 124802:20-24) |
| model_revision | n/a (`sklearn-tfidf-lr`, trained in-process on the 30-sentence corpus) | `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94` | `model_versions` (074102:26, 124802:28-29) |
| run_env | not recorded | `wsl-ubuntu` | `config.run_env` (124802:25) |
| dataset revision | unpinned | unpinned | `datasets.py:26-29` |
| run id | `20260623-074102` | `20260623-124802` | directory names |
| Wilson 95% CI (derived) | acc [0.4982, 0.5852]; toxic P [0.0524, 0.1228]; toxic R [0.4226, 0.7448] | acc [0.9019, 0.9475]; toxic P [0.2326, 0.6127]; toxic R [0.1556, 0.4537] | `derived_intervals.json` next to each envelope |

## Table E10 — datasets & tracks at a glance (Ch5.1)

Source doc: `docs/dataset_cards.md` '## For integration' > '### Table E10' (generated by `scripts/build_dataset_cards.py` -> `docs/dataset_cards.json`; regenerate after any change to `text_model.py` / `run_eval.py` / manifest / envelopes). Evidence runs are named per row; v1 manifest via `git show c8f22a8:data/sample_inputs/triguard_eval_v1/manifest.json`.

| track | dataset | role | source id | licence | split | selection (seed/buffer/cap/filter; sampling frame = buffer + n rows consumed) | n | class balance | evidence run |
|---|---|---|---|---|---|---|---|---|---|
| T2 (sklearn tier only) | bundled 30-sentence corpus (sklearn tier training data) | training-only | `src/triguard/models/text_model.py:48-81` | repo fixture | n/a | all 30 sentences, no sampling | 30 | {"non-toxic(0)": 15, "toxic(1)": 15} | 20260623-074102 (T1 runs do not record the text backend) |
| T1/T5 | T1/T5 hand-built smoke set (EVAL_SET) | evaluation (smoke) | `src/triguard/evaluation/run_eval.py:33-75` | repo fixture | n/a | hand-built, all items; media paths are filename cues only | 14 | {"safe": 5, "borderline": 4, "harmful": 5} | ["20260608-180939", "20260623-063735"] |
| T2 | Civil Comments | evaluation | `google/civil_comments` | CC0-1.0 | test | seed 42 / buffer 10,000 / cap 500 / non-empty text only (empty rows skipped); frame ~10,500 rows | 500 | {"non-toxic": 468, "toxic": 32} | ["20260623-074102 (real)", "20260623-124802 (hf)"] |
| T3 | Memotion (MMSoc repack) | evaluation | `Ahren09/MMSoc_Memotion` | Memotion / SemEval-2020 Task 8 (research use; meme images are third-party copyright — streamed, never committed) | train | seed 42 / buffer 2,000 / cap 50 / label parseable AND image present AND image decodable; frame ~2,050 rows | 50 | {"not_offensive": 18, "offensive": 32} | ["20260704-172017", "20260705-111002"] |
| T4 (ASR / Whisper WER) | LibriSpeech test-clean | evaluation | `openslr/librispeech_asr` / clean | CC BY 4.0 | test | seed 42 / buffer 2,000 / cap 50 / non-empty reference text AND audio array present; frame ~2,050 rows | 50 | n/a (ASR) | 20260704-153729 |
| T4 (event tagging / YAMNet) | ESC-50 | evaluation | `ashraq/esc50` | CC BY-NC 3.0 (Piczak 2015; non-commercial, academic use) | train | seed 42 / buffer 2,000 / cap 50 / category in ESC50_TO_YAMNET (42 mapped categories) AND audio array present; frame >= 2050 (unmapped categories are skipped after being drawn; rows consumed not recorded) | 50 | n/a (multi-category; see categories_used in envelope) | 20260704-153729 |
| T6 (+T7/T8) | triguard_eval_v1 manifest, v1 (AI-drafted starter set) | evaluation | `git show c8f22a8:data/sample_inputs/triguard_eval_v1/manifest.json` | repo fixture | n/a | hand-built, all items; combos {"text": 11, "image": 1, "audio": 1, "text+image+audio": 2, "text+image": 2, "text+audio": 1} | 18 | {"safe": 8, "borderline": 4, "harmful": 6} | 20260704-221056 + inferred ["20260705-113354", "20260705-113456", "20260705-113639"] |
| T6 | triguard_eval_v1 manifest, v2 (student-reviewed; current HEAD) | evaluation | `data/sample_inputs/triguard_eval_v1/manifest.json` | repo fixture | n/a | hand-built, all items; combos {"text": 14, "image": 1, "audio": 1, "text+image+audio": 4, "text+image": 3, "text+audio": 1} | 24 | {"safe": 10, "borderline": 6, "harmful": 8} | ["20260705-160858", "20260725-191000", "20260725-191055"] |

A9 (confounder template, 12 slots / 0 filled) is behind no reported number and is excluded.

## Table E11 — 30-sentence bundled corpus card (Ch4.2)

Source doc: `docs/dataset_cards.md` '## For integration' > '### Table E11'. Corpus: `src/triguard/models/text_model.py:48-81`; hard tokens `text_model.py:140-143`; overlap rows computed by `scripts/build_dataset_cards.py` against `src/triguard/evaluation/run_eval.py` (T1 EVAL_SET), `git show c8f22a8:...manifest.json` (T6 v1) and `data/sample_inputs/triguard_eval_v1/manifest.json` (T6 v2). Authorship row is 'STUDENT TO STATE'.

Source `src/triguard/models/text_model.py:48-81`; role training-only; authorship: STUDENT TO STATE (who wrote the 30 sentences and when); first tracked in git: `1373e06 Tue Jun 23 18:30:12 2026 +0500`; sha256 of the newline-joined sentences `e22d9c9f3f1473b9…`.

| # | label | sentence (verbatim) | hard-token hits |
|---|---|---|---|
| 1 | 0 | I really enjoyed the museum today, it was beautifully laid out | - |
| 2 | 0 | Thanks for the help, the documentation made it easy to follow | - |
| 3 | 0 | The new park looks great and is family friendly | - |
| 4 | 0 | I appreciate your feedback on the draft, will revise tomorrow | - |
| 5 | 0 | Looking forward to the team meeting on Monday | - |
| 6 | 0 | The recipe came out perfectly, would make again | - |
| 7 | 0 | Congratulations on the promotion, well deserved | - |
| 8 | 0 | My commute was peaceful this morning, no traffic | - |
| 9 | 0 | I respectfully disagree with that interpretation | - |
| 10 | 0 | Hope you feel better soon, take care of yourself | - |
| 11 | 0 | Reading the new book before bed is so relaxing | - |
| 12 | 0 | Great explanation, I finally understand the concept | - |
| 13 | 0 | The weather has been pleasant all week | - |
| 14 | 0 | Volunteering at the food bank was rewarding | - |
| 15 | 0 | I appreciate the patience while I learn this software | - |
| 16 | 1 | You are utterly worthless and nobody should ever listen to you | worthless |
| 17 | 1 | I hope something terrible happens to you and your family | - |
| 18 | 1 | Anyone who believes that nonsense is a complete idiot | idiot |
| 19 | 1 | Get lost you pathetic loser nobody likes you | loser |
| 20 | 1 | People like you are a stain on society and should disappear | - |
| 21 | 1 | Shut up you absolute moron nobody cares what you think | moron |
| 22 | 1 | I would happily watch you suffer for being so stupid | stupid |
| 23 | 1 | Disgusting people like you ruin everything around them | disgusting |
| 24 | 1 | You deserve to be humiliated in public for that opinion | - |
| 25 | 1 | Threats and insults are the only thing your kind understands | - |
| 26 | 1 | Your entire group of friends is worthless trash | trash, worthless |
| 27 | 1 | I hope the next disaster takes out your whole community | - |
| 28 | 1 | You are a complete embarrassment to everyone who knows you | - |
| 29 | 1 | Stop breathing my air you absolute waste of space | - |
| 30 | 1 | Anyone with your views deserves to lose everything they care about | - |

Hard-token list (`src/triguard/models/text_model.py:140-143`, 11 tokens): die, disgusting, hate, idiot, kill, loser, moron, scum, stupid, trash, worthless

| overlap check (computed) | T1 EVAL_SET | T6 v1 (c8f22a8) | T6 v2 (HEAD) |
|---|---|---|---|
| items with text | 14 | 16 | 22 |
| exact lowercase match with a corpus sentence | 0 | 1 | 0 |
| items containing >= 1 hard token | 4 | 5 | 2 |

Corpus sentences containing >= 1 hard token: 7 of 30 (toxic-labelled: 7 of 15).

## Table E12 — Table 2.1 replacement body: property columns + TriGuard row (Ch2 §2.7)

Source doc: `docs/ch2_argument_spine.md` '## F. For integration' > '### Table E12'. Cells reduced from `docs/literature_matrix.md:7-14`; Limitation column keeps the submitted draft's own text (`[tadb2d13b]` rows, local mirror `ch2.md:58-65`). Companion tool: `scripts/check_citations.py` (D-034). Every 'partial' (n1-n7) needs the student's confirmation; the column set differs from the earlier five-property list in `docs/report_skeleton.md` (see that file's Ch2 note).

Cell source: `docs/literature_matrix.md:7-14` (matrix columns Method /
Limitation / Gap Identified), reduced to yes / no / partial. The
reduction is this task's reading of those cells; each "partial" is
flagged for the student's confirmation in the notes below. Limitation
cells are the student's own table content and stay `[keep existing]` with
the row anchor. TriGuard row = verified code facts (file:line in the
notes). Caption slot: `[STUDENT]` (numbered caption per P2).

| Source | Text | Image | Audio (speech / events) | Local execution | Human-readable rationale | Backend provenance & reviewer workflow | Limitation for TriGuard's goal |
|---|---|---|---|---|---|---|---|
| Lees et al. (2022) | yes | no | no / no | no | no | no | [keep existing] `[tadb2d13b]` row 1 (ch2.md:58) |
| Kiela et al. (2020) | yes | yes | no / no | partial (n1) | no | no | [keep existing] `[tadb2d13b]` row 2 (ch2.md:59) |
| Li, L.H. et al. (2019) | yes | yes | no / no | partial (n2) | no | no | [keep existing] `[tadb2d13b]` row 3 (ch2.md:60) |
| Li, J. et al. (2022) | partial (n3) | yes | no / no | yes | no | no | [keep existing] `[tadb2d13b]` row 4 (ch2.md:61) |
| Gemmeke et al. (2017) | no | no | no / yes | yes (n4) | no | no | [keep existing] `[tadb2d13b]` row 5 (ch2.md:62) |
| Radford et al. (2023) | no (n5) | no | yes / no | yes | no | no | [keep existing] `[tadb2d13b]` row 6 (ch2.md:63) |
| Zheng et al. (2023) | yes | no | no / no | partial (n6) | yes | no | [keep existing] `[tadb2d13b]` row 7 (ch2.md:64) |
| Gorwa, Binns and Katzenbach (2020) | no | no | no / no | no | no (n7) | no (n7) | [keep existing] `[tadb2d13b]` row 8 (ch2.md:65) |
| TriGuard (this project) | yes | yes | yes / yes | yes | yes | yes | [STUDENT] — facts: E3 toxic recall 0.2812 (`report_evidence_tables.md:53`); E4 AUROC 0.566 (:69); E6c confounder rows empty (:181-183); T7 floor metric only (:235-236); single llama3 run (D-029) |

Notes (facts behind the reduced cells):
- n1 Kiela: `literature_matrix.md:8` "Benchmark only — not a deployable
  system; ... gated access"; baselines are research code — mark "partial"
  or "no" [STUDENT].
- n2 Li, L.H.: `literature_matrix.md:9` "Reproducible; widely used as a
  baseline" and "Depends on pre-extracted Faster-RCNN regions" — research
  implementation (`[tadb2d13b]` row 3 "Research implementation").
- n3 Li, J. (BLIP): `literature_matrix.md:13` image captioning + VQA; the
  text side is an input/output of an image model, not text moderation.
- n4 Gemmeke: `literature_matrix.md:10` "pretrained weights freely
  available" refers to the YAMNet line, not the AudioSet paper itself — see
  E.5 before keeping "yes" against Gemmeke.
- n5 Radford: `literature_matrix.md:11` "Transcription only — no toxicity
  classification".
- n6 Zheng: `literature_matrix.md:12` "Closed-source judge models"; the
  pattern is model-dependent (`[tadb2d13b]` row 7 "Model-dependent").
- n7 Gorwa: `literature_matrix.md:14` "No empirical model evaluation" —
  requirements source, not an implementation.
- TriGuard row code facts: Text `text_model.py:39-40`; Image
  `image_model.py:30-31` (+ OCR `:126`); Audio speech `audio_model.py:111-114`,
  events `audio_model.py:35`; Local — all backends resolve to local
  processes, Ollama host `llm_judge.py:30` (`localhost:11434`), mock/offline
  defaults `text_model.py:15`, `image_model.py:11`, `audio_model.py:12`;
  Rationale `schemas.py:67`; Provenance `schemas.py:91` `model_versions` +
  `pipeline.py:55` `"ollama->rule"`; Workflow `schemas.py:69`
  `recommended_action` + `/ui` compare and `/dashboard` (`CLAUDE.md`
  status table row "FastAPI demo").

## Table E13a — prompt revision log (Ch4.3)

Source doc: `docs/judge_prompt_card.md` '## 8. For integration' > '### E13a'. Derived from `git log -- src/triguard/models/llm_judge.py`, per-commit `git show <c>:src/triguard/models/llm_judge.py`, SHA-256 of the `JUDGE_PROMPT_TEMPLATE` string (D-031).

Source: `git log -- src/triguard/models/llm_judge.py`; per-commit
`git show <c>:src/triguard/models/llm_judge.py`; SHA-256 of the text inside
`JUDGE_PROMPT_TEMPLATE = """..."""`.

| commit | date | change to `llm_judge.py` | prompt text changed? | template SHA-256 (16) |
|---|---|---|---|---|
| `1373e06` | 2026-06-23 | first tracked version of the file (earlier drafting not in git) | n/a | `1df9a321a8f1c535` |
| `4f10803` | 2026-07-02 | call-time host/model/timeout; split fallback tags; `JSONDecodeError` handled | no | `1df9a321a8f1c535` |
| `e866541` | 2026-07-05 | streaming variant added (`_ollama_generate_stream`, `judge_stream`) | no | `1df9a321a8f1c535` |
| `daae032` | 2026-07-25 | `keep_alive` request parameter added | no | `1df9a321a8f1c535` |

Retry suffix (lines 232-233) likewise unchanged across all four commits.

## Table E13b — prompt validation log, pointers only (Ch4.3)

Source doc: `docs/judge_prompt_card.md` '## 8. For integration' > '### E13b'. No metric values by design — each row points to DECISIONS.md lines, Table E7/E7b (run `20260705-113456`) or Table E6c (runs `20260725-191000`, `20260725-191055`).

| date | evidence | n | what was checked | outcome word | pointer |
|---|---|---|---|---|---|
| 2026-06-25 | D-015 real run on `sample_harmful.json` | 1 | schema re-validation; grounding; two fallback modes | passed | `DECISIONS.md` 240-258 |
| 2026-07-05 | T7 grounding run (llama3, v1 set) | 18 | `grounded`, `invented_modalities` | grounded (floor) | Table E7 / E7b; `docs/t7_measurement_card.md` |
| 2026-07-05 | Phase D live smoke (stream + compare) | 1 | schema-valid `source:"ollama"` terminal event; honest degradation offline | passed | `DECISIONS.md` 626-633 |
| 2026-07-25 | T6 v2 two-judge comparison | 24 | rule vs llama3 per condition | compared | Table E6c; `DECISIONS.md` 754 |

## Table M1 — models composed, facts only (Ch3.4)

Source doc: `docs/model_cards.md` '## For integration' > '### Table M1'. Pins checked by `PYTHONPATH=src python scripts/verify_model_cards.py` (exit 1 on drift; always prints the RapidOCR pin warning). Runs named per row. Citation-status cells marked VERIFY / MISSING are external checks the student must perform.

Caption slot: `[STUDENT: justification sentence in Ch3 body]`. No "why"
column by design. Pointers: `file:line` at commit `908b1e5`.

| Modality / role | Model + variant | Pinned id (file:line) | Evidence field filled | Evidence track + run id | Citation status |
|---|---|---|---|---|---|
| Text, real tier | `unitary/toxic-bert` | `text_model.py:39-40` rev `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94` | `TextEvidence.toxicity_score`, `top_labels`, `confidence`, `raw.scores` | T2 `20260623-124802` (acc 0.928, macro-F1 0.6476); T3 `20260705-111002` OCR->text f1 0.4348 | Detoxify `[pc1239dbf]` in draft; not in referencing_notes.md; VERIFY |
| Text, offline floor | sklearn TF-IDF(1,2) + LR(C=4.0) on 30 bundled sentences | none (no weights); `text_model.py:48-81`, `:95-96` | same `TextEvidence` fields; `raw.classifier` = `sklearn-tfidf-lr` | T2 `20260623-074102` (acc 0.542, macro-F1 0.4149) | n/a (library citation MISSING) |
| Image, real tier | `Salesforce/blip-image-captioning-base` | `image_model.py:30-31` rev `82a37760796d32b1411fe092ab5d4e227313294b` | `ImageEvidence.caption`, `visual_risk_cues`, `confidence` | T3 `20260705-111002` (pipeline f1 0.4, auroc 0.566; caption-only f1 0.0606); T6 `20260725-191000` image_only acc 0.5 | S7 Li, J. et al. 2022; `[pd2976f51]` |
| Image, opt-in OCR | RapidOCR default engine (`rapidocr-onnxruntime`) | range only `requirements.txt:28`; exact pin MISSING in `requirements-full.txt`; no model revision | `ImageEvidence.raw["ocr_text"]` -> `visual_risk_cues` | T3 `20260705-111002` `ocr_ablation` (cues delta 0.0; ocr_to_text f1 0.4348, delta 0.3742) | `[pc4f1814e]` RapidAI (n.d.) in draft; not in referencing_notes.md; VERIFY |
| Audio, transcription | Whisper `tiny` (`openai-whisper`) | name string `audio_model.py:122`; lib `openai-whisper==20250625` `requirements-full.txt:64` | `AudioEvidence.transcript`, `transcript_confidence` | T4 `20260704-153729` (wer_corpus 0.0971, wer_mean_per_clip 0.1314) | S5 Radford et al. 2023; `[p4b78a00c]` |
| Audio, event tags | YAMNet TF-Hub `google/yamnet/1` | `audio_model.py:35` (URL `/1`); libs `tensorflow-hub==0.16.1` `:96`, `tensorflow==2.21.0` `:94` | `AudioEvidence.yamnet_tags` | T4 `20260704-153729` (top1_rate 0.32, top5_rate 0.66); T6 `20260725-191000` audio_only acc 0.5 (all `safe`) | S4 Gemmeke 2017 = dataset paper; TF-Hub card `[p47fe03b3]` in draft only; Hershey/Howard MISSING; VERIFY rows 1-4 |
| Judge, optional | `llama3:8b-instruct-q4_K_M` via Ollama | `llm_judge.py:31` (tag only; no digest) | whole `JudgeOutput`; `model_versions.llm_judge` = `ollama` / `ollama->rule` | T7 `20260705-113456` (grounding_rate 1.0, n 18, invented 0); T6 `20260725-191055` multimodal acc 0.4583 | `[pedd4c0e5]`, `[pf3a8bf6e]` in draft; not in referencing_notes.md; VERIFY row 6 |
| Judge, default | rule-based (`_rule_based_judge`) | `llm_judge.py:122-215` | whole `JudgeOutput`; label `rule` | every rule-judge run (T3, T6 `20260725-191000`, T8) | n/a |

## Table E1a — per-layer test inventory (Ch5.2)

Source doc: `docs/evaluation_strategy_matrix.md` '## For integration' > '### Table E1a' (WSL `~/.venv-tri`, fast lane; body copied verbatim from `docs/generated/test_inventory.md`, regenerated 2026-09-26 with `--junit` from a fresh run; offline venv in the footnote). Generator: `scripts/test_inventory.py` (stdlib; `--junit <xml> --out docs/generated/test_inventory.md`); regenerate after any change under `tests/`.

Copied from `docs/generated/test_inventory.md` (Per-layer table). Offline
venv counts in the footnote.

| layer | files | collected | slow-marked | passed | skipped | failed |
|---|---|---|---|---|---|---|
| unit-schema | 1 | 6 | 0 | 6 | 0 | 0 |
| unit-wrapper | 3 | 8 | 0 | 8 | 0 | 0 |
| unit-judge-rule | 1 | 4 | 0 | 4 | 0 | 0 |
| unit-eval-helper | 3 | 4 | 0 | 4 | 0 | 0 |
| unit-tooling | 8 | 34 | 0 | 34 | 0 | 0 |
| regression-fallback | 6 | 18 | 0 | 18 | 0 | 0 |
| integration-orchestrator | 1 | 6 | 0 | 6 | 0 | 0 |
| functional-api-cli | 3 | 15 | 0 | 15 | 0 | 0 |
| real-backend-slow | 6 | 7 | 7 | 0 | 7 | 0 |
| dataset-loader-slow | 3 | 3 | 3 | 0 | 3 | 0 |
| **total** | 32 | 105 | 10 | 95 | 10 | 0 |

Footnote (offline venv, `docs/generated/test_inventory_offline.md`, same
date): 91 collected in 29 files; 8 slow-marked; 83 passed / 8 skipped /
0 failed; per-layer differences from WSL: unit-tooling 8 files / 34 (same),
regression-fallback 5 files / 17, functional-api-cli 1 file / 4,
real-backend-slow 4 files / 5; not collected (module-level importorskip):
`tests/test_api.py`, `tests/test_api_phase_d.py`, `tests/test_image_model_ocr.py`.
Regenerated 2026-09-26 after all task files landed: 0 failures in either lane.

## Table E1b — protocol claim -> discharging test (Ch5.2)

Source doc: `docs/evaluation_strategy_matrix.md` '## Table 2' (= '### Table E1b', "Copy verbatim"). Protocol lines quoted from `docs/evaluation_protocol.md`; tests named per row; "before" = commit 908b1e5, "after" = with `tests/test_llm_judge_retry.py`, `tests/test_pipeline_shielding.py`, `tests/test_cli.py` (D-035).

Protocol text is quoted verbatim from `docs/evaluation_protocol.md` (line in
the first column). Status vocabulary: tested / tested-stream-only / untested.
"Before" = state of the suite at commit 908b1e5 (pre-task); "After" = with
this task's tests.

| protocol line | claim (verbatim) | discharging test (file::name, lines) | before | after | note |
|---|---|---|---|---|---|
| 21 (T1) | "Run 200 synthetic inputs through both mock and real pipelines." | none — the only T1 run is the n=14 mock smoke (`outputs/evaluation/20260623-063735/results.json`, Table E9 row T1) | untested | untested | no 200-input run exists; not changed by this task |
| 22 (T1) | "Validate each wrapper output against its Pydantic schema; validate each `TriGuardResult` against the result schema." | `tests/test_schemas.py` (6); NEW `tests/test_cli.py::test_cli_run_sample_harmful_exit_0_and_valid_result` re-validates the CLI's stdout with `TriGuardResult.model_validate_json` at the process boundary | tested (by construction) | tested | validity is enforced at construction (Table E9 row T1); the new CLI test adds a boundary re-validation |
| 23 (T1) | "Fail the build if validity < 100 %." | none — no build/CI; pytest exit code is the only gate | untested | untested | see CI row of Table 1 |
| 57 (T5) | "text-only input → only text wrapper called, audio/image fields `None` in `JudgeInput`." | `tests/test_orchestrator.py::test_orchestrator_text_only` (lines 6-11) asserts `image_evidence is None and audio_evidence is None` on the result | tested (fields None); "only text wrapper called" (call count) not asserted | unchanged | call-count assertion is a possible follow-up [STUDENT] |
| 58 (T5) | "all three modalities present + judge returns invalid JSON → orchestrator retries once → if still invalid → `borderline` result with `uncertainties=["judge_output_invalid"]`." | NEW `tests/test_llm_judge_retry.py::test_invalid_twice_falls_back_to_rule_after_exactly_two_calls` (exactly 2 `_ollama_generate` calls, tag present, three-modality fixture); NEW `::test_retry_prompt_carries_stricter_suffix_and_second_reply_wins`; NEW `::test_orchestrator_labels_invalid_json_fallback_ollama_to_rule` (through `pipeline.run`, `model_versions["llm_judge"] == "ollama->rule"`) | tested-stream-only (`tests/test_llm_judge_stream.py::test_stream_invalid_json_falls_back_to_rule`, line 91 — the stream path has no retry) | tested — FLIPPED | deviation stands: the result label is the rule judge's own, not a forced `borderline` (Table E9 row "T5 judge failure path"; `llm_judge.py:99-103`) |
| 59 (T5) | "one wrapper raises → orchestrator catches and returns evidence with `confidence=0`." | NEW `tests/test_pipeline_shielding.py` (4): `test_text_wrapper_failure_is_shielded`, `test_image_wrapper_failure_is_shielded`, `test_audio_wrapper_failure_is_shielded`, `test_all_three_wrappers_failing_still_returns_result` — `confidence == 0.0` / `transcript_confidence == 0.0`, `raw["error"]`, `model_versions[...] == "unknown"` (`pipeline.py:96-125`) | untested | tested — FLIPPED | — |
| 60 (T5) | "Coverage measured via `pytest-cov`; target > 80 % branch coverage on `pipeline.py`." | none — `scripts/coverage_report.sh` is ready and refuses without `pytest_cov` | untested (not measured) | untested (not measured) | requires the dev dependency (DECISIONS draft below) |

Flipped by this task: protocol line 58 (tested-stream-only -> tested) and
line 59 (untested -> tested). Line 22 gained a process-boundary re-validation
(status unchanged: tested).

## Table E1c — manual functional checks (Ch5.2)

Source doc: `docs/evaluation_strategy_matrix.md` '## For integration' > '### Table E1c'. Expected cells are the verbatim pass/fail strings of `scripts/demo_up.sh` (line refs in the check column); observed cells cite `DECISIONS.md:700-706` (D-027, 2026-07-25) — the only recorded observation; no per-check timestamps exist in the repo.

Rows are the verbatim pass/fail strings of `scripts/demo_up.sh` (lines
18-19 define `pass()`/`fail()`; pass/fail lines 40, 45, 61, 63-64, 70-71, 77-78)
and the D-027 live-verification items (`DECISIONS.md:700-706`). Observed
column: the only recorded observation is D-027's "Live verification:
demo_up.sh ALL GREEN" on 2026-07-25 (`DECISIONS.md:701`); no per-check
timestamps exist in the repo.

| feature | check | expected | observed (date, source) |
|---|---|---|---|
| Ollama server | `curl /api/tags` (`demo_up.sh:39-40`) | `[OK]   Ollama serving` else `[FAIL] Ollama unreachable (llama3 segments will fall back to rule)` | ALL GREEN, 2026-07-25 (`DECISIONS.md:701`) |
| llama3 warm | `/api/generate` with `keep_alive 60m` (`demo_up.sh:43-45`) | `[OK]   llama3 warm (keep_alive 60m)` else `[FAIL] llama3 warm-up failed` | ALL GREEN, 2026-07-25 (`DECISIONS.md:701`) |
| API up | health JSON `"status": "ok"` (`demo_up.sh:60-61`) | `[OK]   API serving on :$PORT` else `[FAIL] API did not come up (see /tmp/tg_demo.log)` | ALL GREEN, 2026-07-25 (`DECISIONS.md:701`) |
| real backends | health JSON `"text": "hf"` (`demo_up.sh:62-64`) | `[OK]   real backends confirmed via health endpoint` else `[FAIL] health endpoint does not show real backends — wrong env?` | ALL GREEN, 2026-07-25 (`DECISIONS.md:701`) |
| perception warm | `/analyse/preset multimodal_real` reports `real-hf` (`demo_up.sh:67-71`) | `[OK]   perception warm (toxic-bert/BLIP/Whisper loaded)` else `[FAIL] perception warm-up did not report real-hf` | ALL GREEN, 2026-07-25 (`DECISIONS.md:701`) |
| llama3 via API | `/analyse/compare` returns `"judge_label": "ollama"` (`demo_up.sh:74-78`) | `[OK]   llama3 judging via API (label: ollama)` else `[FAIL] compare fell back to rule (check Ollama)` | ALL GREEN, 2026-07-25 (`DECISIONS.md:701`) |
| overall | `FAILED` flag (`demo_up.sh:81-84`) | `ALL GREEN — open http://127.0.0.1:$PORT/ui  (dashboard: /dashboard)` else `SOMETHING RED — fix before going on stage. Logs: /tmp/tg_demo.log /tmp/ollama_serve.log` | `demo_up.sh ALL GREEN`, 2026-07-25 (`DECISIONS.md:701`) |
| D-027 latch (live) | corrupt upload | "mock+`decode_error` for that request then next image still `real-blip`" | 2026-07-25 (`DECISIONS.md:701-703`); automated since as `tests/test_wrapper_latch.py` (4, offline) |
| D-027 mock caption on upload | corrupt `weapon_gun_photo.png` upload | "cue-based mock caption (no temp-name gibberish)" | 2026-07-25 (`DECISIONS.md:703-704`) |
| D-027 dashboard honesty | injected uncommitted newest T6 run | "flagged `committed: false` on /eval/summary and cleanly restored after removal" | 2026-07-25 (`DECISIONS.md:704-705`) |
| D-027 stream | SSE judge stream | "stream healthy (89 tokens, final `ollama`)" | 2026-07-25 (`DECISIONS.md:706`) |
| CLI `--judge` after subcommand | `python -m triguard.cli run <sample> --judge rule` | exit 0, JSON `TriGuardResult` on stdout | D-027 (manual, 2026-07-25); automated 2026-09-24 as `tests/test_cli.py::test_cli_accepts_judge_flag_after_subcommand` (passed both lanes) |
| CLI one-line errors | missing sample file | `error: file not found: ...` on stderr, exit 1, no traceback (`cli.py:69-71`) | automated 2026-09-24 as `tests/test_cli.py::test_cli_missing_file_exits_1_with_one_line_error` (passed both lanes) |
