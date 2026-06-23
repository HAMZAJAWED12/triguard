#!/usr/bin/env bash
# Sprint 3 (audio -> Whisper + YAMNet) via WSL/Ubuntu.
# TensorFlow / numba have no Python 3.14 wheels, so this provisions a standalone
# Python 3.12 venv (.venv-audio) with uv (no sudo) and runs the audio stack there.
# ffmpeg (already apt-installed) is required by Whisper.
set -euo pipefail
cd "/mnt/c/Users/jawed/OneDrive/ICAEWSOFTWARE/FYP UOL/triguard"

# uv: standalone Python + fast installer, no root needed. Bootstrap it via the
# existing .venv-linux pip (system pip is PEP-668 "externally-managed" blocked).
[ -d .venv-linux ] || python3 -m venv .venv-linux
.venv-linux/bin/pip install -q uv
UV=.venv-linux/bin/uv

"$UV" python install 3.12
[ -d .venv-audio ] || "$UV" venv .venv-audio --python 3.12

"$UV" pip install -p .venv-audio \
    pydantic pytest "numpy<2" "scikit-learn==1.5.2" \
    openai-whisper "tensorflow>=2.15,<3" "tensorflow-hub>=0.16" \
    "librosa>=0.10,<1" "soundfile>=0.12"

# Smoke: the heavy audio stack imports on py3.12.
.venv-audio/bin/python -c "import whisper, tensorflow as tf, tensorflow_hub, librosa, soundfile; print('audio stack ok; tf', tf.__version__)"

export PYTHONPATH=src
export TRIGUARD_RUN_ENV=wsl-ubuntu-py312

.venv-audio/bin/python -m pytest -q
# Real audio test SKIPS unless data/sample_inputs/audio_test.wav exists.
.venv-audio/bin/python -m pytest -q --run-slow tests/test_audio_model_real.py
