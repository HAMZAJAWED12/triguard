# Session Handoff — TriGuard

Read this first in a new session, plus `CLAUDE.md`, `DECISIONS.md` (D-001..D-014),
`JOURNAL.md` (Wk1–9), `docs/implementation_notes.md`. This file captures the
non-obvious environment + state so work continues without re-discovery.

## Where we are
Tier-A prototype + **Tier-B done and paused**: all three perception models now
have a real tier (text, image, audio), mock/offline defaults kept. Git history:

- `52ed8d2` chore(lint): silence WSL-only ML imports + loose ML-stub types; tidy yamnet
- `a2dba37` docs: Tier-A video recording cheat-sheet (PDF)
- `0899507` chore(audio): commit espeak test clip + verify real audio; fix venv-path docs
- `f472cdd` feat(audio): real Whisper + YAMNet tier (Sprint 3)
- `1373e06` fix(repo): track src/triguard/models + feat(image): real BLIP tier (Sprint 2)
- `86f29b7` Initial commit: Tier-A + real text model (Sprint 1)

Branch `master`, tree clean. Author `Hamza <jawedh011@gmail.com>`.

## Machine + environments (CRITICAL — three venvs, none has all three)
Windows torch is blocked by Application Control (WDAC): `WinError 4551` on
`c10.dll`. So real ML models run only under WSL/Ubuntu.

| Env | Python | Has | Runs real | Tests |
|---|---|---|---|---|
| Windows `.venv` (in OneDrive) | 3.14 | pydantic, sklearn | nothing (mock + sklearn text only) | `$env:PYTHONPATH="src"; python -m pytest -q` → 23 passed, 5 skipped |
| WSL `.venv-linux` (in repo) | 3.14 | torch, transformers, datasets, pillow | **text (toxic-bert), image (BLIP)** | see below |
| WSL `~/.venv-triguard-audio` (home, off OneDrive) | 3.12 (uv) | whisper, tensorflow, tf-hub, librosa, soundfile | **audio (Whisper+YAMNet)** | see below |

Default everywhere = mock/offline (so the fast suite never downloads). Real tiers
are opt-in: `force_mode="hf"|"blip"|"real"` or env
`TRIGUARD_TEXT_BACKEND=hf` / `TRIGUARD_IMAGE_BACKEND=blip` / `TRIGUARD_AUDIO_BACKEND=real`.
`TRIGUARD_MOCK=1` forces mock.

## Run all tests (from the Windows PowerShell prompt)
```powershell
# 1) Windows offline
$env:PYTHONPATH="src"; python -m pytest -q
# 2) WSL text+image real (27 passed; audio deselected)
wsl -e bash -lc "cd '/mnt/c/Users/jawed/OneDrive/ICAEWSOFTWARE/FYP UOL/triguard' && source .venv-linux/bin/activate && PYTHONPATH=src python -m pytest -q --run-slow --deselect tests/test_audio_model_real.py"
# 3) WSL audio real (1 passed)
wsl -e bash -lc "cd '/mnt/c/Users/jawed/OneDrive/ICAEWSOFTWARE/FYP UOL/triguard' && PYTHONPATH=src ~/.venv-triguard-audio/bin/python -m pytest -q --run-slow tests/test_audio_model_real.py"
```
Never run bare `pytest --run-slow` in one env — slow tests for libs that env
lacks fall back to mock and fail their assertions. Setup-from-scratch scripts:
`scripts/run_wsl_sprint1.sh` / `2` / `3` (sprint3 needs `sudo apt install -y espeak-ng`
once, to regenerate `data/sample_inputs/audio_test.wav`).

## Verified numbers (only what runs wrote — never invent)
- T2 text, Civil Comments 500 rows seed 42: sklearn 0.542 / macro-F1 0.415 (dir `074102`);
  toxic-bert hf **0.928 / 0.6476** (dir `124802`). `run_t2 --backend hf`.
- Audio real (espeak clip): transcript approximate, conf 0.523, yamnet `[('Speech',0.86)]`, mode `real-audio`.
- `run_eval` (14-item Tier-A): accuracy 1.000.
- Fast suite: 23 passed, 5 skipped (offline).

## Pinned models
toxic-bert `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94`; BLIP base
`82a37760796d32b1411fe092ab5d4e227313294b`; Whisper `tiny`; YAMNet TF-Hub `yamnet/1`.

## Working rules (from CLAUDE.md)
Plan-first then wait for "approved"; STOP before commit (user commits/approves);
never invent metrics/citations; OneDrive truncates files → `py_compile` after every
`.py` write; lazy-import heavy ML; keep mock + rule-judge fallbacks; don't change
the public Pydantic schemas; one modality per sprint.

## Next options (pick one to resume)
- **Wk6 Preliminary Report** — nearest graded milestone (10%).
- Wk11 real Ollama judge (path implemented, falls back to rule; not yet exercised).
- Combined py3.12 venv (transformers+pillow+whisper+tf) for full tri-modal-real in one process.
- T3 (image, Hateful Memes/MMHS150K) + T4 (audio, AudioSet) real-data eval.
- FastAPI demo (Prompt 5).
