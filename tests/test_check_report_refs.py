"""Fast, offline tests for scripts/check_report_refs.py.

Each test builds a minimal .docx in ``tmp_path`` (``[Content_Types].xml``,
``_rels/.rels``, ``word/document.xml``, ``word/styles.xml``) with the stdlib and
runs the checker's ``main`` on it. No python-docx, no network.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

_REPO = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO / "scripts" / "check_report_refs.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_report_refs", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod  # dataclasses resolve postponed annotations via sys.modules
    spec.loader.exec_module(mod)
    return mod


crr = _load_module()

_CT = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    "</Types>"
)
_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    "</Relationships>"
)
_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    + "".join(
        f'<w:style w:type="paragraph" w:styleId="{s}"><w:name w:val="{s}"/></w:style>'
        for s in ("Heading1", "FrontMatterHeading", "Caption", "TableCaption", "CodeCaption", "TableSource")
    )
    + "</w:styles>"
)
_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _p(text: str, style: str = "", drawing: bool = False, raw_runs: str | None = None) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    runs = raw_runs if raw_runs is not None else f"<w:r><w:t>{escape(text)}</w:t></w:r>"
    if drawing:
        runs = "<w:r><w:drawing/></w:r>" + runs
    return f"<w:p>{ppr}{runs}</w:p>"


def _tbl(rows: list[list[str]]) -> str:
    body = "".join(
        "<w:tr>" + "".join(f"<w:tc>{_p(c)}</w:tc>" for c in r) + "</w:tr>" for r in rows
    )
    return f"<w:tbl>{body}</w:tbl>"


def _field(instr: str, result: str) -> str:
    """A complex field: begin / instrText / separate / cached result / end."""
    return (
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        f"<w:r><w:instrText>{escape(instr)}</w:instrText></w:r>"
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        f"<w:r><w:t>{escape(result)}</w:t></w:r>"
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    )


def _write_docx(path: Path, body_xml: str, extra: dict[str, str] | None = None) -> Path:
    doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:document {_W}><w:body>{body_xml}<w:sectPr/></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", _CT)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("word/document.xml", doc)
        zf.writestr("word/styles.xml", _STYLES)
        for name, xml in (extra or {}).items():
            zf.writestr(name, xml)
    return path


LONG = "a standalone caption sentence long enough to pass the eight word floor"


def _run(capsys, path: Path, *extra: str) -> tuple[int, dict]:
    code = crr.main([str(path), "--json", *extra])
    out = json.loads(capsys.readouterr().out)
    return code, out


def _codes(out: dict) -> set[tuple[str, str, str]]:
    return {(f["code"], f["kind"], f["id"]) for f in out["findings"]}


# --------------------------------------------------------------------------- #
def test_missing_duplicate_and_repo_id_are_errors(tmp_path, capsys):
    body = "".join([
        _p("Chapter 1: Fixture", "Heading1"),
        _p("Figure 1 shows the pipeline; Table 1.1 and Table 1.2 list the parts."),
        _p("", drawing=True),
        _p(f"Figure 1. {LONG}.", "Caption"),
        _p("", drawing=True),
        _p(f"Figure 2. {LONG}.", "Caption"),  # never referenced
        _p(f"Table 1.1. {LONG}.", "TableCaption"),
        _tbl([["a", "b"], ["1", "2"]]),
        _p(f"Table 1.1. {LONG} again.", "TableCaption"),  # duplicate; 1.2 never captioned
        _tbl([["a", "b"], ["1", "2"]]),
        _p("Source: run 20260705-111002, Table E4b.", "TableSource"),
    ])
    path = _write_docx(tmp_path / "bad.docx", body)
    code, out = _run(capsys, path)
    codes = _codes(out)
    assert ("missing-reference", "Figure", "2") in codes
    assert ("dangling-reference", "Table", "1.2") in codes
    assert ("duplicate-caption", "Table", "1.1") in codes
    assert ("repo-only-id", "Table", "E4b") in codes
    # the duplicate 1.1 also breaks the per-chapter sequence (expected 1.2)
    assert ("non-sequential", "Table", "1.1") in codes
    assert code == 1
    assert out["n_errors"] >= 4
    anchors = {f["anchor"] for f in out["findings"] if f["code"] == "repo-only-id"}
    assert anchors == {"Source: run 20260705-111002, Table E4b."}


def test_allow_ids_suppresses_repo_id_error(tmp_path, capsys):
    body = "".join([
        _p("Chapter 1: Fixture", "Heading1"),
        _p("Table 1.1 lists the parts."),
        _p(f"Table 1.1. {LONG}.", "TableCaption"),
        _tbl([["a"], ["1"]]),
        _p("Source: Table E4b.", "TableSource"),
    ])
    path = _write_docx(tmp_path / "allow.docx", body)
    code, out = _run(capsys, path)
    assert code == 1 and ("repo-only-id", "Table", "E4b") in _codes(out)
    code, out = _run(capsys, path, "--allow-ids", "E4b")
    assert code == 0 and out["n_errors"] == 0


def test_clean_document_exits_zero(tmp_path, capsys):
    body = "".join([
        _p("Chapter 2: Fixture", "Heading1"),
        _p("Figure 1 and Listing 1 are shown; see Table 2.1 and Screenshots S1 and S2."),
        _p("", drawing=True),
        _p(f"Figure 1. {LONG}.", "Caption"),
        _p(f"Table 2.1. {LONG}.", "TableCaption"),
        _tbl([["a"], ["1"]]),
        _p(f"Listing 1. {LONG}.", "CodeCaption"),
        _p("", drawing=True),
        _p(f"Screenshot S1. {LONG}.", "Caption"),
        _p("", drawing=True),
        _p(f"Screenshot S2. {LONG}.", "Caption"),
    ])
    path = _write_docx(tmp_path / "clean.docx", body)
    code, out = _run(capsys, path)
    assert code == 0 and out["findings"] == []
    assert out["captions"] == {"Figure": ["1"], "Table": ["2.1"], "Screenshot": ["S1", "S2"], "Listing": ["1"]}


def test_merged_caption_registers_both_ids_and_warns(tmp_path, capsys):
    body = "".join([
        _p("Chapter 4: Fixture", "Heading1"),
        _p("Screenshots S1-S3 show the surfaces."),
        _p("", drawing=True),
        _p(f"Screenshot S1. {LONG}.", "Caption"),
        _p("", drawing=True),
        _p(f"Screenshot S2 (left). {LONG}. Screenshot S3 (right). {LONG}.", "Caption"),
    ])
    path = _write_docx(tmp_path / "merged.docx", body)
    code, out = _run(capsys, path)
    assert out["captions"]["Screenshot"] == ["S1", "S2", "S3"]
    assert out["references"]["Screenshot"] == ["S1", "S2", "S3"]  # range expanded
    assert ("merged-caption", "Screenshot", "S2") in _codes(out)
    assert code == 0  # a merged caption is a warning, not an error


def test_front_matter_list_is_separate_and_drift_is_flagged(tmp_path, capsys):
    body = "".join([
        _p("List of Figures", "FrontMatterHeading"),
        _p(f"Figure 1. {LONG}. 12"),           # page number stripped -> no drift
        _p(f"Figure 2. {LONG} but reworded. 13"),  # drift
        _p("Chapter 1: Fixture", "Heading1"),
        _p("Figure 1 and Figure 2 are shown."),
        _p("", drawing=True),
        _p(f"Figure 1. {LONG}.", "Caption"),
        _p("", drawing=True),
        _p(f"Figure 2. {LONG}.", "Caption"),
    ])
    path = _write_docx(tmp_path / "lists.docx", body)
    code, out = _run(capsys, path)
    assert code == 0
    assert out["list_entries"]["Figure"] == ["1", "2"]
    assert out["captions"]["Figure"] == ["1", "2"]  # list entries not double-counted
    assert ("list-drift", "Figure", "2") in _codes(out)
    assert ("list-drift", "Figure", "1") not in _codes(out)


def test_field_results_are_read_and_seq_notice_is_printed(tmp_path, capsys):
    caption_runs = (
        "<w:r><w:t xml:space=\"preserve\">Figure </w:t></w:r>"
        + _field(" SEQ Figure \\* ARABIC ", "1")
        + f"<w:r><w:t xml:space=\"preserve\">. {LONG}.</w:t></w:r>"
    )
    ref_runs = (
        "<w:r><w:t xml:space=\"preserve\">As </w:t></w:r>"
        + _field(" REF _Ref1 \\h ", "Figure 1")
        + "<w:r><w:t xml:space=\"preserve\"> shows.</w:t></w:r>"
    )
    body = "".join([
        _p("Chapter 1: Fixture", "Heading1"),
        _p("", raw_runs=ref_runs),
        _p("", drawing=True),
        _p("", "Caption", raw_runs=caption_runs),
    ])
    path = _write_docx(tmp_path / "fields.docx", body)
    code, out = _run(capsys, path)
    assert code == 0 and out["findings"] == []
    assert out["captions"]["Figure"] == ["1"] and out["references"]["Figure"] == ["1"]
    assert out["notices"] == ["SEQ/REF fields present — update fields (F9) before checking"]


def test_header_caption_and_missing_anchor_are_warnings(tmp_path, capsys):
    header = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:hdr {_W}>{_p(f'Figure 9. {LONG}.', 'Caption')}</w:hdr>"
    )
    body = "".join([
        _p("Chapter 1: Fixture", "Heading1"),
        _p("Table 1.1 is far from its table."),
        _p(f"Table 1.1. {LONG}.", "TableCaption"),
        _p("filler one"),
        _p("filler two"),
        _p("filler three"),
        _tbl([["a"], ["1"]]),
    ])
    path = _write_docx(tmp_path / "hdr.docx", body, extra={"word/header1.xml": header})
    code, out = _run(capsys, path)
    assert code == 0
    codes = {f["code"] for f in out["findings"]}
    assert codes == {"caption-in-header", "not-near-anchor"}
    assert out["captions"]["Figure"] == []  # header caption is not a body caption
