# AGENTS.md — TriGuard working rules

This file is read at the start of every Codex session in this repo.
Read it before changing anything.

## Project identity

- **Title:** TriGuard.
- **Module:** CM3070 Computer Science Final Project (University of London).
- **Template:** CM3020 Artificial Intelligence — Project Idea 1: *Orchestrating
  AI Models to Achieve a Goal*.
- **One-line description:** A prototype multimodal, explainable, locally
  deployable content-moderation pipeline that combines pre-trained text,
  image and audio models with a local LLM judge.
- **Status:** Tier-B shipped — real toxic-bert / BLIP(+OCR) / Whisper+YAMNet /
  llama3-via-Ollama behind feature flags, offline mock defaults intact.
  Evaluation tracks T1–T8 committed. Phase D demo (presets, compare, streaming,
  dashboard) shipped. Phase E: draft report in progress (student prose).

## Operating rules

1. **Read before write.** Always read `README.md`,
   `docs/project_design_draft.md`, `DECISIONS.md` and this file before
   editing anything.
2. **Honesty.** Do not invent evaluation numbers, dataset rows or
   citations. If a number is not in `outputs/evaluation/<latest>/results.json`,
   it does not appear in any document.
3. **Tests first.** Run `PYTHONPATH=src python -m pytest -q` before and
   after every change. Do not declare a task done until tests are green.
4. **No silent scope changes.** Ask before:
   - removing the rule-based judge fallback,
   - removing any modality (text / image / audio),
   - removing the explainability / rationale field,
   - adding a heavy dependency,
   - adding any cloud service,
   - changing the public schema (`TextEvidence`, `ImageEvidence`,
     `AudioEvidence`, `JudgeInput`, `JudgeOutput`, `TriGuardResult`).
5. **Document every decision** with a new entry in `DECISIONS.md`
   (date, status, context, options considered, decision, reason, impact).
6. **Update the journal** with a weekly block in `JOURNAL.md` whenever a
   milestone closes.
7. **No fake results.** If something is planned, mark it `[PLANNED]`. If
   something is implemented, point to the files and tests that prove it.

## Code conventions

- Python 3.10+.
- `pydantic` v2 schemas for every cross-module boundary.
- Lazy-import heavy ML libraries (`transformers`, `torch`, `whisper`,
  `tensorflow_hub`) inside loader functions, not at module top.
- Every model wrapper supports a `mock_mode` (env var `TRIGUARD_MOCK=1`)
  that returns deterministic evidence without downloading weights.
- Mark slow / network-requiring tests with `@pytest.mark.slow` and skip
  by default; default test run must not hit the network.
- Use `logging` not `print` inside the package.
- Type hints on every public function.

## What's already real and what's still mock

| Component | Status |
|---|---|
| Pydantic schemas | Real, enforced, frozen |
| Text wrapper | **Real**: sklearn TF-IDF+LR (offline default) + opt-in `unitary/toxic-bert` (`TRIGUARD_TEXT_BACKEND=hf`); mock via `TRIGUARD_MOCK=1` |
| Image wrapper | Mock default; **real BLIP** opt-in (`TRIGUARD_IMAGE_BACKEND=blip`) + opt-in RapidOCR (`TRIGUARD_IMAGE_OCR=1`) |
| Audio wrapper | Mock default; **real Whisper + YAMNet** opt-in (`TRIGUARD_AUDIO_BACKEND=real`), per-component fallback |
| LLM judge — rule-based path | **Real**, deterministic, schema-valid, offline default |
| LLM judge — Ollama path | **Real** (llama3-8B, opt-in), streaming variant for the demo, falls back to rule with honest `ollama->rule` label |
| Orchestrator | Real; retry-on-invalid-JSON, wrapper-failure shielding, honest `model_versions` |
| CLI | Real (`--judge` accepted before or after the subcommand) |
| Evaluation harnesses | Real: T1–T8 + failure analysis; committed evidence under `outputs/evaluation/` |
| FastAPI demo | **Real**: `/ui` (presets, rule-vs-llama3 compare, SSE streaming), `/dashboard` (verbatim eval numbers) |

Replacing a mock with a real component must use a feature flag, must keep
the existing tests green and must add a `slow` test for the real path.

## Word-count caps (for any document edits)

- Chapter 1 Introduction: ≤ 1000 words.
- Chapter 2 Literature Review: ≤ 2500 words.
- Chapter 3 Project Design: ≤ 2000 words.
- Chapter 4 Feature Prototype: ≤ 1500 words.
- Preliminary Report total: ≤ 6000 words.

## Datasets and ethics

- Use only public datasets (Civil Comments, Hateful Memes if access
  granted, AudioSet subset).
- Do not scrape social media. Do not collect participant data.
- Harmful sample content lives in a separate gitignored folder and is
  deleted after submission.
- The system is decision-support; outputs must always say
  "recommended action" and never claim autonomous moderation.
- Use careful language: "supports moderation", "assists human review",
  "demonstrates feasibility". Avoid: "automatically detects", "achieves
  perfect", "replaces moderators".

## Working with model weights

- Never commit weights to the repo. Add to `.gitignore`:
  - `*.bin`, `*.pt`, `*.pth`, `*.safetensors`
  - `models/` (HuggingFace cache)
  - `.cache/`
- Document model name + revision in `docs/implementation_notes.md`.
- Pin a specific revision in code when calling `from_pretrained`.

## How to add a real model wrapper (recipe)

1. Open `docs/CLAUDE_CODE_PROMPTS.md` and find the relevant prompt
   (Prompts 1–4).
2. Branch off `main`.
3. Implement behind a feature flag — the mock must still work via
   `TRIGUARD_MOCK=1`.
4. Add one `slow`-marked test that exercises the real path.
5. Run fast `pytest -q` (no slow) and confirm 22+ green.
6. Run `pytest -m slow` once to verify the real path; capture wall time.
7. Update `DECISIONS.md` and `docs/implementation_notes.md`.
8. Open a small PR and merge.

## When to stop and ask

Ask the user before:
- Reducing the project from multimodal to unimodal.
- Removing the audio component.
- Removing the human-readable rationale.
- Changing the LLM judge contract.
- Adding a cloud or paid service.
- Increasing the repo size by more than 100 MB.

## Reference docs in this repo

- `docs/literature_review_draft.md` — Ch 2 source.
- `docs/project_design_draft.md` — Ch 3 source.
- `docs/chapter1_introduction.md` — Ch 1 source.
- `docs/chapter4_prototype.md` — Ch 4 source.
- `docs/system_architecture.md` — full system spec.
- `docs/evaluation_protocol.md` — eval tracks T1–T8.
- `docs/work_plan.md` — full 24-week Gantt.
- `docs/inclusive_design.md` — accessibility commitments.
- `docs/ethics.md` — data handling rules.
- `docs/referencing_notes.md` — sources and credibility notes.
- `docs/Video_Script_Prototype_Demo.md` — preliminary video shot list.
- `docs/CLAUDE_CODE_PROMPTS.md` — sequential prompts for upcoming work.

## Final reminder

TriGuard is impressive because it is clear, working, evaluated, explainable
and well justified by literature — not because it is overloaded with
features. Keep scope tight. Honest evaluation beats sparkly demos.
