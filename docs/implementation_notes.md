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
| Audio wrapper (real tier) | Whisper (`tiny` default, `small` via `TRIGUARD_WHISPER_MODEL`) + YAMNet (TF-Hub `yamnet/1`) | Transcript via Whisper; `transcript_confidence` = mean `exp(seg.avg_logprob)` clamped; `yamnet_tags` = top-5 classes > 0.2 (60 s chunks averaged); per-component fallback to mock (`raw["whisper_fallback"]`/`["yamnet_fallback"]`; `mode` `real-audio`/`real-audio-partial`). Needs py3.12 + ffmpeg. Select via `force_mode="real"` / `TRIGUARD_AUDIO_BACKEND=real`. RAM observed: _pending_. |
| Audio wrapper (mock) | filename-derived transcript + tags | offline default; `TRIGUARD_MOCK=1` or `force_mode="mock"`. |
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

### Sprint 3 — real audio model (Whisper + YAMNet)

Whisper (`openai-whisper`, `tiny` default) + YAMNet (TF-Hub `yamnet/1`).
**Python constraint:** TensorFlow / numba have no Python 3.14 wheels (the WSL
default), so the audio stack runs in a uv-provisioned standalone **Python 3.12**
venv `~/.venv-triguard-audio` (gitignored). ffmpeg (system) is required by Whisper.

```bash
bash scripts/run_wsl_sprint3.sh   # uv -> py3.12 ~/.venv-triguard-audio, installs audio stack, fast + slow audio test
```

- `transcript_confidence` = mean `exp(segment.avg_logprob)` over Whisper
  segments, clamped to [0,1].
- `yamnet_tags`: top-5 YAMNet classes with mean score > 0.2 (audio chunked into
  60 s windows, scores averaged).
- Per-component fallback: if Whisper or TF/YAMNet is unavailable that half
  degrades to the mock and is flagged in `raw`; `mode` becomes
  `real-audio-partial`.
- Slow test `tests/test_audio_model_real.py` runs against a committed
  public-domain clip at `data/sample_inputs/audio_test.wav` (generated with
  `espeak-ng` TTS, so the transcript is approximate on whisper-tiny). Verified
  run (`~/.venv-triguard-audio`, py3.12, tf 2.21.0 CPU): transcript ≈ "the quick
  brown fox jumps over the lazy dog near the river bank", `transcript_confidence`
  0.523, `yamnet_tags` `[('Speech', 0.8602)]`, `mode` `real-audio`.

Real-data audio evaluation (T4, AudioSet subset) is a separate later sprint.

### Sprint 4 — real LLM judge (Ollama)

The judge's Ollama path (`src/triguard/models/llm_judge.py`) now runs against a
real local instruction model. The rule-based judge remains the offline default;
the Ollama path is opt-in via `TRIGUARD_JUDGE=ollama`.

| Setting | Env var | Default |
|---|---|---|
| Judge path | `TRIGUARD_JUDGE` | `rule` |
| Model tag | `TRIGUARD_OLLAMA_MODEL` (falls back to `OLLAMA_MODEL`) | `llama3:8b-instruct-q4_K_M` |
| Endpoint | `OLLAMA_HOST` | `http://localhost:11434` |
| Client timeout (s) | `OLLAMA_TIMEOUT` | `60` |

Host, model and timeout are read per call (not at import) so environment
overrides always take effect. Fallback is graceful and distinguishable: invalid
JSON after one stricter-prompt retry -> rule judge + uncertainty
`judge_output_invalid`; unreachable/timeout -> rule judge + uncertainty
`ollama_unavailable:<reason>`. No new dependency — HTTP uses stdlib `urllib`.

**Model:** `llama3:8b-instruct-q4_K_M` (Llama-3-8B-Instruct, 4-bit K-quant
q4_K_M). **Observed:** 5.3 GB resident, 100% GPU (WSL CUDA passthrough); cold
load exceeded the 60 s default timeout, so first-call latency needs
`OLLAMA_TIMEOUT` raised or a warm-up (the smoke warms the model first).

**Install (WSL, no sudo):** Ollama v0.31.1 `ollama-linux-amd64.tar.zst` unpacked
to `$HOME/ollama`, decompressed with Python 3.14's stdlib `compression.zstd`
(no system zstd needed); `ollama serve` run as a user process; model cached in
`$HOME/.ollama/models`.

**Reproduce (WSL):**

```bash
export PATH="$HOME/ollama/bin:$PATH"
ollama serve &                      # keep alive
ollama pull llama3:8b-instruct-q4_K_M
cd <repo> && source .venv-linux/bin/activate
OLLAMA_TIMEOUT=300 PYTHONPATH=src python scripts/smoke_ollama.py data/sample_inputs/sample_harmful.json
PYTHONPATH=src python -m pytest -q --run-slow tests/test_llm_judge_ollama.py
```

**Real run** (sample `sample_harmful.json`; evidence: text toxicity 0.7167
[insult, threat], image cue weapon, audio shouting 0.7):

| judge | risk_label | action | flagged | risk_score |
|---|---|---|---|---|
| rule | harmful | block | text, image, audio | — |
| llama3 | borderline | review | text, image | 0.73 |

llama3 rationale (verbatim): "The text evidence suggests a high level of toxicity
with an insult and threat detected, while the image caption and visual risk cues
indicate potential harm. However, the confidence levels are not extremely high,
leading to a borderline classification." Grounding check: grounded (cites insult,
threat, toxicity, image); no invented modalities or numbers; re-validated against
`JudgeOutput`. Honest notes: llama3 was more conservative than the rule judge and
omitted the audio modality from its flags; its risk_score 0.73 is high for a
`borderline` label (still schema-valid). Fallback verified: cold-load timeout ->
`ollama_unavailable:TimeoutError`; server stopped -> `ollama_unavailable:[Errno
111] Connection refused`; both degraded to the rule judge without crashing.
