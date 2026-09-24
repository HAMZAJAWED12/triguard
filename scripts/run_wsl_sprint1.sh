#!/usr/bin/env bash
# Sprint 1 (text -> unitary/toxic-bert) via WSL/Ubuntu.
# Windows blocks torch DLLs via Application Control; Linux binaries bypass it.
# Does NOT touch the Windows .venv or run_eval (Tier-A stays 1.000).
set -euo pipefail
cd "$(dirname "$0")/.."   # repo root, whatever the clone path

# apt deps (python3-venv, python3-pip, ffmpeg) installed manually beforehand.
[ -d .venv-linux ] || python3 -m venv .venv-linux
. .venv-linux/bin/activate

python -m pip install --upgrade pip
pip install "numpy<2" "scikit-learn==1.5.2" pydantic pytest \
    "torch>=2.2,<3" "transformers>=4.40,<5" datasets

python -c "import torch; print('torch', torch.__version__)"   # must NOT error

export PYTHONPATH=src
export TRIGUARD_RUN_ENV=wsl-ubuntu

python -m pytest -q
python -m pytest -q --run-slow tests/test_text_model_hf.py
python -m triguard.evaluation.run_t2 --backend hf --source civil_comments --sample-size 500 --seed 42
