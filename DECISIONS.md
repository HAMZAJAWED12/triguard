# Decision Log — TriGuard

## Decision 001: Project template
Date: 2026-05-13
Status: accepted

Context: CM3070 requires choosing a Level-6 template.
Options considered: CM3020 Idea 1 (orchestration), CM3020 Idea 2 (financial advisor bot).
Decision: CM3020 Project Idea 1 — Orchestrating AI Models to Achieve a Goal.
Reason: Closer fit to a multimodal, explainable, privacy-aware moderation problem; supports a clean orchestration story.
Impact: Drives the architecture (multiple pre-trained models + a judge) and the literature scope (multimodal + LLM-as-judge).
Evidence: pitch deck `TriGuard_Pitch_Deck.pptx`.

## Decision 002: Project domain
Date: 2026-05-13
Status: accepted

Context: Template allows any "goal".
Options considered: mental-health companion, accessibility describer, smart-study buddy, content moderation.
Decision: Content moderation.
Reason: Clear social need; established benchmarks; current legislation (DSA, UK Online Safety Act) creates real demand; cross-modal failures of existing systems are a documented gap.
Impact: Defines literature scope (moderation + multimodal + explainability + privacy).
Evidence: pitch deck.

## Decision 003: Working title
Date: 2026-05-13
Status: accepted

Context: Need a project name for video, report, repo.
Decision: TriGuard.
Reason: Short, memorable, communicates the three modalities and the protective intent.
Impact: All written deliverables use this title.

## Decision 004: Literature review scope
Date: 2026-06-08
Status: accepted

Context: CLAUDE.md §6 requires 4–6 sources, recommends 6–8 for a stronger submission.
Options considered: 6 sources (minimum strong) or 8 (full coverage of all themes).
Decision: 8 sources spanning text moderation, image-text fusion, audio, LLM-as-judge, BLIP methods, and algorithmic-moderation governance.
Reason: Each of the five literature themes in CLAUDE.md §6 must be covered. Eight sources is the smallest number that covers all themes with at least one comparative pair.
Impact: Literature matrix has 8 rows; word budget per source ≈ 280 words.

## Decision 005: Referencing style
Date: 2026-06-08
Status: accepted

Context: CLAUDE.md §8 prefers Harvard.
Decision: Harvard (author-date in body, alphabetical reference list).
Reason: Default UoL style; consistent across all deliverables.
Impact: All citations in lit review, design, and final report use this style.

## Decision 006: Ethics quiz submitted
Date: 2026-06-08
Status: accepted

Context: CM3070 ethics quiz required before any participant-facing work.
Decision: Quiz submitted via VLE. No human-subjects data, no scraping; T7 peer review of rationales is the only low-risk human element and is contingent on tutor approval.
Impact: Unblocks formative Project Proposal acceptance and lets us proceed to Preliminary Report.

## Decision 007: Project Proposal submitted
Date: 2026-06-08
Status: accepted

Context: Topic 2 formative Project Proposal due (Wk 4 of original 24-week plan).
Decision: Submitted via VLE. Content reused from `docs/project_design_draft.md` §1–§5 + §10–§12 trimmed to the proposal form.
Impact: Closes Phase A (Concept + Proposal). Next written milestone is the Preliminary Report (Topic 5, 10% weight).

## Decision 008: Coding starts after Preliminary Report submission
Date: 2026-06-08
Status: accepted

Context: User decision to keep written work uninterrupted until Preliminary Report is in.
Decision: Pause implementation. Mock pipeline, schemas, wrappers, judge, eval scripts — all start in the sprint immediately after the Preliminary Report deadline.
Reason: Concentrates risk on one stream at a time; avoids context-switching between writing and debugging.
Risk: CLAUDE.md §18 + Milestone 10 expect prototype evidence inside the Preliminary Report. If the UoL handbook does require a prototype demo, this decision must be revisited. Flagged in RISK_REGISTER.md as R12.
Impact: Implementation window compresses from 7 weeks to whatever remains after the report deadline. Mitigation: keep the mock-pipeline sprint tight (≤ 1 week to first working mock).

## Decision 009: Coding now required for Preliminary Report
Date: 2026-06-08
Status: accepted (supersedes D-008 in part)

Context: Preliminary Report handbook confirmed (Chapter 4 = Feature Prototype + 3-5 min MP4 demo). R12 in RISK_REGISTER.md is realised.
Decision: Reverse D-008 partially. Build a feature prototype before the Preliminary Report deadline. Scope: Tier-A mock pipeline + at least one real model wrapper + a working orchestrator + saved JSON outputs + a CLI/FastAPI demo, sized to fit a 3-5 minute video.
Reason: The handbook is unambiguous — Chapter 4 requires an implementation, and one of the marking criteria is technical challenge of the prototype.
Impact: Sprint reshuffled. Implementation starts immediately. Word budgets: Ch1 ≤ 1000, Ch2 ≤ 2500, Ch3 ≤ 2000, Ch4 ≤ 1500, total ≤ 6000.

## Decision 010: Preliminary Report assembled as a single PDF with 4 chapters
Date: 2026-06-08
Status: accepted

Context: Handbook specifies one report with four chapters.
Decision: One PDF, title page + ToC + Ch1 + Ch2 + Ch3 + Ch4 + references. Existing lit review PDF and design PDF become Ch2 and Ch3 respectively, polished and trimmed.
Reason: Single deliverable matches submission form.
Impact: Need to add a Ch1 intro and a Ch4 prototype chapter, then merge.

## Decision 011: T2 text-track dataset and metric scheme
Date: 2026-06-23
Status: accepted

Context: T2 (text-side moderation accuracy) needed a real public dataset to
replace the 14-item hand-built set, which the classifier was effectively tuned
against and proves nothing about generalisation.
Options considered:
  (a) Hugging Face `tweet_eval` config `hate` — tiny download, but the hate
      subset is HatEval (SemEval-2019 Task 5), which is permission-gated and
      conflicts with the project's "public datasets only" ethics rule.
  (b) `google/civil_comments` — CC0 1.0 public domain; the dataset already named
      in `docs/evaluation_protocol.md` T2 and listed as approved in CLAUDE.md.
  (c) A larger custom/scraped set — rejected (ethics, scope).
Decision: Use `google/civil_comments` (CC0) as the **default**. Keep
`tweet_eval/hate` available behind `--source tweet_eval` with a documented
permission caveat; it is not used by default and not exercised by tests.
Evaluate as **binary** (`non-toxic`/`toxic`): the dataset's continuous
`toxicity` score is thresholded at 0.5, and the wrapper emits a single
`toxicity_score`, so the protocol's earlier 3-bucket ("borderline") framing does
not apply.
Reason: CC0 is unambiguously usable and ethics-clean; binary is forced by both
the data and the wrapper; streaming + a fixed seed + a cached sample keep it
small, reproducible and offline-after-first-run.
Impact: New `src/triguard/data/datasets.py` loader, `run_t2.py` harness, a
`slow`/network test, `datasets` dependency (optional `eval` extra), `.gitignore`
for `data/hf_cache/` + `data/t2_samples/`, new `docs/implementation_notes.md`.
The T2 line in `docs/evaluation_protocol.md` updated from 3 buckets to binary.
Fast test suite stays at 23 passed (the new test is `slow`, skipped by default).

## Decision 012: Text wrapper — real Hugging Face tier (toxic-bert)
Date: 2026-06-23
Status: accepted

Context: Sprint 1 of making the three perception models real. The sklearn
TF-IDF + logistic-regression baseline over-flags on Civil Comments (T2:
accuracy 0.542 / macro-F1 0.415 over 500 rows).
Options considered:
  (a) swap sklearn -> toxic-bert outright (one real text model);
  (b) add toxic-bert as a new tier and keep mock + sklearn.
Decision: (b). Add an `"hf"` tier = `unitary/toxic-bert`
(revision `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94`), multi-label sigmoid,
lazy-imported transformers/torch, `lru_cache`d, auto-fallback to mock. Keep
mock + sklearn. `force_mode="real"` aliases sklearn (offline); `force_mode=None`
defaults to sklearn (set `TRIGUARD_TEXT_BACKEND=hf` to opt in). `run_t2`
`--backend` defaults to sklearn so `run_eval` (1.000) and the OLD T2 baseline
stay reproducible.
Reason: the fast suite must stay offline — existing `force_mode="real"` text
tests and the orchestrator test call `analyse` with no network; sklearn is the
offline default + sanity floor + OLD T2 baseline; toxic-bert is the headline
real model behind an explicit opt-in.
Impact: new `hf` tier in `text_model.py`; deps `transformers`, `torch`, and a
`numpy<2` pin (guards sklearn against numpy 2.x); slow test
`tests/test_text_model_hf.py`; both T2 result dirs kept (sklearn OLD + hf NEW).
Fast suite stays 23 passed (+ slow hf test skipped).
Result (T2, Civil Comments, 500 rows, seed 42, `run_env=wsl-ubuntu`, model
`unitary/toxic-bert` rev `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94`): hf
**accuracy 0.928, macro-F1 0.6476** (toxic P 0.41 / R 0.28 / F1 0.33) vs the
frozen sklearn baseline 0.542 / 0.415 (toxic P 0.08 / R 0.59 / F1 0.14). hf wins
overall + stops over-flagging (toxic precision 0.08→0.41) but has lower toxic
recall (0.59→0.28). Both result dirs kept (`074102` sklearn, `124802` hf).

## Decision 013: Image wrapper — real BLIP tier
Date: 2026-06-23
Status: accepted

Context: Sprint 2 of making the perception models real. The image wrapper was a
filename-derived mock.
Decision: Add a `"blip"` tier = `Salesforce/blip-image-captioning-base`
(revision `82a37760796d32b1411fe092ab5d4e227313294b`), lazy-imported
transformers/PIL/torch, `lru_cache`d, auto-fallback to mock. Keep the mock as the
**offline default**. `force_mode="blip"` or `TRIGUARD_IMAGE_BACKEND=blip` opts in.
Caption from BLIP; `visual_risk_cues` from a documented keyword vocab
(weapon, violence, hate_symbol, drug, nudity_warning) scanned over the caption;
images downscaled to long-edge ≤ 1024 px; `confidence` = mean greedy-token
softmax probability from generation (fallback 0.6, tagged `raw["confidence_fallback"]`).
Reason: keeps the fast suite offline (mock default), mirrors the Sprint-1 text
pattern; BLIP is the headline real image model behind an explicit opt-in.
Impact: new `blip` tier in `image_model.py`; `pillow` dep; slow test
`tests/test_image_model_blip.py` on a committed synthetic public-domain image;
run via WSL `.venv-linux` (Application Control blocks torch on Windows). Fast
suite stays 23 passed (+ slow blip test skipped). No T3 eval yet (separate sprint).
