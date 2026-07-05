"""Fast unit test for failure_analysis (offline; synthetic results.json)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from triguard.evaluation import failure_analysis


def test_failure_analysis_taxonomy(tmp_path: Path,
                                   monkeypatch: pytest.MonkeyPatch) -> None:
    data = {
        "track": "T3",
        "failures": [
            {"label": "harmful", "pred": "safe", "risk_score": 0.1, "text": "a threat"},
            {"label": "safe", "pred": "harmful", "risk_score": 0.9, "text": "a picnic"},
        ],
    }
    src = tmp_path / "results.json"
    src.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.chdir(tmp_path)          # outputs/ written under the temp dir
    out = failure_analysis.main([str(src)])
    md = Path(out).read_text(encoding="utf-8")
    assert "missed-harmful" in md
    assert "false-positive-harmful" in md
