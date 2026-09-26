"""Every number printed on a data figure must exist in the results.json it cites.

For each SVG under ``docs/figures`` that carries a ``source:`` subtitle, the
test reads the run ids (``\\d{8}-\\d{6}``) and the track (``t<N>/results.json``)
from that subtitle, loads ``outputs/evaluation/<run>/<track>/results.json``,
flattens every numeric leaf to ``{str(v), str(round(v, 4))}`` and asserts that
every decimal token (``-?\\d+\\.\\d+``) and every integer >= 10 that is not
glued to a letter (``p50``, ``T8`` are labels) in the figure's ``<text>``
elements is present. Gridline / axis labels are whitelisted per file
below, explicitly, after inspecting each SVG; the whitelist is itself asserted
to be present in the SVG so it cannot go stale silently. Fast and offline.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_FIG_DIR = _REPO / "docs" / "figures"
_EVAL_DIR = _REPO / "outputs" / "evaluation"

# gridline / axis labels that are plot scaffolding, not results.json values
_GRIDLINES: dict[str, set[str]] = {
    "fig3_t2_text_track.svg": {"0.5", "1.0"},
    "fig4_t6_ablation.svg": {"0.5", "1.0"},
    "fig5_t3_ocr_ablation.svg": {"0.25", "0.50"},
    "fig6_t8_perf.svg": {"2100", "4200", "1500", "3000"},
}

_RUN_RE = re.compile(r"\b(\d{8}-\d{6})\b")
_TRACK_RE = re.compile(r"\b(t\d)/results\.json")
_DECIMAL_RE = re.compile(r"-?\d+\.\d+")
# integers not glued to a letter: "n=500" and "2100" count, "p50" / "T8" / "F1" are labels
_INT_RE = re.compile(r"(?<![\w.])\d+(?![\d.])")
_SVG_NS = "{http://www.w3.org/2000/svg}"


def _text_elements(svg: Path) -> list[str]:
    root = ET.parse(svg).getroot()
    return ["".join(el.itertext()).strip() for el in root.iter(f"{_SVG_NS}text")]


def _flatten(obj, out: set[str]) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        out.add(str(obj))
        out.add(str(round(obj, 4)))
    elif isinstance(obj, dict):
        for v in obj.values():
            _flatten(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _flatten(v, out)


def _tokens(text: str) -> set[str]:
    decimals = set(_DECIMAL_RE.findall(text))
    rest = _DECIMAL_RE.sub(" ", text)
    ints = {t for t in _INT_RE.findall(rest) if int(t) >= 10}
    return decimals | ints


@pytest.mark.parametrize("name", sorted(_GRIDLINES))
def test_figure_numbers_come_from_cited_results_json(name: str) -> None:
    svg = _FIG_DIR / name
    texts = _text_elements(svg)
    source_lines = [t for t in texts if t.lower().startswith("source")]
    assert len(source_lines) == 1, f"{name}: expected one 'source' subtitle line"
    runs = _RUN_RE.findall(source_lines[0])
    tracks = _TRACK_RE.findall(source_lines[0])
    assert runs and len(tracks) == 1, f"{name}: could not read run ids / track from subtitle"

    allowed: set[str] = set()
    for run in runs:
        path = _EVAL_DIR / run / tracks[0] / "results.json"
        assert path.is_file(), f"{name} cites {path} which does not exist"
        _flatten(json.loads(path.read_text(encoding="utf-8")), allowed)

    whitelist = _GRIDLINES[name]
    all_text = " ".join(t for t in texts if t not in source_lines)
    present_whitelist = {w for w in whitelist if re.search(rf"(?<![\d.]){re.escape(w)}(?![\d.])", all_text)}
    assert present_whitelist == whitelist, f"{name}: stale gridline whitelist {whitelist - present_whitelist}"

    missing: dict[str, str] = {}
    for t in texts:
        if t in source_lines:
            continue
        for tok in _tokens(t) - whitelist:
            if tok not in allowed:
                missing[tok] = t
    assert not missing, f"{name}: numbers not in {runs}/{tracks[0]}/results.json: {missing}"


def test_no_repo_table_ids_baked_into_figure_text() -> None:
    """Figure text must not cite repo-only evidence-table ids (E1, E4b, ...)."""
    offenders = {
        svg.name: t
        for svg in sorted(_FIG_DIR.glob("*.svg"))
        for t in _text_elements(svg)
        if re.search(r"\bTable\s+E\d+[a-c]?\b", t)
    }
    assert offenders == {}
