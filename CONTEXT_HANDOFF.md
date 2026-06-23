# Context Handoff — TriGuard (CM3070)

This file is a self-contained dump of everything a new Claude session needs
to continue the project. Paste **Section 0** as the first message in the
new chat; attach this file or the linked files when asked.

---

## Section 0 — Paste this as the first message in the new chat

> Hi Claude. I am continuing my CM3070 Computer Science Final Project from
> a previous chat (different account). My project is **TriGuard**: a
> multimodal, explainable, locally deployable content-moderation pipeline,
> built on the **CM3020 Artificial Intelligence** template, *Project Idea
> 1: Orchestrating AI Models to Achieve a Goal*.
>
> All files live in `E:\OneDrive\ICAEWSOFTWARE\FYP UOL\triguard\`. The
> repo contains the full Tier-A prototype, a 13-page Preliminary Report
> PDF, a literature review PDF, a project design PDF, a 24-week work
> plan, decisions log and risk register.
>
> Before responding to my next task, please read these files in order:
>
> 1. `CLAUDE.md` (operating rules)
> 2. `README.md` (repo layout)
> 3. `DECISIONS.md` (10 decisions logged so far — D-001 to D-010)
> 4. `JOURNAL.md` (weekly entries through Week 5)
> 5. `RISK_REGISTER.md` (12 risks)
> 6. `docs/project_design_draft.md` (system design)
> 7. `docs/chapter4_prototype.md` (current prototype scope)
> 8. `docs/CLAUDE_CODE_PROMPTS.md` (sequential prompts for upcoming work)
> 9. `CONTEXT_HANDOFF.md` (this file — summary of what's done, what's next, open issues)
>
> The previous chat finished by writing the Preliminary Report
> (`docs/TriGuard_Preliminary_Report.pdf`), shipping a working Tier-A
> prototype (22 passing pytest cases), and producing a 3–5 minute video
> shot list (`docs/Video_Script_Prototype_Demo.md`). The user has not yet
> recorded the demo video. Coding work from here is intended for Claude
> Code; high-level planning and documentation work happens in this chat.
>
> One known issue: this repo lives inside a OneDrive folder which has
> previously truncated some Python files mid-write. Fix with `Prompt 0`
> in `docs/CLAUDE_CODE_PROMPTS.md` if any `SyntaxError` appears.
>
> Please confirm you have read those files and then ask me what I want
> to work on.

---

## Section 1 — Project identity (one-screen summary)

- **Title:** TriGuard.
- **Module:** CM3070 Computer Science Final Project, University of London.
- **Template:** CM3020 Artificial Intelligence — Project Idea 1:
  *Orchestrating AI Models to Achieve a Goal*.
- **One-liner:** A prototype, locally deployable content-moderation
  pipeline that orchestrates three pre-trained perception models (text,
  image, audio) with a local LLM acting as judge, producing a structured
  decision plus a written rationale that a human moderator can audit.
- **User:** Hamza, BSc Computer Science, University of London.
- **Working folder:** `E:\OneDrive\ICAEWSOFTWARE\FYP UOL\triguard\`.

## Section 2 — What is finished

| Deliverable | File | Status |
|---|---|---|
| Pitch video script + deck (Wk 2) | `Earlier_Submissions/TriGuard_Pitch_Deck.pptx`, `Earlier_Submissions/Video_Script_TriGuard.md` | Done |
| Ethics quiz (Wk 3) | submitted via VLE | Done |
| Project Proposal (Wk 4) | submitted via VLE | Done |
| Literature Review PDF (Wk 4) | `docs/TriGuard_Literature_Review.pdf` (5 pages, 2040 words, 8 sources) | Done |
| Project Design PDF (Wk 5) | `docs/TriGuard_Project_Design.pdf` (7 pages, ~ 2000 words, 14 sections + architecture figure) | Done |
| System architecture spec | `docs/system_architecture.md` + `docs/architecture.png` | Done |
| Evaluation protocol (8 tracks) | `docs/evaluation_protocol.md` | Done |
| Work plan (24 weeks) | `docs/work_plan.md` | Done |
| Inclusive design + ethics docs | `docs/inclusive_design.md`, `docs/ethics.md` | Done |
| Risk register (12 risks) | `RISK_REGISTER.md` | Done |
| Decision log (10 decisions) | `DECISIONS.md` | Done |
| Journal (Wk 1–5) | `JOURNAL.md` | Done |
| Referencing notes (8 sources) | `docs/referencing_notes.md` | Done |
| Literature matrix | `docs/literature_matrix.md` | Done |
| Preliminary Report PDF (Wk 6, 4 chapters, ≤ 6000 words) | `docs/TriGuard_Preliminary_Report.pdf` (13 A4 pages, 5994 body words) | Done |
| Chapter 1 introduction (≤ 1000 words) | `docs/chapter1_introduction.md` (898 w) | Done |
| Chapter 4 prototype writeup (≤ 1500 words) | `docs/chapter4_prototype.md` (1274 w) | Done |
| Tier-A feature prototype (Python package) | `src/triguard/` + `tests/` (22 pytest cases passing) | Done |
| Tier-A evaluation harness | `src/triguard/evaluation/run_eval.py` + saved `outputs/evaluation/<ts>/results.json` | Done |
| Prototype demo video shot list (3–5 min) | `docs/Video_Script_Prototype_Demo.md` | Done |
| CLAUDE.md operating rules | `CLAUDE.md` | Done |
| Sequential Claude Code prompts | `docs/CLAUDE_CODE_PROMPTS.md` (9 prompts) | Done |

## Section 3 — What is next

| Item | Owner | Where described |
|---|---|---|
| **Record the 3–5 min MP4 demo video** | User (own voice required) | `docs/Video_Script_Prototype_Demo.md` |
| Submit Preliminary Report (PDF + MP4) via VLE (Wk 6) | User | n/a |
| **Tier-B real wrappers** (toxic-bert → BLIP → Whisper → Ollama) | Claude Code | Prompts 1–4 in `docs/CLAUDE_CODE_PROMPTS.md` |
| FastAPI demo + accessible HTML page | Claude Code | Prompt 5 |
| Evaluation harness expansion (T3 + T6 + failure analysis) | Claude Code | Prompts 6–7 |
| Final Report (60 %) — formative draft Wk 18 | Mixed (user prose + Claude assist) | n/a |
| Final Report integration (real numbers) | Claude Code | Prompt 8 |
| Final demo video (different from preliminary) | User | Wk 23 of `docs/work_plan.md` |
| Final submission Wk 24 | User | n/a |

## Section 4 — Tier-A prototype (what already exists)

Working modules under `src/triguard/`:

```
orchestrator/
  schemas.py      Pydantic models: TextEvidence, ImageEvidence, AudioEvidence,
                  JudgeInput, JudgeOutput, TriGuardResult
                  Invariants enforced: safe label ≠ block; harmful label ≠ allow;
                  JudgeInput requires ≥ 1 modality.
  pipeline.py     run(text=, image=, audio=, judge_mode=) -> TriGuardResult
                  Calls only the wrappers needed; catches wrapper exceptions;
                  attaches latency_ms and model_versions.
models/
  text_model.py   REAL sklearn TF-IDF + logistic regression on a 30-item
                  bundled corpus; lazy-imports sklearn; auto-falls-back to a
                  rule-based mock if sklearn or its native deps are broken.
                  Modes: "real" / "mock". raw["mode"] = "real" | "mock".
  image_model.py  Mock; deterministic caption + cues derived from filename.
  audio_model.py  Mock; deterministic transcript + YAMNet-style tags from name.
  llm_judge.py    Two paths:
                  - rule-based judge (default, deterministic, schema-valid)
                  - Ollama HTTP path with retry-on-invalid-JSON and graceful
                    fallback to the rule judge. Default model
                    "llama3:8b-instruct-q4_K_M".
evaluation/
  run_eval.py     14-item hand-built tri-modal eval set; reports per-class
                  P/R/F1, confusion matrix, latency p50/p95, saves a JSON
                  envelope under outputs/evaluation/<ts>/results.json.
cli.py            python -m triguard.cli run <sample.json>
                  python -m triguard.cli analyse --text "..."
```

Tests under `tests/`:

- `test_schemas.py` — schema bounds + invariant enforcement.
- `test_text_model.py` — mock + real text classifier on benign + toxic.
- `test_image_model.py` — mock cues.
- `test_audio_model.py` — mock tags.
- `test_llm_judge.py` — rule judge benign / harmful / mixed, Ollama fallback.
- `test_orchestrator.py` — partial inputs, missing inputs, version tagging.

Run command:

```powershell
cd "E:\OneDrive\ICAEWSOFTWARE\FYP UOL\triguard"
$env:PYTHONPATH="src"
python -m pytest -q                 # expected: 22 passed
python -m triguard.evaluation.run_eval
python -m triguard.cli run data\sample_inputs\sample_harmful.json
```

## Section 5 — Decisions log summary

| ID | Decision | Status |
|---|---|---|
| D-001 | CM3020 Idea 1 template chosen | accepted |
| D-002 | Domain = content moderation | accepted |
| D-003 | Project name = TriGuard | accepted |
| D-004 | 8-source literature review scope | accepted |
| D-005 | Harvard referencing | accepted |
| D-006 | Ethics quiz submitted | accepted |
| D-007 | Project Proposal submitted | accepted |
| D-008 | Coding deferred until after Preliminary Report | superseded |
| D-009 | Coding required for Preliminary Report (supersedes D-008) | accepted |
| D-010 | Preliminary Report = single PDF, 4 chapters | accepted |

Full text in `DECISIONS.md`.

## Section 6 — Open issues / known traps

1. **OneDrive truncation.** Files in this repo have been truncated
   mid-write on at least three occasions. Fix with `Prompt 0` in
   `docs/CLAUDE_CODE_PROMPTS.md`. Always re-run `python -m py_compile`
   on every Python file after any Write tool use.
2. **User's global Python env at `D:\Downloads\Lib` is broken.** NumPy
   2.4.3 vs old pyarrow DLL. Solution: use a `.venv` in the repo (see
   the venv block in `docs/CLAUDE_CODE_PROMPTS.md` and `README.md`).
3. **Peer-review feedback on Ch 2 and Ch 3 is pending.** When it
   arrives, re-polish those chapters and rebuild the PDF.
4. **Preliminary Report total wordcount counts tables.** Current build
   is 5994 / 6000 — almost no slack. Any addition to a table requires
   trimming elsewhere.
5. **Ollama is not exercised in CI.** Tests cover the fallback path
   only. Live Ollama smoke test is a manual step on the user's laptop.
6. **Hateful Memes dataset is gated.** Access not yet applied for. T3
   evaluation uses a public fallback set if access is refused.

## Section 7 — Operating rules (one-page version)

1. Read `CLAUDE.md`, `README.md`, `DECISIONS.md`,
   `docs/project_design_draft.md` before changing anything.
2. Do not invent evaluation numbers, dataset rows or citations.
3. Run `PYTHONPATH=src python -m pytest -q` before and after every
   change. Target: ≥ 22 passed.
4. Ask before: removing the rule-based judge fallback; removing any
   modality; removing the rationale field; adding a heavy dependency;
   adding a cloud service; changing the public schema.
5. Document every decision in `DECISIONS.md`.
6. Update the journal weekly in `JOURNAL.md`.
7. Mark planned things `[PLANNED]`; mark real things with the files
   that prove them.
8. Lazy-import heavy ML libraries inside loader functions.
9. Every wrapper must support a `mock_mode` (`TRIGUARD_MOCK=1`).
10. Slow / network tests must be marked `@pytest.mark.slow` and skipped
    by default.

Full version: `CLAUDE.md`.

## Section 8 — Word-count caps (per Preliminary Report handbook)

| Chapter | Cap |
|---|---|
| 1 Introduction | 1000 |
| 2 Literature Review | 2500 |
| 3 Project Design | 2000 |
| 4 Feature Prototype | 1500 |
| **Total** | **6000** (strict) |

Current: 898 / 1827 / 1971 / 1274 = **5970** in the chapter files (the
report build adds chapter headings, landing at 5994 in the PDF).

## Section 9 — References used so far (Harvard)

| Author / year | Used for |
|---|---|
| Gemmeke et al. (2017) | Audio Set / YAMNet baseline |
| Gorwa, Binns & Katzenbach (2020) | Algorithmic moderation governance |
| Kiela et al. (2020) | Hateful Memes benchmark |
| Lazar (2023) | Born-accessible design |
| Lees et al. (2022) | Perspective API |
| Li, J. et al. (2022) | BLIP |
| Li, L.H. et al. (2019) | VisualBERT |
| Radford et al. (2023) | Whisper |
| Zheng et al. (2023) | LLM-as-a-judge |

Full bibliographic data + access dates: `docs/referencing_notes.md`.

## Section 10 — Submission status

| Submission | Wk | Weight | Status |
|---|---|---|---|
| Pitch video (Topic 1) | 2 | 5 % | Done (separate from preliminary demo video) |
| Ethics quiz (Topic 2) | 3 | pass / fail | Done |
| Project Proposal (Topic 2) | 4 | 0 % (formative) | Done |
| Literature review peer review (Topic 3) | 4 | 0 % | Done |
| Project design peer review (Topic 4) | 5 | 0 % | Done |
| **Preliminary Report (Topic 5)** | 6 | **10 %** | PDF ready, video pending recording |
| Written exam | 22 | 20 % | Not started |
| Final demo video | 23 | 5 % | Not started |
| **Final Report + code** | 24 | **60 %** | Not started |

## Section 11 — If something is unclear, look here first

| Question | File |
|---|---|
| What's the project about? | `README.md`, `docs/chapter1_introduction.md` |
| What's the system architecture? | `docs/system_architecture.md`, `docs/architecture.png` |
| What's the evaluation plan? | `docs/evaluation_protocol.md` |
| What's left to build? | `docs/CLAUDE_CODE_PROMPTS.md` |
| What sources can I cite? | `docs/referencing_notes.md` |
| What decisions have been made? | `DECISIONS.md` |
| What's gone wrong so far? | `JOURNAL.md`, this file Section 6 |
| What's the report PDF? | `docs/TriGuard_Preliminary_Report.pdf` |
| How do I run the prototype? | `README.md` Quick start |
| What do I record for the video? | `docs/Video_Script_Prototype_Demo.md` |

---

*End of handoff. The new Claude session should now ask the user what to
work on. Typical next ask: "I want to record the demo video" or "Help me
swap the text wrapper for HuggingFace toxic-bert" — for which the answer
is "open Claude Code, paste Prompt 0 or Prompt 1 from
`docs/CLAUDE_CODE_PROMPTS.md`".*
