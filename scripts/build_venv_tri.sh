#!/usr/bin/env bash
# Sprint 5 — ONE py3.12 CPU venv that runs text + image + audio + the Ollama judge
# in a single process. Built in $HOME (NOT /mnt/c OneDrive: avoids multi-GB sync +
# slow Windows-FS I/O). Repo code stays on /mnt/c. Reuses uv bootstrapped from
# .venv-linux. Model weights come from the shared HF / Whisper / TF-Hub caches
# populated in Sprints 1-3, so this installs wheels only, not weights.
#
# Windows .venv and its offline defaults are untouched. CPU wheels only (no CUDA).
set -euo pipefail
cd "$(dirname "$0")/.."   # repo root, whatever the clone path

VENV="$HOME/.venv-tri"

# uv (system pip is PEP-668 blocked); bootstrap from the existing .venv-linux.
[ -d .venv-linux ] || python3 -m venv .venv-linux
.venv-linux/bin/pip install -q uv
UV=.venv-linux/bin/uv

"$UV" python install 3.12
[ -d "$VENV" ] || "$UV" venv "$VENV" --python 3.12

# CPU torch FIRST so nothing pulls the ~2.5 GB CUDA stack.
"$UV" pip install -p "$VENV" torch --index-url https://download.pytorch.org/whl/cpu

# Rest of the stack, one resolve. numpy<2 guards sklearn + torch; TensorFlow
# constrains protobuf (let the resolver pick within TF's range).
"$UV" pip install -p "$VENV" \
    "numpy<2" "scikit-learn==1.5.2" pydantic "pytest>=7,<10" "datasets>=2.18,<4" \
    "transformers>=4.40,<5" "pillow>=10,<12" openai-whisper \
    "tensorflow-cpu>=2.15,<3" "tensorflow-hub>=0.16" "librosa>=0.10,<1" "soundfile>=0.12"

# Optional per-track extras: T2 WER (jiwer), FastAPI demo, opt-in OCR.
# RapidOCR is ONNX-based / torch-free (easyocr's torchvision is ABI-incompatible
# with torch 2.12.1+cpu here). Re-pin numpy<2 last since some extras pull numpy 2.x.
"$UV" pip install -p "$VENV" \
    "jiwer>=3.0,<4" "fastapi>=0.110,<1" "uvicorn>=0.27,<1" \
    "python-multipart>=0.0.9,<1" "httpx>=0.27,<1" "rapidocr-onnxruntime>=1.3,<2"
"$UV" pip install -p "$VENV" "numpy<2"

echo "### IMPORT PROOF (one process)"
"$VENV/bin/python" - <<'PY'
import torch, transformers, PIL, whisper, tensorflow as tf, tensorflow_hub, sklearn, pydantic, numpy
print("numpy       ", numpy.__version__)
print("torch       ", torch.__version__)
print("transformers", transformers.__version__)
print("pillow      ", PIL.__version__)
print("whisper     ", getattr(whisper, "__version__", "n/a"))
print("tensorflow  ", tf.__version__)
print("tf_hub      ", tensorflow_hub.__version__)
print("sklearn     ", sklearn.__version__)
print("pydantic    ", pydantic.__version__)
PY

echo "### FAST SUITE (offline defaults intact)"
PYTHONPATH=src "$VENV/bin/python" -m pytest -q
echo "BUILD_VENV_TRI_DONE"
