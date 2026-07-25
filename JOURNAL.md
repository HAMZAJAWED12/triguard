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

---

## Week 11 — Single-process tri-modal integration (~/.venv-tri)
### Planned work
- Build one py3.12 CPU venv running text + image + audio + the Ollama judge in a
  single orchestrator pass; capture an all-real TriGuardResult.

### Completed work
- `scripts/build_venv_tri.sh` — uv py3.12 `~/.venv-tri` (CPU torch first), full stack.
- `requirements-full.txt` — 95 exact pins (Python 3.12.13).
- `data/sample_inputs/sample_multimodal_real.json` — real toxic text + committed
  synthetic image/audio.
- One-pass all-real run captured (`outputs/demo_full_real.json`) + graceful-fallback
  run (`outputs/demo_harmful_fallback.json`); Sprint-5 section in
  `docs/implementation_notes.md`.

### Problems encountered
- SIGSEGV: `transformers` eagerly imports TensorFlow when both frameworks are
  installed -> torch+TF crash on pipeline run. Isolated to the text step; fixed
  environment-only with `USE_TF=0` (no code change). KMP/OMP/MKL flags did not help.

### Decisions made
- D-016: combined `~/.venv-tri` + `USE_TF=0` guard; schema/wrappers/Windows `.venv`
  untouched.

### Tests/evidence produced
- Import proof (all eight libs, one process). Fast suite 23 passed / 6 skipped in
  the new venv. All-real TriGuardResult: real-hf 0.9751, real-blip caption,
  real-audio Whisper+YAMNet, llama3 harmful/block grounded. RAM 2.98 GB + 5.3 GB
  VRAM; latency_ms 49421 cold.

### Next steps
- Optional: fix `model_versions` reporting (pipeline); T3/T4 real-data eval;
  FastAPI demo; Preliminary Report assembly.

---

## Week 12 — Audio evaluation (track T4)
### Planned work
- Measure the real audio wrapper on public ground truth: Whisper WER + YAMNet
  event accuracy. Honest numbers, no perception-code change.

### Completed work
- `src/triguard/data/audio_datasets.py` — LibriSpeech + ESC-50 streamed loaders
  (seed + cap, persist wavs + manifest, gitignored `data/t4_samples/`).
- `src/triguard/evaluation/run_t4.py` — WER (jiwer) + YAMNet top-1/top-5 vs an
  approximate ESC-50 -> AudioSet map; writes `outputs/evaluation/<ts>/t4/results.json`.
- `tests/test_run_t4.py` — one slow loader test (clean-skip offline).
- `jiwer` pinned in `[eval]` + `requirements.txt`; `data/t4_samples/` gitignored.

### Problems encountered
- AudioSet (protocol T4) ships only YouTube ids -> substituted LibriSpeech (WER)
  + ESC-50 (tagging) as public, ungated proxies; documented as a limitation.

### Decisions made
- D-017: T4 proxies + approximate YAMNet map; top-5 the fair headline.

### Tests/evidence produced
- Run `20260704-153729` (`~/.venv-tri`, seed 42, n=50 each, both `real-audio`):
  Whisper WER corpus 0.0971 / mean-clip 0.1314 (tiny); YAMNet top-1 0.32 /
  top-5 0.66 (ESC-50, 29 categories). Fast suite 23 passed / 7 skipped.

### Next steps
- Optional: T3 image-text eval; fix `model_versions` pipeline hardcode; FastAPI demo.

---

## Week 13 — Image-text evaluation (track T3)
### Planned work
- Measure the image track on a public labelled image-text set: pipeline
  flag-vs-label. Honest numbers, no perception-code change.

### Completed work
- Repo relocated off OneDrive to `C:\dev\triguard` (`/mnt/c/dev/triguard`); the 4
  `scripts/*.sh` `cd` paths repointed.
- Verified dataset options first: Hateful Memes gated; MMHS150K mirror = 6.5 GB
  zip (unstreamable) + licence unclear -> rejected. Chose `Ahren09/MMSoc_Memotion`
  (Memotion; ungated, embedded images, `offensive` label + OCR text).
- `src/triguard/data/image_datasets.py` (stream + persist images to gitignored
  `data/t3_samples/`, never committed); `src/triguard/evaluation/run_t3.py`
  (flag-vs-label P/R/F1 + confusion + AUROC + text-only baseline);
  `tests/test_run_t3.py` (one slow loader test, clean-skip offline).

### Problems encountered
- No clean CC-licensed streamable image-text hate benchmark exists (meme/tweet
  images are third-party copyright); used Memotion with media streamed + never
  committed, documented as a limitation.

### Decisions made
- D-018: Memotion flag-vs-label; captioner-not-classifier framing; media never committed.

### Tests/evidence produced
- Run 20260704-172017 (`~/.venv-tri`, seed 42, n=50, real-hf + real-blip, rule
  judge): pipeline P 0.6923 / R 0.2812 / F1 0.40 / acc 0.46 / AUROC 0.566;
  text-only baseline F1 0.3636. Fast suite 23 passed / 8 skipped.

### Next steps
- Optional: fix `model_versions` pipeline hardcode; FastAPI demo; Preliminary
  Report update.

---

## Week 14 — FastAPI demo surface (Prompt 5)
### Planned work
- A small HTTP surface so a non-technical reviewer can submit content and read the
  structured decision. Demo layer only.

### Completed work
- `src/triguard/api/main.py` — `GET /` (health), `GET /ui`, `POST /analyse/text`,
  `POST /analyse/multimodal` (uploads -> temp files -> pipeline -> cleanup). Env
  flags honoured; no real models forced; binds 127.0.0.1.
- `src/triguard/api/static/index.html` — one self-contained page (no CDN, WCAG-AA,
  >=16px, system fonts) posting to `/analyse/multimodal`.
- `tests/test_api.py` — importorskip + `TRIGUARD_MOCK=1`; GET / + text endpoints.
- Deps `fastapi`/`uvicorn`/`python-multipart`/`httpx` pinned in requirements +
  `[eval]`; README run line.

### Problems encountered
- The relocated repo had no `.venv-linux` (gitignored, path-bound) -> installed the
  api deps into `~/.venv-tri` via `ensurepip` + pip.

### Decisions made
- D-020: FastAPI demo layer; offline/skip-safe tests; no core changes.

### Tests/evidence produced
- Fast suite 27 passed / 8 skipped (`~/.venv-tri`); 24 passed / 9 skipped (Windows,
  api module importorskip-skips). Boot smoke: uvicorn 127.0.0.1:8001 serves `/`,
  `/analyse/text`, `/ui`.

### Next steps
- Optional: Preliminary Report update with the API demo + eval numbers.

---

## Week 15 — T6 tri-modal ablation harness (roadmap Phase A)
### Planned work
- Build the harness to demonstrate the thesis (multimodal vs unimodal); scaffold the
  hand-built T6 set.

### Completed work
- `src/triguard/evaluation/run_t6.py` — 4-condition ablation (text/image/audio-only
  vs multimodal), rule judge, per-condition metrics + `cross_modal_ablation` table.
- `data/sample_inputs/triguard_eval_v1/` — manifest schema + README; an AI-DRAFTED
  starter set of 18 non-confounder items (provenance recorded; to be reviewed/owned).
- `tests/test_run_t6.py` — fast offline manifest-parse test.

### Problems encountered
- Genuine cross-modal confounders can't be auto-authored: only two benign committed
  media assets, and the confounder design + labels are the student's own work.

### Decisions made
- D-022: T6 ablation harness; AI-drafted starter manifest kept separate from the
  student's confounder-case design.

### Tests/evidence produced
- Fast suite 26 passed / 9 skipped (Windows). Real ablation
  (`outputs/evaluation/20260704-221056/t6/`): multimodal 0.7778 acc / 0.6852 macro-F1
  >= text-only 0.75 / 0.6746 > image/audio-only. cross_modal harmful items: 0.

### Next steps
- Student: author ~30–50 cross-modal confounder cases + media -> re-run T6 for the
  headline multimodal-vs-unimodal recall delta. Then roadmap Phase B (OCR).

---

## Week 16 — Opt-in OCR for the image track (roadmap Phase B)
### Planned work
- Add OCR so meme text feeds moderation; measure the delta on the image track.

### Completed work
- `image_model.py` — opt-in OCR (`TRIGUARD_IMAGE_OCR=1`) via RapidOCR (torch-free);
  `raw["ocr_text"]` + folded into image cues. No schema/pipeline change.
- `run_t3.py --ocr` — image-track-alone +/-OCR ablation (dataset text dropped).
- `data/sample_inputs/ocr_test.png` + slow test `tests/test_image_model_ocr.py`.
- Deps: `rapidocr-onnxruntime` pinned; `build_venv_tri.sh` updated.

### Problems encountered
- easyocr broke the venv: its torchvision is ABI-incompatible with torch 2.12.1+cpu
  and its install bumped numpy to 2.5.x, crashing transformers/BLIP. Purged
  easyocr+torchvision, re-pinned numpy<2, switched to torch-free RapidOCR.

### Decisions made
- D-023: opt-in OCR via RapidOCR; image-track-alone ablation.

### Tests/evidence produced
- Fast suite 26 passed / 10 skipped. Slow OCR test passes (reads the synthetic clip).
  T3 OCR ablation (real, n=50, `outputs/evaluation/20260705-111002/t3/`, OCR 50/50) vs
  BLIP-caption-only F1 0.0606: OCR->keyword-cues 0.0606 (delta 0.0, sub-finding);
  OCR->toxic-bert text track F1 0.4348 (delta +0.3742, headline). OCR is valuable when
  routed to a real classifier; the narrow keyword cues were the bottleneck.

### Next steps
- Roadmap Phase C (failure analysis, T7 grounding, T8 perf). Optionally route OCR
  text to the toxic-bert text track to realise its value.

---

## Week 17 — Evaluation completeness: failure analysis + T7 + T8 (roadmap Phase C)
### Planned work
- Finish the designed-but-unbuilt eval utilities: failure taxonomy, rationale
  grounding, hardware viability.

### Completed work
- `src/triguard/evaluation/failure_analysis.py` — top-N worst cases + taxonomy from
  any results.json.
- `src/triguard/evaluation/grounding.py` + `run_t7.py` — rationale grounding rate
  (headline = ollama/llama3; rule ~1.0 by construction); blank human usefulness column.
- `src/triguard/evaluation/run_t8.py` — p50/p95 + cold-start latency + peak RSS
  (psutil), mock vs real.
- Fast tests `test_grounding.py`, `test_failure_analysis.py`; `psutil` pinned.

### Decisions made
- D-024: Phase-C eval utilities (failure analysis + T7 grounding + T8 perf).

### Tests/evidence produced
- Fast suite 29 passed / 10 skipped. Real (T6 n=18): T7 grounding ollama 1.0
  measured (0 invented modalities; rule ~1.0 by construction, not separately
  measured); T8 real p50 31.1 ms / p95 4075 ms / cold-start 4075 ms
  / peak RSS 2.87 GB (mock p50 0.0 ms / RSS 34.5 MB); failure_analysis 10 failures.

### Next steps
- Roadmap Phase D (demo wow) + Phase E (report integration). Optional: LLM-judge
  bias audit (Zheng).

---

## Week 18 — Demo surface: presets, compare, streaming judge, dashboard (roadmap Phase D)
### Planned work
- Make the demo showcase the real system: one-click presets, a rule-vs-llama3
  side-by-side, live llama3 token streaming, and charts of the committed eval
  numbers — without touching schemas, wrappers or offline defaults.

### Completed work
- `llm_judge.py` — additive `judge_stream()` + `_ollama_generate_stream`
  (NDJSON, `stream:true`); token events presentation-only, terminal event =
  schema-validated JudgeOutput with the same fallback tags as `judge()`.
- `pipeline.py` — fallback labelling promoted to public `judge_label()`
  (behaviour identical; `run()` now calls it).
- `api/main.py` — `GET /presets`, `POST /analyse/preset` (whitelisted committed
  samples only), `POST /analyse/compare` (perception once, judged twice),
  `POST /analyse/stream` (SSE), `GET /eval/summary` (verbatim whitelist copy of
  the latest committed results.json per track), `GET /dashboard`.
- `static/index.html` — preset buttons, judge-mode selector, two-column compare
  with honest `ollama->rule` warning, SSE consumer (tokens via `textContent`),
  dashboard link. New self-contained `static/dashboard.html` (no CDN) rendering
  T2/T3/T4/T6/T7/T8 with each run's limitations + the T6 provenance warning.
- Tests: `test_llm_judge_stream.py` (3 offline) + `test_api_phase_d.py`
  (8 fast offline incl. a closed-port fallback path and an eval-summary
  equals-the-committed-file check; 1 slow real-ollama test).

### Problems encountered
- Dashboard bars rendered empty: the fill `<span>` was inline so `width` was
  ignored — fixed with `display:block` (caught by browser preview, not tests).
- PowerShell quoting mangled a long inline WSL smoke command — moved smokes
  into script files.
- A multi-agent adversarial review of the diff confirmed 8 defects (all
  fixed): a temp-file-leak regression in `_gather_inputs`, missing
  python-multipart importorskip (tests ERROR not skip on lean venvs), preset
  buttons clickable mid-stream (UI corruption), dashboard `toFixed` rounding +
  hardcoded `+` sign + dropped T2 limitations + invisible run config (a mock
  re-run could have charted as real) + an error message printing the HTTP
  status, and a T8 `config.mock`-absent run defaulting to the `real` label.

### Decisions made
- D-025: Phase D demo surface (presets whitelist, perception-once compare,
  additive streaming judge, read-verbatim dashboard).

### Tests/evidence produced
- Fast suite: WSL 45 passed / 10 skipped; Windows offline venv 33 passed / 11
  skipped. Live smoke (mock perception, warm llama3): stream produced 98 token
  events + a schema-valid `source:"ollama"` verdict; compare rule 0 ms vs
  llama3 5451 ms on identical evidence; offline smoke shows `ollama->rule`
  fallback on every llama3 surface. `--run-slow` on the Phase D files with
  Ollama up: 12 passed. Dashboard render verified in a real browser
  (verbatim values, config lines, limitations, provenance warning).

### Next steps
- Phase E — report integration (tables/figures from committed numbers;
  prose + T6 confounder set remain the student's own work).

---

## Week 18b — T6 evaluation set v2 (student-reviewed)
### Planned work
- Replace the AI-drafted T6 starter set with a set reviewed and owned by the
  student; update the declaration honestly; re-run T6.

### Completed work
- New `triguard_eval_v1/manifest.json` v2: 24 items (10 safe / 6 borderline /
  8 harmful) authored as an AI-assisted draft, then reviewed, edited and
  approved by the student; provenance field records exactly that (D-026).
- `run_t6.py`: hardcoded "AI-DRAFTED starter set" limitation replaced with a
  neutral pointer to `manifest_provenance`.
- Real T6 re-run on the v2 set (run 20260705-160858).

### Decisions made
- D-026: adopt v2 manifest; disclosure preserved (manifest provenance +
  report AI-use section), per the UoL Generative AI policy.

### Tests/evidence produced
- Fast suite 45 passed / 10 skipped (WSL). T6 v2 (real hf+blip+real-audio,
  rule judge, n=24): multimodal 0.625 acc / 0.4945 macro-F1 >= text-only
  0.5909 / 0.4786 > image/audio-only 0.5 / 0.2222; cross_modal harmful 0.
  Honest note: lower than v1 because v2's borderline items are milder than
  the rule judge's 0.35 threshold catches — a real recall finding.

### Next steps
- Phase E: report skeleton + evidence tables once the CM3070 spec + module
  AI-level statement are supplied.

---

## Week 19 — Demo-readiness hardening (pre-video audit)
### Planned work
- Full-codebase audit before the FYP demo: find anything that could break or
  embarrass a live run; fix on approval.

### Completed work
- Audit (multi-agent + live reproduction) confirmed 4 demo-breakers; all fixed
  (D-027): per-request decode failures no longer latch BLIP/Whisper/YAMNet off;
  `USE_TF=0` added to every documented real command (missing guard segfaulted
  the server — reproduced); `scripts/demo_up.sh` one-command pre-demo ritual;
  llama3 `keep_alive` (30m) ends idle-unload dead air.
- Surface: health endpoint + /ui banner show effective backends (mock vs real
  at a glance); /eval/summary flags uncommitted (rehearsal) runs and the
  dashboard warns on them; upload filenames keep their stem (mock cues work);
  CLI takes `--judge` after the subcommand + friendly errors.
- Hygiene: README truncation repaired, CLAUDE.md real-vs-mock table rewritten,
  CONTEXT_HANDOFF.md deleted, .gitignore deduped, session lock untracked,
  preliminary video script marked historical.

### Tests/evidence produced
- Fast suites 49 passed / 10 skipped (WSL), 37 passed / 11 skipped (offline);
  +4 latch regression tests. Live: demo_up.sh ALL GREEN; corrupt-then-good
  upload keeps BLIP real; injected uncommitted run flagged on the dashboard;
  stream 89 tokens -> final `ollama`.

### Next steps
- Record the final demo video off demo_up.sh; finish the final report.

---

## Week 19b — Confounder-set infrastructure (thesis-metric gap)
### Planned work
- Remove every mechanical obstacle to the student authoring the cross-modal
  confounder set; keep the design and labels the student's own (D-028).

### Completed work
- `run_t6 --judge {rule,ollama}` (default unchanged) — enables the two-judge
  confounder experiment; the rule judge is structurally blind to
  combination-only harm, llama3 reads evidence jointly.
- `confounders_TEMPLATE.json` (12 empty CF slots) + `README_confounders.md`
  (concept per Kiela et al. 2020, validity property, four combination
  patterns, ethics rails, two-judge protocol + BLIP-caption caveat).
- `scripts/make_confounder_media.py` (TTS + own-photo import with EXIF strip)
  and `scripts/check_confounders.py` (pre-merge validator; verified against
  good and deliberately broken items).

### Tests/evidence produced
- Fast suites unchanged: 49/10 (WSL), 37/11 (offline). Toolkit smoke: TTS wav
  + metadata-stripped PNG produced.

### Next steps
- Student: design 8–12 confounder cases, produce media, fill template, run
  the validator, merge into manifest v3, re-run T6 twice (rule / ollama),
  compare cross_modal recall. Then T7 usefulness ratings.
