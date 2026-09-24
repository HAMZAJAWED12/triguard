"""Benign media toolkit for the confounder set.

Two modes, both writing into data/sample_inputs/confounders/:

  TTS speech clip (espeak-ng, same tool that produced audio_test.wav; 22.05 kHz
  mono wav — the audio wrapper resamples to its own 16 kHz):
      python scripts/make_confounder_media.py --tts "the words to speak" --out cf1_words.wav

  Import an own photo (resize to <=1024 long edge, convert to PNG, strip
  EXIF/metadata so no location or device info is committed):
      python scripts/make_confounder_media.py --import photo.jpg --out cf2_object.png

  BLIP pre-flight (real caption of a candidate image — keep the pairing only
  if the harm-carrying object survives the one-line caption; WSL only):
      USE_TF=0 PYTHONPATH=src ~/.venv-tri/bin/python \
        scripts/make_confounder_media.py --caption cf2_object.png

Run inside WSL for --tts (espeak-ng) and --caption (~/.venv-tri has
transformers/torch; USE_TF=0 mandatory). --import needs Pillow (present in
both venvs). The tool only creates files and reads captions; whether an image
or phrase belongs in the evaluation set is the author's design decision — see
data/sample_inputs/triguard_eval_v1/README_confounders.md.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_OUT_DIR = _REPO / "data" / "sample_inputs" / "confounders"


def _tts(text: str, out: Path) -> int:
    if shutil.which("espeak-ng") is None:
        print("error: espeak-ng not found (run inside WSL: sudo-free install "
              "or `apt`); audio_test.wav was made the same way", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    # espeak-ng writes 22.05 kHz mono; the audio wrapper resamples to 16 kHz.
    cmd = ["espeak-ng", "-v", "en", "-s", "150", "-w", str(out), text]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"error: espeak-ng failed: {proc.stderr.strip()}", file=sys.stderr)
        return 1
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


def _import_photo(src: Path, out: Path) -> int:
    try:
        from PIL import Image
    except ImportError:
        print("error: Pillow not installed in this interpreter", file=sys.stderr)
        return 1
    if not src.is_file():
        print(f"error: no such file: {src}", file=sys.stderr)
        return 1
    img = Image.open(src)
    img = img.convert("RGB")          # drops alpha and all EXIF/metadata
    img.thumbnail((1024, 1024))       # same long-edge cap the wrapper uses
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG")       # fresh PNG: no EXIF, no GPS, no device
    print(f"wrote {out} ({out.stat().st_size} bytes; metadata stripped)")
    return 0


def _caption(path: Path) -> int:
    """Real-BLIP caption of one image — the pre-flight check for candidate
    confounder images. Sets USE_TF=0 before transformers can import TF."""
    import os
    os.environ.setdefault("USE_TF", "0")  # D-016 segfault guard
    sys.path.insert(0, str(_REPO / "src"))
    if not path.is_absolute() and not path.is_file():
        candidate = _OUT_DIR / path
        if candidate.is_file():
            path = candidate
    if not path.is_file():
        print(f"error: no such image: {path}", file=sys.stderr)
        return 1
    from triguard.models import image_model
    ev = image_model.analyse(path, force_mode="blip")
    mode = ev.raw.get("mode")
    print(f"caption ({mode}): {ev.caption}")
    if ev.visual_risk_cues:
        print(f"risk cues: {ev.visual_risk_cues}")
    if mode != "real-blip":
        print("warning: BLIP did not actually run (fell back to mock) — "
              "use WSL ~/.venv-tri with USE_TF=0 and cached weights",
              file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--tts", metavar="TEXT",
                   help="speak TEXT to a 22.05 kHz mono wav (the audio "
                        "wrapper resamples to its own 16 kHz)")
    g.add_argument("--import", dest="import_", metavar="PHOTO",
                   help="import an own photo (resize + strip metadata)")
    g.add_argument("--caption", metavar="IMAGE",
                   help="print the real BLIP caption of IMAGE (pre-flight)")
    p.add_argument("--out",
                   help="output file name for --tts/--import (relative names "
                        "land in data/sample_inputs/confounders/)")
    args = p.parse_args(argv)

    if args.caption:
        return _caption(Path(args.caption))

    if not args.out:
        p.error("--out is required with --tts/--import")
    out = Path(args.out)
    if not out.is_absolute():
        out = _OUT_DIR / out

    if args.tts:
        return _tts(args.tts, out)
    return _import_photo(Path(args.import_), out)


if __name__ == "__main__":
    sys.exit(main())
