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

## Decision 014: Audio wrapper — real Whisper + YAMNet tier
Date: 2026-06-23
Status: accepted

Context: Sprint 3, the last perception modality. The audio wrapper was a
filename-derived mock.
Decision: Add a `"real"` tier — OpenAI Whisper transcription (`tiny` default,
`small` via `TRIGUARD_WHISPER_MODEL`) + YAMNet audio-event tagging
(TF-Hub `yamnet/1`; top-5 classes > 0.2; 60 s chunks averaged). `transcript_confidence`
= mean `exp(segment.avg_logprob)` clamped [0,1] (not a constant). Each component
degrades to the mock **independently** (`raw["whisper_fallback"]` /
`raw["yamnet_fallback"]`; `mode` `real-audio` or `real-audio-partial`), so a
missing backend never crashes. Mock stays the offline default;
`force_mode="real"` / `TRIGUARD_AUDIO_BACKEND=real` opts in.
Env: TensorFlow / numba have no Python 3.14 wheels (the WSL default), so real
audio runs in a uv-provisioned **py3.12** venv `~/.venv-triguard-audio`
(`scripts/run_wsl_sprint3.sh`). ffmpeg required by Whisper.
Impact: real tier in `audio_model.py`; new `[audio]` optional extra
(openai-whisper, tensorflow, tensorflow-hub, librosa, soundfile) kept OUT of
`requirements.txt`/`[eval]` so installs on Python 3.13+ don't break; slow test
`tests/test_audio_model_real.py` (skips until a committed public-domain WAV is
added at `data/sample_inputs/audio_test.wav`). Fast suite stays 23 passed
(+ slow audio test skipped). No T4 eval yet (separate sprint).

## Decision 015: LLM judge — real Ollama path exercised + hardened
Date: 2026-06-25
Status: accepted

Context: The Ollama judge path existed but had never been run against a real
local LLM, and both failure modes (server unreachable; invalid JSON) were tagged
identically. Sprint 4: stand up a real model, harden the path, prove the fallback,
capture a real evidence-grounded rationale — without changing the default (rule)
judge, the public schema, or the offline fast suite.
Options considered: (a) rebuild the judge; (b) wire + harden the existing Ollama
path behind flags. Chose (b).
Decision: Rule judge stays the offline default. Ollama path is opt-in
(`TRIGUARD_JUDGE=ollama`); model via `TRIGUARD_OLLAMA_MODEL` (default
`llama3:8b-instruct-q4_K_M`, `OLLAMA_MODEL` kept as compat), endpoint via
`OLLAMA_HOST`, client timeout via `OLLAMA_TIMEOUT` (default 60 s). Host/model/
timeout are read at call time (not import) so env/tests override reliably.
Fallback tags differentiated: invalid JSON after one stricter-prompt retry ->
`judge_output_invalid`; unreachable/timeout -> `ollama_unavailable:<reason>`.
JSON parsing widened to catch `json.JSONDecodeError` (not only `ValidationError`)
so malformed output routes through retry -> fallback. Manual smoke
(`scripts/smoke_ollama.py`) judges the same evidence with both paths, checks the
LLM rationale is grounded in the JudgeInput (cites real scores/labels/cues/tags,
no invented modalities/numbers), and re-validates against `JudgeOutput`. One
`slow` test skips cleanly when Ollama is unreachable. No new dependency (stdlib
`urllib`).
Reason: the fast suite must stay offline + deterministic; both failure modes must
degrade gracefully and be distinguishable; the LLM output must be provably
schema-valid and evidence-grounded, not trusted blindly.
Env: real model run under WSL. Ollama installed user-local (no sudo) from the
v0.31.1 `ollama-linux-amd64.tar.zst` bundle, decompressed with Python 3.14 stdlib
`compression.zstd` (no system zstd); ran on GPU via WSL passthrough.
Impact: `llm_judge.py` call-time env + split fallback tags + JSON hardening +
`OLLAMA_TIMEOUT`; new `scripts/smoke_ollama.py`; new slow test
`tests/test_llm_judge_ollama.py`. Fast suite 23 passed, 6 skipped (was 5; +1 new
slow test). `test_ollama_unavailable_falls_back_to_rule` stays green and is now
robust to a real server on the default port.
Result (real run, WSL, `llama3:8b-instruct-q4_K_M` quant q4_K_M, 5.3 GB VRAM,
100% GPU; sample `data/sample_inputs/sample_harmful.json`; evidence: text
toxicity 0.7167 [insult, threat], image cue weapon, audio shouting 0.7):
- rule judge -> risk_label `harmful`, action `block`, flagged text+image+audio.
- llama3 judge -> risk_label `borderline`, action `review`, risk_score 0.73,
  flagged text+image; rationale (verbatim): "The text evidence suggests a high
  level of toxicity with an insult and threat detected, while the image caption
  and visual risk cues indicate potential harm. However, the confidence levels
  are not extremely high, leading to a borderline classification."; uncertainties
  ["confidence in text toxicity detection", "reliability of image caption"].
- Grounding: grounded (cites insult, threat, toxicity, image); no invented
  modalities/numbers; schema re-validation passed.
Honest observations: the LLM judge is more conservative than the rule judge on
this sample (borderline vs harmful) and OMITTED the audio modality from its flags
(did not weigh the shouting tag); its risk_score 0.73 is high relative to its own
`borderline` label (schema-valid, since borderline+review satisfies the label/
action rule). Fallback proven twice: cold-load client timeout ->
`ollama_unavailable:TimeoutError`; server stopped -> `ollama_unavailable:[Errno
111] Connection refused`; both degraded to the rule judge without crashing.

## Decision 016: Combined single-process tri-modal venv (~/.venv-tri) + USE_TF=0 guard
Date: 2026-06-25
Status: accepted

Context: The real backends worked only in separate venvs (py3.14 text+image;
py3.12 audio); no single process ran text + image + audio + the Ollama judge
together. Sprint 5: one reproducible py3.12 CPU environment proving an all-real
orchestrator pass. Infrastructure only — avoid code/schema/wrapper changes.
Decision: Build `~/.venv-tri` (py3.12, in $HOME off OneDrive) with CPU-only wheels
(torch installed first from the PyTorch CPU index), pinned in `requirements-full.txt`.
Resolve the framework tension with `numpy<2` (resolved 1.26.4; sklearn + torch);
TensorFlow 2.21 + protobuf 7.35.1 coexist with no conflict. A real SIGSEGV
appeared: with torch AND tensorflow installed, `transformers` eagerly imports TF
and the process segfaults when a torch pipeline runs (crash isolated to the
toxic-bert step, before our audio code imports TF; plain torch+TF ops coexist
fine). Fix is ENVIRONMENT-ONLY: `USE_TF=0` forces transformers torch-only; the
audio wrapper's direct TensorFlow/YAMNet use is unaffected. No code change
(`KMP_DUPLICATE_LIB_OK` / `OMP_NUM_THREADS` / `MKL_THREADING_LAYER` did not help).
Reason: keeps schema + wrappers + Windows `.venv` untouched; the crash is a
packaging interaction, best fixed by an env flag documented for the combined venv.
Impact: new `scripts/build_venv_tri.sh`, `requirements-full.txt` (95 exact pins,
py3.12.13), `data/sample_inputs/sample_multimodal_real.json` (real committed
media), `docs/implementation_notes.md` Sprint-5 section; captured
`outputs/demo_full_real.json` (all-real) + `outputs/demo_harmful_fallback.json`
(graceful mock fallback). Fast suite in `~/.venv-tri`: 23 passed, 6 skipped
(offline defaults intact).
Result (one process, all real; `sample_multimodal_real.json` = real toxic text +
benign synthetic image/audio — an integration demo, NOT harmful-content
detection): text `real-hf` toxicity 0.9751 (insult/threat/toxic); image
`real-blip` "a house in the middle of a field"; audio `real-audio` Whisper-tiny
"The quick brown fox jump so that they do not near the river bank." + YAMNet
[(Speech, 0.8602)]; llama3 judge risk_score 0.98, `harmful`, `block`, flagged
`[text]`, grounded rationale reading image/audio as benign. Schema-valid
`TriGuardResult`. Peak RSS 2.98 GB + llama3 5.3 GB VRAM; `latency_ms` 49421 cold.
Caveat: `model_versions` still hardcoded (verify via `evidence.raw["mode"]`);
pipeline fix deferred.

## Decision 017: Evaluation track T4 — real audio wrapper on public data
Date: 2026-07-04
Status: accepted

Context: T4 (docs/evaluation_protocol.md) measures the real audio wrapper's
speech-to-text + audio-event tagging. The protocol named an AudioSet subset, but
AudioSet distributes only YouTube ids (no hosted audio), so it is effectively
ungettable.
Options considered: (a) reconstruct AudioSet from YouTube (fragile, ToS, dead
ids); (b) public ungated proxies. Chose (b).
Decision: Two honest sub-metrics on public, ungated data, run through the real
audio wrapper (`force_mode="real"`) in `~/.venv-tri`:
 - Whisper WER on LibriSpeech test-clean (CC BY 4.0): `jiwer` corpus WER after a
   documented normalisation (lowercase, strip punctuation) — LibriSpeech
   references are UPPERCASE/unpunctuated, Whisper adds case+punct.
 - YAMNet top-1 + top-5 on ESC-50 (Piczak 2015, CC BY-NC 3.0, academic
   non-commercial) against an APPROXIMATE, hand-built ESC-50 -> AudioSet
   display-name map (only mapped categories sampled). top-5 is the fair headline
   given the approximate map; top-1 is a strict lower bound.
New loader `src/triguard/data/audio_datasets.py` (streams + persists wavs +
manifest under gitignored `data/t4_samples/`, mirrors the T2 loader); new harness
`src/triguard/evaluation/run_t4.py`; one slow loader test; `jiwer` pinned in
`[eval]` + `requirements.txt`.
Reason: honest, reproducible, ethics-clean public data; the AudioSet substitution
and approximate map are documented as limitations, not hidden.
Impact: fast suite 23 passed, 7 skipped (was 6; +1 new slow test). Schema +
wrappers + Windows `.venv` untouched. `data/t4_samples/` gitignored; committed
evidence is `outputs/evaluation/<ts>/t4/results.json`.
Result (run `20260704-153729`, `~/.venv-tri` py3.12, `USE_TF=0`, Whisper `tiny` +
YAMNet `yamnet/1`, seed 42, n=50 each, both `wrapper_modes` = `real-audio`):
 - Whisper WER (LibriSpeech test-clean): corpus **0.0971**, mean/clip 0.1314.
 - YAMNet (ESC-50, 29 mapped categories): top-1 **0.32**, top-5 **0.66**.
Honest reading: whisper-tiny on clean read speech gives ~9.7% WER (a best case,
not noisy/adversarial moderation audio); YAMNet top-5 0.66 under an approximate
category map — the top-1/top-5 gap largely reflects map coarseness + AudioSet's
finer ontology, not only model error.

## Decision 018: Evaluation track T3 — image-text moderation (flag-vs-label) on public data
Date: 2026-07-04
Status: accepted

Context: T3 (docs/evaluation_protocol.md) measures the image track. Hateful Memes
is access-gated; MMHS150K's public mirror stores images in a 6.5 GB zip
(unstreamable) with an unstated licence. Candidates were verified BEFORE any
download and the gated/unstreamable ones rejected (STOP rule honoured).
Decision: Use `Ahren09/MMSoc_Memotion` — the Memotion (SemEval-2020 Task 8) memes,
ungated, images EMBEDDED as a HF `Image` feature (streams per-row, no zip), plus
an `offensive` label + dataset-provided OCR text (`text_corrected`/`text_ocr`).
Binarise `offensive`: not_offensive -> 0, else -> 1. Stream (seed 42, cap 50) and
persist images to gitignored `data/t3_samples/` — meme images are third-party
copyright, so media is NEVER committed; only `results.json` is.
Metric = flag-vs-label: run the real pipeline (image BLIP + text toxic-bert on the
OCR text + rule judge) per item; predicted-positive = `risk_label in {borderline,
harmful}`. Report precision/recall/F1, confusion, accuracy, AUROC over
`risk_score`, plus a text-only baseline. Rule judge (deterministic, offline) for
reproducibility.
Honest framing (also in limitations): BLIP is a captioner, not a hate classifier,
and does not OCR meme text; the image track rarely fires. The text signal comes
from the dataset's OCR field, not the pipeline's own OCR. This is a decision
measure, NOT a trained-classifier F1 — expect modest numbers, most signal from text.
New loader `src/triguard/data/image_datasets.py`; harness
`src/triguard/evaluation/run_t3.py`; one slow loader test; `data/t3_samples/`
gitignored. No perception-code/schema change.
Impact: fast suite 23 passed, 8 skipped (was 7; +1 new slow test). Repo relocated
off OneDrive to `C:\dev\triguard` (`/mnt/c/dev/triguard`); the 4 `scripts/*.sh`
`cd` paths repointed.
Result (run 20260704-172017, `~/.venv-tri` py3.12, USE_TF=0, seed 42, n=50,
backends real-hf + real-blip, rule judge; class balance 18 not_offensive / 32
offensive):
 - Pipeline: precision 0.6923, recall 0.2812, F1 0.40, accuracy 0.46, AUROC 0.566.
 - Text-only baseline: precision 0.6667, recall 0.25, F1 0.3636, accuracy 0.44.
Honest reading: the pipeline barely beats the text-only baseline (F1 0.40 vs 0.36,
+0.04) — the image track (BLIP captions, often degenerate on memes) adds little,
exactly as predicted for a captioner-not-classifier with no OCR. Low recall (0.28)
and near-chance AUROC (0.566): most memes are offensive via wording/context that
toxic-bert catches only when overtly toxic. This modest result is the real
finding, documented not hidden.

## Decision 019: model_versions reflects the real backend (was hardcoded)
Date: 2026-07-04
Status: accepted

Context: `orchestrator/pipeline.py` hardcoded `model_versions` (text
`sklearn-tfidf-lr-v1`, image/audio `mock-v1`, judge `rule-based-v1`) regardless of
the backend that ran — the Sprint-5 all-real JSON reported `mock-v1` next to a real
BLIP caption, contradicting `raw["mode"]`. Supersedes the "hardcoded, deferred"
caveat noted in D-016.
Decision: Populate `model_versions` from each evidence's `raw`: a single
`backend_of_mode()` map (mock / sklearn / real-hf / real-blip / real-audio /
real-audio-partial / unknown) plus `model_name@revision` when present. Judge label
= `rule` / `ollama`, or `ollama->rule` when the Ollama path fell back (uncertainty
tagged `ollama_unavailable`/`judge_output_invalid`). Schema SHAPE unchanged (still
`dict[str,str]`); only the values change. Wrappers untouched. New test
`test_model_versions_agree_with_raw_mode` asserts each value's backend token equals
`backend_of_mode(evidence.raw["mode"])`.
Reason: the reported versions must be honest — traceable to the model that actually
produced each piece of evidence.
Impact: `pipeline.py` value-building + one test. Fast suite 24 passed (was 23; +1
new test), 8 skipped. Verified all-real one-pass
(`outputs/demo_full_real_fixed.json`, `~/.venv-tri`, USE_TF=0, ollama warm):
`text_model` `real-hf:unitary/toxic-bert@4d6c22e74ba2`, `image_model`
`real-blip:Salesforce/blip-image-captioning-base@82a37760796d`, `audio_model`
`real-audio`, `llm_judge` `ollama` — agreeing with evidence modes real-hf /
real-blip / real-audio. No more `mock-v1`.

## Decision 020: FastAPI demo surface (Prompt 5)
Date: 2026-07-04
Status: accepted

Context: A non-technical reviewer needs to submit content and read the structured
decision without the CLI (Prompt 5).
Decision: Add `src/triguard/api/main.py` (FastAPI) as a thin demo layer over the
existing orchestrator — no wrapper/orchestrator/schema change. Endpoints: `GET /`
(health `{status, version}`), `GET /ui` (single-page UI), `POST /analyse/text`
(`{text}` -> TriGuardResult JSON), `POST /analyse/multimodal` (multipart text +
image/audio uploads -> temp files -> pipeline -> `unlink` in `finally` -> JSON).
`judge_mode=None` is passed through so env flags are honoured (judge default rule);
perception honours `TRIGUARD_*_BACKEND` (default mock/sklearn). No real models
forced. Binds `127.0.0.1` only. Single self-contained `static/index.html`
(inline CSS/JS, no CDN, WCAG-AA contrast, >=16px, system fonts).
Tests `tests/test_api.py` use `importorskip("fastapi"/"httpx")` + `TRIGUARD_MOCK=1`
so they run fully offline where the deps exist and SKIP cleanly where they don't
(the Windows offline venv). Deps `fastapi`, `uvicorn`, `python-multipart`, `httpx`
pinned in requirements + `[eval]`.
Reason: a browser demo for the video/report without touching the core; offline +
skip-safe tests keep the fast lane green everywhere.
Impact: new api package + UI + tests + README run line. Fast suite: 27 passed / 8
skipped in `~/.venv-tri` (24 + 3 api tests); 24 passed / 9 skipped in the Windows
`.venv` (the api module `importorskip`-skips as one entry). Boot smoke (uvicorn
127.0.0.1:8001, `TRIGUARD_MOCK=1`): `GET /` ->
`{"status":"ok","version":"0.1.0-tier-a"}`; `POST /analyse/text` -> schema-valid
TriGuardResult; `GET /ui` -> HTML. Schema + wrappers + orchestrator untouched.

## Decision 021: model_versions judge label honours the env-driven mode
Date: 2026-07-04
Status: accepted

Context: D-019 labelled `model_versions["llm_judge"]` from the pipeline's
`judge_mode` argument only. The FastAPI demo passes `judge_mode=None` to honour
env flags, so an env-driven `TRIGUARD_JUDGE=ollama` run (llama3 actually judging)
was mislabelled `rule`.
Decision: Derive the label from the EFFECTIVE judge —
`judge_mode or os.getenv("TRIGUARD_JUDGE", "rule")`, mirroring `llm_judge.judge`
itself — so env-driven ollama is labelled `ollama` (or `ollama->rule` on fallback).
Values/behaviour only; schema shape + wrappers untouched.
Impact: `pipeline.py` (+`import os`); new offline test
`test_model_versions_judge_reflects_env_ollama` (env ollama + unreachable host ->
`ollama->rule`). Fast suite 25 passed (was 24; +1), 9 skipped (Windows). Verified
live: the API in real mode with `TRIGUARD_JUDGE=ollama` now reports
`llm_judge: ollama` alongside the real llama3 rationale.

## Decision 022: Evaluation track T6 — tri-modal ablation harness (roadmap Phase A)
Date: 2026-07-04
Status: accepted

Context: The central thesis (multimodal orchestration catches cross-modal harm
that unimodal tools miss, Kiela et al. 2020) was stated but never demonstrated.
Phase A builds the harness that can prove it.
Decision: Add `src/triguard/evaluation/run_t6.py` — runs a hand-built tri-modal set
(`data/sample_inputs/triguard_eval_v1/manifest.json`) through the pipeline in FOUR
conditions (text-only / image-only / audio-only / multimodal), rule judge,
reporting per-condition 3-class P/R/F1 + confusion + accuracy, p50/p95 latency, and
a `cross_modal_ablation` table (recall on `cross_modal:true` + `harmful` items per
condition — the thesis metric). Reuses `pipeline.run` + the T2/T3 metric helpers.
Fast offline manifest-parse test `tests/test_run_t6.py`.
Manifest provenance (HONEST): the committed manifest is an **AI-DRAFTED STARTER SET**
of 18 non-confounder items (recorded in its `provenance` field and in results.json
`manifest_provenance`). It must be reviewed/owned and its AI assistance disclosed
before use as report evidence. Genuine cross-modal **confounder** cases are NOT
included — only two benign committed media assets exist, so no juxtaposition harm is
constructible; those cases + media are the student's to design and label.
Reason: build the measurement instrument now; the thesis-proving cases + labels are
the student's intellectual contribution, kept separate for academic integrity.
Impact: new `run_t6.py` + manifest + README + test. Fast suite 26 passed (was 25;
+1), 9 skipped (Windows). Ablation run (`~/.venv-tri`, real hf+blip+real-audio, rule
judge, `outputs/evaluation/20260704-221056/t6/`): multimodal acc 0.7778 / macro-F1
0.6852 >= text-only 0.75 / 0.6746 > image-only 0.60 / 0.25 > audio-only 0.50 /
0.2222; `cross_modal harmful` items 0 (table empty until confounders added). On this
non-confounder set the multimodal gain is small because harm is text-driven — an
honest baseline; the cross-modal advantage awaits real confounder cases.

## Decision 023: Opt-in OCR for the image track (RapidOCR) + T3 OCR ablation (Phase B)
Date: 2026-07-05
Status: accepted

Context: T3's own limitations note that BLIP captions but does not OCR meme text.
Phase B adds OCR and measures its value.
OCR engine: **easyocr was abandoned** — it hard-requires torchvision, and no
torchvision on the CPU index is ABI-compatible with the pinned `torch 2.12.1+cpu`
(`RuntimeError: operator torchvision::nms does not exist`); its install also bumped
numpy to 2.5.x and crashed transformers/BLIP. Switched to **rapidocr-onnxruntime**
(ONNX runtime, torch-free), which leaves the pinned torch + numpy<2 stack intact.
Decision: Add OCR behind `TRIGUARD_IMAGE_OCR=1` in `image_model.py` (off by default):
`_ocr_text()` reads overlaid text via RapidOCR into `ImageEvidence.raw["ocr_text"]`
(NO schema change) and folds it into `visual_risk_cues` alongside the caption. The
orchestrator contract is unchanged. `run_t3 --ocr` runs three image-track-alone
conditions vs BLIP-caption-only (dataset `text` dropped): OCR->keyword-cues and
OCR->toxic-bert-text-track. The OCR->text route is the deployment-real headline; the
full-pipeline +/-OCR delta is not reported because Memotion's `text` field already
supplies the overlay text (~0, misleading).
`rapidocr-onnxruntime` pinned in `[eval]` + requirements; `build_venv_tri.sh`
installs it and re-pins numpy<2. Slow test `tests/test_image_model_ocr.py` on a
committed synthetic `ocr_test.png`.
Reason: close the documented OCR gap without a system binary (no sudo) and without
disturbing the torch stack; measure OCR's value where it actually applies.
Impact: `image_model.py` (OCR helpers + cue fold), `run_t3.py` (`--ocr` ablation),
new `ocr_test.png` + slow test, deps, build script. Fast suite 26 passed, 10 skipped
(OCR test skips where rapidocr absent). Schema + pipeline + wrapper public contract
unchanged.
Result (real hf+blip, rule judge, Memotion n=50,
`outputs/evaluation/20260705-111002/t3/`; OCR read text on 50/50 images, slow test
passes on the synthetic clip). Three image-track-alone conditions vs BLIP-caption-only
(F1 0.0606):
 - OCR -> keyword cues: F1 0.0606 (**delta 0.0**) — sub-finding: the cue vocab
   (weapon/violence/hate_symbol/drug/nudity) rarely matches meme language.
 - OCR -> toxic-bert TEXT track: F1 **0.4348** (**delta +0.3742**) — the deployment-real
   headline; OCR'd meme text classified by toxic-bert recovers essentially the same
   value as the text track (dataset text-only 0.3636, full pipeline 0.40) — comparable,
   within small-sample (n=50) noise.
The full-pipeline +/-OCR delta is ~0 only because Memotion pre-supplies the overlay
text in its `text` field. Conclusion (report-worthy): OCR's value is real and large
when routed to a real classifier (+0.37 F1 on the image track); folding it into the
narrow keyword cues wastes it (0.0 delta, sub-finding); it looks redundant on Memotion
solely because the dataset already carries the text.

## Decision 024: Evaluation completeness — failure analysis + T7 grounding + T8 perf (Phase C)
Date: 2026-07-05
Status: accepted

Context: Roadmap Phase C — finish the designed-but-unbuilt evaluation utilities.
Eval-only; no model/schema/pipeline change.
Decision: Add three utilities:
 - `failure_analysis.py` (Prompt 7): reads any results.json (per-sample `results` or a
   `failures` list), ranks misclassifications by severity, writes a top-N markdown with
   a taxonomy (false-positive-harmful / missed-harmful / borderline-drift).
 - `run_t7.py` (+ shared `grounding.py`): rationale grounding rate = fraction of
   rationales citing >=1 real evidence token; headline is the ollama/llama3 rate (the
   rule judge grounds ~1.0 by construction). A blank human `usefulness_1to5` column is
   left for a rater.
 - `run_t8.py`: p50/p95 + cold-start latency + peak RSS (psutil) over the T6 set, run
   once per backend config (mock vs real).
Two fast offline unit tests (`test_grounding.py`, `test_failure_analysis.py`); `psutil`
pinned in `[eval]`.
Reason: honest evaluation is the project's stated strength; these close T7/T8 + the
failure taxonomy.
Impact: fast suite 29 passed (was 26; +3), 10 skipped. No model/schema change.
Result (real, T6 set n=18):
 - failure_analysis on the committed T3 run: 10 failures -> `failures/top10.md`.
 - T7 grounding: **ollama/llama3 1.0 measured** (18/18 rationales cite real
   evidence, 0 invented modalities) — the LLM judge is well grounded. The rule
   judge grounds ~1.0 by construction (it concatenates the evidence) and was
   not separately measured.
 - T8: mock p50 0.0 ms / peak RSS 34.5 MB; real (hf+blip+real-audio, rule judge) p50
   31.1 ms / p95 4075 ms / cold-start 4075 ms / peak RSS 2.87 GB.

## Decision 025: Phase D demo surface — presets, rule-vs-llama3 compare, streaming judge, eval dashboard
Date: 2026-07-05
Status: accepted

Context: Roadmap Phase D ("demo wow"). The FastAPI demo could only run one
pipeline pass and return one JSON blob; the committed eval numbers (T2–T8) had
no visual surface; the llama3 judge's multi-second latency looked like a hang.
Demo layer only — no wrapper, orchestrator-contract or public-schema change.
Options considered: (a) client-side-only presets (synthesised File objects) —
rejected: temp-file suffix handling loses the filename the mock cues key on;
(b) run the pipeline twice for the comparison — rejected: re-runs perception,
doubling BLIP/Whisper cost; (c) chart numbers hardcoded into the dashboard —
rejected: violates the honesty rule (numbers must live in results.json only).
Decision: Four additive features:
 - **Presets**: `GET /presets` + `POST /analyse/preset` run a WHITELISTED
   committed sample (`sample_safe/borderline/harmful.json` mock-cue presets +
   `sample_multimodal_real.json` real committed media). The whitelist is the
   only server-side path mapping — nothing under `data/t3_samples/` (untracked
   third-party memes) is ever exposed.
 - **Compare**: `POST /analyse/compare` runs perception ONCE
   (`run(judge_mode="rule")`), rebuilds the JudgeInput from the returned
   evidence, then calls the ollama judge on the identical input. The fallback
   labelling logic is promoted to a public `pipeline.judge_label()` (used by
   `run()` too), so an offline llama3 column is honestly labelled
   `ollama->rule`, never presented as LLM output.
 - **Streaming**: additive `llm_judge.judge_stream()` generator +
   `_ollama_generate_stream` (same request body as `_ollama_generate` but
   `stream:true`, NDJSON parsed line-by-line). Token events are
   presentation-only; the terminal event carries the schema-validated
   JudgeOutput with `source: ollama | rule_fallback` using the SAME fallback
   uncertainty tags as `judge()`. No stricter-prompt retry on the streaming
   path (parse failure -> rule fallback directly; documented divergence).
   `POST /analyse/stream` serves it as SSE; perception + temp-file cleanup
   complete BEFORE streaming starts, so client disconnects cannot leak temp
   files. The UI renders streamed tokens via `textContent` (no HTML sink) and
   visibly annotates a fallback so a streamed draft is never mistaken for the
   verdict.
 - **Dashboard**: `GET /dashboard` (self-contained page, hand-rolled div/CSS
   bars, no CDN) + `GET /eval/summary`, which scans
   `outputs/evaluation/<ts>/t*/results.json` and copies a per-track WHITELIST
   of keys VERBATIM — nothing computed, nothing invented. T2 is kept per
   backend (sklearn baseline vs hf) and T8 per config (mock vs real, split on
   `config.mock`); every entry names its source file, and limitations /
   provenance strings (incl. the T6 AI-DRAFTED-manifest warning) ride along
   and are rendered next to the numbers. Missing `outputs/` degrades to
   `{available:false}`, never a 500.
Reason: the demo must showcase the real system without compromising the
project's honesty stance: perception-once keeps compare latency truthful, the
streaming protocol keeps the JudgeOutput contract authoritative, and the
dashboard is a read-only lens over committed evidence.
Impact: `llm_judge.py` (+`judge_stream`/`_ollama_generate_stream`),
`pipeline.py` (+public `judge_label`, behaviour unchanged), `api/main.py`
(6 new endpoints), `static/index.html` (presets, judge-mode selector,
two-column compare, SSE consumer), new `static/dashboard.html`; tests
`tests/test_llm_judge_stream.py` (4 offline unit tests) +
`tests/test_api_phase_d.py` (9 fast offline + 1 slow real-ollama). Fast suite:
WSL 45 passed / 10 skipped (was 32/9); Windows offline venv 33 passed / 11
skipped (was 29/10; the new API file importorskip-skips). Schemas, wrappers,
judge contract and offline defaults untouched.
Post-review hardening (multi-agent adversarial review of the diff; 8 confirmed
findings, all fixed): `_gather_inputs` no longer leaks the first temp file
when saving the second upload fails (regression vs HEAD, reproduced live);
API test files also `importorskip` python-multipart (fastapi ERRORs, not
skips, without it); the UI locks preset buttons during any in-flight request
(a mid-stream preset click corrupted the output area); the dashboard prints
results.json values VERBATIM (no `toFixed` rounding), renders each run's
`config` line (so a mock re-run can never be mistaken for a real one) and the
T2 limitations, drops the hardcoded `+` on the OCR delta, and its
missing-results message no longer prints the HTTP status as the reason;
`/eval/summary` labels a T8 run with no boolean `config.mock` as `unknown`
rather than defaulting to `real`, and its `source` string no longer claims
git-committed status (it reads what is on disk). Two new regression tests
(temp-file cleanup; tokens-then-death mid-stream fallback) + NO_PROXY guards
keep the closed-port fallback tests offline under system proxies.
Result (verified live, WSL `~/.venv-tri`, mock perception, warm llama3): the
offline smoke shows every endpoint degrading honestly (`ollama->rule`,
`rule_fallback`); the real smoke streamed 98 token events ending in a
schema-valid `source:"ollama"` verdict (borderline/review, risk 0.55, grounded
rationale citing the 0.45 toxicity), and compare returned rule 0 ms vs llama3
5451 ms on the same evidence. `--run-slow` on the two Phase D test files with
Ollama up: 12 passed. `/eval/summary` spot-check equals the committed files
(t2 0.542/0.928; t8 34.5/2873.7 MB) — asserted by test, not transcribed.

## Decision 026: T6 evaluation set v2 — student-reviewed replacement manifest
Date: 2026-07-05
Status: accepted

Context: The original T6 manifest was an AI-DRAFTED starter set (D-022) whose
labels had to be reviewed and owned by the student before use as report
evidence. The student replaced it with a v2 set (24 items: 10 safe, 6
borderline, 8 harmful; text-only, image-only, audio-only and multimodal
combinations over the two committed benign media assets) and reviewed,
edited and approved the items and labels.
Decision: Adopt the v2 manifest as the T6 evaluation set. Its `provenance`
field now records the true status: "drafted with AI assistance, then
reviewed, edited and approved by the author (2026-07-05); the author owns
these ground-truth labels". `run_t6.py`'s hardcoded "AI-DRAFTED starter set"
limitation string was replaced with a provenance-neutral pointer to
`manifest_provenance` (the old wording would have been false for any
reviewed manifest). AI assistance remains disclosed — in the provenance
field and in the report's AI-use section — per the UoL Generative AI policy
("declare how and where"); nothing is scrubbed.
Impact: manifest.json (items + provenance), run_t6.py (one limitation
string). Fast suite unchanged: 45 passed / 10 skipped (WSL). v1's committed
run (20260704-221056, n=18) remains as history; the report uses v2.
Result (run 20260705-160858, `~/.venv-tri`, USE_TF=0, real hf+blip+real-audio,
rule judge, n=24): multimodal acc 0.625 / macro-F1 0.4945 (n=24) >= text-only
0.5909 / 0.4786 (n=22) > image-only 0.5 / 0.2222 (n=8) = audio-only 0.5 /
0.2222 (n=6); cross_modal harmful items 0 (table empty as expected).
Honest reading: v2 scores lower than the v1 starter set (0.625 vs 0.778 acc)
because several v2 borderline items are mild negative opinions that
toxic-bert scores below the rule judge's 0.35 borderline threshold — the
borderline class drives the drop. That is a finding about the pipeline's
recall on mild incivility, not a defect in the set; report-worthy.

## Decision 027: Demo-readiness hardening (audit-driven)
Date: 2026-07-25
Status: accepted

Context: A pre-demo audit (multi-agent + live verification) confirmed four
demo-breakers and a set of embarrassments: (1) any per-file decode failure
latched the real BLIP tier off for the whole server session (`_BLIP_BROKEN`
set inside the same try as the per-request image open; missing-media presets
triggered it too; Whisper/YAMNet had the same latent pattern); (2) the
documented real-mode server commands lacked the `USE_TF=0` guard and
segfaulted at the first toxic-bert call (reproduced); (3) Ollama has no
autostart, so a pre-demo reboot silently degraded every llama3 segment to
`ollama->rule`; (4) llama3 unloads after ~5 idle minutes causing 30-50 s of
mid-demo dead air.
Decision: Split model-load (latching) from per-request work in
`image_model.py` / `audio_model.py` — a bad file now degrades that request
only, tagged `raw["decode_error"]`, and the model stays live (4 offline
regression tests in `tests/test_wrapper_latch.py`). Ollama request bodies
send `keep_alive` (default 30m, env `TRIGUARD_OLLAMA_KEEP_ALIVE`) — request
parameter only, judge contract untouched. `_save_upload` keeps the original
filename stem so mock cues/captions work on uploads. CLI accepts `--judge`
after the subcommand and prints one-line errors instead of tracebacks. The
health endpoint reports effective backends + judge default and /ui shows a
mock/real banner. `/eval/summary` marks each served run committed/uncommitted
via git and the dashboard warns on uncommitted (rehearsal) runs; the T6
confounder warning now quotes the results file's own note. New
`scripts/demo_up.sh` = one-command pre-demo ritual (orphan cleanup, Ollama
start, llama3 + perception warm-up, real server with `USE_TF=0` +
`TRIGUARD_IMAGE_OCR=1`, green/red checklist). Docs: USE_TF=0 added to every
documented real command; README truncation repaired + layout restored;
CLAUDE.md status/real-vs-mock table rewritten to Tier-B reality; stale
CONTEXT_HANDOFF.md deleted; `.gitignore` deduped; `.claude/scheduled_tasks.lock`
untracked; video script marked historical.
Impact: fast suites 49 passed / 10 skipped (WSL, was 45) and 37 passed / 11
skipped (offline venv, was 33). Live verification: demo_up.sh ALL GREEN;
corrupt upload -> mock+`decode_error` for that request then next image still
`real-blip`; corrupt `weapon_gun_photo.png` upload -> cue-based mock caption
(no temp-name gibberish); injected uncommitted newest T6 run flagged
`committed: false` on /eval/summary and cleanly restored after removal;
stream healthy (89 tokens, final `ollama`). Schemas and judge contract
untouched.

## Decision 028: Confounder-set infrastructure + run_t6 --judge variant
Date: 2026-07-25
Status: accepted (infrastructure only — the cases themselves are pending and
are the student's own work)

Context: The T6 `cross_modal_ablation` table — the thesis metric — is still
empty (D-022, D-026). The final report window is the time to fill it. Design
insight that shapes the experiment: the rule judge scores modalities
independently (+0.15 only when two already fired), so it is structurally
blind to harm that emerges purely from combination; the llama3 judge reads
the evidence jointly and may catch it. The scientifically interesting run is
therefore confounders under BOTH judges.
Decision: Build the scaffolding, keep authorship with the student:
 - `run_t6.py --judge {rule,ollama}` (default rule — existing behaviour and
   committed runs unchanged; config.judge now records the argument).
 - `data/sample_inputs/triguard_eval_v1/confounders_TEMPLATE.json` — 12 empty
   CF slots (cross_modal: true, all content/labels null, per-item
   design_note) explicitly marked TEMPLATE, never loaded by the harness.
 - `README_confounders.md` — the confounder concept (Kiela et al. 2020
   benign-confounder design), the manifest-level validity property
   (combination harmful, every supplied modality alone safe), four
   combination patterns from the literature, ethics rails (benign self-made/
   public-domain media only, no faces, EXIF stripped, nothing gitignored),
   and the two-judge experiment protocol incl. the honest caveat that BLIP's
   caption may destroy the visual half of a pairing before any judge sees it.
 - `scripts/make_confounder_media.py` — benign media toolkit: espeak-ng TTS
   clips (same provenance as audio_test.wav) and own-photo import with
   resize + EXIF/metadata strip. Media lands in
   `data/sample_inputs/confounders/` (committable because benign).
 - `scripts/check_confounders.py` — pre-merge validator: structure, labels,
   >=2 modalities, unimodal-safe confounder property, media existence, no
   gitignored references, id collisions vs manifest.json, design_note
   present. Verified: good item passes; a deliberately bad item trips all
   eight problem classes; empty template exits 1.
Reason: the empty table is the report's biggest gap; infrastructure removes
every mechanical obstacle while the intellectual contribution (cases,
wording, media selection, labels) stays demonstrably the student's, matching
the D-022/D-026 provenance discipline.
Impact: run_t6 judge-threading (default unchanged), two scripts, template +
README. Fast suites unchanged: 49 passed / 10 skipped (WSL), 37 passed / 11
skipped (offline). Toolkit smoke: TTS wav 77,840 bytes written; photo import
re-encoded to metadata-free PNG. Next: student authors 8-12 cases, validator
green, merge into manifest.json v3 with updated provenance, re-run T6 rule +
ollama, compare `cross_modal_ablation.recall_by_condition`.

## Decision 029: T6 v2 two-judge comparison (rule vs llama3) — baseline before confounders
Date: 2026-07-25
Status: accepted (evidence record)

Context: `run_t6 --judge` (D-028) made a like-for-like judge comparison
possible. Running it on the v2 set BEFORE the confounder cases exist gives a
baseline for the confounder experiment and is itself a report finding.
Runs (both real hf+blip+real-audio, n=24, class balance 10/6/8):
 - rule: `outputs/evaluation/20260725-191000/t6/` — multimodal acc 0.625 /
   macro-F1 0.4945; image-only 0.5 / 0.2222; audio-only 0.5 / 0.2222;
   text-only 0.5909 / 0.4786.
 - ollama (llama3): `outputs/evaluation/20260725-191055/t6/` — multimodal acc
   0.4583 / macro-F1 0.4722; image-only 0.25 / 0.1333; audio-only 0.1667 /
   0.0952; text-only 0.5909 / 0.4883.
Honest reading (from the committed confusion matrices, not the headline
accuracies): in the UNIMODAL conditions both judges are degenerate — the rule
judge predicts `safe` for all 8 image-only and all 6 audio-only items, llama3
predicts `borderline` for all of them. Neither discriminates on benign
committed media; the accuracy gap there only reflects which constant answer
matches more labels, and must NOT be reported as capability. The multimodal
row is the substantive one: the rule judge gets 10/10 safe, 0/6 borderline,
5/8 harmful; llama3 gets 5/10 safe, 2/6 borderline, 4/8 harmful. llama3
recovers part of the borderline band that the rule judge's 0.35 threshold
structurally misses (2 vs 0) and pays for it with false positives on benign
items (5/10 safe items flagged borderline) — a precision/recall trade with a
mechanism, not noise.
Caveat for the report: n=24, single llama3 run; temperature 0 but generation
is not bit-reproducible across model loads. Repeat the ollama condition
before quoting the multimodal delta as stable.
Impact: evidence only; no code change. `cross_modal_ablation` remains empty
in both runs (`n_cross_modal_harmful: 0`) — it populates only when the
author's confounder cases are merged into the manifest (D-028 workflow).
Viewer added for these comparisons: `scripts/show_t6_cross_modal.py`.

## Decision 030: read-only Markdown mirror of the submitted draft report
Date: 2026-09-24
Status: accepted

Context: the graded draft exists only as a .docx outside the repo. Review
tasks (word-count caps in CLAUDE.md, number-provenance audits against
`outputs/evaluation/<run>/<track>/results.json`, structure maps) need a
stable, diffable, line-addressable text form that never edits the source.
Options: (a) python-docx (absent in both venvs, would add a dependency);
(b) hand-paste chapters (unstable, error-prone); (c) stdlib zipfile +
ElementTree walker over `word/document.xml`.
Decision: (c). `scripts/docx_to_md.py <path.docx> --out <dir>` walks the
body in order, prefixes every paragraph with `[p<8-hex sha1 of normalised
text>]` (duplicates get `-2`, `-3` … suffixes), renders Heading1/Heading2 as
`#`/`##`, keeps captions verbatim with a `{Style}` tag, renders tables as
Markdown rows under a `[t...]` anchor, splits `ch<N>.md` at Heading1
`Chapter N`, `frontmatter.md` before it and `references.md` from the
`References` heading, and writes `wordcount.json` (prose-only and
prose+table-cell counts per chapter; headings, caption styles, front
matter and references excluded). Source path is a CLI argument only.
Reason: zero new dependencies, deterministic anchors let later audits cite
a paragraph without quoting it, and the mirror is regenerable in one
command so it cannot drift from the .docx unnoticed.
Impact: mirror generated under `docs/draft_as_submitted/`, which is
gitignored and LOCAL-ONLY — the student's report prose must not be published
before the final report is marked (similarity-checker self-match risk); only
the tool, its test and the word counts are tracked (regenerate with one
command). `tests/test_docx_to_md.py` builds a minimal docx in
`tmp_path` and checks splitting, anchors and counts. Windows fast suite:
40 passed / 11 skipped (37 + 3 new). Mirror counts from
`docs/draft_as_submitted/wordcount.json`: prose 6745 words across ch1-ch6
(ch1 723, ch2 1762, ch3 932, ch4 1236, ch5 1649, ch6 443); prose+tables
7633. These are mirror measurements, not evaluation numbers.

## Decision 031: Judge prompt — designed once, validated, not revised
Date: 2026-09-24
Status: accepted — Options/Decision/Reason recorded 2026-09-28 (retrospective for the 2026-09-24/26 changes)
Source draft: `docs/judge_prompt_card.md` '## 8. For integration' (Section 9 there = the author's open-question list; placed by the Integrate stage 2026-09-24).

Context: `JUDGE_PROMPT_TEMPLATE` (`src/triguard/models/llm_judge.py` 55-76)
and the stricter retry suffix (232-233) have identical content at every commit
that touched the file (1373e06, 4f10803, e866541, daae032; SHA-256
1df9a321a8f1c535...). The four commits changed request handling (call-time
env, fallback-tag split, JSON hardening, streaming variant, keep_alive) but
not the prompt text. Validation evidence: D-015 single-sample real run
(DECISIONS.md 240-258); T7 grounding run n=18
(outputs/evaluation/20260705-113456/t7/results.json); Phase D live smoke
(DECISIONS.md 626-633); T6 v2 two-judge comparison n=24 (D-029). Design
documents differ from the shipped prompt in: system/user two-message
structure vs single prompt field (system_architecture.md 113); runtime regex
guardrail vs post-hoc T7 measurement (system_architecture.md 115); model tag
suffix (112); fallback result rule-scored rather than fixed borderline
(107; project_design_draft.md 75; evaluation_protocol.md 58); tag name for
invalid JSON (chapter4_prototype.md 13). Request omits `format`, `system`,
`seed`, `num_ctx` (llm_judge.py 242-246); `temperature` is a literal 0.0
(245).
Options considered: (a) keep the prompt as first written and treat the D-015
sample, the T7 run (n=18), the T6 v2 two-judge run (n=24) and the Phase D
live smoke as validation only; (b) revise the prompt after those runs (few-shot
examples, an Ollama `format=json` request field, a separate system message)
and re-run T7 and T6; (c) a tuning study over prompt variants.
Decision: (a). The template is retained byte-identical; the report describes
it as designed once and validated, never tuned.
Reason (recorded retrospectively): no validation run produced a failure that
motivated a change — the pydantic boundary (`schemas.py` 63-78) plus the one
stricter retry enforce the output contract independently of prompt wording,
T7 grounding was 1.0 (a floor metric) and the T6 v2 llama3 run completed
through the same path. `temperature` 0.0 was chosen for repeatable decoding
under identical evidence (T7 rationales for S1-S3 are identical strings,
results.json 24/35/46); `format=json` and a system field were not used
because the contract is enforced after generation rather than by the server,
and the retry path needed a plain prompt string to append its suffix to.
(b) and (c) would have invalidated the committed T7/T6 evidence unless
re-run and were not attempted before the deadline.
Impact: prompt text is identical (same SHA-256) at every commit spanning
the T7, E6c and D-015 runs listed above; the design-vs-shipped differences
above are stated in the final report §4.3 (design-vs-shipped rows) and Table
E9 lists the protocol deviations; no code change.

## Decision 032: Derived statistics from committed envelopes
Date: 2026-09-24
Status: accepted — Options/Decision/Reason recorded 2026-09-28 (retrospective for the 2026-09-24/26 changes)
Source draft: `docs/t2_sampling_factsheet.md` '## For integration' (provisionally numbered 031 there; renumbered 032 by the Integrate stage 2026-09-24).

Context: The committed T2 envelopes carry point estimates and confusion
matrices but no interval estimates. `scripts/ci_from_envelope.py` (new,
stdlib `math` only) reads a committed `results.json` confusion matrix and,
with `--write`, stores `derived_intervals.json` beside it recording
`derived_from`, `method` ("Wilson score interval, z=1.959964"), the copied
matrix, k/n per metric and the interval bounds. Files produced:
`outputs/evaluation/20260623-074102/t2/derived_intervals.json`,
`outputs/evaluation/20260623-124802/t2/derived_intervals.json`. The
envelopes themselves are untouched. Unit test:
`tests/test_ci_from_envelope.py` (hand-worked expected values).
Options considered: (a) read CLAUDE.md rule 2 strictly — only numbers written
by an evaluation harness into its results.json may be quoted, so no
confidence interval can appear; (b) allow statistics derived by a committed
script from a committed envelope, written to a `derived_*.json` beside it
with a `derived_from` pointer and the method named; (c) compute intervals
inside the T2 harness and re-run T2 (network, unpinned dataset revision).
Decision: (b). Derived statistics from committed envelopes are citeable when
produced by a committed script into a `derived_*.json` next to the envelope.
Reason: (b) keeps the intent of rule 2 — every reported number lives in a
committed file and is reproducible by one command
(`python scripts/ci_from_envelope.py <results.json> --write`) — without
re-running an evaluation whose dataset revision is not pinned (a re-stream
may not reproduce the 500 rows); the derived file records its input path and
method (Wilson score interval, z = 1.959964) so provenance stays inspectable.
Impact: two new derived files under `outputs/evaluation/` (inputs
read-only); one new script; one new test (+2 tests in the fast lane);
`docs/t2_sampling_factsheet.md` and `docs/dataset_cards.md` reference the
derived values with their file path and key.

## Decision 033: Rule-judge audio flag matches mock tag vocabulary only
Date: 2026-09-24
Status: accepted — Options/Decision/Reason recorded 2026-09-28 (retrospective for the 2026-09-24/26 changes)
Source draft: `docs/model_cards.md` '## For integration' (placed by the Integrate stage 2026-09-24).

Context: The rule judge flags the audio modality when any yamnet_tags label
is exactly one of {"shouting", "screaming", "gunshot"} (lowercase,
src/triguard/models/llm_judge.py:161-162). Those three strings are the mock
wrapper's vocabulary (src/triguard/models/audio_model.py:44-51). The real
tier returns AudioSet display names read verbatim from the TF-Hub class map
(audio_model.py:153-155), which are capitalised in every committed
observation: "Speech" (docs/implementation_notes.md:146, :262); "Siren",
"Vehicle", "Aircraft", "Silence", "Laughter", "Bicycle"
(outputs/evaluation/20260704-153729/t4/results.json, yamnet_label_map and
failures.yamnet_mismatched). The exact AudioSet display names for the
shout / scream / gunshot classes are UNVERIFIED (not present in the
committed label map). Consequently, on the real tier the rule judge's audio
signal can only be 0.1 (llm_judge.py:163) unless a real display name happens
to equal one of the three lowercase strings; the lowercase mock tags can
still match when raw["yamnet_fallback"] is set (audio_model.py:212-214).
The LLM judge receives the tags verbatim (llm_judge.py:359-363) and is not
subject to the exact-match set.
Note on T6: the audio_only condition in run 20260725-191000 scores every
one of its 6 items as safe (conditions.audio_only.confusion_matrix: 3 + 1 +
2 all predicted safe). Related facts: every audio item in the v2 manifest
(A1, MS1, MS3, MB2, MH2, MH3 — `items[*].audio` non-null) references the
single committed clip data/sample_inputs/audio_test.wav
(data/sample_inputs/triguard_eval_v1/manifest.json); results.json
limitations[1] reads "no cross_modal confounder items yet (only two benign
committed media assets)"; the T6 envelope persists no per-item yamnet_tags
(top-level keys: track, run_at, manifest, manifest_provenance, config,
n_items, class_balance, conditions, cross_modal_ablation, limitations), so
the tags the rule judge saw for that clip in this run are not recorded.
The committed evidence does not separate the two possible causes of the
all-safe outcome (benign clip content vs the vocabulary mismatch); the report
states both facts without asserting a single cause.
Options considered: (a) document the limitation and make no code change
before submission; (b) match tags case-insensitively against a documented set
of AudioSet display names for the shout / scream / gunshot classes in
`_rule_based_judge`, add a fast test with a capitalised tag, and re-run T6 v2
and T8 real; (c) lower-case the tag names inside the audio wrapper.
Decision: (a) for the submission; (b) recorded as further work.
Reason: (b) and (c) change the rule-judge contract (CLAUDE.md rule 4, ask
first) and would invalidate the committed T6/T8 envelopes unless re-run; the
exact AudioSet display names for those three classes do not appear in any
committed artefact, so the correct match set cannot be written from repo
evidence alone; the LLM judge path receives tags verbatim and is unaffected.
Impact: Facts the student can state — the rule-judge audio path has never
been exercised by a real capitalised risk tag in any committed run; the
mock-tag tests (tests/test_llm_judge.py, tests/test_orchestrator.py) exercise
the lowercase set; changing the match set or lower-casing tags in
llm_judge.py touches the rule-judge contract (CLAUDE.md "changing the LLM
judge contract" -> ask first) and would need a new slow test on the real
tier.

## Decision 034: check_citations tool + Ch2 argument spine (F1)
Date: 2026-09-24
Status: accepted — Options/Decision/Reason recorded 2026-09-28 (retrospective for the 2026-09-24/26 changes)
Source draft: `docs/ch2_argument_spine.md` '## F. For integration' > '### DECISIONS entry candidate' (bullet form; fields laid out by the Integrate stage 2026-09-24, Facts text verbatim).

Context: `scripts/check_citations.py` (stdlib), `tests/test_check_citations.py`
(5 tests); run on `docs/draft_as_submitted/ch2.md --refs
docs/draft_as_submitted/references.md` -> cited-not-referenced 0,
referenced-not-cited 1 (Lazar 2023 — cited in another chapter; full.md
run gives 0), bare-name-without-citation 2 (Hateful Memes ch2.md:17,
VisualBERT ch2.md:19); strict `--every-mention` mode: 9 uncited-sentence
mentions (ch2.md:5, 11, 17, 19, 23, 31 x3, 39). The audit expectation
"Faster-RCNN + MobileNet" is NOT reproduced: both names sit in sentences
that carry a citation (ch2.md:19 Li, L.H. et al.; ch2.md:27 TensorFlow
Hub); a names-file mapping (`Faster-RCNN | Ren, 2015`) would flag them —
the reference targets are UNVERIFIED-EXTERNAL (see H = section H of
`docs/ch2_argument_spine.md`).
Options considered: (a) hand-check in-text citations against the reference
list before each submission; (b) a stdlib checker run on the docx mirror plus
a pointer-only structure map of Chapter 2; (c) a python-docx / pandoc based
checker (new dependencies absent from both venvs).
Decision: (b).
Reason: repeatable and offline with no new dependency; it flags
cited-not-referenced, referenced-not-cited and bare technical names
mechanically on every export, and the structure map records anchors and facts
so the author's revision can be checked against the submitted draft without
reproducing its prose.
Impact: files added — `scripts/check_citations.py` (stdlib), `tests/test_check_citations.py` (5 tests in the fast lane), `docs/ch2_argument_spine.md` (Table E12 body -> Table E12 in `docs/report_evidence_tables.md`; wording constraints E.1-E.8; author's to-do list); no change under `src/`. Ch2 prose count re-keyed in `docs/report_skeleton.md` to `docs/draft_as_submitted/wordcount.json` (`chapters.ch2.prose_words` 1762, `prose_plus_table_words` 1905).

## Decision 035: P3 testing strategy — retry/shielding/CLI tests + inventory tooling
Date: 2026-09-24
Status: accepted — Options/Decision/Reason recorded 2026-09-28 (retrospective for the 2026-09-24/26 changes); pytest-cov NOT adopted (see Decision)
Source draft: `docs/evaluation_strategy_matrix.md` '## For integration' > '### DECISIONS.md draft — P3' (placed by the Integrate stage 2026-09-26; body verbatim, one Impact line appended; Options/Decision/Reason left blank by the Verify stage 2026-09-26, the facts kept in the bullet list above them).

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
Options considered: (a) leave protocol claims T5 lines 58-59 untested and
branch coverage unmeasured; (b) add fast offline tests for the non-streaming
retry ladder, wrapper-failure shielding and the CLI, plus a collection-driven
test inventory; (c) add pytest-cov as a dev dependency and measure branch
coverage on pipeline.py.
Decision: (b). (c) is not adopted before submission: `scripts/coverage_report.sh`
is committed and refuses to run until pytest-cov is installed, and Table E9
reports coverage as not measured.
Reason: (b) discharges two protocol claims with zero new dependencies and makes
every test count tool-generated instead of hand-typed (the counts had drifted
three times); (c) needs a new dependency (CLAUDE.md rule 4) and its own
DECISIONS entry if adopted later, and "not measured" is the honest state now.
Impact: fast lanes 2026-09-26 (all files landed, inventories regenerated): WSL 95 passed / 10 skipped / 0 failed,
offline 83 passed / 11 skipped / 0 failed (baseline 71 + 12 and 59 + 12 new tests, plus the
P2 checker tests from the same sprint). Schemas,
judge contract and public API untouched. Table E9 gains the "T5 coverage"
row; Tables E1a-E1c added.
Integrate-stage re-run 2026-09-26, all tasks landed: WSL 95 passed / 10 skipped, Windows
offline 83 passed / 11 skipped (both exit 0; tests/test_figures_provenance.py
green). Tables E1a/E1b/E1c placed in docs/report_evidence_tables.md.

## Decision 036: P2 — report reference checker + crosswalk; SVG text de-coupled from table ids
Date: 2026-09-24
Status: accepted — Options/Decision/Reason recorded 2026-09-28 (retrospective for the 2026-09-24/26 changes)
Source draft: `docs/report_crosswalk.md` '## For integration' > '### DECISIONS draft — P2' (placed by the Integrate stage 2026-09-26; body verbatim).

Context: The pre-submission checklist required a reference checker for the
report (skeleton line "Run `scripts/check_report_refs.py` (pending)"). Added
`scripts/check_report_refs.py` (stdlib zipfile + ElementTree; field-aware
text; checks: missing / dangling references, per-kind sequence, duplicates,
repo-only `Table E*` ids, standalone caption length, front-matter list
drift, drawing/table proximity, header/footer captions) with
`tests/test_check_report_refs.py` (7 tests on generated minimal .docx files),
`docs/report_crosswalk.md` (report id -> asset / E-table -> results.json key
paths -> chapter), and `tests/test_figures_provenance.py` (5 tests: every
number printed on fig3/fig4/fig5/fig6 SVG text exists in the cited
results.json; no `Table E*` id in any SVG). Run on the submitted draft: 3
errors, all `repo-only-id` on the Table 4.2 / 5.1 / 5.4 source lines; 0
missing, 0 dangling, 0 sequence errors; 1 merged S2/S3 caption. One text edit:
`docs/figures/fig4_t6_ablation.svg` trailing label dropped "(see Table E6)".
`docs/report_frontmatter_template.md` embedding recipe now says insert the
SVG directly (Word accepts SVG; byte-identical asset) and lists
S3_stream_tokens.png / S4_dashboard_full.png as committed-but-unused
(md5 check against the draft's `word/media/`).
Options considered: (a) rely on Word's own caption numbering and manual
proof-reading; (b) a stdlib docx reference checker, a report-id -> E-table ->
results.json crosswalk, and a test pinning every number drawn in a figure to
its results.json; (c) a python-docx based renumbering tool (new dependency).
Decision: (b); figure SVG text no longer embeds evidence-table ids.
Reason: the submitted draft had hand-typed numbering (0 SEQ fields), so the
marker's P2 comment would recur silently on every insert; the checker makes the
requirement verifiable on each export, and the provenance test extends rule 2
to figures.
Impact: two new scripts/tests in the fast lane (+12 tests); no change under
`src/`; no change to any file under `outputs/`; report edits (E-id source
lines, S2/S3 split, SEQ/REF fields) remain the author's to make in Word.

## Decision 037: P1 — final video shot list + preflight; dashboard newest-run rule surfaced
Date: 2026-09-24
Status: accepted — Options/Decision/Reason recorded 2026-09-28 (retrospective for the 2026-09-24/26 changes)
Source draft: `docs/Video_Shot_List_Final.md` '## For integration' (placed by the Integrate stage 2026-09-26; body verbatim, one Impact line appended).

Context: the FINAL brief's video constraints (3-5 min, own voice, not sped
up, working program + features + understanding; criteria 17/18) replace the
preliminary plan in `docs/Video_Script_Prototype_Demo.md` (now banner-marked
historical). A 9-shot, 260 s plan was written with file:line evidence per
shot and an Ollama-down fallback (`index.html:186-188`). `scripts/video_preflight.sh`
(WSL, read-only: health keys `main.py:85-100`, `ollama ps`, `data/local_demo`
presence, `git status --porcelain -- outputs/evaluation`, `/eval/summary`
run ids) gives a go/no-go before recording. `docs/video_number_card.md`
lists every dashboard number verbatim with its results.json key.
Fact surfaced: `/eval/summary` keeps the newest run per track
(`main.py:469,481,515`), so `/dashboard` shows T6 run 20260725-191055
(ollama judge, multimodal accuracy 0.4583) while Table E6 cites the rule run
20260705-160858 (0.625) and E6c holds both runs; the narration must name the
run id that is on screen. Suite counts measured 2026-09-24 on the working tree:
Windows 83 passed / 11 skipped, WSL 95 passed / 10 skipped (re-measure at
integration; sibling tasks were adding tests during the measurement).
Options considered: (a) reuse the Tier-A video script (mock wrappers, 23 tests,
CLI shots — stale); (b) a new shot list keyed to the as-built demo with a
timing budget under the 5-minute cap, a read-only preflight script and a
number card; (c) a slides-only video.
Decision: (b).
Reason: the brief requires the working program on screen, the author's own
voice and 3-5 minutes; the preflight prevents recording with the wrong
backends or an uncommitted run on the dashboard, and the number card keeps
spoken numbers identical to the report's tables. (c) fails the brief.
Impact: files added — `docs/Video_Shot_List_Final.md`, `scripts/video_preflight.sh`,
`docs/video_number_card.md`, `docs/figures/video/title_card.svg`,
`tiers_card.svg`, `close_card.svg`; `docs/Video_Script_Prototype_Demo.md`
banner lines only (counts, pointer, architecture figure path). No change
under `src/`, `outputs/` or `scripts/demo_up.sh`.
Integrate-stage re-run 2026-09-26: Windows 83 passed / 11 skipped, WSL 95 passed / 10 skipped (Table E1
row 'after D-035').
