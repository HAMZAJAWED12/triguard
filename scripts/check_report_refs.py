"""Check figure / table / screenshot / listing captions and cross-references in a .docx.

    python scripts/check_report_refs.py <path.docx> [--json] [--allow-ids E1 E9 ...]
                                        [--min-words 8]

Stdlib only (``zipfile`` + ``xml.etree``); no python-docx. The source document is
read-only and its path comes from the CLI only.

What is read
------------
* ``word/document.xml`` body: paragraphs and table cells in document order, each
  with its ``pStyle``. Text is *field-aware*: ``w:t`` runs inside a
  ``fldChar begin .. separate .. end`` field are read from the result part only,
  ``w:instrText`` is ignored, ``w:fldSimple`` results are kept. When any SEQ or
  REF field instruction exists the notice
  ``SEQ/REF fields present — update fields (F9) before checking`` is printed,
  because the cached field results are what this tool sees.
* ``word/header*.xml`` / ``word/footer*.xml``: scanned for caption-like paragraphs
  (warning only — a caption belongs in the body).

Caption detection
-----------------
``pStyle`` in {Caption, TableCaption, CodeCaption} OR the paragraph starts with
``^(Figure|Table|Screenshot|Listing)\\s+(S?\\d+(?:\\.\\d+)?)\\.\\s`` (an optional
``(left)``-style parenthetical may sit between the id and the full stop). Inside a
caption paragraph every ``Kind N.`` / ``Kind N (side).`` head is registered, so a
merged caption such as ``Screenshot S2 (left). ... Screenshot S3 (right). ...``
registers both ids and raises a ``merged-caption`` warning.

Front-matter lists (a FrontMatterHeading / Heading1 whose text starts with
``List of`` up to the next heading) are recorded separately as list entries and
excluded from the in-text counts.

In-text mentions
----------------
``\\b(Figure|Fig\\.|Table|Screenshot|Listing)s?\\s+(S?\\d+(?:\\.\\d+)?)(?:\\s*(?:and|,|-|–)\\s*(S?\\d+(?:\\.\\d+)?))*\\b``
with lists and ``a-b`` ranges expanded; only ids of the same shape as the first
id (dotted / plain / S-prefixed) are kept from the expansion so ``Figure 3, 455``
does not register a ``Figure 455``. Mentions inside caption paragraphs and
front-matter lists are not counted. Chapter detection uses Heading1 text
``^Chapter\\s+(\\d+)\\b``.

Checks (E = error, W = warning)
-------------------------------
E missing-reference     caption with zero body references
E dangling-reference    reference with no caption
E non-sequential        Figure / Listing global, Screenshot S-n, Table X.Y within
                        its chapter (Y restarts at 1 per chapter)
E chapter-mismatch      Table X.Y captioned under Chapter != X
E duplicate-caption     the same id captioned twice
E repo-only-id          ``Table E<digits>[a-c]`` (repo evidence-table ids) in body
                        text, unless listed in --allow-ids
W not-standalone        caption text after the number < --min-words words
W merged-caption        more than one caption head in one paragraph
W list-drift            front-matter list entry text != caption text (a trailing
                        page number on the entry is stripped first)
W list-entry-orphan     list entry with no matching body caption
W not-near-anchor       figure/screenshot caption not within 2 blocks of a
                        ``w:drawing``; table caption not within 2 blocks of a
                        ``w:tbl``
W caption-in-header     caption-like paragraph in a header/footer part
W unparsed-caption      caption-styled paragraph without a recognisable head

Output: one line per finding (level, code, kind id, anchor = first 6 words of
the paragraph, detail), then a summary line. Exit code 0 only with zero errors.
``--json`` prints the same as one JSON object instead.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


CAPTION_STYLES: frozenset[str] = frozenset({"Caption", "TableCaption", "CodeCaption"})
HEADING_STYLES: frozenset[str] = frozenset({"Heading1", "Title", "FrontMatterHeading"})
KINDS = ("Figure", "Table", "Screenshot", "Listing")

ID_PAT = r"S?\d+(?:\.\d+)?"
CAPTION_START_RE = re.compile(
    rf"^(Figure|Table|Screenshot|Listing)\s+({ID_PAT})(?:\s*\([^)]*\))?\.\s"
)
# a caption head: at paragraph start, or after a sentence end (merged captions)
CAPTION_HEAD_RE = re.compile(
    rf"(?:^|(?<=\.)\s+)(Figure|Table|Screenshot|Listing)\s+({ID_PAT})(?:\s*\([^)]*\))?\.(?=\s|$)"
)
MENTION_RE = re.compile(
    rf"\b(Figure|Fig\.|Table|Screenshot|Listing)s?\s+({ID_PAT})"
    rf"(?:\s*(?:and|,|-|–)\s*({ID_PAT}))*\b"
)
ID_ONLY_RE = re.compile(ID_PAT)
RANGE_SEP_RE = re.compile(rf"({ID_PAT})\s*[-–]\s*({ID_PAT})")
E_ID_RE = re.compile(r"\bTable\s+(E\d+[a-c]?)\b")
CHAPTER_RE = re.compile(r"^Chapter\s+(\d+)\b")
LIST_HEADING_RE = re.compile(r"^List\s+of\b", re.IGNORECASE)
SEQ_REF_RE = re.compile(r"^\s*(SEQ|REF)\b", re.IGNORECASE)
TRAILING_PAGE_RE = re.compile(r"\s+\d+$")


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
@dataclass
class Block:
    """One paragraph (body-level or table cell) or a table marker."""

    idx: int
    part: str  # "body" | header/footer part name
    kind: str  # "p" | "tbl"
    style: str = ""
    text: str = ""
    has_drawing: bool = False
    table_idx: int | None = None  # for cell paragraphs: index of the enclosing tbl block


@dataclass
class Caption:
    kind: str
    id: str
    text: str  # words after the head, up to the next head
    block: Block
    chapter: int | None
    in_list: bool


@dataclass
class Mention:
    kind: str
    id: str
    block: Block
    chapter: int | None


@dataclass
class Finding:
    level: str  # "error" | "warning"
    code: str
    kind: str
    id: str
    anchor: str
    detail: str

    def line(self) -> str:
        lvl = "ERROR" if self.level == "error" else "WARN "
        return f'{lvl} {self.code:<20} {self.kind} {self.id:<6} "{self.anchor}"  {self.detail}'


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
    captions: dict[str, list[str]] = field(default_factory=dict)
    references: dict[str, list[str]] = field(default_factory=dict)
    list_entries: dict[str, list[str]] = field(default_factory=dict)

    @property
    def n_errors(self) -> int:
        return sum(1 for f in self.findings if f.level == "error")

    @property
    def n_warnings(self) -> int:
        return sum(1 for f in self.findings if f.level == "warning")


# --------------------------------------------------------------------------- #
# XML reading
# --------------------------------------------------------------------------- #
def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def anchor_of(text: str, n: int = 6) -> str:
    return " ".join(text.split()[:n])


def paragraph_text(p: ET.Element) -> str:
    """Field-aware run text: skip instrText and the instruction part of complex fields."""
    parts: list[str] = []
    stack: list[str] = []  # "instr" | "result" per open complex field
    for el in p.iter():
        tag = el.tag
        if tag == _w("fldChar"):
            typ = el.get(_w("fldCharType"), "")
            if typ == "begin":
                stack.append("instr")
            elif typ == "separate" and stack:
                stack[-1] = "result"
            elif typ == "end" and stack:
                stack.pop()
        elif tag == _w("instrText"):
            continue
        elif tag == _w("t"):
            if stack and stack[-1] == "instr":
                continue
            parts.append(el.text or "")
        elif tag in (_w("tab"), _w("br"), _w("cr")):
            parts.append(" ")
    return normalise("".join(parts))


def paragraph_style(p: ET.Element) -> str:
    ps = p.find(f"{_w('pPr')}/{_w('pStyle')}")
    return ps.get(_w("val"), "") if ps is not None else ""


def has_drawing(el: ET.Element) -> bool:
    return el.find(f".//{_w('drawing')}") is not None or el.find(f".//{_w('pict')}") is not None


def field_instructions(root: ET.Element) -> list[str]:
    instr = [normalise(el.text or "") for el in root.iter(_w("instrText"))]
    instr += [normalise(el.get(_w("instr"), "")) for el in root.iter(_w("fldSimple"))]
    return [i for i in instr if i]


def iter_blocks(container: ET.Element, part: str, blocks: list[Block]) -> None:
    """Append body-level paragraphs, table markers and table-cell paragraphs in order."""
    for child in container:
        if child.tag == _w("p"):
            text = paragraph_text(child)
            drawing = has_drawing(child)
            if not text and not drawing:
                continue
            blocks.append(
                Block(len(blocks), part, "p", paragraph_style(child), text, drawing)
            )
        elif child.tag == _w("tbl"):
            marker = Block(len(blocks), part, "tbl", "", "", has_drawing(child))
            blocks.append(marker)
            for tc in child.iter(_w("tc")):
                for p in tc.iter(_w("p")):
                    text = paragraph_text(p)
                    if not text:
                        continue
                    blocks.append(
                        Block(
                            len(blocks),
                            part,
                            "p",
                            paragraph_style(p),
                            text,
                            has_drawing(p),
                            table_idx=marker.idx,
                        )
                    )
        elif child.tag in (_w("sdt"), _w("sdtContent")):
            iter_blocks(child, part, blocks)


def load_document(docx_path: Path) -> tuple[list[Block], list[Block], list[str]]:
    """Return (body blocks, header/footer blocks, field instructions)."""
    with zipfile.ZipFile(docx_path) as zf:
        names = set(zf.namelist())
        root = ET.fromstring(zf.read("word/document.xml"))
        body = root.find(_w("body"))
        if body is None:
            raise SystemExit("no <w:body> in word/document.xml")
        blocks: list[Block] = []
        iter_blocks(body, "body", blocks)
        instr = field_instructions(root)
        hf_blocks: list[Block] = []
        for name in sorted(names):
            if re.fullmatch(r"word/(header|footer)\d*\.xml", name):
                hf_root = ET.fromstring(zf.read(name))
                hf: list[Block] = []
                iter_blocks(hf_root, name, hf)
                hf_blocks.extend(hf)
                instr.extend(field_instructions(hf_root))
    return blocks, hf_blocks, instr


# --------------------------------------------------------------------------- #
# Parsing captions and mentions
# --------------------------------------------------------------------------- #
def id_shape(id_: str) -> str:
    if id_.startswith("S"):
        return "S"
    return "dotted" if "." in id_ else "plain"


def expand_ids(span: str) -> list[str]:
    """Ids in a mention span, ranges expanded, filtered to the first id's shape."""
    ids: list[str] = []
    for m in RANGE_SEP_RE.finditer(span):
        a, b = m.group(1), m.group(2)
        if id_shape(a) == id_shape(b) == "plain":
            ids.extend(str(i) for i in range(int(a), int(b) + 1))
        elif id_shape(a) == id_shape(b) == "S" and a[1:].isdigit() and b[1:].isdigit():
            ids.extend(f"S{i}" for i in range(int(a[1:]), int(b[1:]) + 1))
        elif id_shape(a) == id_shape(b) == "dotted":
            ca, ya = a.split(".")
            cb, yb = b.split(".")
            if ca == cb:
                ids.extend(f"{ca}.{i}" for i in range(int(ya), int(yb) + 1))
    for m in ID_ONLY_RE.finditer(span):
        if m.group(0) not in ids:
            ids.append(m.group(0))
    if not ids:
        return ids
    first = ids[0]
    return [i for i in ids if id_shape(i) == id_shape(first)]


def caption_heads(text: str) -> list[tuple[str, str, str]]:
    """[(kind, id, trailing text)] for every caption head in a paragraph."""
    heads = list(CAPTION_HEAD_RE.finditer(text))
    out: list[tuple[str, str, str]] = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out.append((m.group(1), m.group(2), text[m.end():end].strip()))
    return out


def mentions_in(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for m in MENTION_RE.finditer(text):
        kind = "Figure" if m.group(1) == "Fig." else m.group(1)
        for id_ in expand_ids(m.group(0)[m.end(1) - m.start():]):
            out.append((kind, id_))
    return out


def is_caption_block(b: Block) -> bool:
    return b.kind == "p" and (b.style in CAPTION_STYLES or bool(CAPTION_START_RE.match(b.text)))


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #
def analyse(
    blocks: list[Block],
    hf_blocks: list[Block],
    instr: list[str],
    allow_ids: set[str],
    min_words: int,
) -> Report:
    rep = Report()
    if any(SEQ_REF_RE.match(i) for i in instr):
        rep.notices.append("SEQ/REF fields present — update fields (F9) before checking")

    captions: list[Caption] = []
    list_entries: list[Caption] = []
    mentions: list[Mention] = []
    chapter: int | None = None
    in_list = False

    for b in blocks:
        if b.kind != "p":
            continue
        if b.style in HEADING_STYLES:
            m = CHAPTER_RE.match(b.text)
            if m:
                chapter = int(m.group(1))
            in_list = bool(LIST_HEADING_RE.match(b.text))
            continue
        if is_caption_block(b):
            heads = caption_heads(b.text)
            if not heads:
                rep.findings.append(
                    Finding("warning", "unparsed-caption", "-", "-", anchor_of(b.text),
                            "caption-styled paragraph without a 'Kind N.' head")
                )
                continue
            target = list_entries if in_list else captions
            for kind, id_, rest in heads:
                target.append(Caption(kind, id_, rest, b, chapter, in_list))
            if len(heads) > 1 and not in_list:
                rep.findings.append(
                    Finding("warning", "merged-caption", heads[0][0], heads[0][1],
                            anchor_of(b.text),
                            "one paragraph carries " + ", ".join(f"{k} {i}" for k, i, _ in heads)
                            + " — split into standalone captions")
                )
            continue
        if in_list:
            continue
        for kind, id_ in mentions_in(b.text):
            mentions.append(Mention(kind, id_, b, chapter))
        for m in E_ID_RE.finditer(b.text):
            eid = m.group(1)
            if eid in allow_ids:
                continue
            rep.findings.append(
                Finding("error", "repo-only-id", "Table", eid, anchor_of(b.text),
                        f"'{m.group(0)}' is a repository evidence-table id, not a report table")
            )

    # header / footer parts
    for b in hf_blocks:
        if is_caption_block(b):
            rep.findings.append(
                Finding("warning", "caption-in-header", "-", "-", anchor_of(b.text),
                        f"caption-like paragraph in {b.part}")
            )

    # inventories
    cap_by_key: dict[tuple[str, str], list[Caption]] = {}
    for c in captions:
        cap_by_key.setdefault((c.kind, c.id), []).append(c)
    ref_by_key: dict[tuple[str, str], list[Mention]] = {}
    for m in mentions:
        ref_by_key.setdefault((m.kind, m.id), []).append(m)
    for kind in KINDS:
        rep.captions[kind] = [c.id for c in captions if c.kind == kind]
        rep.references[kind] = sorted(
            {m.id for m in mentions if m.kind == kind}, key=_sort_key
        )
        rep.list_entries[kind] = [c.id for c in list_entries if c.kind == kind]

    # duplicates
    for (kind, id_), cs in cap_by_key.items():
        if len(cs) > 1:
            rep.findings.append(
                Finding("error", "duplicate-caption", kind, id_, anchor_of(cs[1].block.text),
                        f"captioned {len(cs)} times")
            )

    # missing / dangling
    for (kind, id_), cs in cap_by_key.items():
        if (kind, id_) not in ref_by_key:
            rep.findings.append(
                Finding("error", "missing-reference", kind, id_, anchor_of(cs[0].block.text),
                        "caption has no in-text reference")
            )
    for (kind, id_), ms in ref_by_key.items():
        if (kind, id_) not in cap_by_key:
            rep.findings.append(
                Finding("error", "dangling-reference", kind, id_, anchor_of(ms[0].block.text),
                        f"referenced {len(ms)}x but never captioned")
            )

    # sequence
    expected_global: dict[str, int] = {"Figure": 1, "Listing": 1, "Screenshot": 1}
    expected_table: dict[int, int] = {}
    for c in captions:
        anchor = anchor_of(c.block.text)
        if c.kind == "Table":
            if "." not in c.id:
                rep.findings.append(
                    Finding("error", "non-sequential", c.kind, c.id, anchor,
                            "table ids are chapter-scoped X.Y")
                )
                continue
            ch_s, y_s = c.id.split(".", 1)
            ch = int(ch_s)
            if c.chapter is not None and ch != c.chapter:
                rep.findings.append(
                    Finding("error", "chapter-mismatch", c.kind, c.id, anchor,
                            f"captioned under Chapter {c.chapter}")
                )
            exp = expected_table.get(ch, 1)
            if int(y_s) != exp:
                rep.findings.append(
                    Finding("error", "non-sequential", c.kind, c.id, anchor,
                            f"expected Table {ch}.{exp}")
                )
            expected_table[ch] = int(y_s) + 1
        else:
            num_s = c.id[1:] if c.kind == "Screenshot" and c.id.startswith("S") else c.id
            if c.kind == "Screenshot" and not c.id.startswith("S"):
                rep.findings.append(
                    Finding("error", "non-sequential", c.kind, c.id, anchor,
                            "screenshot ids are S-n")
                )
            if not num_s.isdigit():
                rep.findings.append(
                    Finding("error", "non-sequential", c.kind, c.id, anchor, "non-integer id")
                )
                continue
            exp = expected_global[c.kind]
            if int(num_s) != exp:
                prefix = "S" if c.kind == "Screenshot" else ""
                rep.findings.append(
                    Finding("error", "non-sequential", c.kind, c.id, anchor,
                            f"expected {c.kind} {prefix}{exp}")
                )
            expected_global[c.kind] = int(num_s) + 1

    # standalone
    for c in captions:
        n = len(c.text.split())
        if n < min_words:
            rep.findings.append(
                Finding("warning", "not-standalone", c.kind, c.id, anchor_of(c.block.text),
                        f"{n} words after the number (< {min_words})")
            )

    # list drift / orphans
    for e in list_entries:
        cs = cap_by_key.get((e.kind, e.id))
        if not cs:
            rep.findings.append(
                Finding("warning", "list-entry-orphan", e.kind, e.id, anchor_of(e.block.text),
                        "front-matter list entry has no body caption")
            )
            continue
        entry = TRAILING_PAGE_RE.sub("", normalise(e.block.text))
        if entry != normalise(cs[0].block.text):
            rep.findings.append(
                Finding("warning", "list-drift", e.kind, e.id, anchor_of(e.block.text),
                        "front-matter list text differs from the body caption")
            )

    # anchor proximity
    by_idx = {b.idx: b for b in blocks}
    for c in captions:
        if c.kind == "Listing":
            continue
        centres = [c.block.idx]
        if c.block.table_idx is not None:
            centres.append(c.block.table_idx)
        near = False
        for centre in centres:
            for i in range(centre - 2, centre + 3):
                nb = by_idx.get(i)
                if nb is None:
                    continue
                if c.kind == "Table" and nb.kind == "tbl":
                    near = True
                if c.kind in ("Figure", "Screenshot") and nb.has_drawing:
                    near = True
        if not near:
            what = "w:tbl" if c.kind == "Table" else "w:drawing"
            rep.findings.append(
                Finding("warning", "not-near-anchor", c.kind, c.id, anchor_of(c.block.text),
                        f"no {what} within 2 blocks of the caption")
            )

    rep.findings.sort(key=lambda f: (f.level != "error", f.code, f.kind, _sort_key(f.id)))
    return rep


def _sort_key(id_: str) -> tuple:
    s = id_[1:] if id_.startswith("S") else id_
    try:
        return tuple(int(x) for x in s.split("."))
    except ValueError:
        return (10**9, id_)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def summary_line(rep: Report) -> str:
    caps = ", ".join(f"{k} {len(v)}" for k, v in rep.captions.items())
    refs = ", ".join(f"{k} {len(v)}" for k, v in rep.references.items())
    lists = ", ".join(f"{k} {len(v)}" for k, v in rep.list_entries.items() if v)
    return (
        f"summary: {rep.n_errors} errors, {rep.n_warnings} warnings; "
        f"captions: {caps}; referenced ids: {refs}; front-matter list entries: {lists or 'none'}"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("docx", type=Path, help="source .docx (read-only)")
    ap.add_argument("--json", action="store_true", help="print one JSON object instead of lines")
    ap.add_argument("--allow-ids", nargs="*", default=[], metavar="ID",
                    help="repo evidence-table ids (E1, E4b, ...) allowed in body text")
    ap.add_argument("--min-words", type=int, default=8,
                    help="minimum words after the number for a standalone caption (default 8)")
    args = ap.parse_args(argv)
    try:  # Windows consoles may default to a non-UTF-8 code page
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    if not args.docx.is_file():
        print(f"not a file: {args.docx}", file=sys.stderr)
        return 2
    blocks, hf_blocks, instr = load_document(args.docx)
    rep = analyse(blocks, hf_blocks, instr, set(args.allow_ids), args.min_words)
    if args.json:
        print(json.dumps({
            "notices": rep.notices,
            "findings": [asdict(f) for f in rep.findings],
            "captions": rep.captions,
            "references": rep.references,
            "list_entries": rep.list_entries,
            "n_errors": rep.n_errors,
            "n_warnings": rep.n_warnings,
        }, indent=2, ensure_ascii=False))
    else:
        for n in rep.notices:
            print(f"NOTICE {n}")
        for f in rep.findings:
            print(f.line())
        print(summary_line(rep))
    return 0 if rep.n_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
