"""Fast, offline tests for scripts/docx_to_md.py (stdlib docx -> anchored Markdown)."""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts"))

import docx_to_md  # noqa: E402

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.'
    'openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)


def _p(text: str, style: str | None = None) -> str:
    ppr = f"<w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>" if style else ""
    return f"<w:p>{ppr}<w:r><w:t>{text}</w:t></w:r></w:p>"


def _tbl(rows: list[list[str]]) -> str:
    trs = "".join(
        "<w:tr>" + "".join(f"<w:tc>{_p(c)}</w:tc>" for c in row) + "</w:tr>"
        for row in rows
    )
    return f"<w:tbl>{trs}</w:tbl>"


def _build_docx(path: Path) -> None:
    body = "".join(
        [
            _p("Abstract", "FrontMatterHeading"),
            _p("one two three"),  # front matter prose, must not count
            _p("Chapter 1: A", "Heading1"),
            _p("1.1 Sub", "Heading2"),
            _p("alpha beta gamma delta"),  # 4 prose words
            _p("Table 1.1. Caption words here.", "Caption"),  # excluded
            _tbl([["h1", "h2"], ["cell one", "cell two"]]),  # 6 table words
            _p("Chapter 2: B", "Heading1"),
            _p("epsilon zeta"),  # 2 prose words
            _p("References", "Heading1"),
            _p("Ref entry (2020).", "Reference"),
        ]
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{_W}"><w:body>{body}<w:sectPr/></w:body></w:document>'
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("word/document.xml", xml)


@pytest.fixture()
def mirror(tmp_path: Path) -> Path:
    docx = tmp_path / "mini.docx"
    _build_docx(docx)
    out = tmp_path / "out"
    assert docx_to_md.main([str(docx), "--out", str(out)]) == 0
    return out


def test_files_and_split(mirror: Path) -> None:
    for name in ("full.md", "frontmatter.md", "ch1.md", "ch2.md", "references.md", "wordcount.json"):
        assert (mirror / name).is_file(), name
    full = (mirror / "full.md").read_text(encoding="utf-8")
    assert full.startswith(docx_to_md.README_LINE)
    ch1 = (mirror / "ch1.md").read_text(encoding="utf-8")
    ch2 = (mirror / "ch2.md").read_text(encoding="utf-8")
    assert ch1.splitlines()[0].startswith("# [p") and ch1.splitlines()[0].endswith("Chapter 1: A")
    assert "## [p" in ch1 and "1.1 Sub" in ch1
    assert "{Caption} Table 1.1. Caption words here." in ch1
    assert "| h1 | h2 |" in ch1 and "| cell one | cell two |" in ch1
    assert ch2.splitlines()[0].endswith("Chapter 2: B")
    assert "epsilon zeta" in ch2 and "epsilon zeta" not in ch1
    fm = (mirror / "frontmatter.md").read_text(encoding="utf-8")
    assert "one two three" in fm and "Abstract" in fm
    refs = (mirror / "references.md").read_text(encoding="utf-8")
    assert "{Reference} Ref entry (2020)." in refs and "Ref entry" not in ch2


def test_anchor_is_stable_sha1_prefix(mirror: Path) -> None:
    ch1 = (mirror / "ch1.md").read_text(encoding="utf-8")
    expected = docx_to_md.anchor_for("alpha   beta gamma delta")  # whitespace-normalised
    assert f"[{expected}] alpha beta gamma delta" in ch1
    assert len(expected) == 9 and expected.startswith("p")


def test_wordcount_excludes_headings_captions_tables(mirror: Path) -> None:
    wc = json.loads((mirror / "wordcount.json").read_text(encoding="utf-8"))
    assert wc["chapters"]["ch1"]["prose_words"] == 4
    assert wc["chapters"]["ch1"]["prose_plus_table_words"] == 4 + 6
    assert wc["chapters"]["ch2"]["prose_words"] == 2
    assert wc["chapters"]["ch2"]["prose_plus_table_words"] == 2
    assert wc["totals"] == {"prose_words": 6, "prose_plus_table_words": 12}
    assert "frontmatter" not in wc["chapters"] and "references" not in wc["chapters"]
