#!/usr/bin/env bash
# Sprint 3 (audio -> Whisper + YAMNet) via WSL/Ubuntu.
# TensorFlow / numba have no Python 3.14 wheels, so this provisions a standalone
# Python 3.12 venv with uv (no sudo). CPU-only wheels (no CUDA) keep it small.
# The venv lives in $HOME (NOT on /mnt/c OneDrive) to avoid multi-GB sync + slow
# Windows-FS I/O. ffmpeg (already apt-installed) is required by Whisper.
set -euo pipefail
cd "/mnt/c/dev/triguard"

VENV="$HOME/.venv-triguard-audio"

# Bootstrap uv via the existing .venv-linux pip (system pip is PEP-668 blocked).
[ -d .venv-linux ] || python3 -m venv .venv-linux
.venv-linux/bin/pip install -q uv
UV=.venv-linux/bin/uv

"$UV" python install 3.12
[ -d "$VENV" ] || "$UV" venv "$VENV" --python 3.12

# CPU-only torch first so Whisper does not pull the ~2.5 GB CUDA stack.
"$UV" pip install -p "$VENV" torch --index-url https://download.pytorch.org/whl/cpu
"$UV" pip install -p "$VENV" \
    pydantic pytest "numpy<2" "scikit-learn==1.5.2" \
    openai-whisper "tensorflow-cpu>=2.15,<3" "tensorflow-hub>=0.16" \
    "librosa>=0.10,<1" "soundfile>=0.12"

# Smoke: the heavy audio stack imports on py3.12.
"$VENV/bin/python" -c "import whisper, tensorflow as tf, tensorflow_hub, librosa, soundfile; print('audio stack ok; tf', tf.__version__)"

export PYTHONPATH=src
export TRIGUARD_RUN_ENV=wsl-ubuntu-py312

"$VENV/bin/python" -m pytest -q
# Real audio test SKIPS unless data/sample_inputs/audio_test.wav exists.
"$VENV/bin/python" -m pytest -q --run-slow tests/test_audio_model_real.py
echo "SPRINT3_DONE"
