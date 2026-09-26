"""Functional tests for the ``python -m triguard.cli`` entry point.

Runs the CLI as a real subprocess (the calling interpreter, ``sys.executable``)
with ``TRIGUARD_MOCK=1`` and ``PYTHONPATH=src`` so the run is fully offline and
deterministic. Asserts the exit code and that stdout is one JSON document that
validates as ``TriGuardResult`` (``cli.py`` prints ``result.model_dump()``).
The ``--judge`` flag is accepted both before and after the subcommand
(D-027); both spellings are exercised.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from triguard.orchestrator.schemas import TriGuardResult

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SAMPLE = "data/sample_inputs/sample_harmful.json"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["TRIGUARD_MOCK"] = "1"
    env["PYTHONPATH"] = "src"
    env.setdefault("USE_TF", "0")
    return subprocess.run(
        [sys.executable, "-m", "triguard.cli", *args],
        cwd=str(_REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )


def _assert_result(proc: subprocess.CompletedProcess[str]) -> TriGuardResult:
    assert proc.returncode == 0, proc.stderr
    result = TriGuardResult.model_validate_json(proc.stdout)
    assert result.model_versions["orchestrator"]
    assert result.model_versions["llm_judge"] == "rule"
    return result


def test_cli_run_sample_harmful_exit_0_and_valid_result() -> None:
    proc = _run_cli("run", _SAMPLE)

    result = _assert_result(proc)
    assert result.text_evidence is not None
    assert result.image_evidence is not None
    assert result.audio_evidence is not None
    assert result.model_versions["text_model"].startswith("mock")
    assert result.model_versions["image_model"].startswith("mock")
    assert result.model_versions["audio_model"].startswith("mock")


def test_cli_accepts_judge_flag_after_subcommand() -> None:
    proc = _run_cli("run", _SAMPLE, "--judge", "rule")

    _assert_result(proc)


def test_cli_accepts_judge_flag_before_subcommand() -> None:
    proc = _run_cli("--judge", "rule", "run", _SAMPLE)

    _assert_result(proc)


def test_cli_missing_file_exits_1_with_one_line_error() -> None:
    proc = _run_cli("run", "data/sample_inputs/does_not_exist.json")

    assert proc.returncode == 1
    assert proc.stdout == ""
    assert proc.stderr.strip().startswith("error: file not found:")
    assert "Traceback" not in proc.stderr
