# Implementation Notes — TriGuard

Records concrete implementation choices: datasets used, model names/revisions,
and exact reproduction commands. Numbers live only in
`outputs/evaluation/<timestamp>/...` — this file documents *how*, not results.

## Evaluation datasets

### T2 — text-track toxicity (`src/triguard/data/datasets.py`)

Loader: `triguard.data.datasets.load_toxicity_sample(...)`. Streams rows lazily
(stops after `sample_size`), so no full split is ever downloaded. The exact
sampled rows are persisted to `data/t2_samples/*.json` (gitignored): on the
machine that produced them, reruns are byte-identical and fully offline. A fresh
clone has no cache and re-streams from the Hub — and because the dataset
revision is not pinned, that re-stream is **not** guaranteed identical; the
committed evidence of any run is its `outputs/evaluation/<ts>/t2/results.json`
(tracked). Caches are gitignored and do not affect tracked repo size:
`data/hf_cache/` is passed to `datasets` as `cache_dir`; in streaming mode raw
shards are fetched via `huggingface_hub`'s hub cache (`~/.cache/huggingface` or
`$HF_HOME`). `datasets` is a lazy import (optional extra:
`pip install -e ".[eval]"`).

| Field | Value |
|---|---|
| **Default dataset** | `google/civil_comments` (Hugging Face Hub) |
| **Licence** | **CC0 1.0** (public domain). Exact replica of the Jigsaw "Unintended Bias in Toxicity Classification" Kaggle data; released CC0, as is the comment text. |
| **Config / split** | default config, `test` split (≈ 97k rows) |
| **Fields used** | `text` (str), `toxicity` (float 0–1) |
| **Label rule** | binary: `1` (toxic) if `toxicity >= 0.5` else `0` (non-toxic) |
| **Sample size / seed** | 500 rows, seed 42 (seeded buffered shuffle; buffer scales with sample size, capped at 10000) |
| **Decision threshold** | wrapper `toxicity_score >= 0.5` → toxic |

**Optional, permission-gated dataset:** `tweet_eval` config `hate`
(`--source tweet_eval`). The hate subset originates from **HatEval
(SemEval-2019 Task 5)** and is **permission-required** — the Hugging Face card
marks it "Need permission" and the benchmark has no single public licence. It is
**not** used by default and **not** exercised by the test suite. Only use it if
you hold the HatEval usage agreement. Labels are already integers
(`0` = non-hate, `1` = hate).

#### Reproduce (Windows PowerShell)

```powershell
# one-time: install the eval extra into the venv
.\.venv\Scripts\python.exe -m pip install "datasets>=2.18,<4"

# run T2 on the CC0 default (Civil Comments), 500 rows, seed 42
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m triguard.evaluation.run_t2 --source civil_comments --sample-size 500 --seed 42
# -> writes outputs/evaluation/<timestamp>/t2/results.json
```

The harness writes whatever it computed — accuracy, macro-F1, per-class
precision/recall/F1, confusion matrix, class balance, and up to 10 example
misclassifications — into the JSON envelope. Never transcribe a number into any
document that is not present in that file.

## Models

| Component | Name / revision | Notes |
|---|---|---|
| Text wrapper (hf tier) | `unitary/toxic-bert`, revision `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94` | Multi-label sigmoid heads (toxic, severe_toxic, obscene, threat, insult, identity_hate). `toxicity_score` = `toxic` head; `top_labels` = heads ≥ 0.5; `raw["mode"]="real-hf"`. ~440 MB weights, lazy transformers/torch, `lru_cache`d. Select via `force_mode="hf"` or `TRIGUARD_TEXT_BACKEND=hf`. RAM observed: _pending CPU run_ (Sprint-1 hf ran on WSL GPU, cuda:0). |
| Text wrapper (sklearn tier) | sklearn `TfidfVectorizer(ngram_range=(1,2))` + `LogisticRegression(C=4.0, max_iter=500)` | Trained at runtime on 30 bundled examples; offline default + sanity floor. `force_mode="real"` aliases this. No persisted weights. |
| Text wrapper (mock) | deterministic keyword heuristic | `TRIGUARD_MOCK=1` or `force_mode="mock"`. |
| Image wrapper (blip tier) | `Salesforce/blip-image-captioning-base`, revision `82a37760796d32b1411fe092ab5d4e227313294b` | Caption via BLIP; `visual_risk_cues` from keyword vocab; long edge downscaled ≤ 1024 px; `confidence` = mean greedy-token softmax prob (fallback 0.6, tagged `raw["confidence_fallback"]`); `raw["mode"]="real-blip"`. ~990 MB weights, lazy transformers/PIL, `lru_cache`d. Select via `force_mode="blip"` / `TRIGUARD_IMAGE_BACKEND=blip`. RAM observed: _pending_. |
| Image wrapper (mock) | filename-derived caption + cues | offline default; `TRIGUARD_MOCK=1` or `force_mode="mock"`. |
| Audio wrapper | mock (filename-derived cues) | Real Whisper / YAMNet are Sprint 3 (see `docs/CLAUDE_CODE_PROMPTS.md` Prompt 3). |
| LLM judge | rule-based (default) + Ollama path | Ollama falls back to the rule judge on failure. |

### Sprint 1 — real text model (toxic-bert)

`unitary/toxic-bert` is pinned to revision
`4d6c22e74ba2fdd26bc4f7238f50766b045a0d94` in `text_model.py` (`_HF_REVISION`).
Weights download to the Hugging Face cache (`~/.cache/huggingface`, gitignored,
outside the repo) on first use; never committed. Install + run the hf tier:

```powershell
.\.venv\Scripts\python.exe -m pip install "numpy<2" "transformers>=4.40,<5" "torch>=2.2,<3"

# T2 with the real hf model (writes a NEW results.json; sklearn OLD dir kept)
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m triguard.evaluation.run_t2 --source civil_comments --sample-size 500 --seed 42 --backend hf
```

T2 numbers (Civil Comments, 500 rows, seed 42; `run_env=wsl-ubuntu`,
revision `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94`):

| backend | accuracy | macro-F1 | toxic P / R / F1 | dir |
|---|---|---|---|---|
| sklearn (OLD, frozen) | 0.542 | 0.415 | 0.08 / 0.59 / 0.14 | `outputs/evaluation/20260623-074102/t2/` |
| hf toxic-bert (NEW) | 0.928 | 0.6476 | 0.41 / 0.28 / 0.33 | `outputs/evaluation/20260623-124802/t2/` |

hf wins on accuracy + macro-F1 and curbs over-flagging (toxic precision
0.08→0.41); toxic recall drops (0.59→0.28). Toxic class is small (32/500) so its
F1 is noisy. Both dirs retained.

### Sprint 2 — real image model (BLIP)

`Salesforce/blip-image-captioning-base` pinned to revision
`82a37760796d32b1411fe092ab5d4e227313294b` in `image_model.py` (`_BLIP_REVISION`).
Weights download to the Hugging Face cache (gitignored, outside the repo).
`visual_risk_cues` keyword vocab (substring match on the lowercased caption):

| cue | keywords |
|---|---|
| weapon | gun, rifle, pistol, knife, weapon |
| violence | blood, fight, punch, attack |
| hate_symbol | swastika, nazi |
| drug | syringe, needle, cocaine, drug |
| nudity_warning | nude, naked |

`confidence` = mean greedy-token softmax probability from `generate(output_scores=True)`
(clamped to [0,1]); if scores are unavailable it falls back to 0.6 and tags
`raw["confidence_fallback"]=True`. Run (WSL, reuses `.venv-linux`):

```bash
bash scripts/run_wsl_sprint2.sh   # generates data/sample_inputs/blip_test.png, runs fast + slow blip test
```

Real-data image evaluation (T3, Hateful Memes / MMHS150K) is a separate later
sprint — not run here.
