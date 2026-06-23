# Claude Code Handoff Prompts — TriGuard

This file contains a sequence of self-contained prompts to give Claude Code,
in order. Each prompt assumes Claude Code starts a fresh session with no
prior context, and tells it everything it needs.

## How to use

1. Open Claude Code in this repo: `cd "E:\OneDrive\ICAEWSOFTWARE\FYP UOL\triguard" && claude`.
2. Paste **the single prompt** for the task you want done (do not paste the whole file).
3. Wait for it to finish; verify the acceptance criteria; commit.
4. Move to the next prompt.

## General rules to put at the top of every Claude Code session

Paste this header **before any prompt below** if you want belt-and-braces:

> You are working in the TriGuard repository (CM3070 final project, CM3020 AI
> template, Project Idea 1). Read `CLAUDE.md` (if present), `README.md`,
> `DECISIONS.md` and `docs/project_design_draft.md` before changing anything.
> Code conventions: Python 3.10+, `pydantic` v2 schemas, `pytest` for tests,
> lazy-import heavy ML libraries, every wrapper must support a `mock_mode`
> for unit tests, never download model weights inside unit tests. Do not
> remove the rule-based judge fallback. Do not break the existing 22 tests.
> Always run `PYTHONPATH=src python -m pytest -q` before declaring done.

---

# Prompt 0 — Fix OneDrive truncation, verify clean run

> **Task.** The repository is stored under a OneDrive folder which has
> previously truncated some Python files mid-write, causing
> `SyntaxError: '[' was never closed`-style failures. Verify every Python
> file in `src/triguard/` and `tests/` is well-formed, fix any truncation
> by rewriting the affected file end-to-end, then prove the suite is green.
>
> **What to do, exactly.**
> 1. Run `python -m py_compile` on every `*.py` under `src/` and `tests/`.
>    Report any failure.
> 2. For any file that fails to compile, open it and rewrite it completely;
>    do not patch — write the whole file fresh, then re-run `py_compile`.
> 3. Once `py_compile` passes everywhere, run
>    `PYTHONPATH=src python -m pytest -q`. Target: at least 22 passed, no
>    errors during collection.
> 4. Run `PYTHONPATH=src python -m triguard.evaluation.run_eval` and
>    confirm it prints `Accuracy: 1.000` and saves a JSON envelope under
>    `outputs/evaluation/<timestamp>/results.json`.
> 5. Run `PYTHONPATH=src python -m triguard.cli run data\sample_inputs\sample_harmful.json`
>    and confirm `risk_label = "harmful"`, `recommended_action = "block"`,
>    and `text_evidence.raw.mode = "real"`.
>
> **What NOT to do.**
> - Do not introduce new dependencies.
> - Do not change the public API of any module.
> - Do not delete `tests/` files.
> - If a file looks intact but a downstream import fails, suspect
>   `sklearn` / `numpy` mismatch and fix the venv — do not weaken the test.
>
> **Acceptance.** `pytest -q` shows `>= 22 passed`, the CLI run produces
> a schema-valid JSON in real mode, and `git status` shows only the fixed
> files modified.

---

# Prompt 1 — Upgrade text wrapper to a real HuggingFace toxicity model

> **Task.** Replace the sklearn TF-IDF + logistic regression baseline in
> `src/triguard/models/text_model.py` with a real HuggingFace toxicity
> classifier, keeping the same `analyse(text, *, force_mode=None) ->
> TextEvidence` contract.
>
> **Constraints.**
> - Use `unitary/toxic-bert` (≈ 440 MB) or
>   `cardiffnlp/twitter-roberta-base-sentiment-latest` (≈ 500 MB) — pick the
>   one that runs on CPU, 8 GB RAM. Document the choice in
>   `docs/implementation_notes.md`.
> - Lazy-import `transformers` and `torch` inside the loader function, not
>   at module top. Tests must still pass when those libraries are missing
>   (fall back to the existing mock path).
> - Keep `force_mode="mock"` working for unit tests; tests must not
>   download weights.
> - Maintain the `TextEvidence.raw["mode"]` field; new mode is
>   `"real-hf"`. Add `model_name` and `model_revision` to `raw`.
> - Add a new test `tests/test_text_model_hf.py` that is **marked**
>   `@pytest.mark.slow` and **skipped by default**; running with
>   `pytest -m slow` should download the model once and verify a benign
>   sample scores < 0.3 and a clearly toxic sample scores > 0.7.
>
> **Acceptance.** `pytest -q` (fast lane) still passes; `pytest -q -m slow`
> exercises the real HF model end-to-end. `docs/implementation_notes.md`
> describes the model picked and why. `requirements.txt` adds `transformers`
> and `torch` with version pins.

---

# Prompt 2 — Real image wrapper (BLIP captioning)

> **Task.** Replace the mock image wrapper in
> `src/triguard/models/image_model.py` with a real implementation that
> uses BLIP for captioning, while keeping the existing interface
> `analyse(path_or_bytes) -> ImageEvidence`.
>
> **Constraints.**
> - Use `Salesforce/blip-image-captioning-base` (≈ 990 MB). Lazy-import
>   `transformers` and `PIL` inside the loader; cache the model with
>   `functools.lru_cache`.
> - Auto-downscale images so the long edge is ≤ 1024 px before captioning.
> - `visual_risk_cues` should be derived from the BLIP caption by a small
>   keyword rule over a documented vocabulary (`weapon`, `violence`,
>   `hate_symbol`, `drug`, `nudity_warning`). Document the vocabulary in
>   `docs/implementation_notes.md`.
> - Keep `mock_mode=True` (via env var `TRIGUARD_MOCK=1`) returning the
>   existing deterministic mock.
> - Add `tests/test_image_model_blip.py` marked `slow`, skipped by default,
>   that runs BLIP on one of the sample images in `data/sample_inputs/`
>   (commit a small public-domain test image).
>
> **Acceptance.** Fast `pytest -q` still passes with 22+ green. With
> `TRIGUARD_MOCK=1` the existing tests behave unchanged. `pytest -m slow`
> exercises BLIP and produces a non-empty caption.

---

# Prompt 3 — Real audio wrapper (Whisper + YAMNet)

> **Task.** Replace the mock audio wrapper in
> `src/triguard/models/audio_model.py` with a real implementation that
> uses OpenAI Whisper for transcription and YAMNet for audio-event
> tagging, while keeping the existing interface
> `analyse(path_or_bytes) -> AudioEvidence`.
>
> **Constraints.**
> - Use `whisper-tiny` (≈ 75 MB) by default; allow `whisper-small`
>   (≈ 244 MB) via an env var. Lazy-import `whisper`.
> - For YAMNet, use the TensorFlow Hub model `yamnet/1`. Lazy-import
>   `tensorflow_hub` and `tensorflow`.
> - Clip audio to 60 s; chunk longer audio and average tag scores.
> - Keep `transcript_confidence` honest: use Whisper's
>   `avg_logprob` mapped to a 0..1 range, not a constant.
> - Populate `yamnet_tags` as `[(label, score), ...]` from the top-5
>   YAMNet classes that exceed 0.2 confidence.
> - Keep `mock_mode=True` returning the existing deterministic mock.
> - Add `tests/test_audio_model_real.py` marked `slow`, skipped by default,
>   that runs both Whisper and YAMNet on a tiny WAV in
>   `data/sample_inputs/` (commit a short public-domain clip).
>
> **Acceptance.** Fast `pytest -q` still passes. `pytest -m slow`
> exercises Whisper + YAMNet end-to-end. `docs/implementation_notes.md`
> notes Whisper variant + YAMNet hub URL + RAM observed.

---

# Prompt 4 — Real LLM judge via Ollama

> **Task.** Wire the existing Ollama path in `src/triguard/models/llm_judge.py`
> to a real local instruction-tuned model, with strict JSON-schema enforcement
> and a graceful fallback to the rule-based judge.
>
> **Constraints.**
> - Default Ollama model: `llama3:8b-instruct-q4_K_M`. Override via env
>   `TRIGUARD_OLLAMA_MODEL`.
> - Use the existing `JUDGE_PROMPT_TEMPLATE`. Do not change the schema.
> - On JSON parse failure: retry once with a stricter prompt (the existing
>   logic). On second failure: fall back to the rule judge and tag
>   `uncertainties` with `"judge_output_invalid"`.
> - On network failure (Ollama not running): fall back silently to the
>   rule judge with `uncertainties` tagged `"ollama_unavailable:<reason>"`
>   — the existing test `test_ollama_unavailable_falls_back_to_rule` must
>   still pass.
> - Add a **manual** smoke script `scripts/smoke_ollama.py` that runs
>   `python scripts/smoke_ollama.py data/sample_inputs/sample_harmful.json`
>   and prints the judge output. Document the prerequisite (`ollama pull
>   llama3:8b-instruct-q4_K_M` and `ollama serve`).
> - **No CI test** depends on Ollama running.
>
> **Acceptance.** Existing 22 tests still pass; the smoke script returns a
> schema-valid JudgeOutput on a host that has Ollama installed; on a host
> without Ollama, the smoke script does not crash — it prints the
> fallback rationale and the uncertainty tag.

---

# Prompt 5 — FastAPI demo

> **Task.** Implement a small FastAPI demo at `src/triguard/api/main.py`
> exposing the pipeline so a non-technical reviewer can submit content
> and read the structured decision.
>
> **Constraints.**
> - Endpoints:
>   - `GET /` — health check, returns `{ "status": "ok", "version": ... }`.
>   - `POST /analyse/multimodal` — accepts `multipart/form-data` with
>     optional `text` (str), `image` (file), `audio` (file); returns
>     a `TriGuardResult` as JSON.
>   - `POST /analyse/text` — accepts `{ "text": "..." }`, returns
>     `TriGuardResult` JSON.
> - Run with `uvicorn triguard.api.main:app --host 127.0.0.1 --port 8001`.
> - Do not change any wrapper or schema.
> - Add `tests/test_api.py` using `fastapi.testclient.TestClient` covering
>   the health check and the text-only endpoint. Tests must pass without
>   real models (mock mode).
> - Add a single-page HTML template at `src/triguard/api/static/index.html`
>   that posts to `/analyse/multimodal` and renders the JSON nicely. WCAG-
>   AA contrast, ≥ 16 px body font, system fonts.
>
> **Acceptance.** `pytest -q` shows green; `uvicorn ...` boots in
> < 5 s in mock mode; the HTML page accepts a text input and shows a
> rationale + recommended action.

---

# Prompt 6 — Evaluation harness expansion (T3 + T6)

> **Task.** Extend `src/triguard/evaluation/run_eval.py` and add new
> harnesses for the evaluation tracks T3 (image-text on Hateful Memes
> or fallback) and T6 (50-item hand-built tri-modal set).
>
> **Constraints.**
> - Add `src/triguard/evaluation/run_t3.py` that loads either Hateful
>   Memes (`data/hateful_memes/dev_seen.jsonl`) or a public fallback set
>   under `data/mmhs150k_sample/` (whichever exists). Report F1 and AUROC.
> - Add `src/triguard/evaluation/run_t6.py` that loads
>   `data/sample_inputs/triguard_eval_v1/` (you create this folder with
>   a `manifest.json` listing 50 items: 17 safe + 16 borderline + 17
>   harmful). Items are mocks for image/audio (filename-based cues are OK).
>   Report per-class precision/recall/F1, confusion matrix, latency p50/p95
>   and explanation grounding rate (percentage of rationales that mention
>   at least one piece of evidence — regex check).
> - Update `docs/evaluation_protocol.md` with the new commands.
> - Do **not** invent metric numbers. The harness must always write the
>   exact numbers it computed.
>
> **Acceptance.** `python -m triguard.evaluation.run_t6` produces a JSON
> envelope in `outputs/evaluation/<ts>/t6/results.json` with all required
> metrics. `pytest -q` still passes.

---

# Prompt 7 — Failure-case analysis script

> **Task.** Add `src/triguard/evaluation/failure_analysis.py` that takes
> a results JSON from any harness and writes a top-10 list of the worst
> cases (largest gap between true and predicted label) to
> `outputs/evaluation/<ts>/failures/top10.md`.
>
> **Constraints.**
> - Output is markdown so it can be pasted into the Final Report.
> - Each row: sample id, true label, predicted label, risk score,
>   flagged modalities, rationale, uncertainties.
> - Include a short header explaining the failure-class taxonomy
>   (false-positive harmful; missed harmful; borderline drift).
>
> **Acceptance.** Running on the T6 results JSON from Prompt 6 produces a
> markdown table with up to 10 rows. The script exits 0 even if there
> are no failures (writes "No failures" message).

---

# Prompt 8 — Final Report integration

> **Task.** Update the Preliminary Report markdown sources in `docs/`
> (`chapter1_introduction.md`, `chapter4_prototype.md`,
> `literature_review_draft.md`, `project_design_draft.md`) to reflect
> the new real wrappers and evaluation numbers, then re-build the report
> PDF via `python docs/build_preliminary.py`.
>
> **Constraints.**
> - Keep per-chapter word caps: Ch1 ≤ 1000, Ch2 ≤ 2500, Ch3 ≤ 2000,
>   Ch4 ≤ 1500, total ≤ 6000.
> - Only insert real numbers — those that appear in
>   `outputs/evaluation/<latest>/results.json`. Do not invent.
> - Where the text wrapper has been swapped to HF, update the chapter
>   accordingly and remove the sklearn-specific paragraphs.
> - Re-run the build script and inspect the resulting PDF (page count,
>   word count, references list).
> - Do not modify the references unless a new source was actually cited.
>
> **Acceptance.** `docs/TriGuard_Preliminary_Report.pdf` rebuilt;
> body word count ≤ 6000; no fabricated numbers; `git diff` shows only
> sentences referring to the new evidence have changed.

---

## Guardrails to repeat in every prompt if you want to be safe

- "Do not invent metric numbers."
- "Do not weaken existing tests to make new code pass."
- "Do not commit large model weights to the repo (.gitignore `models/`,
  `*.pt`, `*.safetensors`, `*.bin`)."
- "Always run `PYTHONPATH=src python -m pytest -q` before declaring done."
- "If a step needs a heavy download and the user is offline, stop and
  ask — do not silently switch to a mock path that the user might
  miss."

## When NOT to use Claude Code on this project

- Writing the Final Report prose. Markers expect a student voice; use
  Claude Code for code and the chapter shells, then **you** polish the
  paragraphs and add your own reflection (CLAUDE.md §36).
- Recording the demo video. The voiceover must be yours — Claude Code
  can only write the shot list (already done; see
  `Video_Script_Prototype_Demo.md`).
- Inventing evaluation numbers. Always run the harness, copy the
  numbers from the saved JSON envelope.

## Reference layout (already in this repo)

```
triguard/
├── README.md
├── CLAUDE.md  (if you maintain one; the design lives in docs/)
├── DECISIONS.md     ← log every model / dataset / scope choice
├── JOURNAL.md       ← weekly entries
├── RISK_REGISTER.md
├── src/triguard/
│   ├── orchestrator/  (schemas.py, pipeline.py)
│   ├── models/        (text_model.py, image_model.py, audio_model.py, llm_judge.py)
│   ├── evaluation/    (run_eval.py, future: run_t3.py, run_t6.py, failure_analysis.py)
│   ├── api/           (main.py — Prompt 5)
│   └── cli.py
├── tests/             (test_schemas.py, test_*_model.py, test_orchestrator.py, test_llm_judge.py, future: test_api.py, *_slow tests)
├── data/sample_inputs/
└── outputs/
    ├── evaluation/<timestamp>/
    └── demo_*.json
```
