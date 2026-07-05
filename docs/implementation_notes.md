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

### Sprint 5 — combined tri-modal venv (`~/.venv-tri`)

Until now the real backends lived in separate venvs (py3.14 text+image; py3.12
audio) — no single process ran all of them. Sprint 5 builds ONE Python 3.12 CPU
environment that runs text + image + audio + the Ollama judge in a single
orchestrator pass, purely as integration infrastructure. No code, schema or
wrapper changes.

**Build:** `scripts/build_venv_tri.sh` (uv-provisioned py3.12 `~/.venv-tri` in
`$HOME`, off OneDrive; CPU torch installed first so nothing pulls the CUDA stack).
Model weights come from the shared HF / Whisper / TF-Hub caches populated in
Sprints 1-3, so the build installs wheels only. Windows `.venv` and its offline
defaults are untouched. Exact pins in `requirements-full.txt` (Python 3.12.13).

Import proof (one process): numpy 1.26.4, torch 2.12.1+cpu, transformers 4.57.6,
pillow 11.3.0, openai-whisper 20250625, tensorflow 2.21.0, tensorflow-hub 0.16.1,
scikit-learn 1.5.2, pydantic 2.13.4.

**numpy/protobuf + the torch/TF segfault.** `numpy<2` (resolved 1.26.4) keeps
sklearn + torch happy; TensorFlow 2.21 accepts it. protobuf resolved to 7.35.1
(TF-driven) with no conflict. The real trap was a **SIGSEGV**: with both torch and
TensorFlow installed, `transformers` eagerly imports TF when a pipeline runs, and
the torch+TF interaction crashes the process (verified: the crash is at the
toxic-bert step, before our audio code loads TF; isolating it, plain torch+TF ops
coexist fine, but transformers' TF path does not). Fix is **environment-only, no
code change**: `export USE_TF=0` forces transformers to stay torch-only. Our audio
wrapper imports TensorFlow directly for YAMNet and is unaffected. (`KMP_DUPLICATE_LIB_OK`,
`OMP_NUM_THREADS`, `MKL_THREADING_LAYER` did **not** help — only `USE_TF=0` did.)

**One-pass command (all real backends + Ollama judge):**

```bash
export PATH="$HOME/ollama/bin:$PATH"; ollama serve &   # keep alive
cd <repo>
USE_TF=0 TRIGUARD_TEXT_BACKEND=hf TRIGUARD_IMAGE_BACKEND=blip \
TRIGUARD_AUDIO_BACKEND=real OLLAMA_TIMEOUT=300 PYTHONPATH=src \
  ~/.venv-tri/bin/python -m triguard.cli --judge ollama run \
    data/sample_inputs/sample_multimodal_real.json
```

Note: the judge is selected with `--judge ollama` (the CLI passes `rule`
explicitly, so `TRIGUARD_JUDGE` env alone would not switch it).

**All-real integration run** — this is an integration demonstration on **benign
synthetic media plus a real toxic-text signal**, NOT harmful-content detection.
Input `data/sample_inputs/sample_multimodal_real.json` = a real toxic sentence +
the committed synthetic `blip_test.png` + the committed espeak `audio_test.wav`
(no harmful media is committed). Captured to `outputs/demo_full_real.json`:

| modality | mode | real output |
|---|---|---|
| text | `real-hf` | toxicity 0.9751; labels insult, threat, toxic (`unitary/toxic-bert`) |
| image | `real-blip` | caption "a house in the middle of a field"; no risk cues |
| audio | `real-audio` | Whisper-tiny "The quick brown fox jump so that they do not near the river bank."; YAMNet `[(Speech, 0.8602)]` |
| judge | `ollama` (llama3) | risk_score 0.98, `harmful`, action `block`, flagged `[text]` |

llama3 rationale (verbatim): "The text evidence is flagged as 'toxic' with a
confidence of 0.95 and contains labels such as 'insult', 'threat', which indicates
a high risk of harm. Although the image and audio evidence do not indicate any
harmful content, the overall toxicity score suggests that this content should be
flagged." The judge correctly attributed the risk to the text only and read the
image/audio as benign — an honest, grounded verdict. The result is a schema-valid
`TriGuardResult` (constructed through pydantic; `JudgeOutput` fields validated).

**RAM/latency:** peak resident 2.98 GB (`/usr/bin/time -v`, all four models in one
Python process) + llama3 5.3 GB VRAM (100% GPU, `ollama ps`); end-to-end
`latency_ms` 49421 on a cold first pass.

**Graceful-fallback evidence** (`outputs/demo_harmful_fallback.json`): the same
real-backend command on `sample_harmful.json` — whose `image`/`audio` point at
placeholder paths that do not exist — keeps text `real-hf` but degrades image and
audio to `mode: "mock"` (missing files), and llama3 returns `borderline`/`review`.
This shows the per-component fallback working end-to-end in the combined process.

**Caveat (RESOLVED in D-019):** `TriGuardResult.model_versions` used to be
hardcoded (`sklearn-tfidf-lr-v1` / `mock-v1` even on an all-real run). It now
derives from each evidence's `raw["mode"]`/`model_name`/`model_revision`, so it
reads e.g. `real-hf:unitary/toxic-bert@4d6c22e74ba2`,
`real-blip:Salesforce/blip-image-captioning-base@82a37760796d`, `real-audio`,
`ollama` (or `ollama->rule` on fallback). See D-019 and the orchestrator test
`test_model_versions_agree_with_raw_mode`. The judge label is derived from the
EFFECTIVE judge (`judge_mode or TRIGUARD_JUDGE`), so an env-driven ollama run
(e.g. from the API, which passes `judge_mode=None`) is labelled `ollama`, not
`rule` (D-021).

**Fast suite in `~/.venv-tri`:** `PYTHONPATH=src ~/.venv-tri/bin/python -m pytest
-q` -> 23 passed, 6 skipped (offline defaults intact; `TRIGUARD_MOCK=1` still works).

### Evaluation track T4 — real audio wrapper (Whisper WER + YAMNet events)

Measures the real audio wrapper (`force_mode="real"`) on public, ungated data.
The protocol named an AudioSet subset, but AudioSet ships only YouTube ids (no
hosted audio); LibriSpeech test-clean (WER) and ESC-50 (event tagging) are used as
public proxies — documented as a limitation, not hidden.

| sub-metric | dataset | licence | metric |
|---|---|---|---|
| Whisper WER | LibriSpeech test-clean (`openslr/librispeech_asr`, clean/test) | CC BY 4.0 | jiwer corpus WER (normalised) |
| YAMNet events | ESC-50 (`ashraq/esc50`, Piczak 2015) | CC BY-NC 3.0 (academic, non-commercial) | top-1 + top-5 hit rate |

Loader `src/triguard/data/audio_datasets.py` streams (seed + cap), writes each
clip as a 16 kHz wav + `manifest.json` under gitignored `data/t4_samples/`
(mirrors the T2 loader). WER normalisation: lowercase, remove punctuation, collapse
spaces (LibriSpeech references are UPPERCASE/unpunctuated; Whisper adds
case+punct). YAMNet scoring uses an APPROXIMATE, hand-built ESC-50 -> AudioSet
display-name map (`ESC50_TO_YAMNET`, echoed verbatim into results.json); only
mapped categories are sampled, so top-1 is a strict lower bound and top-5 is the
fair headline. `jiwer` is pinned in the `[eval]` extra.

**Reproduce (WSL, `~/.venv-tri`, `USE_TF=0`):**

```bash
# once: WER dep into the venv
.venv-linux/bin/uv pip install -p ~/.venv-tri "jiwer>=3.0,<4"
USE_TF=0 PYTHONPATH=src ~/.venv-tri/bin/python -m triguard.evaluation.run_t4 \
  --sample-size 50 --seed 42
# -> outputs/evaluation/<ts>/t4/results.json
```

**Result** (run `20260704-153729`, py3.12 `~/.venv-tri`, seed 42, n=50 each, both
`wrapper_modes` = `real-audio`; Whisper `tiny` + YAMNet `yamnet/1`):

| sub-metric | n | result |
|---|---|---|
| Whisper WER (LibriSpeech test-clean) | 50 | corpus 0.0971, mean/clip 0.1314 |
| YAMNet events (ESC-50, 29 mapped categories) | 50 | top-1 0.32, top-5 0.66 |

Honest reading: whisper-tiny on clean read speech ~9.7% WER — a best case, not
noisy/adversarial moderation audio. YAMNet top-5 0.66 under an approximate map; the
top-1/top-5 gap largely reflects map coarseness + AudioSet's finer ontology, not
only model error. Fast suite: 23 passed, 7 skipped (offline defaults intact).

### Evaluation track T3 — image-text moderation (flag-vs-label)

Measures the image track on public labelled memes. Hateful Memes is gated;
MMHS150K's mirror keeps images in a 6.5 GB zip (unstreamable, licence unclear).
Used `Ahren09/MMSoc_Memotion` — Memotion (SemEval-2020 Task 8), ungated, images
embedded as a HF `Image` feature (streams per-row), with `offensive` label +
dataset OCR text.

| item | value |
|---|---|
| dataset | `Ahren09/MMSoc_Memotion` (Memotion, SemEval-2020) |
| licence | research use; meme images third-party copyright -> streamed, never committed |
| label | binary: `not_offensive` -> 0, else -> 1 |
| decision rule | predicted-positive = `risk_label in {borderline, harmful}` |
| backends | text `real-hf` (toxic-bert on OCR text) + image `real-blip` + rule judge |

Loader `src/triguard/data/image_datasets.py` streams (seed + cap), persists images
to gitignored `data/t3_samples/img/` + a manifest; media is never committed. BLIP
does not OCR meme text — the text signal comes from the dataset's OCR field, so T3
is a flag-vs-label decision measure, NOT a trained-classifier F1.

Reproduce (WSL, `~/.venv-tri`, `USE_TF=0`):

```bash
TRIGUARD_TEXT_BACKEND=hf TRIGUARD_IMAGE_BACKEND=blip USE_TF=0 PYTHONPATH=src \
  ~/.venv-tri/bin/python -m triguard.evaluation.run_t3 --sample-size 50 --seed 42
```

Result (run `20260704-172017`, py3.12, seed 42, n=50; real-hf + real-blip; class
balance 18 not_offensive / 32 offensive):

| metric | pipeline (image+text) | text-only baseline |
|---|---|---|
| precision | 0.6923 | 0.6667 |
| recall | 0.2812 | 0.25 |
| F1 | 0.40 | 0.3636 |
| accuracy | 0.46 | 0.44 |
| AUROC | 0.566 | — |

Honest reading: the pipeline barely beats text-only (F1 0.40 vs 0.36) — the image
track adds ~0.04 F1; BLIP captions are often degenerate on memes and fire few risk
cues. Low recall (0.28) + near-chance AUROC (0.566): most memes are offensive via
wording/context that toxic-bert flags only when overtly toxic. Modest by design,
documented. Fast suite: 23 passed, 8 skipped. (Note: in the combined venv a
`pytest --run-slow` process can SIGSEGV at interpreter teardown — a torch atexit
artifact; the test assertions pass first, and the default fast lane is unaffected.)

### FastAPI demo surface (Prompt 5)

A thin HTTP layer (`src/triguard/api/main.py`) over the orchestrator — no wrapper,
orchestrator or schema change. Endpoints:

| method + path | purpose |
|---|---|
| `GET /` | health `{status:"ok", version}` |
| `GET /ui` | single-page demo UI (`static/index.html`) |
| `POST /analyse/text` | `{text}` -> TriGuardResult JSON |
| `POST /analyse/multimodal` | multipart text + image/audio uploads -> TriGuardResult JSON |

Uploads are written to temp files, passed to the pipeline, and removed in a
`finally`. `judge_mode=None` is passed through so `TRIGUARD_JUDGE` (default rule)
and `TRIGUARD_*_BACKEND` (default mock/sklearn) are honoured — the API never forces
real models. Binds `127.0.0.1` only. The UI page is self-contained (inline CSS/JS,
no CDN, WCAG-AA contrast, >=16px body, system fonts).

```bash
pip install fastapi uvicorn python-multipart          # or pip install -e ".[eval]"
PYTHONPATH=src uvicorn triguard.api.main:app --host 127.0.0.1 --port 8001
# http://127.0.0.1:8001/ui   (health at http://127.0.0.1:8001/)
```

Tests (`tests/test_api.py`) use `pytest.importorskip("fastapi"/"httpx")` +
`TRIGUARD_MOCK=1` — fully offline where the deps exist, clean skip where they
don't. Fast suite: 27 passed / 8 skipped in `~/.venv-tri`; 24 passed / 9 skipped in
the Windows `.venv` (the api module importorskip-skips as one entry). Boot smoke
(uvicorn 127.0.0.1:8001, `TRIGUARD_MOCK=1`): `GET /` ->
`{"status":"ok","version":"0.1.0-tier-a"}`, `POST /analyse/text` -> schema-valid
TriGuardResult, `GET /ui` -> HTML.

### Opt-in OCR for the image track (Phase B)

`TRIGUARD_IMAGE_OCR=1` turns on OCR in the blip tier of `image_model.py`: RapidOCR
(`rapidocr-onnxruntime`, ONNX runtime — **torch-free**, chosen because easyocr's
torchvision is ABI-incompatible with the pinned `torch 2.12.1+cpu`
[`operator torchvision::nms does not exist`] and its install bumps numpy to 2.x) reads
overlaid text into `ImageEvidence.raw["ocr_text"]` (no schema change) and folds it
into `visual_risk_cues`. Off by default; the orchestrator contract is unchanged.

`run_t3 --ocr` runs the **image-track-alone** ablation (image-only caption vs
image-only caption+OCR, dataset `text` dropped). The full-pipeline +/-OCR delta is
intentionally not the headline: Memotion's `text` field already supplies the overlay
text, so it is ~0 and misleading.

Result (real hf+blip, rule judge, n=50; OCR read text on 50/50 memes). Three
image-track-alone conditions vs BLIP-caption-only (F1 0.0606):

| route | F1 | delta |
|---|---|---|
| BLIP caption only | 0.0606 | — |
| +OCR -> keyword cues | 0.0606 | 0.0 (sub-finding) |
| +OCR -> toxic-bert text track | **0.4348** | **+0.3742** |

OCR's value is real and large when the extracted text is routed to a real classifier
(+0.37 F1), recovering essentially the same value as the dataset-text pipeline (0.40)
and text-only (0.3636) — comparable, within small-sample (n=50) noise.
Folding OCR into the narrow keyword cue vocab adds ~0 — that vocab, not OCR, is the
bottleneck. The full-pipeline +/-OCR delta is ~0 only because Memotion already supplies
the overlay text in its `text` field.

Install note: `rapidocr-onnxruntime` (pinned in `[eval]`); re-pin `numpy<2` after
(some OCR deps pull numpy 2.x). Do NOT use easyocr in this venv — its torchvision
breaks the torch stack.
