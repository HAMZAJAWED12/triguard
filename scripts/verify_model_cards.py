"""Verify the machine-checked tokens in docs/model_cards.md (read-only checker).

    PYTHONPATH=src python scripts/verify_model_cards.py [--card docs/model_cards.md]

Three token kinds are parsed from the card (inline code spans):

    `code:_NAME=<python literal>`   compared with the live attribute of the
                                     wrapper module that owns _NAME (wrappers are
                                     imported with TRIGUARD_MOCK=1; no weights,
                                     no network)
    `t4:<key.path>=<python literal>` compared with
                                     outputs/evaluation/20260704-153729/t4/results.json
    `pin:<package>==<version>`       compared with requirements-full.txt
    `pin:<package>=MISSING`          asserts the package is absent from that file

Exit status 0 when every token matches and every required token is present,
1 otherwise. The script writes nothing. A missing exact RapidOCR pin in
requirements-full.txt is reported as a warning (it is a documented gap, not a
card error).
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
DEFAULT_CARD = REPO / "docs" / "model_cards.md"
DEFAULT_T4 = REPO / "outputs" / "evaluation" / "20260704-153729" / "t4" / "results.json"
DEFAULT_REQ = REPO / "requirements-full.txt"

# constant name -> owning module (imported mock-safe, lazily)
CODE_CONSTANTS: dict[str, str] = {
    "_YAMNET_URL": "triguard.models.audio_model",
    "_SR": "triguard.models.audio_model",
    "_MAX_SECONDS": "triguard.models.audio_model",
    "_TAG_THRESHOLD": "triguard.models.audio_model",
    "_TOP_K": "triguard.models.audio_model",
    "_HF_MODEL": "triguard.models.text_model",
    "_HF_REVISION": "triguard.models.text_model",
    "_BLIP_MODEL": "triguard.models.image_model",
    "_BLIP_REVISION": "triguard.models.image_model",
    "_MAX_EDGE": "triguard.models.image_model",
    "_BLIP_CONF_FALLBACK": "triguard.models.image_model",
    "_DEFAULT_OLLAMA_MODEL": "triguard.models.llm_judge",
    "_DEFAULT_OLLAMA_HOST": "triguard.models.llm_judge",
}
# tokens the card MUST carry (task W3 list)
REQUIRED_CODE = (
    "_YAMNET_URL", "_SR", "_MAX_SECONDS", "_TAG_THRESHOLD", "_TOP_K",
    "_HF_MODEL", "_HF_REVISION", "_BLIP_MODEL", "_BLIP_REVISION", "_MAX_EDGE",
    "_DEFAULT_OLLAMA_MODEL",
)
REQUIRED_T4 = (
    "model_versions.whisper_model", "model_versions.yamnet",
    "yamnet_events.top1_rate", "yamnet_events.top5_rate",
    "whisper_wer.wer_corpus",
)
REQUIRED_PINS = ("openai-whisper", "tensorflow-hub", "transformers", "torch")
RAPIDOCR_PKG = "rapidocr-onnxruntime"

_TOKEN = re.compile(r"`(code|t4|pin):([A-Za-z0-9_.+\-]+)(==?)([^`]+)`")


def parse_tokens(text: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    """-> ({kind: {name: raw_value}}, problems). Conflicting duplicates are problems."""
    found: dict[str, dict[str, str]] = {"code": {}, "t4": {}, "pin": {}}
    problems: list[str] = []
    for kind, name, op, raw in _TOKEN.findall(text):
        raw = raw.strip()
        if kind == "pin":
            if op == "==":
                value = raw
            elif raw == "MISSING":
                value = "MISSING"
            else:
                problems.append(f"pin token `{name}` must use == or =MISSING (got {op}{raw})")
                continue
        else:
            if op != "=":
                problems.append(f"{kind} token `{name}` must use a single '=' (got ==)")
                continue
            value = raw
        prev = found[kind].get(name)
        if prev is not None and prev != value:
            problems.append(f"{kind}:{name} appears with conflicting values {prev!r} and {value!r}")
        found[kind][name] = value
    return found, problems


def _literal(raw: str) -> Any:
    return ast.literal_eval(raw)


def _lookup(obj: Any, path: str) -> Any:
    for part in path.split("."):
        if isinstance(obj, list):
            obj = obj[int(part)]
        else:
            obj = obj[part]
    return obj


def parse_pins(req_text: str) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in req_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        if "==" in line:
            name, ver = line.split("==", 1)
            pins[name.strip().lower()] = ver.strip()
    return pins


def _import_constants(names: set[str]) -> dict[str, Any]:
    """Import only the modules needed, mock-safe (TRIGUARD_MOCK=1, src on path)."""
    os.environ.setdefault("TRIGUARD_MOCK", "1")
    src = str(REPO / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    live: dict[str, Any] = {}
    for name in names:
        mod_name = CODE_CONSTANTS.get(name)
        if mod_name is None:
            continue
        mod = importlib.import_module(mod_name)
        live[name] = getattr(mod, name)
    return live


def check(
    card: Path = DEFAULT_CARD,
    t4_path: Path = DEFAULT_T4,
    req_path: Path = DEFAULT_REQ,
) -> tuple[list[str], list[str], list[str]]:
    """-> (problems, warnings, summary). Empty problems == pass. Writes nothing."""
    problems: list[str] = []
    warnings: list[str] = []
    summary: list[str] = []

    text = card.read_text(encoding="utf-8")
    found, parse_problems = parse_tokens(text)
    problems.extend(parse_problems)

    # --- code constants -----------------------------------------------------
    for name in REQUIRED_CODE:
        if name not in found["code"]:
            problems.append(f"card is missing required token code:{name}")
    unknown = sorted(n for n in found["code"] if n not in CODE_CONSTANTS)
    for n in unknown:
        problems.append(f"code:{n} is not a checkable constant (add it to CODE_CONSTANTS)")
    live = _import_constants(set(found["code"]) & set(CODE_CONSTANTS))
    for name, raw in sorted(found["code"].items()):
        if name not in live:
            continue
        try:
            expected = _literal(raw)
        except (ValueError, SyntaxError) as e:
            problems.append(f"code:{name} value {raw!r} is not a python literal ({e})")
            continue
        actual = live[name]
        if expected != actual or type(expected) is not type(actual):
            problems.append(f"code:{name} card={expected!r} code={actual!r}")
        else:
            summary.append(f"code:{name} == {actual!r}")

    # --- T4 results.json ----------------------------------------------------
    t4 = json.loads(t4_path.read_text(encoding="utf-8"))
    for path in REQUIRED_T4:
        if path not in found["t4"]:
            problems.append(f"card is missing required token t4:{path}")
    for path, raw in sorted(found["t4"].items()):
        try:
            expected = _literal(raw)
        except (ValueError, SyntaxError) as e:
            problems.append(f"t4:{path} value {raw!r} is not a python literal ({e})")
            continue
        try:
            actual = _lookup(t4, path)
        except (KeyError, IndexError, ValueError, TypeError):
            problems.append(f"t4:{path} not found in {t4_path.name}")
            continue
        if expected != actual:
            problems.append(f"t4:{path} card={expected!r} file={actual!r}")
        else:
            summary.append(f"t4:{path} == {actual!r}")

    # --- requirements-full.txt pins ----------------------------------------
    pins = parse_pins(req_path.read_text(encoding="utf-8"))
    for pkg in REQUIRED_PINS:
        if pkg not in found["pin"]:
            problems.append(f"card is missing required token pin:{pkg}")
    for pkg, ver in sorted(found["pin"].items()):
        actual = pins.get(pkg.lower())
        if ver == "MISSING":
            if actual is not None:
                problems.append(f"pin:{pkg} card says MISSING but {req_path.name} pins {actual}")
            else:
                summary.append(f"pin:{pkg} absent from {req_path.name} (as stated)")
        elif actual is None:
            problems.append(f"pin:{pkg} not pinned in {req_path.name}")
        elif actual != ver:
            problems.append(f"pin:{pkg} card={ver} file={actual}")
        else:
            summary.append(f"pin:{pkg}=={actual}")
    if RAPIDOCR_PKG not in pins:
        warnings.append(f"RapidOCR exact pin: MISSING ({RAPIDOCR_PKG} not in {req_path.name})")

    return problems, warnings, summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--card", type=Path, default=DEFAULT_CARD)
    ap.add_argument("--t4", type=Path, default=DEFAULT_T4)
    ap.add_argument("--requirements", type=Path, default=DEFAULT_REQ)
    ap.add_argument("-q", "--quiet", action="store_true", help="print problems/warnings only")
    args = ap.parse_args(argv)

    problems, warnings, summary = check(args.card, args.t4, args.requirements)
    if not args.quiet:
        for line in summary:
            print(f"ok   {line}")
    for line in warnings:
        print(f"WARN {line}")
    for line in problems:
        print(f"FAIL {line}")
    print(f"verify_model_cards: {len(summary)} checks passed, "
          f"{len(problems)} problems, {len(warnings)} warnings")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
