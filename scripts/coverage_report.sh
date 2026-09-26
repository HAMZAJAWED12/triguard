#!/usr/bin/env bash
# scripts/coverage_report.sh — T5 branch-coverage run for the orchestrator and
# the LLM judge (docs/evaluation_protocol.md T5: "Coverage measured via
# pytest-cov; target > 80 % branch coverage on pipeline.py").
#
# Intended for the WSL venv:   source ~/.venv-tri/bin/activate && bash scripts/coverage_report.sh
#
# WHAT IS MEASURED: the FAST lane only (no --run-slow). Reason: in the combined
# venv a `pytest --run-slow` process can SIGSEGV at interpreter teardown (a
# torch atexit artifact — docs/implementation_notes.md, "Fast suite" note), which
# would truncate the coverage data file before it is written. The slow tests
# exercise real model weights, not orchestrator/judge branches, so the fast
# lane is the honest measurement target for T5.
#
# REFUSES CLEANLY when pytest-cov is not installed. It is NOT installed in
# either project venv today and this script never installs anything: adding a
# dev dependency needs the author's approval (CLAUDE.md rule 4 / DECISIONS.md).
set -euo pipefail

cd "$(dirname "$0")/.."

PY="${PYTHON:-python}"

if ! "$PY" -c "import pytest_cov" >/dev/null 2>&1; then
  cat >&2 <<EOF
coverage_report.sh: pytest-cov is not installed in this interpreter
  ($("$PY" -c 'import sys; print(sys.executable)'))
Nothing was run and nothing was installed. T5 coverage stays "not measured".
If the author approves pytest-cov as a dev dependency (record it in DECISIONS.md
and requirements-dev / requirements-full), install it with:

    "$PY" -m pip install pytest-cov

then re-run:  bash scripts/coverage_report.sh
EOF
  exit 2
fi

TS="$(date -u +%Y%m%d-%H%M%S)"
OUT="outputs/coverage/${TS}"
mkdir -p "$OUT"

echo "== TriGuard T5 coverage (fast lane, no --run-slow) -> ${OUT}"
export USE_TF=0
export PYTHONPATH=src
set +e
"$PY" -m pytest -q -p no:cacheprovider \
  --cov=triguard.orchestrator \
  --cov=triguard.models.llm_judge \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report="xml:${OUT}/coverage.xml" \
  --junitxml="${OUT}/junit.xml" \
  tests 2>&1 | tee "${OUT}/coverage_term.txt"
RC="${PIPESTATUS[0]}"
set -e

{
  echo "run_at_utc: ${TS}"
  echo "interpreter: $("$PY" -c 'import sys; print(sys.executable)')"
  echo "python: $("$PY" -c 'import platform; print(platform.python_version())')"
  echo "pytest: $("$PY" -m pytest --version 2>&1 | head -1)"
  echo "pytest_cov: $("$PY" -c 'import pytest_cov; print(getattr(pytest_cov, "__version__", "unknown"))')"
  echo "lane: fast (no --run-slow) — see header comment for the teardown SIGSEGV reason"
  echo "targets: triguard.orchestrator (pipeline.py, schemas.py), triguard.models.llm_judge"
  echo "pytest_rc: ${RC}"
  echo "git_head: $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
} > "${OUT}/RUN_INFO.txt"

echo "== done (pytest rc=${RC}); artefacts: ${OUT}/{coverage.xml,coverage_term.txt,junit.xml,RUN_INFO.txt}"
exit "$RC"
