# Video number card — every number visible in shots 7-8 (verbatim)

Purpose: while recording shots 7 (/dashboard) and 8 (critical evaluation on
screen) of `docs/Video_Shot_List_Final.md`, every figure on screen is listed
here with the file, key and raw line it comes from, copied verbatim (no
rounding). Values were read on 2026-09-24 from the committed
`outputs/evaluation/<run>/<track>/results.json` files; the raw-line numbers
are `grep -n` results on those files. No narration text here.

What the dashboard prints is chosen by `src/triguard/api/main.py`
`_TRACK_KEYS` (`:405-418`), `_trim_track` (`:421-439`) and the newest-run rule
in `/eval/summary` (`:469`, sorted scan `:481`, `tracks[track] = entry` `:515`;
T2 is kept per `config.backend` `:503-508`, T8 per `config.mock` `:509-513`).
Each section also prints `source: <file> (run <id>)` and `config: k=v, ...`
(`src/triguard/api/static/dashboard.html:73-79`).

## Run -> E-table map

| track | run on the dashboard | results.json | E-table in `docs/report_evidence_tables.md` |
|---|---|---|---|
| T2 hf | 20260623-124802 | `outputs/evaluation/20260623-124802/t2/results.json` | E3 (`:46-61`) |
| T2 sklearn (also on screen — T2 keeps both backends) | 20260623-074102 | `outputs/evaluation/20260623-074102/t2/results.json` | E3 (`:46-61`) |
| T3 | 20260705-111002 | `outputs/evaluation/20260705-111002/t3/results.json` | E4 (`:63-76`), E4b (`:77-91`) |
| T4 | 20260704-153729 | `outputs/evaluation/20260704-153729/t4/results.json` | E5 (`:92-107`) |
| T6 rule | 20260725-191000 | `outputs/evaluation/20260725-191000/t6/results.json` | E6c (`:142-195`); E6 (`:108-127`) cites the earlier rule run 20260705-160858 with identical accuracy / macro-F1 cells |
| T6 ollama — **dashboard shows this one** | 20260725-191055 | `outputs/evaluation/20260725-191055/t6/results.json` | E6c (`:142-195`) |
| T7 | 20260705-113456 | `outputs/evaluation/20260705-113456/t7/results.json` | E7 (`:196-245`), E7b (`:247-265`) |
| T8 mock | 20260705-113354 | `outputs/evaluation/20260705-113354/t8/results.json` | E8 (`:267-280`) |
| T8 real | 20260705-113639 | `outputs/evaluation/20260705-113639/t8/results.json` | E8 (`:267-280`) |

Dashboard T6 rule (`main.py:481` sorted scan; `:515` overwrite): run dirs
sort as strings, `20260725-191055` > `20260725-191000` > `20260705-160858`
> `20260704-221056`, so the ollama run is the last `t6` written into
`tracks["t6"]`. Table E6 (`report_evidence_tables.md:108-119`) cites rule run
`20260705-160858`, multimodal accuracy `0.625`; on screen the T6 section says
`config: judge=ollama, ...` and multimodal accuracy `0.4583`. Both runs are
in Table E6c (`:160-161`).

## T2 — text track (dashboard `sectionT2`, `dashboard.html:87-109`) -> Table E3

File A (hf): `outputs/evaluation/20260623-124802/t2/results.json`
File B (sklearn): `outputs/evaluation/20260623-074102/t2/results.json`

| on screen | key | value (verbatim) | file:line |
|---|---|---|---|
| source / run | — | `20260623-124802` (hf), `20260623-074102` (sklearn) | dir names |
| config (hf) | `config` | `backend=hf, sample_size=500, seed=42, threshold=0.5, wrapper_mode=real-hf, run_env=wsl-ubuntu` | A `config` |
| toxic-bert (hf) accuracy | `accuracy` | `0.928` | A:31 |
| toxic-bert (hf) macro-F1 | `macro_f1` | `0.6476` | A:32 |
| toxic class precision | `per_class.toxic.precision` | `0.4091` | A:40 |
| toxic class recall | `per_class.toxic.recall` | `0.2812` | A:41 |
| toxic class F1 | `per_class.toxic.f1` | `0.3333` | A:42 |
| class balance (printed as JSON) | `class_balance` | `{"non-toxic":468,"toxic":32}` | A `class_balance` |
| sklearn TF-IDF baseline accuracy | `accuracy` | `0.542` | B:28 |
| sklearn TF-IDF baseline macro-F1 | `macro_f1` | `0.4149` | B:29 |
| n (in section text via config) | `n_samples` | `500` | A:10, B:10 |
| limitations (bullets, de-duplicated across A and B) | `limitations[]` | A: 3 strings (binary scheme; toxic-bert real-hf; crowd rating thresholded at 0.5) | A `limitations` |

Not on screen but in E3 (`:54`): sklearn toxic P/R/F1 `0.0809` / `0.5938` / `0.1423` (B:37-39).

## T3 — image-text track (`sectionT3`, `dashboard.html:111-129`) -> Table E4 / E4b

File: `outputs/evaluation/20260705-111002/t3/results.json`

| on screen | key | value (verbatim) | line |
|---|---|---|---|
| config | `config` | `sample_size=50, seed=42, decision_rule=predicted_positive = risk_label in {borderline, harmful}, judge=rule, text_backend=hf, image_backend=blip, run_env=wsl-ubuntu-py312-tri` | `config` (judge at :14) |
| pipeline (image + dataset text) F1 | `metrics_pipeline.f1` | `0.4` | :31 |
| text-only baseline F1 | `metrics_text_only_baseline.f1` | `0.3636` | :38 |
| OCR ablation heading | `ocr_ablation.measured_on` | `image track alone (dataset text dropped)` | `ocr_ablation` |
| BLIP caption only F1 | `ocr_ablation.image_only_noocr.f1` | `0.0606` | :136 |
| +OCR -> keyword cues F1 | `ocr_ablation.image_only_ocr_cues.f1` | `0.0606` | :144 |
| +OCR -> toxic-bert text track F1 | `ocr_ablation.image_only_ocr_to_text.f1` | `0.4348` | :152 |
| delta F1 (OCR->text route) | `ocr_ablation.delta_f1_ocr_to_text` | `0.3742` | :158 |
| warn box | `ocr_ablation.note` | starts `Two OCR routes vs BLIP-caption-only.` | `ocr_ablation.note` |
| limitations | `limitations[]` | 6 strings; `[2]` = `this is a flag-vs-label decision measure, NOT a trained-classifier F1` | `limitations` |
| n | `n_samples` | `50` | :23 |

E4 also carries pipeline precision `0.6923` (:29), recall `0.2812` (:30), accuracy `0.46` (:32), AUROC `0.566`; baseline precision `0.6667` (:36), recall `0.25` (:37), accuracy `0.44` (:39) — not drawn on the dashboard.

## T4 — audio track (`sectionT4`, `dashboard.html:131-146`) -> Table E5

File: `outputs/evaluation/20260704-153729/t4/results.json`

| on screen | key | value (verbatim) | line |
|---|---|---|---|
| config | `config` | `sample_size=50, seed=42, run_env=wsl-ubuntu-py312-tri` | `config` |
| corpus WER | `whisper_wer.wer_corpus` | `0.0971` | :29 |
| mean per clip WER | `whisper_wer.wer_mean_per_clip` | `0.1314` | :30 |
| YAMNet top-1 (strict lower bound) | `yamnet_events.top1_rate` | `0.32` | :37 |
| YAMNet top-5 (fair headline) | `yamnet_events.top5_rate` | `0.66` | :38 |
| n per sub-track (in E5, not drawn) | `whisper_wer.n`, `yamnet_events.n` | `50`, `50` | :28, :36 |
| limitations | `limitations[]` | 6 strings (AudioSet ids-only substitute; approximate ESC-50 map; clean read speech best case; ...) | `limitations` |

## T6 — tri-modal ablation (`sectionT6`, `dashboard.html:148-165`) -> Table E6 / E6c

Dashboard shows run **20260725-191055** (`config.judge` = `ollama`, :7).
Rule run 20260725-191000 (`config.judge` = `rule`, :7) has the same line
layout; both listed.

| on screen (ollama run = what the dashboard prints) | key | ollama 20260725-191055 | rule 20260725-191000 | line (both files) |
|---|---|---|---|---|
| config | `config` | `judge=ollama, text_backend=hf, image_backend=blip, audio_backend=real, run_env=wsl-ubuntu-py312-tri` | `judge=rule, ...` (same other keys) | `config` |
| n items (not drawn; in provenance context) | `n_items` | `24` | `24` | :13 |
| text only accuracy | `conditions.text_only.accuracy` | `0.5909` | `0.5909` | :22 |
| image only accuracy | `conditions.image_only.accuracy` | `0.25` | `0.5` | :66 |
| audio only accuracy | `conditions.audio_only.accuracy` | `0.1667` | `0.5` | :110 |
| multimodal accuracy | `conditions.multimodal.accuracy` | `0.4583` | `0.625` | :154 |
| text only macro-F1 | `conditions.text_only.macro_f1` | `0.4883` | `0.4786` | :23 |
| image only macro-F1 | `conditions.image_only.macro_f1` | `0.1333` | `0.2222` | :67 |
| audio only macro-F1 | `conditions.audio_only.macro_f1` | `0.0952` | `0.2222` | :111 |
| multimodal macro-F1 | `conditions.multimodal.macro_f1` | `0.4722` | `0.4945` | :155 |
| per-condition n (not drawn) | `conditions.<c>.n` | text 22 / image 8 / audio 6 / multimodal 24 | same | :21, :65, :109, :153 |
| provenance box | `manifest_provenance` | starts `v2 evaluation set: drafted with AI assistance, then reviewed, edited and approved by the author (2026-07-05).` | identical | `manifest_provenance` |
| confounder box | `cross_modal_ablation.n_cross_modal_harmful` / `.note` | `0` / `no cross_modal harmful items in the manifest; add confounder cases to populate this table` | identical | `cross_modal_ablation` |
| limitations | `limitations[]` | 5 strings; `[4]` = `ollama/llama3 judge (non-deterministic; falls back to rule when unreachable — check model_versions in per-run logs)` | `[4]` = `rule judge (deterministic)`; `[0..3]` identical | `limitations` |

E6 (`report_evidence_tables.md:108-119`) source is run `20260705-160858`
(`outputs/evaluation/20260705-160858/t6/results.json`, `config.judge` =
`rule`); its multimodal accuracy `0.625` / macro-F1 `0.4945` match the
20260725-191000 rule cells above (E6c caveat `:186-191` records that only the
latencies differ).

## T7 — rationale grounding (`sectionT7`, `dashboard.html:167-176`) -> Table E7 / E7b

File: `outputs/evaluation/20260705-113456/t7/results.json`

| on screen | key | value (verbatim) | line |
|---|---|---|---|
| bar label `grounding rate (judge: ollama, n=18)` | `judge`, `n` | `ollama`, `18` | :4, :5 |
| grounding rate | `grounding_rate` | `1.0` | :6 |
| invented (unsupplied) modalities cited | `invented_modality_count` | `0` | :7 |
| config | `config` | `text_backend=hf, image_backend=blip, audio_backend=real, run_env=wsl-ubuntu-py312-tri` | `config` |
| warn box | `note` | `grounding_rate = fraction of rationales citing >=1 evidence token. The rule judge grounds ~1.0 by construction (it concatenates the evidence), so the meaningful headline is the ollama/llama3 rate. usefulness_1to5 is left blank for a human rater.` | `note` |

E7 caveat line to hold beside the `1.0` on screen (verbatim from
`docs/report_evidence_tables.md:223-224`): `18/18 grounded, of which 17
native llama3 + 1 suspected rule-fallback of unrecorded cause` — short form
used in the shot list: `18/18 grounded; 17 native + 1 suspected rule-fallback
(MB1)`. The dashboard prints none of the E7 caveats (`:242-245`). Set = v1
18-item manifest (`:208-213`); `usefulness_1to5` null for all 18
(`:237-239`; `docs/feedback_traceability.md:42`).

## T8 — latency and memory (`sectionT8`, `dashboard.html:178-205`) -> Table E8

File M (mock): `outputs/evaluation/20260705-113354/t8/results.json`
File R (real): `outputs/evaluation/20260705-113639/t8/results.json`

| on screen | key | value (verbatim) | file:line |
|---|---|---|---|
| config (real) | `config` | `judge=rule, mock=false, text_backend=hf, image_backend=blip, audio_backend=real, run_env=wsl-ubuntu-py312-tri` | R `config` |
| config (mock) | `config` | `judge=rule, mock=true, text_backend=sklearn, image_backend=mock, audio_backend=mock, run_env=win32` | M `config` |
| mock p50 | `latency_ms.p50` | `0.0` ms | M:14 |
| mock p95 | `latency_ms.p95` | `0.1` ms | M:15 |
| real p50 | `latency_ms.p50` | `31.1` ms | R:14 |
| real p95 | `latency_ms.p95` | `4075.1` ms | R:15 |
| real cold start | `latency_ms.cold_start_ms` | `4075.1` ms | R:18 |
| peak RSS mock | `peak_rss_mb` | `34.5` MB | M:20 |
| peak RSS real | `peak_rss_mb` | `2873.7` MB | R:20 |
| n (not drawn) | `n` | `18` | M:4, R:4 |
| warn box | `note` | `cold_start_ms is the first-call latency (includes model load for real backends). Run once per backend config to compare mock vs real.` | R `note` (M identical) |

Not drawn: mock `cold_start_ms` `0.1` (M:18).

## Suite counts quoted in the video plan (not dashboard numbers)

Measured 2026-09-24 on the uncommitted working tree (sibling tasks' tests
included):
- Windows offline venv: `83 passed, 11 skipped` (`<windows-venv> -m pytest -q`, `PYTHONPATH=src`).
- WSL `~/.venv-tri`: `95 passed, 10 skipped` (`USE_TF=0 PYTHONPATH=src ~/.venv-tri/bin/python -m pytest -q`).
Counts rose during this session (70->83, 82->95) as sibling tasks added
tests; re-measure before recording. The committed README (`README.md:22-25`) still
says 52/10 and 40/11.
