"""Harvard citation cross-checker for an anchored Markdown chapter (stdlib only).

    python scripts/check_citations.py <markdown file> [--refs <references.md>]
                                      [--names-file <path>] [--every-mention]

Parses Harvard in-text citations — narrative ``Lees et al. (2022)``,
``Li, L.H. et al. (2019)``, ``Gorwa, Binns and Katzenbach (2020)``,
``Hanu and Unitary team (2020)`` — and parenthetical ones —
``(Borkan et al., 2019)``, ``(RapidAI, n.d.)``, ``(TensorFlow Hub, 2024)``,
``(Llama Team, AI@Meta, 2024)``,
``(European Parliament and Council, 2022; UK Parliament, 2023)`` — and the
reference list (lines tagged ``{Reference}`` in the docx mirror, or any
paragraph that starts ``Surname, I.`` / ``Organisation`` followed by
``(year)``). Every citation and every entry is reduced to the same key,
``(first author or organisation, year)``, so both sides compare like for like.

Three lists are printed, each with 1-indexed line numbers of the input file:

  cited-not-referenced        in-text citation with no reference-list entry
  referenced-not-cited        reference-list entry never cited in the file
  bare-name-without-citation  watch-list name (ViLBERT, YAMNet, DSA, ...) in a
                              sentence that carries no citation

Bare-name coverage is document-level by default: a name is reported only
when NO sentence in the file contains both the name and a citation (repeat
mentions after a cited first mention are not noise). ``--every-mention``
switches to the strict rule — every uncited sentence is reported.

``--names-file`` replaces the built-in watch-list: one name per line,
``#`` comments; an optional ``Name | Surname, YEAR`` mapping demands that
specific citation in the sentence rather than any citation.

Exit status: 0 all three lists empty, 1 any list non-empty, 2 usage error.
Read-only: the tool never edits its inputs.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

_YEAR = r"(?:\d{4}[a-z]?|n\.d\.)"
_PAREN_RE = re.compile(r"\(([^()]*?" + _YEAR + r")\)")
_PART_RE = re.compile(r"^(.+?),\s*(" + _YEAR + r")$")
_ANCHOR_RE = re.compile(r"\[[pt][0-9a-f]{1,8}(?:-\d+)?\]")
_TAG_RE = re.compile(r"\{[A-Za-z]+\}")
_ETAL_RE = re.compile(r"\s*\bet al\.?")
_INITIALS_RE = re.compile(r",?\s+(?:[A-Z]\.)+(?=[\s,]|$)")
_LEAD_RE = re.compile(r"^(?:see|see also|cf\.|e\.g\.|also|in|after|following)\s+", re.I)
_REF_HEAD_RE = re.compile(r"^(.+?)\s\((" + _YEAR + r")\)")
_REF_HEADING_RE = re.compile(r"^#+\s*(?:\[[^\]]+\]\s*)?(?:References|Bibliography)\b", re.I)
_PROTECT_RE = re.compile(
    r"\bet al\.|\bn\.d\.|\b(?:e\.g|i\.e|cf|vs|Fig|Figs|No|pp|Vol|etc|approx|ch|Ch)\."
    r"|(?:\b[A-Z]\.)+|\d+\.\d+"
)
_SENT_END_RE = re.compile(r"[.!?](?=\s|$)")
_DOT = "․"  # one-dot leader: same width as '.', never a sentence end

_ALLOW_LOWER = {"et", "al.", "and", "&", "team", "of", "the", "de", "van",
                "der", "von", "du", "da", "la", "le"}

DEFAULT_WATCH_LIST: tuple[str, ...] = (
    "ViLBERT", "VisualBERT", "Faster-RCNN", "MobileNet", "YAMNet", "GPT-4",
    "Llama", "toxic-bert", "Detoxify", "RapidOCR", "Civil Comments", "Memotion",
    "LibriSpeech", "ESC-50", "AudioSet", "Hateful Memes", "Perspective API",
    "Digital Services Act", "DSA", "Online Safety Act", "Ollama",
    "TensorFlow Hub",
)

Key = tuple[str, str]


@dataclass(frozen=True)
class Citation:
    key: Key
    text: str
    line: int
    start: int  # char offset in the (cleaned) line
    end: int


@dataclass(frozen=True)
class RefEntry:
    key: Key
    text: str
    line: int


@dataclass(frozen=True)
class BareName:
    name: str
    line: int
    sentence: str


@dataclass
class Report:
    cited_not_referenced: list[Citation] = field(default_factory=list)
    referenced_not_cited: list[RefEntry] = field(default_factory=list)
    bare_names: list[BareName] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    references: list[RefEntry] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.cited_not_referenced or self.referenced_not_cited
                    or self.bare_names)


# ---------------------------------------------------------------------------
# keys
# ---------------------------------------------------------------------------

def author_key(author: str) -> str:
    """Reduce an author phrase to its first surname / organisation, lowercased.

    'Lees et al.' -> 'lees'; 'Li, L.H. et al.' -> 'li';
    'Gorwa, R., Binns, R. and Katzenbach, C.' -> 'gorwa';
    'Hanu, L. and Unitary team' == 'Hanu and Unitary team' -> 'hanu';
    'Llama Team, AI@Meta' -> 'llama team'; 'RapidAI' -> 'rapidai'.
    """
    s = _LEAD_RE.sub("", author.strip())
    s = _ETAL_RE.sub("", s)
    s = _INITIALS_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip(" ,;")
    first = re.split(r",|\s+and\s+|\s*&\s*", s, maxsplit=1)[0].strip()
    return first.lower()


def _norm_year(year: str) -> str:
    return "n.d." if year.startswith("n.d") else year


def clean_line(line: str) -> str:
    """Drop mirror anchors ``[pXXXXXXXX]`` / ``[tXXXXXXXX]`` and ``{Style}`` tags."""
    return _TAG_RE.sub("", _ANCHOR_RE.sub("", line)).rstrip("\n")


# ---------------------------------------------------------------------------
# reference list
# ---------------------------------------------------------------------------

def parse_reference_line(line: str, lineno: int) -> Optional[RefEntry]:
    if line.lstrip().startswith(("#", "|", "-", "*", ">")):
        return None
    clean = clean_line(line).strip()
    if not clean or not clean[0].isupper():
        return None
    m = _REF_HEAD_RE.match(clean)
    if not m:
        return None
    head, year = m.group(1), m.group(2)
    # An entry head is an author list or organisation: it never contains a
    # sentence-final full stop before the year (paragraph prose does).
    if re.search(r"[a-z]\.\s+[A-Z]", head) and " et al" not in head:
        return None
    return RefEntry(key=(author_key(head), _norm_year(year)), text=clean, line=lineno)


def parse_references(lines: Iterable[str], *, tagged_only: bool = False) -> list[RefEntry]:
    """Parse reference entries from a references file or a chapter's tail.

    With ``tagged_only`` every ``{Reference}``-tagged line is an entry and
    untagged lines are ignored; otherwise every line after a References
    heading (or every eligible line when there is no heading) is tried.
    """
    entries: list[RefEntry] = []
    raw = list(lines)
    tagged = [i for i, ln in enumerate(raw) if "{Reference}" in ln]
    if tagged:
        for i in tagged:
            e = parse_reference_line(raw[i], i + 1)
            if e:
                entries.append(e)
        return entries
    if tagged_only:
        return entries
    start = 0
    for i, ln in enumerate(raw):
        if _REF_HEADING_RE.match(ln):
            start = i + 1
            break
    for i in range(start, len(raw)):
        e = parse_reference_line(raw[i], i + 1)
        if e:
            entries.append(e)
    return entries


def reference_line_numbers(lines: list[str]) -> set[int]:
    """0-based indices of lines that belong to the reference list (excluded from
    the in-text scan)."""
    idx = {i for i, ln in enumerate(lines) if "{Reference}" in ln}
    if idx:
        return idx
    for i, ln in enumerate(lines):
        if _REF_HEADING_RE.match(ln):
            return set(range(i, len(lines)))
    return set()


# ---------------------------------------------------------------------------
# in-text citations
# ---------------------------------------------------------------------------

def _is_name_token(tok: str) -> bool:
    if tok in _ALLOW_LOWER:
        return True
    t = tok.rstrip(",")
    if not t or t in _ALLOW_LOWER:
        return bool(t)
    if re.fullmatch(r"(?:[A-Z]\.)+", t):
        return True  # initials such as L.H. or J.
    if t.endswith("."):
        return False  # sentence-final word, e.g. 'approach.'
    return re.fullmatch(r"[A-Z][^\s|()\[\]{}]*", t) is not None


def _narrative_author(pre: str, year: str, refs: set[Key]) -> Optional[str]:
    """Walk back from ``Author phrase (year)`` over name-like tokens; prefer the
    longest suffix whose key is a known reference, else the whole phrase."""
    tokens = pre.rstrip().split()
    collected: list[str] = []
    for tok in reversed(tokens):
        if _is_name_token(tok):
            collected.append(tok)
        else:
            break
    collected.reverse()
    while collected and collected[0] in _ALLOW_LOWER:
        collected.pop(0)
    if not collected:
        return None
    for i in range(len(collected)):
        phrase = " ".join(collected[i:])
        if (author_key(phrase), year) in refs:
            return phrase
    return " ".join(collected)


def find_citations(line: str, lineno: int, refs: set[Key]) -> list[Citation]:
    """All Harvard citations on one (cleaned) line, with char spans."""
    found: list[Citation] = []
    for m in _PAREN_RE.finditer(line):
        inner = m.group(1).strip()
        parts = [p.strip() for p in inner.split(";") if p.strip()]
        parsed: list[tuple[str, str]] = []
        for part in parts:
            pm = _PART_RE.match(part)
            if pm:
                parsed.append((pm.group(1).strip(), pm.group(2)))
        if parsed and len(parsed) == len(parts):
            for author, year in parsed:
                found.append(Citation(
                    key=(author_key(author), _norm_year(year)),
                    text=f"{author}, {year}", line=lineno,
                    start=m.start(), end=m.end()))
            continue
        if re.fullmatch(_YEAR, inner):
            year = _norm_year(inner)
            author = _narrative_author(line[:m.start()], year, refs)
            if author:
                start = line.rfind(author, 0, m.start())
                found.append(Citation(
                    key=(author_key(author), year),
                    text=f"{author} ({inner})", line=lineno,
                    start=start if start >= 0 else m.start(), end=m.end()))
    return found


# ---------------------------------------------------------------------------
# sentences and watch-list names
# ---------------------------------------------------------------------------

def _protect(text: str) -> str:
    """Same-length copy with non-terminal full stops replaced by a leader dot."""
    out = list(text)
    for m in _PROTECT_RE.finditer(text):
        for i in range(m.start(), m.end()):
            if out[i] == ".":
                out[i] = _DOT
    return "".join(out)


def split_sentences(line: str) -> list[tuple[int, int]]:
    """Char spans of sentences on one line; table cells are separate sentences."""
    spans: list[tuple[int, int]] = []
    segments: list[tuple[int, int]] = []
    if line.lstrip().startswith("|"):
        pos = 0
        for cell in line.split("|"):
            segments.append((pos, pos + len(cell)))
            pos += len(cell) + 1
    else:
        segments.append((0, len(line)))
    for seg_start, seg_end in segments:
        protected = _protect(line[seg_start:seg_end])
        last = 0
        for m in _SENT_END_RE.finditer(protected):
            spans.append((seg_start + last, seg_start + m.end()))
            last = m.end()
        if protected[last:].strip():
            spans.append((seg_start + last, seg_end))
    return spans


def load_names_file(path: Path) -> dict[str, Optional[Key]]:
    names: dict[str, Optional[Key]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("#"):
            continue
        if "|" in ln:
            name, target = (s.strip() for s in ln.split("|", 1))
            tm = _PART_RE.match(target)
            names[name] = (author_key(tm.group(1)), _norm_year(tm.group(2))) if tm else None
        else:
            names[ln] = None
    return names


def _name_re(name: str) -> re.Pattern[str]:
    """Proper names match case-sensitively ('hateful memes' as a search term is
    not the benchmark); lowercase-styled names (toxic-bert) also match their
    sentence-initial capitalised form."""
    flags = re.I if name[:1].islower() else 0
    return re.compile(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", flags)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def check(md_lines: list[str], ref_lines: Optional[list[str]],
          names: Optional[dict[str, Optional[Key]]] = None,
          *, every_mention: bool = False) -> Report:
    names = names if names is not None else {n: None for n in DEFAULT_WATCH_LIST}
    if ref_lines is None:
        references = parse_references(md_lines)
        skip = reference_line_numbers(md_lines)
    else:
        references = parse_references(ref_lines)
        skip = reference_line_numbers(md_lines)
    ref_keys = {e.key for e in references}
    report = Report(references=references)

    covered: dict[str, bool] = {n: False for n in names}
    uncited_hits: list[BareName] = []
    name_res = {n: _name_re(n) for n in names}

    for i, raw in enumerate(md_lines):
        if i in skip or raw.lstrip().startswith("#"):
            continue
        line = clean_line(raw)
        cites = find_citations(line, i + 1, ref_keys)
        report.citations.extend(cites)
        for s, e in split_sentences(line):
            sentence = line[s:e]
            in_sent = [c for c in cites if c.start < e and c.end > s]
            for name, rx in name_res.items():
                if not rx.search(sentence):
                    continue
                target = names[name]
                cited_here = bool(in_sent) if target is None else any(
                    c.key == target for c in in_sent)
                if cited_here:
                    covered[name] = True
                else:
                    uncited_hits.append(BareName(name, i + 1, sentence.strip()))

    cited_keys = {c.key for c in report.citations}
    seen: set[tuple[Key, int]] = set()
    for c in report.citations:
        if c.key not in ref_keys and (c.key, c.line) not in seen:
            seen.add((c.key, c.line))
            report.cited_not_referenced.append(c)
    report.referenced_not_cited = [e for e in references if e.key not in cited_keys]
    report.bare_names = [h for h in uncited_hits
                         if every_mention or not covered[h.name]]
    return report


def format_report(report: Report, *, every_mention: bool = False) -> str:
    out: list[str] = []
    out.append(f"citations found: {len(report.citations)}; "
               f"reference entries: {len(report.references)}")
    out.append(f"== cited-not-referenced ({len(report.cited_not_referenced)}) ==")
    for c in report.cited_not_referenced:
        out.append(f"  line {c.line}: {c.text}  [key {c.key[0]!r}, {c.key[1]}]")
    out.append(f"== referenced-not-cited ({len(report.referenced_not_cited)}) ==")
    for e in report.referenced_not_cited:
        out.append(f"  refs line {e.line}: {e.text[:90]}  [key {e.key[0]!r}, {e.key[1]}]")
    mode = "every uncited mention" if every_mention else "names never cited in any sentence"
    out.append(f"== bare-name-without-citation ({len(report.bare_names)}; {mode}) ==")
    for b in report.bare_names:
        snippet = b.sentence if len(b.sentence) <= 110 else b.sentence[:107] + "..."
        out.append(f"  line {b.line}: {b.name}  | {snippet}")
    return "\n".join(out)


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("markdown", type=Path, help="chapter / document Markdown file")
    ap.add_argument("--refs", type=Path, default=None,
                    help="reference-list Markdown (default: parsed from the input file)")
    ap.add_argument("--names-file", type=Path, default=None,
                    help="watch-list file (one name per line; 'Name | Surname, YEAR' maps)")
    ap.add_argument("--every-mention", action="store_true",
                    help="report every uncited sentence, not only never-cited names")
    args = ap.parse_args(argv)
    for p in (args.markdown, args.refs, args.names_file):
        if p is not None and not p.is_file():
            print(f"error: not a file: {p}", file=sys.stderr)
            return 2
    names = load_names_file(args.names_file) if args.names_file else None
    report = check(_read_lines(args.markdown),
                   _read_lines(args.refs) if args.refs else None,
                   names, every_mention=args.every_mention)
    print(format_report(report, every_mention=args.every_mention))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
