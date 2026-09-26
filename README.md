# TriGuard — Tier-A Prototype

**CM3070 Computer Science Final Project — University of London / Goldsmiths.**
**Template:** CM3020 Artificial Intelligence — Project Idea 1: *Orchestrating AI Models to Achieve a Goal*.

TriGuard is a prototype multimodal, explainable, locally deployable content-moderation pipeline. It combines several pre-trained AI models (text, image, audio) with a local LLM judge that produces a structured risk decision and a human-readable rationale.

## Status

Tier-A feature prototype — used in Chapter 4 of the Preliminary Report.

- **Text wrapper**: sklearn TF-IDF + logistic regression (offline default) with an
  opt-in real **toxic-bert** tier (`TRIGUARD_TEXT_BACKEND=hf`).
- **Image wrapper**: deterministic mock (offline default) with an opt-in real
  **BLIP** captioning tier (`TRIGUARD_IMAGE_BACKEND=blip`) and opt-in OCR
  (`TRIGUARD_IMAGE_OCR=1`, RapidOCR).
- **Audio wrapper**: deterministic mock (offline default) with an opt-in real
  **Whisper + YAMNet** tier (`TRIGUARD_AUDIO_BACKEND=real`).
- **Rule-based judge** (default) + real **Ollama/llama3 path** (opt-in), with a
  graceful, honestly-labelled fallback; the demo can stream llama3 tokens live.
- **Pydantic schemas** enforce a 100 % schema-validity rate by construction.
- Fast pytest lane is fully offline: **95 passed / 10 skipped** in the full WSL
  venv; **83 passed / 11 skipped** in the minimal offline venv (API tests skip
  where `fastapi`/`httpx`/`python-multipart` are absent). `slow` tests need
  `--run-slow`.
- Evaluation tracks **T1–T8** on public data (Civil Comments, Memotion,
  LibriSpeech, ESC-50) — see `docs/evaluation_protocol.md` and
  `outputs/evaluation/`.

## Quick start

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m pytest -q                 # fast lane, no network
PYTHONPATH=src python -m triguard.evaluation.run_eval
PYTHONPATH=src python -m triguard.cli run data/sample_inputs/sample_harmful.json
```

### FastAPI demo (browser UI)

```bash
# offline demo (mock backends, rule judge) — any venv with the [eval] extras
pip install fastapi uvicorn python-multipart          # (or: pip install -e ".[eval]")
TRIGUARD_MOCK=1 PYTHONPATH=src uvicorn triguard.api.main:app --host 127.0.0.1 --port 8001
# open http://127.0.0.1:8001/ui   (health JSON at /,  dashboard at /dashboard)
```

```bash
# REAL demo (WSL ~/.venv-tri). USE_TF=0 is REQUIRED with real text — without it
# transformers imports TensorFlow and the first toxic-bert call segfaults the
# server (D-016). Easiest: the one-command ritual below.
bash scripts/demo_up.sh
# ...or by hand:
USE_TF=0 TRIGUARD_TEXT_BACKEND=hf TRIGUARD_IMAGE_BACKEND=blip \
TRIGUARD_AUDIO_BACKEND=real TRIGUARD_IMAGE_OCR=1 OLLAMA_TIMEOUT=300 \
PYTHONPATH=src ~/.venv-tri/bin/uvicorn triguard.api.main:app --host 127.0.0.1 --port 8006
```

`scripts/demo_up.sh` = pre-demo ritual: clears orphan servers, starts Ollama if
down, warms llama3 (long keep_alive) and the perception models, then prints a
green/red checklist. The `/` health endpoint and the banner on `/ui` show which
backends are active — check them before presenting. Binds localhost only. Demo
endpoints (Phase D):

| endpoint | purpose |
|---|---|
| `GET /presets`, `POST /analyse/preset` | one-click committed sample presets |
| `POST /analyse/compare` | rule vs llama3 side by side (perception runs once) |
| `POST /analyse/stream` | SSE: instant rule verdict, then live llama3 tokens, then the final schema-validated verdict |
| `GET /dashboard`, `GET /eval/summary` | charts of the committed T2–T8 results.json numbers, read verbatim |

Without a running Ollama server the compare/stream llama3 side falls back to the
rule judge and is labelled `ollama->rule` — never presented as LLM output.

### Text-track evaluation on a real dataset (T2)

```bash
pip install -e ".[eval]"                           # adds `datasets` (Hugging Face)
PYTHONPATH=src python -m triguard.evaluation.run_t2 --source civil_comments --sample-size 500 --seed 42
# -> outputs/evaluation/<timestamp>/t2/results.json   (macro-F1, per-class P/R/F1, confusion matrix)
PYTHONPATH=src python -m pytest -q --run-slow      # include the slow dataset test
```

The sampled rows are cached under `data/t2_samples/` and dataset shards under
the Hugging Face cache (both gitignored); reruns on the same machine are offline
and identical, while a fresh clone re-streams from the Hub. The committed
evidence of a run is its `outputs/evaluation/<ts>/t2/results.json`. See
`docs/implementation_notes.md` for datasets, licences, and reproduction.

## Layout

```
triguard/
├── README.md                       this file
├── pyproject.toml                  package metadata + [eval]/[audio] extras
├── requirements.txt                pinned fast-lane deps
├── requirements-full.txt           exact pins of the WSL combined venv
├── CLAUDE.md / DECISIONS.md / JOURNAL.md   working rules, decision log, journal
├── docs/                           writeups, report scaffolding, figures
├── data/sample_inputs/             committed benign media + presets + T6 manifest
├── data/local_demo/                gitignored local demo media (see its README)
├── src/triguard/
│   ├── orchestrator/               pipeline + frozen pydantic schemas
│   ├── models/                     text/image/audio wrappers + LLM judge
│   ├── data/                       dataset loaders (T2/T3/T4)
│   ├── evaluation/                 run_eval + T2-T8 harnesses + failure analysis
│   └── api/                        FastAPI demo (/ui, /dashboard) + static pages
├── scripts/                        venv builders, smokes, demo_up.sh
├── tests/                          fast offline lane + slow-marked real paths
└── outputs/evaluation/<run>/       committed results.json evidence per track
```
