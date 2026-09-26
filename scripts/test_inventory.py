#!/usr/bin/env python
"""Test-suite inventory for TriGuard (stdlib only, no new dependencies).

Collects the pytest suite with the CALLING interpreter (``sys.executable``),
classifies every collected test id into an evaluation layer via an explicit
mapping table keyed on the test file's basename (plus a few test-name
overrides), detects test modules that dropped out of collection (module-level
``pytest.importorskip``) by diffing the collected files against
``tests/test_*.py`` on disk, and emits a Markdown report.

Optionally ``--junit <xml>`` adds pass/skip/fail counts per layer from a
``pytest --junitxml=<xml>`` run made with the same interpreter.

Usage (from the repo root):

    PYTHONPATH=src python -m pytest -q --junitxml=/tmp/junit.xml
    python scripts/test_inventory.py --env-label "WSL ~/.venv-tri" \
        --junit /tmp/junit.xml --out docs/generated/test_inventory.md

Exit status 1 if any collected test id falls into the ``unclassified`` bucket
(the mapping table must be extended before the inventory is accepted).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Layer mapping (explicit; edit here when a new test file is added)
# ---------------------------------------------------------------------------

LAYER_ORDER = [
    "unit-schema",
    "unit-wrapper",
    "unit-judge-rule",
    "unit-eval-helper",
    "unit-tooling",
    "regression-fallback",
    "integration-orchestrator",
    "functional-api-cli",
    "real-backend-slow",
    "dataset-loader-slow",
    "unclassified",
]

# basename (without .py) -> layer, for tests without a name-level override.
FILE_LAYER: dict[str, str] = {
    "test_schemas": "unit-schema",
    "test_text_model": "unit-wrapper",
    "test_image_model": "unit-wrapper",
    "test_audio_model": "unit-wrapper",
    "test_llm_judge": "unit-judge-rule",
    "test_grounding": "unit-eval-helper",
    "test_failure_analysis": "unit-eval-helper",
    "test_run_t6": "unit-eval-helper",
    "test_docx_to_md": "unit-tooling",
    "test_check_citations": "unit-tooling",
    "test_ci_from_envelope": "unit-tooling",
    "test_dataset_cards": "unit-tooling",
    "test_verify_model_cards": "unit-tooling",
    "test_smoke_ollama_save": "unit-tooling",
    "test_check_report_refs": "unit-tooling",
    "test_figures_provenance": "unit-tooling",
    "test_llm_judge_stream": "regression-fallback",
    "test_wrapper_latch": "regression-fallback",
    "test_llm_judge_retry": "regression-fallback",
    "test_pipeline_shielding": "regression-fallback",
    "test_orchestrator": "integration-orchestrator",
    "test_api": "functional-api-cli",
    "test_api_phase_d": "functional-api-cli",
    "test_cli": "functional-api-cli",
    "test_text_model_hf": "real-backend-slow",
    "test_image_model_blip": "real-backend-slow",
    "test_image_model_ocr": "real-backend-slow",
    "test_audio_model_real": "real-backend-slow",
    "test_llm_judge_ollama": "real-backend-slow",
    "test_t2_dataset": "dataset-loader-slow",
    "test_run_t3": "dataset-loader-slow",
    "test_run_t4": "dataset-loader-slow",
}

# (basename, compiled test-name regex) -> layer; checked before FILE_LAYER.
NAME_OVERRIDES: list[tuple[str, re.Pattern[str], str]] = [
    ("test_llm_judge", re.compile(r"falls_back"), "regression-fallback"),
    ("test_api_phase_d", re.compile(r"^test_gather_inputs"), "regression-fallback"),
    ("test_api_phase_d", re.compile(r"^test_compare_real_ollama$"), "real-backend-slow"),
]

_NODEID_RE = re.compile(r"^(?P<file>tests/[^:\s]+\.py)::(?P<name>.+)$")


def classify(file_path: str, test_name: str, is_slow: bool) -> str:
    """Return the layer for one collected test id."""
    base = Path(file_path).stem
    bare = test_name.split("[", 1)[0]
    # Class-based tests appear as Class::method; use the last segment.
    bare = bare.split("::")[-1]
    for fbase, pat, layer in NAME_OVERRIDES:
        if base == fbase and pat.search(bare):
            return layer
    layer = FILE_LAYER.get(base)
    if layer is None:
        return "unclassified"
    # A slow test in a fast-layer file is still counted in that file's layer,
    # but is flagged in the per-file table via the slow column.
    return layer


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", "src")
    env.setdefault("USE_TF", "0")
    return subprocess.run(
        cmd, cwd=str(cwd), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def collect_ids(python: str, cwd: Path, extra: list[str]) -> tuple[list[str], str]:
    cmd = [python, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
           *extra, "tests"]
    proc = _run(cmd, cwd)
    ids = [ln.strip() for ln in proc.stdout.splitlines() if _NODEID_RE.match(ln.strip())]
    summary = ""
    for ln in proc.stdout.splitlines()[::-1]:
        if "collected" in ln or "selected" in ln or "no tests" in ln:
            summary = ln.strip()
            break
    if proc.returncode not in (0, 5):  # 5 = no tests collected (e.g. -m slow empty)
        sys.stderr.write(proc.stdout[-2000:] + proc.stderr[-2000:])
        raise SystemExit(f"pytest collection failed (rc={proc.returncode}): {' '.join(cmd)}")
    return ids, summary


def pytest_version(python: str, cwd: Path) -> str:
    proc = _run([python, "-m", "pytest", "--version"], cwd)
    out = (proc.stdout or proc.stderr).strip().splitlines()
    return out[0] if out else "unknown"


# ---------------------------------------------------------------------------
# JUnit parsing
# ---------------------------------------------------------------------------


def parse_junit(path: Path) -> tuple[dict[tuple[str, str], str], dict[str, str]]:
    """Return ({(file, name): 'passed'|'skipped'|'failed'}, {file: module-skip reason})."""
    tree = ET.parse(path)
    per_test: dict[tuple[str, str], str] = {}
    module_skips: dict[str, str] = {}
    for tc in tree.iter("testcase"):
        classname = tc.get("classname", "")
        name = tc.get("name", "")
        # Module-level importorskip (pytest 8/9 xunit2): classname="" and
        # name="tests.test_x" — one testcase per dropped module.
        if classname == "" and re.match(r"^tests\.test_\w+$", name):
            file_path = name.replace(".", "/") + ".py"
            sk = tc.find("skipped")
            module_skips[file_path] = (sk.get("message", "") if sk is not None else "")
            continue
        file_attr = tc.get("file")
        if file_attr:
            file_path = file_attr.replace("\\", "/")
        else:
            # classname is tests.test_x[.Class]; the module is the first two parts.
            parts = classname.split(".")
            mod = parts[:2] if len(parts) >= 2 else parts
            file_path = "/".join(mod) + ".py"
        if tc.find("failure") is not None or tc.find("error") is not None:
            status = "failed"
        elif tc.find("skipped") is not None:
            status = "skipped"
        else:
            status = "passed"
        per_test[(file_path, name)] = status
    return per_test, module_skips


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def build_report(args: argparse.Namespace) -> tuple[str, int]:
    root = Path(args.root).resolve()
    python = args.python or sys.executable
    tests_dir = root / "tests"

    extra = list(args.extra_arg)
    all_ids, all_summary = collect_ids(python, root, extra)
    slow_ids, slow_summary = collect_ids(python, root, [*extra, "-m", "slow"])
    slow_set = set(slow_ids)

    on_disk = sorted(p.as_posix() for p in tests_dir.glob("test_*.py"))
    on_disk_rel = [f"tests/{Path(p).name}" for p in on_disk]
    collected_files = sorted({m.group("file") for m in map(_NODEID_RE.match, all_ids) if m})
    dropped = [f for f in on_disk_rel if f not in collected_files]

    junit_status: dict[tuple[str, str], str] = {}
    module_skips: dict[str, str] = {}
    if args.junit:
        junit_status, module_skips = parse_junit(Path(args.junit))

    # classify
    rows: list[dict] = []
    for nid in all_ids:
        m = _NODEID_RE.match(nid)
        assert m
        f, n = m.group("file"), m.group("name")
        layer = classify(f, n, nid in slow_set)
        st = junit_status.get((f, n), "")
        if not st and "[" in n:  # parametrised ids: junit name keeps the [param]
            st = junit_status.get((f, n), "")
        rows.append({"id": nid, "file": f, "name": n, "layer": layer,
                     "slow": nid in slow_set, "status": st})

    per_layer: dict[str, dict] = OrderedDict(
        (l, {"files": set(), "n": 0, "slow": 0, "passed": 0, "skipped": 0, "failed": 0,
             "unknown": 0}) for l in LAYER_ORDER)
    per_file: dict[str, dict] = OrderedDict()
    for r in rows:
        L = per_layer[r["layer"]]
        L["files"].add(r["file"])
        L["n"] += 1
        L["slow"] += int(r["slow"])
        key = r["status"] or "unknown"
        L[key] += 1
        F = per_file.setdefault(r["file"], {"layers": set(), "n": 0, "slow": 0,
                                            "passed": 0, "skipped": 0, "failed": 0,
                                            "unknown": 0})
        F["layers"].add(r["layer"])
        F["n"] += 1
        F["slow"] += int(r["slow"])
        F[key] += 1

    unclassified = [r["id"] for r in rows if r["layer"] == "unclassified"]

    has_junit = bool(args.junit)
    today = _dt.date.today().isoformat()
    lines: list[str] = []
    lines.append("# Test inventory (generated — do not hand-edit)")
    lines.append("")
    lines.append(f"- date: {today}")
    lines.append(f"- interpreter label: {args.env_label}")
    lines.append(f"- python: {platform.python_version()} ({platform.system()})")
    lines.append(f"- {pytest_version(python, root)}")
    lines.append("- generator: `scripts/test_inventory.py` (stdlib only)")
    if extra:
        lines.append("- extra pytest args (both collect runs): `" + " ".join(extra) + "`")
    lines.append("- collect command: `python -m pytest --collect-only -q -p no:cacheprovider tests`"
                 f" -> {all_summary or 'n/a'}")
    lines.append("- slow-select command: `python -m pytest --collect-only -q -p no:cacheprovider"
                 f" -m slow tests` -> {slow_summary or 'n/a'}")
    if has_junit:
        # basename only: never write a local absolute path into a repo file
        lines.append(f"- junit: `{Path(args.junit).name}` from `python -m pytest -q"
                     " --junitxml=...` (fast lane: no --run-slow; slow tests appear as"
                     " skipped)")
    else:
        lines.append("- junit: not supplied (no pass/skip/fail columns)")
    lines.append("")
    lines.append(f"Totals: {len(all_ids)} collected test ids in {len(collected_files)} files; "
                 f"{len(slow_ids)} slow-marked; {len(dropped)} test module(s) not collected "
                 f"(module-level importorskip); {len(unclassified)} unclassified.")
    lines.append("")

    # per-layer table
    lines.append("## Per-layer")
    lines.append("")
    hdr = "| layer | files | collected | slow-marked |"
    sep = "|---|---|---|---|"
    if has_junit:
        hdr += " passed | skipped | failed |"
        sep += "---|---|---|"
    lines.append(hdr)
    lines.append(sep)
    for layer in LAYER_ORDER:
        L = per_layer[layer]
        if layer == "unclassified" and L["n"] == 0:
            continue
        row = f"| {layer} | {len(L['files'])} | {L['n']} | {L['slow']} |"
        if has_junit:
            row += f" {L['passed']} | {L['skipped']} | {L['failed']} |"
        lines.append(row)
    tot = {k: sum(per_layer[l][k] for l in LAYER_ORDER)
           for k in ("n", "slow", "passed", "skipped", "failed")}
    row = f"| **total** | {len(collected_files)} | {tot['n']} | {tot['slow']} |"
    if has_junit:
        row += f" {tot['passed']} | {tot['skipped']} | {tot['failed']} |"
    lines.append(row)
    lines.append("")

    # per-file table
    lines.append("## Per-file")
    lines.append("")
    hdr = "| file | layer(s) | collected | slow-marked |"
    sep = "|---|---|---|---|"
    if has_junit:
        hdr += " passed | skipped | failed |"
        sep += "---|---|---|"
    lines.append(hdr)
    lines.append(sep)
    for f, F in per_file.items():
        row = (f"| `{f}` | {', '.join(sorted(F['layers']))} | {F['n']} | {F['slow']} |")
        if has_junit:
            row += f" {F['passed']} | {F['skipped']} | {F['failed']} |"
        lines.append(row)
    lines.append("")

    lines.append("## Slow-marked test ids (skipped unless `--run-slow`)")
    lines.append("")
    for nid in slow_ids:
        lines.append(f"- `{nid}`")
    if not slow_ids:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Test modules not collected in this environment (module-level importorskip)")
    lines.append("")
    if dropped:
        for f in dropped:
            reason = module_skips.get(f, "")
            lines.append(f"- `{f}`" + (f" — {reason}" if reason else ""))
    else:
        lines.append("- (none: every `tests/test_*.py` on disk was collected)")
    lines.append("")

    if unclassified:
        lines.append("## UNCLASSIFIED (extend FILE_LAYER / NAME_OVERRIDES)")
        lines.append("")
        for nid in unclassified:
            lines.append(f"- `{nid}`")
        lines.append("")

    return "\n".join(lines) + "\n", (1 if unclassified else 0)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--env-label", default="unlabelled interpreter",
                    help="e.g. 'WSL ~/.venv-tri' or 'offline venv'")
    ap.add_argument("--junit", default=None, help="pytest --junitxml output to fold in")
    ap.add_argument("--out", default=None, help="Markdown output path (default: stdout)")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]),
                    help="repo root (default: parent of scripts/)")
    ap.add_argument("--python", default=None,
                    help="interpreter to collect with (default: sys.executable)")
    ap.add_argument("--extra-arg", action="append", default=[],
                    help="extra pytest argument for BOTH collect runs (repeatable), e.g. "
                         "--extra-arg=--ignore=tests/test_broken.py; recorded in the header")
    args = ap.parse_args(argv)

    report, rc = build_report(args)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        sys.stderr.write(f"wrote {out} (rc={rc})\n")
    else:
        sys.stdout.write(report)
    return rc


if __name__ == "__main__":
    sys.exit(main())
