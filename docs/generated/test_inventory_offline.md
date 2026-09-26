# Test inventory (generated — do not hand-edit)

- date: 2026-09-26
- interpreter label: offline venv
- python: 3.12.10 (Windows)
- pytest 8.4.2
- generator: `scripts/test_inventory.py` (stdlib only)
- collect command: `python -m pytest --collect-only -q -p no:cacheprovider tests` -> 91 tests collected in 0.38s
- slow-select command: `python -m pytest --collect-only -q -p no:cacheprovider -m slow tests` -> 8/91 tests collected (83 deselected) in 0.37s
- junit: `junit_win.xml` from `python -m pytest -q --junitxml=...` (fast lane: no --run-slow; slow tests appear as skipped)

Totals: 91 collected test ids in 29 files; 8 slow-marked; 3 test module(s) not collected (module-level importorskip); 0 unclassified.

## Per-layer

| layer | files | collected | slow-marked | passed | skipped | failed |
|---|---|---|---|---|---|---|
| unit-schema | 1 | 6 | 0 | 6 | 0 | 0 |
| unit-wrapper | 3 | 8 | 0 | 8 | 0 | 0 |
| unit-judge-rule | 1 | 4 | 0 | 4 | 0 | 0 |
| unit-eval-helper | 3 | 4 | 0 | 4 | 0 | 0 |
| unit-tooling | 8 | 34 | 0 | 34 | 0 | 0 |
| regression-fallback | 5 | 17 | 0 | 17 | 0 | 0 |
| integration-orchestrator | 1 | 6 | 0 | 6 | 0 | 0 |
| functional-api-cli | 1 | 4 | 0 | 4 | 0 | 0 |
| real-backend-slow | 4 | 5 | 5 | 0 | 5 | 0 |
| dataset-loader-slow | 3 | 3 | 3 | 0 | 3 | 0 |
| **total** | 29 | 91 | 8 | 83 | 8 | 0 |

## Per-file

| file | layer(s) | collected | slow-marked | passed | skipped | failed |
|---|---|---|---|---|---|---|
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

- `tests/test_audio_model_real.py::test_real_audio_shape`
- `tests/test_image_model_blip.py::test_blip_caption_shape`
- `tests/test_llm_judge_ollama.py::test_ollama_judge_returns_schema_valid_output`
- `tests/test_run_t3.py::test_t3_loader_shape`
- `tests/test_run_t4.py::test_t4_loaders_shape`
- `tests/test_t2_dataset.py::test_load_toxicity_sample_shape`
- `tests/test_text_model_hf.py::test_hf_benign_scores_low`
- `tests/test_text_model_hf.py::test_hf_toxic_scores_high`

## Test modules not collected in this environment (module-level importorskip)

- `tests/test_api.py` — collection skipped
- `tests/test_api_phase_d.py` — collection skipped
- `tests/test_image_model_ocr.py` — collection skipped

