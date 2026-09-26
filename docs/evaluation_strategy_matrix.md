# Evaluation strategy matrix (P3 — testing strategy)

Generated 2026-09-24 by the W5 task. Facts, pointers and tables only; every
sentence of analysis or justification is the student's (`[STUDENT]`).
Status cells come from `docs/generated/test_inventory.md` (WSL, primary) and
`docs/generated/test_inventory_offline.md` (Windows offline venv, footnote).
Both were produced by `scripts/test_inventory.py` from a fresh
`pytest -q --junitxml` run on 2026-09-24. "Purpose" cells quote a docstring
or protocol line verbatim (file:line); where no such text exists the cell
says `see §5.2 [STUDENT]`.

Suite counts on 2026-09-24 (after this task's 12 new tests, and with two
in-progress files from another task present — see "Known state" below):

| lane | count line (pytest -q) | source |
|---|---|---|
| WSL `~/.venv-tri` (USE_TF=0 PYTHONPATH=src) | `95 passed, 10 skipped` (2026-09-26) | junit_wsl.xml -> `docs/generated/test_inventory.md` |
| Windows offline venv (PYTHONPATH=src) | `83 passed, 11 skipped` (2026-09-26) | junit_win.xml -> `docs/generated/test_inventory_offline.md` |

Known state (2026-09-26): both lanes green — 83 passed / 11 skipped (Windows offline venv) and
95 passed / 10 skipped (WSL); the transient `tests/test_figures_provenance.py` failure seen while
the P2 checker was being written is resolved. Counts come from `scripts/test_inventory.py --junit`.

## Table 1 — Layer matrix

| Layer | Purpose (quoted) | What is tested | How (mechanism, env, command) | Evidence path | Status (inventory, 2026-09-24) |
|---|---|---|---|---|---|
| unit-schema | "Validation is strict; an invalid output is treated as an evidence-gap signal rather than silently passed through." (`src/triguard/orchestrator/schemas.py:5-6`) | `TextEvidence` bounds; `JudgeInput` needs >= 1 modality and accepts partial; `JudgeOutput` safe-cannot-block / harmful-cannot-allow validators; `TriGuardResult` inherits them (`tests/test_schemas.py:12-54`, 6 tests) | pydantic `ValidationError` assertions, pure Python, no env flags; `PYTHONPATH=src python -m pytest -q tests/test_schemas.py` | `tests/test_schemas.py`; `src/triguard/orchestrator/schemas.py` | WSL 6/6 passed; offline 6/6 passed |
| unit-wrapper | text: `"mock": deterministic keyword heuristic, no weights. For unit tests.` (`src/triguard/models/text_model.py:5`); image: `"mock" (default, offline): deterministic caption + visual risk cues derived from the file name` (`image_model.py:5-6`); audio: "Each component degrades to the mock independently" (`audio_model.py:8`) | mock tier returns evidence with expected cue/tag/score direction; sklearn tier classifies benign vs toxic; empty text input (`tests/test_text_model.py`, `test_image_model.py`, `test_audio_model.py`, 8 tests) | direct `analyse(...)` calls with `force_mode="mock"` or file-name cues; offline; same command with those three files | `tests/test_{text,image,audio}_model.py` | WSL 8/8; offline 8/8 |
| unit-judge-rule | "For the Tier-A prototype demo the rule-based judge is the default because it runs without Ollama, fits 8 GB RAM, and produces fully schema-valid output." (`src/triguard/models/llm_judge.py:10-11`) | benign -> safe/allow; harmful tri-modal -> harmful/block with evidence-referencing rationale; all three modalities flagged; single-modality borderline (`tests/test_llm_judge.py:35-60`, 4 non-`falls_back` tests) | `llm_judge.judge(..., force_mode="rule")` on hand-built `JudgeInput` fixtures; offline | `tests/test_llm_judge.py` | WSL 4/4; offline 4/4 |
| unit-eval-helper | "Fast unit tests for the T7 grounding check (pure function, no models)." (`tests/test_grounding.py:1`); "Fast, offline test for the T6 manifest loader." (`tests/test_run_t6.py:1`); "Fast unit test for failure_analysis (offline; synthetic results.json)." (`tests/test_failure_analysis.py:1`) | grounding cites evidence / detects invented modality; failure taxonomy on a synthetic results file; committed T6 manifest parses (4 tests) | pure functions + tmp_path; offline | `tests/test_grounding.py`, `tests/test_failure_analysis.py`, `tests/test_run_t6.py`; `src/triguard/evaluation/{grounding,failure_analysis,run_t6}.py` | WSL 4/4; offline 4/4 |
| unit-tooling | "Fast, offline tests for scripts/docx_to_md.py (stdlib docx -> anchored Markdown)." (`tests/test_docx_to_md.py:1`); "the card must never carry a typed number" (`tests/test_dataset_cards.py:5-6`) | report-support scripts: docx mirror, citation checker, Wilson CI from envelope, dataset cards vs committed envelope, model-card checker, `smoke_ollama --save` envelope; plus the P2 checker tests (`test_check_report_refs.py`, `test_figures_provenance.py`) | script-level tests via `importlib`/subprocess on tmp dirs; `TRIGUARD_MOCK=1` where a wrapper is imported; offline | `tests/test_{docx_to_md,check_citations,ci_from_envelope,dataset_cards,verify_model_cards,smoke_ollama_save,check_report_refs,figures_provenance}.py` | WSL 34 passed of 34; offline 34 passed of 34 (2026-09-26) |
| regression-fallback (incl. D-027 latch, 4 tests) | "Per-request failures must NOT latch the real tiers off (demo-breaker fix)." (`tests/test_wrapper_latch.py:1`); "If parsing fails it retries once with a stricter prompt; if it fails again the orchestrator falls back to a deterministic rule-based judge so the pipeline never crashes." (`src/triguard/models/llm_judge.py:5-8`); `# never crash the pipeline on a wrapper bug` (`src/triguard/orchestrator/pipeline.py:96`) | (a) Ollama unreachable -> rule + `ollama_unavailable` tag (`test_llm_judge.py:63`); (b) stream path: unreachable / mid-stream death / invalid JSON -> `rule_fallback` final event (`test_llm_judge_stream.py`, 4); (c) D-027 latch: decode failure does not set `_BLIP_BROKEN`, load failure does; Whisper / YAMNet clip failure does not latch (`test_wrapper_latch.py:15,31,45,59`); (d) NEW `test_llm_judge_retry.py` (4): invalid twice -> exactly 2 `_ollama_generate` calls + `judge_output_invalid`; second prompt = first prompt + verbatim stricter suffix (`llm_judge.py:232-233`) and the second reply is returned untagged; valid first reply = 1 call; end-to-end `pipeline.run(judge_mode="ollama")` labels `model_versions["llm_judge"] == "ollama->rule"`; (e) NEW `test_pipeline_shielding.py` (4): each wrapper raising `RuntimeError` -> `TriGuardResult` with confidence / transcript_confidence 0.0, `raw["error"]`, `model_versions[<modality>] == "unknown"`, plus all-three-failing; (f) API temp-file cleanup on save failure (`test_api_phase_d.py:87`) | monkeypatch of `llm_judge._ollama_generate` / `_ollama_generate_stream`, wrapper loaders and `*.analyse`; closed local port `OLLAMA_HOST=http://127.0.0.1:1` for unreachable cases; `TRIGUARD_MOCK=1`; offline | `tests/test_llm_judge_retry.py`, `tests/test_pipeline_shielding.py`, `tests/test_wrapper_latch.py`, `tests/test_llm_judge_stream.py`, `tests/test_llm_judge.py::test_ollama_unavailable_falls_back_to_rule`, `tests/test_api_phase_d.py::test_gather_inputs_cleans_up_on_save_failure` | WSL 18/18; offline 17/17 (the `test_gather_inputs*` case needs fastapi, not collected offline) |
| integration-orchestrator (model_versions honesty D-019 / D-021) | "Orchestrator: ties the wrappers and judge together." (`src/triguard/orchestrator/pipeline.py:2`); "Honest label for the judge that actually answered." (`pipeline.py:44`); protocol T5: "Does the orchestrator combine evidence correctly?" (`docs/evaluation_protocol.md:13`) | text-only run leaves image/audio evidence `None`; tri-modal harmful -> block with all three flagged; no inputs raises `ValueError`; versions + latency attached; `model_versions` token equals `backend_of_mode(raw["mode"])` per evidence and offline defaults are `sklearn`/`mock`/`mock`/`rule` (D-019); env `TRIGUARD_JUDGE=ollama` with `judge_mode=None` is labelled `ollama` or `ollama->rule`, never `rule` (D-021) (`tests/test_orchestrator.py:6-62`, 6 tests) | `pipeline.run(...)` with offline defaults; monkeypatched env + closed port for the D-021 case | `tests/test_orchestrator.py`; DECISIONS.md D-019 (line 375), D-021 (line 430) | WSL 6/6; offline 6/6 |
| functional-api-cli | "A thin HTTP layer so a non-technical reviewer can submit content and read the structured decision." (`src/triguard/api/main.py:3-4`); "Subcommand-level --judge wins over the top-level flag." (`src/triguard/cli.py:19`) | API: health, analyse harmful/benign (`test_api.py`, 3); presets list/run/404, compare + stream offline fallback, monkeypatched token stream, dashboard page, and `/eval/summary` verbatim-vs-file assertion — every served number compared to the committed `results.json` it names (`tests/test_api_phase_d.py:184-227`) (8 non-slow, non-regression); NEW CLI (`tests/test_cli.py`, 4): `python -m triguard.cli run data/sample_inputs/sample_harmful.json` exits 0 and stdout re-validates as `TriGuardResult` with mock backends; `--judge rule` accepted after AND before the subcommand; missing file -> exit 1, one-line `error: file not found:` on stderr, no traceback | FastAPI `TestClient` (skips at module level without `fastapi`/`httpx`/`python-multipart`, `test_api_phase_d.py:20-27`); CLI via `subprocess.run([sys.executable, "-m", "triguard.cli", ...], env TRIGUARD_MOCK=1 PYTHONPATH=src USE_TF=0, cwd=repo root)` | `tests/test_api.py`, `tests/test_api_phase_d.py`, `tests/test_cli.py` | WSL 15/15; offline 4/4 (`test_api*.py` not collected: `fastapi` absent — importorskip) |
| real-backend-slow (runtime skip conditions) | "Tests marked ``@pytest.mark.slow`` (network / model-download / dataset loads) are skipped by default so the fast lane stays fully offline" (`tests/conftest.py:4-6`); "Even with ``--run-slow`` it SKIPS cleanly (never fails) when Ollama is not reachable, so no CI run can depend on Ollama being up." (`tests/test_llm_judge_ollama.py:3-5`) | toxic-bert benign low / toxic high with `raw["mode"]=="real-hf"` and `model_name` (`test_text_model_hf.py:17-29`, 2; no runtime skip beyond the marker — first run downloads ~440 MB, docstring line 8); BLIP caption shape + `raw["mode"]=="real-blip"` (`test_image_model_blip.py:19`, 1; ~990 MB download, line 8); OCR reads DANGER/WEAPON overlay (`test_image_model_ocr.py:21`; module `importorskip("rapidocr_onnxruntime")` line 13, `pytest.skip` if `ocr_test.png` missing lines 23-24); real audio shape (`test_audio_model_real.py:24`; `pytest.skip` if `data/sample_inputs/audio_test.wav` absent lines 26-27); Ollama judge returns schema-valid `JudgeOutput` (`test_llm_judge_ollama.py:50-53`, skip when `/api/tags` unreachable); API compare with real llama3 (`test_api_phase_d.py:249-253`, same skip) | `PYTHONPATH=src python -m pytest -q --run-slow <file>` in WSL `~/.venv-tri` with `USE_TF=0`; teardown SIGSEGV caveat for the combined venv (`docs/implementation_notes.md:384-386`) | the six files named; `tests/conftest.py:34-43` (skip injection) | WSL 7 collected / 7 skipped (fast lane); offline 5 collected / 5 skipped (`test_image_model_ocr.py` + `test_api_phase_d.py` not collected). No `--run-slow` run was made by this task. |
| dataset-loader-slow | "asserts the loader's output shape — not specific numbers." (`tests/test_t2_dataset.py:10`); "SKIPS cleanly (never fails) when the dataset is unreachable" (`tests/test_run_t3.py:4`, `test_run_t4.py:4`) | civil_comments stream of <= 10 rows with `force_download=True` (`test_t2_dataset.py:22-29`, no runtime skip); Memotion loader shape (`test_run_t3.py:19-24`, skip on exception); LibriSpeech + ESC-50 loader shape (`test_run_t4.py:22-28`, skip on exception) | `--run-slow`, network, `datasets` package | `tests/test_t2_dataset.py`, `tests/test_run_t3.py`, `tests/test_run_t4.py` | WSL 3/3 skipped (fast lane); offline 3/3 skipped |
| AI component: toxic-bert (text, `unitary/toxic-bert`) | T2: "Runs the *real* text wrapper ... over a small, reproducible sample of a public toxicity dataset and reports binary classification metrics" (`src/triguard/evaluation/run_t2.py:4-7`) | T2 Civil Comments n=500 seed 42, hf run vs sklearn floor (Table E3); slow unit `test_text_model_hf.py` (2); latch not applicable (text tier has no per-request latch test) | `PYTHONPATH=src python -m triguard.evaluation.run_t2 --source civil_comments --sample-size 500 --seed 42` with `TRIGUARD_TEXT_BACKEND=hf` (protocol lines 40-41) | `outputs/evaluation/20260623-124802/t2/results.json` (hf), `outputs/evaluation/20260623-074102/t2/results.json` (sklearn); `docs/report_evidence_tables.md` Table E3 / E3a | eval: committed; unit: slow, skipped in fast lane (2 skipped both lanes) |
| AI component: BLIP + RapidOCR (image) | T3: "BLIP is a CAPTIONER, not a hate classifier, and does NOT OCR the text baked into a meme" (`src/triguard/evaluation/run_t3.py:7-8`) | T3 Memotion n=50 flag-vs-label + `ocr_ablation` (Tables E4, E4b); slow units `test_image_model_blip.py` (1), `test_image_model_ocr.py` (1); D-027 latch regression `test_wrapper_latch.py:15,31` (2, offline) | `run_t3` with `TRIGUARD_IMAGE_BACKEND=blip` (+ `TRIGUARD_IMAGE_OCR=1` for the ablation) | `outputs/evaluation/20260705-111002/t3/results.json` (keys `metrics_pipeline`, `metrics_text_only_baseline`, `ocr_ablation`); Table E4 / E4b | eval: committed; slow units skipped in fast lane; latch tests 2/2 passed both lanes |
| AI component: Whisper (audio ASR, `tiny`) | T4: "**Whisper WER** on LibriSpeech test-clean (CC BY 4.0). Corpus word error rate via ``jiwer``" (`src/triguard/evaluation/run_t4.py:6-7`) | T4 WER corpus / mean-per-clip n=50 (Table E5); slow unit `test_audio_model_real.py` (1, skips without `audio_test.wav`); latch regression `test_wrapper_latch.py:45` (1) | `run_t4` with `TRIGUARD_AUDIO_BACKEND=real`, `USE_TF=0`, ffmpeg on PATH | `outputs/evaluation/20260704-153729/t4/results.json` (`whisper_wer`); Table E5 | eval: committed; slow unit skipped; latch 1/1 passed |
| AI component: YAMNet (audio events, `yamnet/1`) | T4: "**YAMNet event accuracy** on ESC-50 ... top-1 and top-5 hit rate against an APPROXIMATE, hand-built ESC-50 -> AudioSet display-name map" (`run_t4.py:9-11`) | T4 top-1 / top-5 n=50 (Table E5); same slow unit as Whisper; latch regression `test_wrapper_latch.py:59` (1); rule-judge tag vocabulary note D-033 (`DECISIONS.md:878`) | as Whisper | `outputs/evaluation/20260704-153729/t4/results.json` (`yamnet_events`); Table E5 | eval: committed; latch 1/1 passed |
| AI component: llama3 judge (Ollama, `llama3:8b-instruct-q4_K_M`) | "Headline = the **llama3 / ollama** grounding rate ... that is the judge whose explanation quality is genuinely in question." (`src/triguard/evaluation/run_t7.py:7-9`) | T7 grounding rate on v1 n=18 (Tables E7 / E7b); T6 two-judge comparison on v2 n=24, ollama run (Table E6c, D-029); T8: NO llama3 T8 run — E8 context latency comes "from D-015/D-025 live runs, not T8" (`docs/report_evidence_tables.md:275`); offline contract tests: retry (`test_llm_judge_retry.py`, 4), stream (`test_llm_judge_stream.py`, 4), unreachable (`test_llm_judge.py:63`); slow real-path `test_llm_judge_ollama.py`, `test_api_phase_d.py::test_compare_real_ollama` | `run_t7 --judge ollama`; `run_t6 --judge ollama`; Ollama server on `localhost:11434` | `outputs/evaluation/20260705-113456/t7/results.json`; `outputs/evaluation/20260725-191055/t6/results.json`; Tables E6c, E7, E7b, E8 (context note) | eval: committed; offline contract tests 9/9 passed both lanes; real-path slow tests skipped in fast lane |
| AI component: rule judge (deterministic) | "The rule judge grounds ~100% by construction (it builds the rationale by concatenating the evidence it saw), so its rate is reported but noted as trivial." (`run_t7.py:9-11`) | T6 v2 ablation, rule run (Table E6); T6 two-judge rule run (Table E6c); T8 latency / RSS per backend config, rule judge (Table E8); unit `test_llm_judge.py` (4) | `run_t6` (default judge rule); `run_t8` mock (win32) and real (WSL) | `outputs/evaluation/20260705-160858/t6/results.json`; `outputs/evaluation/20260725-191000/t6/results.json`; `outputs/evaluation/20260705-113354/t8/`, `outputs/evaluation/20260705-113639/t8/`; Tables E6, E6c, E8 | eval: committed; unit 4/4 passed both lanes |
| user testing | see §5.2 [STUDENT] | none with participants; contingent peer review not pursued (`docs/ethics.md:12-14`, `DECISIONS.md:58`); author-only T7 usefulness via `scripts/rate_t7.py` | `scripts/rate_t7.py --init` -> `data/t7_ratings.json` (exists: 18 entries, all `usefulness_1to5` = null on 2026-09-24) -> `--merge` | `data/t7_ratings.json`; `docs/report_evidence_tables.md` Table E9 rows "T7 raters", "T7 scale wording" | status pending (no rating filled) |
| coverage (T5 branch coverage) | protocol: "Coverage measured via `pytest-cov`; target > 80 % branch coverage on `pipeline.py`." (`docs/evaluation_protocol.md:60`) | branch coverage of `triguard.orchestrator` + `triguard.models.llm_judge`, fast lane only (teardown SIGSEGV caveat, `docs/implementation_notes.md:384-386`) | `bash scripts/coverage_report.sh` in WSL; refuses with an install line when `import pytest_cov` fails | `scripts/coverage_report.sh`; would write `outputs/coverage/<ts>/{coverage.xml,coverage_term.txt,junit.xml,RUN_INFO.txt}` | not measured — pytest-cov absent (script refuses; ran 2026-09-24 in WSL, exit 2, nothing installed) |
| CI | see §5.2 [STUDENT] | no CI service / workflow file in the repo (no `.github/`, no CI config found) | inventory regenerated by `scripts/test_inventory.py` after a `pytest -q --junitxml` run, per interpreter | `docs/generated/test_inventory.md` (WSL), `docs/generated/test_inventory_offline.md` (offline) | none; inventory regenerated by `scripts/test_inventory.py` |

## Table 2 — Protocol claim -> discharging test

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

## For integration

Owned by the Integrate stage (`docs/report_evidence_tables.md`,
`DECISIONS.md`); drafts below are copy-ready.

### Table E1a — per-layer test inventory (WSL `~/.venv-tri`, 2026-09-26, fast lane)

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

### Table E1b — protocol claim -> discharging test

Body = Table 2 above (columns protocol line | claim | discharging test |
before | after | note). Copy verbatim.

### Table E1c — manual functional checks

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
| overall | `FAILED` flag (`demo_up.sh:81-84`) | `ALL GREEN — open http://127.0.0.1:$PORT/ui  (dashboard: /dashboard)` else `SOMETHING RED — fix before going on stage.` | `demo_up.sh ALL GREEN`, 2026-07-25 (`DECISIONS.md:701`) |
| D-027 latch (live) | corrupt upload | "mock+`decode_error` for that request then next image still `real-blip`" | 2026-07-25 (`DECISIONS.md:701-703`); automated since as `tests/test_wrapper_latch.py` (4, offline) |
| D-027 mock caption on upload | corrupt `weapon_gun_photo.png` upload | "cue-based mock caption (no temp-name gibberish)" | 2026-07-25 (`DECISIONS.md:703-704`) |
| D-027 dashboard honesty | injected uncommitted newest T6 run | "flagged `committed: false` on /eval/summary and cleanly restored after removal" | 2026-07-25 (`DECISIONS.md:704-705`) |
| D-027 stream | SSE judge stream | "stream healthy (89 tokens, final `ollama`)" | 2026-07-25 (`DECISIONS.md:706`) |
| CLI `--judge` after subcommand | `python -m triguard.cli run <sample> --judge rule` | exit 0, JSON `TriGuardResult` on stdout | D-027 (manual, 2026-07-25); automated 2026-09-24 as `tests/test_cli.py::test_cli_accepts_judge_flag_after_subcommand` (passed both lanes) |
| CLI one-line errors | missing sample file | `error: file not found: ...` on stderr, exit 1, no traceback (`cli.py:69-71`) | automated 2026-09-24 as `tests/test_cli.py::test_cli_missing_file_exits_1_with_one_line_error` (passed both lanes) |

### Table E9 — additional row (draft)

| track | protocol plan (docs/evaluation_protocol.md) | actual (pointer) | why (decision) |
|---|---|---|---|
| T5 coverage | `pytest-cov`, > 80 % branch coverage on `pipeline.py` (line 60) | not measured (pytest-cov not installed; `scripts/coverage_report.sh` ready, refuses cleanly, ran 2026-09-24 exit 2) | dev dependency needs author approval (CLAUDE.md rule 4); P3 DECISIONS draft below |

### DECISIONS.md draft — P3: retry/shielding/CLI tests + test inventory tooling

```
## Decision 0NN: P3 testing strategy — retry/shielding/CLI tests + inventory tooling
Date: 2026-09-24
Status: draft — Options/Decision/Reason to be completed by the author; pytest-cov dev dependency proposed, not installed

Context: docs/evaluation_protocol.md T5 (lines 56-60) names three fixture-
driven behaviours and a pytest-cov target; before this change only the
text-only case (test_orchestrator.py:6) and the stream-path invalid-JSON case
(test_llm_judge_stream.py:91) had tests; the retry-once contract
(llm_judge.py:223-238), wrapper-failure shielding (pipeline.py:93-125) and the
CLI entry point (cli.py) had none; test counts in docs were typed by hand.
Facts on record for the author's Options / Decision / Reason fields:
- candidate options listed by the P3 task: (a) leave the protocol rows as
  "untested" in E9; (b) add offline tests that discharge lines 58-59 and
  generate the inventory mechanically; (c) also install pytest-cov to
  discharge line 60;
- files added: tests/test_llm_judge_retry.py (4 tests), tests/test_pipeline_
  shielding.py (4), tests/test_cli.py (4) — offline, monkeypatch/subprocess,
  no new dependency; scripts/test_inventory.py (stdlib: collects with the
  calling interpreter, classifies by an explicit file-basename table, diffs
  collected files against tests/test_*.py to expose importorskip drop-outs,
  folds in a --junitxml run, exits 1 on any unclassified id; outputs
  docs/generated/test_inventory.md (WSL) and
  docs/generated/test_inventory_offline.md); scripts/coverage_report.sh
  (refuses without pytest_cov; otherwise fast lane only — teardown SIGSEGV,
  docs/implementation_notes.md:384-386);
- pytest-cov: not installed; listed as a PROPOSED dev dependency
  (requirements-dev / requirements-full) pending the author's approval
  (CLAUDE.md rule 4);
- protocol status after the change (docs/evaluation_strategy_matrix.md
  Table 2): line 58 tested-stream-only -> tested; line 59 untested -> tested;
  line 60 not measured (unchanged).
Options considered: [STUDENT]
Decision: [STUDENT]
Reason: [STUDENT]
Impact: fast lanes 2026-09-26 (all files landed, inventories regenerated): WSL 95 passed / 10 skipped / 0 failed,
offline 83 passed / 11 skipped / 0 failed (baseline 71 + 12 and 59 + 12 new tests, plus the
P2 checker tests from the same sprint). Schemas,
judge contract and public API untouched. Table E9 gains the "T5 coverage"
row; Tables E1a-E1c added.
```

## [STUDENT] pointers for §5.1 / §5.2 (and the §4.6 struggle)

Facts and file:line anchors only; the sentences are yours.

- Fast-vs-slow rationale: `tests/conftest.py:4-9` (docstring: slow = "network /
  model-download / dataset loads", skipped by default so "the fast lane stays
  fully offline"; two commands shown), `:34-43` (skip injected at collection
  unless `--run-slow`). CLAUDE.md "Code conventions" bullet: "default test run
  must not hit the network".
- Never-fail skip policy for real backends: `tests/test_llm_judge_ollama.py:3-6`
  ("SKIPS cleanly (never fails) ... so no CI run can depend on Ollama being
  up"); same wording in `tests/test_run_t3.py:4-5`, `tests/test_run_t4.py:4-5`;
  file-presence skips at `tests/test_audio_model_real.py:26-27`,
  `tests/test_image_model_ocr.py:13,23-24`; `tests/test_api_phase_d.py:20-27`
  module-level importorskip so the offline venv skips at collection instead of
  erroring (see the "not collected" list in `docs/generated/test_inventory_offline.md`).
- Honesty properties asserted by tests (each is an assertion, not a claim):
  `model_versions` token == `backend_of_mode(raw["mode"])` per evidence and
  offline defaults `sklearn`/`mock`/`mock`/`rule` (`tests/test_orchestrator.py:36-54`,
  D-019); env-driven ollama never labelled `rule` (`test_orchestrator.py:57-62`,
  D-021); fallback tagged `ollama_unavailable` / `judge_output_invalid` and
  labelled `ollama->rule` (`tests/test_llm_judge.py:63-73`,
  `tests/test_llm_judge_retry.py:78-94,133-156`); wrapper failure -> `unknown`
  backend token, confidence 0.0, `raw["error"]` (`tests/test_pipeline_shielding.py`);
  `/eval/summary` numbers equal the committed file they name
  (`tests/test_api_phase_d.py:184-227`); dataset card numbers equal the
  committed envelope (`tests/test_dataset_cards.py:3-6`).
- D-027 story for §4.6: `DECISIONS.md:667-705` — audit found that "any per-file
  decode failure latched the real BLIP tier off for the whole server session"
  (lines 672-674); fix = split model-load (latching) from per-request work
  (lines 682-686); regression tests `tests/test_wrapper_latch.py:15,31,45,59`
  (4); live verification lines 700-705. Related: `USE_TF=0` segfault (D-016,
  `DECISIONS.md:260`; `demo_up.sh:47-49` comment); teardown SIGSEGV note
  `docs/implementation_notes.md:384-386`.
- What the suite does NOT show (facts): no branch-coverage number (pytest-cov
  absent; `scripts/coverage_report.sh` refuses); no 200-input T1 run
  (`Table E9` row T1; only n=14 mock smoke); no CI service; slow real-path tests
  were not executed by this task (all 10 skipped in both lanes on 2026-09-24);
  the text-only claim's "only text wrapper called" call-count is not asserted
  (`tests/test_orchestrator.py:6-11`); the protocol's forced `borderline` on
  judge failure is NOT what the code does — the rule judge's own label is
  returned, tagged (`llm_judge.py:99-103`; Table E9 row "T5 judge failure path");
  no participant user testing (`docs/ethics.md:12-14`, `DECISIONS.md:58`);
  T7 usefulness column still all-null (`data/t7_ratings.json`, 18 entries,
  2026-09-24); wrapper-level tests (`tests/test_{text,image,audio}_model.py`) call the
  mock and sklearn tiers only; no fast-lane test asserts a model accuracy
  number (accuracy values: the T2-T4 envelopes under `outputs/evaluation/`).
- Test-count provenance for Ch5.2: quote the two count lines from the header
  of this file (or regenerate: `python scripts/test_inventory.py --env-label
  "<label>" --junit <xml> --out docs/generated/test_inventory.md`), not
  hand-typed numbers; `docs/report_evidence_tables.md` Table E1 rows dated
  2026-07-06 / 2026-09-24 are the earlier baselines (45/10, 33/11, 52/10, 40/11).
