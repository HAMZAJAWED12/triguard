# TriGuard — Tier-A Prototype

**CM3070 Computer Science Final Project — University of London / Goldsmiths.**
**Template:** CM3020 Artificial Intelligence — Project Idea 1: *Orchestrating AI Models to Achieve a Goal*.

TriGuard is a prototype multimodal, explainable, locally deployable content-moderation pipeline. It combines several pre-trained AI models (text, image, audio) with a local LLM judge that produces a structured risk decision and a human-readable rationale.

## Status

Tier-A feature prototype — used in Chapter 4 of the Preliminary Report.

- **Real text wrapper**: TF-IDF + logistic regression (`sklearn`).
- **Mock image / audio wrappers**: deterministic evidence derived from file names.
- **Rule-based judge** (default) + **Ollama path** (production), with graceful fallback.
- **Pydantic schemas** enforce a 100 % schema-validity rate by construction.
- **23 pytest cases** passing (fast lane); **+1 `slow` network test, skipped by default**.
- Evaluation sets: 14-item hand-built tri-modal set, plus **T2** on the public
  **Civil Comments (CC0)** dataset for the text track.

## Quick start

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m pytest -q                 # fast lane, no network
PYTHONPATH=src python -m triguard.evaluation.run_eval
PYTHONPATH=src python -m triguard.cli run data/sample_inputs/sample_harmful.json
```

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