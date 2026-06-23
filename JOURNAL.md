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
