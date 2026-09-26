"""Fast, offline tests for scripts/verify_model_cards.py against the real card.

The checker imports the wrappers mock-safe (TRIGUARD_MOCK=1) and reads the
committed T4 results.json + requirements-full.txt; nothing is downloaded and
nothing is written.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts"))

import verify_model_cards as vmc  # noqa: E402

_CARD = _REPO / "docs" / "model_cards.md"


def _variant_card(tmp_path: Path, old: str, new: str) -> Path:
    text = _CARD.read_text(encoding="utf-8")
    assert old in text, f"fixture token {old!r} not in the real card"
    out = tmp_path / "card.md"
    out.write_text(text.replace(old, new, 1), encoding="utf-8")
    return out


def test_real_card_passes() -> None:
    problems, warnings, summary = vmc.check()
    assert problems == [], problems
    # the documented gap is surfaced, not hidden
    assert any("RapidOCR exact pin: MISSING" in w for w in warnings)
    # every required token was actually checked
    checked = "\n".join(summary)
    for name in vmc.REQUIRED_CODE:
        assert f"code:{name} ==" in checked
    for path in vmc.REQUIRED_T4:
        assert f"t4:{path} ==" in checked
    for pkg in vmc.REQUIRED_PINS:
        assert f"pin:{pkg}==" in checked


def test_code_constant_mismatch_is_reported(tmp_path: Path) -> None:
    card = _variant_card(tmp_path, "`code:_SR=16000`", "`code:_SR=8000`")
    problems, _, _ = vmc.check(card=card)
    assert any(p.startswith("code:_SR ") for p in problems), problems


def test_t4_number_mismatch_is_reported(tmp_path: Path) -> None:
    card = _variant_card(
        tmp_path,
        "`t4:yamnet_events.top1_rate=0.32`",
        "`t4:yamnet_events.top1_rate=0.99`",
    )
    problems, _, _ = vmc.check(card=card)
    assert any(p.startswith("t4:yamnet_events.top1_rate ") for p in problems), problems


def test_pin_mismatch_and_missing_pin_are_reported(tmp_path: Path) -> None:
    card = _variant_card(tmp_path, "`pin:torch==2.12.1+cpu`", "`pin:torch==0.0.0`")
    problems, _, _ = vmc.check(card=card)
    assert any(p.startswith("pin:torch ") for p in problems), problems

    card2 = _variant_card(
        tmp_path, "`pin:rapidocr-onnxruntime=MISSING`", "`pin:rapidocr-onnxruntime==1.4.4`"
    )
    problems2, _, _ = vmc.check(card=card2)
    assert any(p.startswith("pin:rapidocr-onnxruntime ") for p in problems2), problems2


def test_missing_required_token_is_reported(tmp_path: Path) -> None:
    card = _variant_card(tmp_path, "`code:_TOP_K=5`", "`code:_TOP_K_typo=5`")
    problems, _, _ = vmc.check(card=card)
    assert any("missing required token code:_TOP_K" in p for p in problems), problems


def test_main_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert vmc.main(["-q"]) == 0
    out = capsys.readouterr().out
    assert "WARN RapidOCR exact pin: MISSING" in out
    bad = _variant_card(tmp_path, "`code:_MAX_EDGE=1024`", "`code:_MAX_EDGE=512`")
    assert vmc.main(["-q", "--card", str(bad)]) == 1
