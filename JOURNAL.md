# Journal — TriGuard

## Week 1–2 — Project pitch
### Planned work
- Choose template (CM3020 / Project Idea 1).
- Pitch video (3–5 min) + slides.

### Completed work
- Template chosen: CM3020 / Project Idea 1 — Orchestrating AI Models.
- Working title: TriGuard.
- Pitch deck (9 slides) and voice-over script prepared.

### Decisions made
- Logged in `DECISIONS.md` (D-001 to D-003).

### Next steps
- Topic 3 literature matrix + draft.
- Topic 4 project design + architecture + evaluation protocol.

---

## Week 3 — Literature foundation
### Planned work
- Open and read 8 sources.
- Populate `docs/referencing_notes.md`.
- Build `docs/literature_matrix.md`.
- Draft `docs/literature_review_draft.md` (≤2500 words).

### Completed work
- _(fill in as work progresses)_

### Problems encountered
- _(fill in)_

### Decisions made
- _(fill in)_

### Tests/evidence produced
- _(fill in)_

### What I learned
- _(fill in)_

### Next steps
- Move to Topic 4 — project design draft + system architecture + evaluation protocol.

---

## Week 4 — Topic 2 submissions
### Planned work
- Submit ethics quiz.
- Submit formative Project Proposal.

### Completed work
- Ethics quiz submitted via VLE.
- Project Proposal submitted via VLE.

### Decisions made
- D-006 (ethics quiz), D-007 (proposal), D-008 (coding deferred until after Preliminary Report).

### Tests/evidence produced
- VLE submission receipts (kept locally).

### What changed in the project
- Phase A closed.
- Sequencing changed: written deliverables fully precede coding now.

### Next steps
- Confirm Preliminary Report scope with tutor (word limit, prototype requirement).
- Assemble Preliminary Report from existing `docs/` files.

---

## Week 5 — Preliminary Report kickoff
### Planned work
- Confirm Preliminary Report scope.
- Reshape plan around 4-chapter report + feature prototype + MP4 video.

### Decisions made
- D-009 reverses D-008: coding starts now (prototype required for Ch4).
- D-010: single PDF, four chapters.

### Next steps
- Decide prototype ambition (mock only vs partial real vs full real).
- Start repo skeleton + schemas + mock pipeline.
- Polish lit review + design into Ch2 / Ch3.
- Draft Ch1 intro and Ch4 prototype chapter.
- Write video script.

---

## Week 6 — First real dataset (T2 text track)
### Planned work
- Evaluate the real text wrapper on a real public toxicity dataset (track T2),
  reporting honest macro-F1 / per-class precision-recall / confusion matrix.

### Completed work
- Added `src/triguard/data/datasets.py` — streaming, reproducible loader
  (`load_toxicity_sample`) with a fixed-seed buffered shuffle and an offline
  sample cache under `data/t2_samples/`.
- Added `src/triguard/evaluation/run_t2.py` — runs the real text wrapper over
  the sample and writes a metrics envelope to
  `outputs/evaluation/<ts>/t2/results.json`.
- Added a `slow`/network test + a `--run-slow` gate (`tests/conftest.py`); fast
  lane stays offline at 23 passed.
- Added `datasets` dependency (optional `eval` extra) and `.gitignore`.

### Problems encountered
- The originally planned primary dataset (`tweet_eval/hate`) turned out to be
  permission-gated (HatEval), conflicting with the "public datasets only" rule.
  Switched the default to `google/civil_comments` (CC0); see D-011.

### Decisions made
- D-011: Civil Comments (CC0) default; binary toxic/non-toxic scheme.

### Tests/evidence produced
- `outputs/evaluation/<ts>/t2/results.json` (numbers as computed — not invented).

### Next steps
- Consider the HF text classifier swap (Prompt 1) and re-run T2 to compare
  against the sklearn sanity floor.

---

## Week 7 — Real text model (Sprint 1)
### Planned work
- Make the text wrapper real: add a Hugging Face `unitary/toxic-bert` tier,
  keep mock + sklearn, re-run T2 (OLD sklearn vs NEW hf).

### Completed work
- Added `"hf"` tier to `text_model.py` (toxic-bert, pinned revision
  `4d6c22e7...`), lazy transformers/torch, `lru_cache`, auto-fallback to mock.
- Slow test `tests/test_text_model_hf.py` (benign < 0.3, toxic > 0.7).
- `run_t2 --backend {sklearn,hf,mock}` (default sklearn); both T2 dirs kept.
- Deps: `transformers`, `torch`, `numpy<2` pin (+ `[eval]` extra).

### Decisions made
- D-012: add hf tier; keep sklearn as offline default + baseline.

### Tests/evidence produced
- `outputs/evaluation/<ts>/t2/results.json` (sklearn OLD + hf NEW).

### Next steps
- Sprint 2 — real image wrapper (BLIP captioning).

---

## Week 8 — Real image model (Sprint 2)
### Planned work
- Make the image wrapper real: add a BLIP captioning tier, keep mock default.

### Completed work
- Added `"blip"` tier to `image_model.py`
  (`Salesforce/blip-image-captioning-base`, pinned rev `82a3776…`); caption +
  keyword-vocab cues; downscale ≤1024; confidence from generation scores
  (fallback 0.6, tagged in `raw`); auto-fallback to mock.
- Slow test `tests/test_image_model_blip.py` on a committed synthetic
  public-domain image (`data/sample_inputs/blip_test.png`).
- `pillow` dep (+ `[eval]`); `scripts/run_wsl_sprint2.sh`.

### Decisions made
- D-013: add BLIP tier; mock stays offline default.

### Tests/evidence produced
- Fast suite green; slow BLIP test produces a non-empty caption (run via WSL).

### Next steps
- Sprint 3 — real audio wrapper (Whisper + YAMNet).

---

## Week 9 — Real audio model (Sprint 3)
### Planned work
- Make the audio wrapper real: Whisper transcription + YAMNet tagging, keep
  mock default.

### Completed work
- Added `"real"` tier to `audio_model.py` (Whisper `tiny`/`small` +
  TF-Hub `yamnet/1`); transcript_confidence from `avg_logprob`; top-5 tags >0.2;
  per-component fallback to mock; auto-degrade never crashes.
- Slow test `tests/test_audio_model_real.py` (skips until a public-domain WAV is
  dropped at `data/sample_inputs/audio_test.wav`).
- `[audio]` optional extra (whisper, tensorflow, tensorflow-hub, librosa,
  soundfile) kept out of requirements/[eval] (py3.12-only); `~/.venv-triguard-audio`
  gitignored; `scripts/run_wsl_sprint3.sh` (uv → py3.12).

### Problems encountered
- WSL default is Python 3.14 → no TF/numba wheels. Resolved with a uv-provisioned
  py3.12 venv (no sudo) for the audio stack only.

### Decisions made
- D-014: add real audio tier; mock stays offline default; py3.12 ~/.venv-triguard-audio.

### Tests/evidence produced
- Fast suite green; audio stack import smoke + slow test (pending the WAV clip).

### Next steps
- All three perception models now have real tiers. Optional: T3/T4 real-data
  evaluation; HF/CPU repins; FastAPI demo (Prompt 5).

---

## Week 10 — Real LLM judge (Ollama)
### Planned work
- Exercise + harden the existing Ollama judge path against a real local LLM,
  prove the graceful fallback, and capture a real, evidence-grounded rationale.

### Completed work
- `llm_judge.py`: read host/model/timeout per call (`TRIGUARD_OLLAMA_MODEL`,
  `OLLAMA_HOST`, `OLLAMA_TIMEOUT`); split fallback tags (`judge_output_invalid`
  vs `ollama_unavailable:<reason>`); catch `json.JSONDecodeError` in the
  retry/fallback path. Default judge stays rule + offline; public schema untouched.
- `scripts/smoke_ollama.py`: judges the same evidence via rule and Ollama, runs a
  grounding/hallucination check on the LLM rationale, and re-validates against
  `JudgeOutput`.
- `tests/test_llm_judge_ollama.py`: one `slow` test; skips cleanly when Ollama is
  unreachable. No CI dependency on Ollama.
- Stood up Ollama user-local in WSL (no sudo; v0.31.1 tar.zst decompressed via
  Python 3.14 stdlib `compression.zstd`); pulled `llama3:8b-instruct-q4_K_M`;
  ran on GPU (WSL passthrough).

### Problems encountered
- No passwordless sudo -> installed Ollama from the release tarball into $HOME.
- WSL had no zstd binary and `tar` lacked zstd support -> decompressed with
  Python 3.14's `compression.zstd`.
- Flaky link reset the 1.4 GB bundle download -> resumable retry loop.
- First (cold) inference exceeded the 60 s client timeout and fell back -> added
  `OLLAMA_TIMEOUT`; warmed the model before the timed smoke.

### Decisions made
- D-015: Ollama path exercised + hardened; rule stays default; no new dependency.

### Tests/evidence produced
- Fast suite 23 passed, 6 skipped (offline). Slow ollama test 1 passed with the
  server up. Real rule-vs-llama3 comparison + grounding + fallback captured (see
  D-015 and docs/implementation_notes.md).

### Next steps
- Optional: combined py3.12 tri-modal venv; T3/T4 real-data eval; FastAPI demo;
  Preliminary Report assembly.
