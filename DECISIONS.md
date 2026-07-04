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
