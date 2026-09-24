#!/usr/bin/env bash
# Sprint 2 (image -> Salesforce/blip-image-captioning-base) via WSL/Ubuntu.
# Reuses the Sprint-1 .venv-linux (torch already installed). Windows blocks
# torch DLLs via Application Control; Linux binaries bypass it.
set -euo pipefail
cd "$(dirname "$0")/.."   # repo root, whatever the clone path

. .venv-linux/bin/activate
pip install "pillow>=10,<12"

# Generate the committed synthetic public-domain test image if missing
# (PIL-drawn benign scene: sky, sun, grass, small house).
python - <<'PY'
from pathlib import Path
from PIL import Image, ImageDraw
p = Path("data/sample_inputs/blip_test.png")
if p.exists():
    print("exists", p)
else:
    img = Image.new("RGB", (256, 160), (135, 206, 235))   # sky
    d = ImageDraw.Draw(img)
    d.rectangle([0, 120, 256, 160], fill=(34, 139, 34))    # grass
    d.ellipse([28, 18, 78, 68], fill=(255, 221, 0))        # sun
    d.rectangle([150, 80, 200, 120], fill=(139, 69, 19))   # house body
    d.polygon([(150, 80), (175, 55), (200, 80)], fill=(178, 34, 34))  # roof
    img.save(p)
    print("generated", p)
PY

export PYTHONPATH=src
export TRIGUARD_RUN_ENV=wsl-ubuntu

python -m pytest -q
python -m pytest -q --run-slow tests/test_image_model_blip.py
