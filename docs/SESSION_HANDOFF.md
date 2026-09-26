# Session Handoff — TriGuard

Read this FIRST in a new session, plus `CLAUDE.md`, `DECISIONS.md` (D-001..D-026),
`JOURNAL.md` (Wk1..18b), `docs/implementation_notes.md`. This captures the current
state + the non-obvious environment so work resumes without re-discovery.

## Location (CHANGED — off OneDrive)
Repo now at **`C:\dev\triguard`** (WSL **`/mnt/c/dev/triguard`**). Git history intact,
branch `master`. The old OneDrive copy
(outside this repo) is stale — do not use it,
EXCEPT its `.venv` is still the Windows offline interpreter (see below).

Latest commits (newest first):
- (pending) fix(demo): demo-readiness — un-latch per-request wrapper failures, demo_up.sh, health backends, uncommitted-run badge, docs refresh
- `a8f2bb2` docs(report): S1-S4 demo/dashboard screenshots, frontmatter template, real-backend launch config
- `9e2c0e8` docs(report): draft-report skeleton, evidence tables E1-E9, figures (Phase E scaffolding)
- `33ade3d` docs: numbers audit (195 claims, 0 numeric errors) + T7 wording, D-025/026 ordering, test env isolation
- `6bfdfc3` feat(eval): T6 v2 student-reviewed set (D-026) + gitignored local_demo preset media
- `e866541` feat(demo): Phase D - presets, rule-vs-llama3 compare, streaming judge, eval dashboard (D-025)
- earlier: Phase C eval utilities, Phase B OCR, Phase A T6 harness, FastAPI demo, combined venv, real judges, T2/T3/T4.

Demo boot: `bash scripts/demo_up.sh` (WSL) — orphan cleanup, Ollama start, llama3
+ perception warm-up, real server on :8006, green/red checklist. USE_TF=0 is baked
in. CONTEXT_HANDOFF.md deleted (was stale; this file is the only handoff).

## Environments (CRITICAL)
Windows torch is blocked (WDAC). Real ML runs only in WSL.

| Env | Python | Use |
|---|---|---|
| Windows `.venv` (lives in the old OneDrive checkout, outside this repo; written `<windows-venv>` below) | — | offline defaults only (mock/sklearn/rule) + pytest + reportlab. Call by ABSOLUTE path. |
| WSL `~/.venv-tri` (py3.12, in $HOME) | 3.12 | **everything real**: torch 2.12.1+cpu, transformers, BLIP, whisper, tensorflow, sklearn, fastapi, jiwer, rapidocr-onnxruntime, psutil |
| Ollama | — | `$HOME/ollama/bin`, model `llama3:8b-instruct-q4_K_M`, endpoint `localhost:11434` |

- The clone has **no `.venv-linux`** (gitignored, path-bound); `scripts/build_venv_tri.sh`
  recreates it on demand. Install extras into `~/.venv-tri` via `~/.venv-tri/bin/python -m pip`.
- **Always `export USE_TF=0`** in `~/.venv-tri` (transformers eagerly imports TF and
  segfaults otherwise; D-016).
- **Do NOT install easyocr** — its torchvision is ABI-incompatible with torch 2.12.1+cpu
  and breaks the stack (D-023). OCR = rapidocr-onnxruntime (torch-free). Re-pin `numpy<2`
  after any OCR/torch install.

## Test commands
```powershell
# Windows offline (from any dir): 83 passed / 11 skipped (2026-09-26)
$env:PYTHONPATH="C:\dev\triguard\src"; & "<windows-venv>\Scripts\python.exe" -m pytest -q C:\dev\triguard\tests
```
```bash
# WSL real, fast lane: 95 passed / 10 skipped (2026-09-26)
wsl -e bash -lc "cd /mnt/c/dev/triguard && PYTHONPATH=src ~/.venv-tri/bin/python -m pytest -q"
# WSL with slow tests (hf/blip/audio/ocr/ollama; needs models/server)
wsl -e bash -lc "cd /mnt/c/dev/triguard && USE_TF=0 PYTHONPATH=src ~/.venv-tri/bin/python -m pytest -q --run-slow"
```
Full command reference (server run, CLI, evals, ollama): **`study/TriGuard_Commands.pdf`**
(gitignored; regen `python study/build_commands_pdf.py`). PowerShell: single-quote any
`wsl -e bash -lc '...'` containing `$`.

## What is real + done
Text (toxic-bert), image (BLIP), audio (Whisper+YAMNet), rule + real llama3 judge, one
combined `~/.venv-tri` runs all in one pass. FastAPI demo (`triguard.api.main:app`,
`/`, `/ui`, `/analyse/text`, `/analyse/multimodal`) + Phase D demo surface (D-025):
`/presets`, `/analyse/preset`, `/analyse/compare` (perception once, rule vs llama3),
`/analyse/stream` (SSE llama3 tokens + validated final), `/eval/summary` +
`/dashboard` (committed numbers, verbatim). Evals T1–T4, T6 ablation, T7
grounding, T8 perf, failure_analysis. model_versions reflects the real backend.

## Verified numbers (committed under `outputs/evaluation/`; never invent, never edit)
- T2 text: sklearn 0.542 -> toxic-bert **0.928** (macro-F1 0.6476).
- T3 image-text (Memotion, n=50): pipeline F1 0.40 / AUROC 0.566; text-only 0.3636;
  **OCR->text-track +0.37** (image-only 0.06 -> 0.43); OCR->keyword-cues 0.0 (sub-finding).
- T4 audio: Whisper WER **0.097** (LibriSpeech); YAMNet top-1 0.32 / top-5 0.66 (ESC-50).
- T6 ablation v2 (n=24, student-reviewed set, run 20260705-160858): multimodal
  0.625/0.4945 >= text-only 0.5909/0.4786 > image/audio-only 0.5/0.2222.
  `cross_modal harmful` items = 0 (no suitable media for confounders). The old
  v1 AI-starter run (n=18, 0.778/0.685) stays committed as history; report uses v2.
- T7 grounding: llama3 **1.0** (floor metric, cites >=1 token, n=18).
- T8: real p50 31 ms / p95 4.1 s / cold-start 4.1 s / peak RSS 2.87 GB; mock 0.0 ms / 34.5 MB.

## Roadmap remaining (see `~/.claude/plans/how-we-can-improve-*.md`)
- **Phase D** — demo wow: DONE (D-025, Wk18) — presets, rule-vs-llama3 compare,
  streaming llama3, `/dashboard`. Verified live (98 streamed tokens, honest
  `ollama->rule` fallback offline).
- **Phase E** — report integration. **The report prose + the T6 cross-modal confounder
  set/labels are the STUDENT's own work** (assistant supplies tables/figures + verifies
  numbers only).

## Integrity (established this session)
- T6 confounder cases + ground-truth labels = student's design; the committed manifest is
  a marked AI-DRAFTED starter (its `provenance` field). Do not present it as the
  student's evaluation.
- Disclose AI assistance per CM3070; report in a student voice.
- Assistant declines to scrub AI provenance / rewrite git history to hide AI use.

## Working rules
Plan-first then wait "approved"; STOP before commit (user commits, or authorises);
never invent numbers/citations; `py_compile` after every `.py` write; lazy-import heavy
ML; keep mock + rule-judge fallbacks + offline defaults; don't change the public Pydantic
schema; caveman reply style (skill `anthropic-skills:caveman`).

## Immediate next action
Final report (Phase E). Get the CM3070 final-report spec (required sections + word count),
build a skeleton mapped to the verified numbers above; the student writes the prose. The
assistant needs `C:\dev\triguard` connected to read files + verify numbers.

## Kickoff prompt for a new session (paste this)
> Continuing my CM3070 TriGuard final project. Connect C:\dev\triguard. Read
> docs/SESSION_HANDOFF.md first, then CLAUDE.md, DECISIONS.md, JOURNAL.md,
> docs/implementation_notes.md. Build phase is complete; we're on the final report
> (Phase E). I use Claude Code for building (plan-first, ONE sprint, STOP before commit)
> and this chat for review + report assembly. Terse/caveman style. Confirm you're up to
> speed, then I'll paste the CM3070 final-report spec.
