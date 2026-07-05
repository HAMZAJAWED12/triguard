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
- Fast pytest lane is fully offline: **45 passed / 10 skipped** in the full WSL
  venv; **33 passed / 11 skipped** in the minimal offline venv (API tests skip
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
pip install fastapi uvicorn python-multipart          # (or: pip install -e ".[eval]")
PYTHONPATH=src uvicorn triguard.api.main:app --host 127.0.0.1 --port 8001
# open http://127.0.0.1:8001/ui   (health JSON at http://127.0.0.1:8001/)
# evaluation dashboard: http://127.0.0.1:8001/dashboard
```

Defaults are offline (mock/rule); set `TRIGUARD_TEXT_BACKEND=hf` etc. to opt into
real models. Binds localhost only. Demo endpoints (Phase D):

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
├── pyproject.toml
├── requirements.txt
├── docs/                           writeups (lit review, design, chapters, 