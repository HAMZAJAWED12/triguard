# Test inventory (generated — do not hand-edit)

- date: 2026-09-26
- interpreter label: WSL ~/.venv-tri
- python: 3.12.13 (Linux)
- pytest 9.1.1
- generator: `scripts/test_inventory.py` (stdlib only)
- collect command: `python -m pytest --collect-only -q -p no:cacheprovider tests` -> 105 tests collected in 1.20s
- slow-select command: `python -m pytest --collect-only -q -p no:cacheprovider -m slow tests` -> 10/105 tests collected (95 deselected) in 1.22s
- junit: `junit_wsl.xml` from `python -m pytest -q --junitxml=...` (fast lane: no --run-slow; slow tests appear as skipped)

Totals: 105 collected test ids in 32 files; 10 slow-marked; 0 test module(s) not collected (module-level importorskip); 0 unclassified.

## Per-layer

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

## Per-file

| file | layer(s) | collected | slow-marked | passed | skipped | failed |
|---|---|---|---|---|---|---|
| `tests/test_api.py` | functional-api-cli | 3 | 0 | 3 | 0 | 0 |
| `tests/test_api_phase_d.py` | functional-api-cli, real-backend-slow, regression-fallback | 10 | 1 | 9 | 1 | 0 |
| `tests/test_audio_model.py` | unit-wrapper | 2 | 0 | 2 | 0 | 0 |
| `tests/test_audio_model_real.py` | real-backend-slow | 1 | 1 | 0 | 1 | 0 |
| `tests/test_check_citations.py` | unit-tooling | 5 | 0 | 5 | 0 | 0 |
| `tests/test_check_report_refs.py` | unit-tooling | 7 | 0 | 7 | 0 | 0 |
| `tests/test_ci_from_envelope.py` | unit-tooling | 2 | 0 | 2 | 0 | 0 |
| `tests/test_cli.py` | functional-api-cli | 4 | 0 | 4 | 0 | 0 |
| `tests/test_dataset_cards.py` | unit-tooling | 2 | 0 | 2 | 0 | 0 |
| `tests/test_docx_to_md.py` | unit-tooling | 3 | 0 | 3 | 0 | 0 |
| `tests/test_failure_analysis.py` | unit-eval-helper | 1 | 0 | 1 | 0 | 0 |
| `tests/test_figures_provenance.py` | unit-tooling | 5 | 0 | 5 | 0 | 0 |
| `tests/test_grounding.py` | unit-eval-helper | 2 | 0 | 2 | 0 | 0 |
| `tests/test_image_model.py` | unit-wrapper | 2 | 0 | 2 | 0 | 0 |
| `tests/test_image_model_blip.py` | real-backend-slow | 1 | 1 | 0 | 1 | 0 |
| `tests/test_image_model_ocr.py` | real-backend-slow | 1 | 1 | 0 | 1 | 0 |
| `tests/test_llm_judge.py` | regression-fallback, unit-judge-rule | 5 | 0 | 5 | 0 | 0 |
| `tests/test_llm_judge_ollama.py` | real-backend-slow | 1 | 1 | 0 | 1 | 0 |
| `tests/test_llm_judge_retry.py` | regression-fallback | 4 | 0 | 4 | 0 | 0 |
| `tests/test_llm_judge_stream.py` | regression-fallback | 4 | 0 | 4 | 0 | 0 |
| `tests/test_orchestrator.py` | integration-orchestrator | 6 | 0 | 6 | 0 | 0 |
| `tests/test_pipeline_shielding.py` | regression-fallback | 4 | 0 | 4 | 0 | 0 |
| `tests/test_run_t3.py` | dataset-loader-slow | 1 | 1 | 0 | 1 | 0 |
| `tests/test_run_t4.py` | dataset-loader-slow | 1 | 1 | 0 | 1 | 0 |
| `tests/test_run_t6.py` | unit-eval-helper | 1 | 0 | 1 | 0 | 0 |
| `tests/test_schemas.py` | unit-schema | 6 | 0 | 6 | 0 | 0 |
| `tests/test_smoke_ollama_save.py` | unit-tooling | 4 | 0 | 4 | 0 | 0 |
| `tests/test_t2_dataset.py` | dataset-loader-slow | 1 | 1 | 0 | 1 | 0 |
| `tests/test_text_model.py` | unit-wrapper | 4 | 0 | 4 | 0 | 0 |
| `tests/test_text_model_hf.py` | real-backend-slow | 2 | 2 | 0 | 2 | 0 |
| `tests/test_verify_model_cards.py` | unit-tooling | 6 | 0 | 6 | 0 | 0 |
| `tests/test_wrapper_latch.py` | regression-fallback | 4 | 0 | 4 | 0 | 0 |

## Slow-marked test ids (skipped unless `--run-slow`)

- `tests/test_api_phase_d.py::test_compare_real_ollama`
- `tests/test_audio_model_real.py::test_real_audio_shape`
- `tests/test_image_model_blip.py::test_blip_caption_shape`
- `tests/test_image_model_ocr.py::test_ocr_reads_overlay_text`
- `tests/test_llm_judge_ollama.py::test_ollama_judge_returns_schema_valid_output`
- `tests/test_run_t3.py::test_t3_loader_shape`
- `tests/test_run_t4.py::test_t4_loaders_shape`
- `tests/test_t2_dataset.py::test_load_toxicity_sample_shape`
- `tests/test_text_model_hf.py::test_hf_benign_scores_low`
- `tests/test_text_model_hf.py::test_hf_toxic_scores_high`

## Test modules not collected in this environment (module-level importorskip)

- (none: every `tests/test_*.py` on disk was collected)

