"""
Pytest configuration shared by the TriGuard test suite.

Registers the ``slow`` marker and a ``--run-slow`` command-line flag. Tests
marked ``@pytest.mark.slow`` (network / model-download / dataset loads) are
skipped by default so the fast lane stays fully offline:

    PYTHONPATH=src python -m pytest -q            # fast lane, slow tests skipped
    PYTHONPATH=src python -m pytest -q --run-slow # include slow tests
"""
from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register the ``slow`` marker."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests that require network/downloads (skipped unless --run-slow)",
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the ``--run-slow`` flag."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run tests marked @pytest.mark.slow (these may hit the network)",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip ``slow``-marked tests unless ``--run-slow`` was passed."""
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="needs --run-slow (network/download test)")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
