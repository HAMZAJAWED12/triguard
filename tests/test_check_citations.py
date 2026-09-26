"""Fast, offline tests for scripts/check_citations.py (Harvard citation cross-check)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts"))

import check_citations as cc  # noqa: E402

# 20-line chapter fixture in the docx-mirror format: anchors, a table, an
# organisation author (Hanu and Unitary team; Llama Team, AI@Meta; European
# Parliament and Council; Ollama n.d.), a ghost citation (Nobody et al., 2001)
# and two bare watch-list names (VisualBERT line 7, toxic-bert line 20).
_CHAPTER = """# [pa4bd7f84] Chapter 9: Fixture

## [p11111111] 9.1 Text

[p22222222] Lees et al. (2022) describe a text service. The Detoxify weights come from an organisation (Hanu and Unitary team, 2020).

[p33333333] VisualBERT represents the fusion approach. Li, L.H. et al. (2019) combine words with Faster-RCNN regions.

[p44444444] The judge runs through a local server (Ollama, n.d.; Llama Team, AI@Meta, 2024).

[p55555555] Gorwa, Binns and Katzenbach (2020) argue for governance. Article 17 of the Digital Services Act applies (European Parliament and Council, 2022).

[p66666666] A ghost citation appears here (Nobody et al., 2001).

[t77777777]
| Source | Role |
|---|---|
| Kiela et al. (2020) | Benchmark |

[p88888888] Toxic-bert has six heads, e.g. threat and insult, at 0.5 recall."""

_REFS = """# [p5d20d0fe] References

[p1] {Reference} European Parliament and Council (2022) Regulation (EU) 2022/2065 (Digital Services Act). Official Journal, L 277.

[p2] {Reference} Gorwa, R., Binns, R. and Katzenbach, C. (2020) 'Algorithmic content moderation', Big Data & Society, 7(1), pp. 1-15.

[p3] {Reference} Hanu, L. and Unitary team (2020) Detoxify: Trained models and code. Available at: https://example.invalid (Accessed: 1 January 2026).

[p4] {Reference} Kiela, D., Firooz, H. and Testuggine, D. (2020) 'The Hateful Memes Challenge', in Advances in Neural Information Processing Systems, 33.

[p5] {Reference} Lazar, J. (2023) 'A framework for born-accessible development', in INTERACT 2023. Cham: Springer, pp. 333-338.

[p6] {Reference} Lees, A., Tran, V.Q. and Vasserman, L. (2022) 'A new generation of Perspective API', in Proceedings of KDD. New York: ACM.

[p7] {Reference} Li, L.H., Yatskar, M. and Chang, K.W. (2019) 'VisualBERT: A simple and performant baseline', arXiv preprint, arXiv:1908.03557.

[p8] {Reference} Llama Team, AI@Meta (2024) 'The Llama 3 herd of models', arXiv preprint, arXiv:2407.21783.

[p9] {Reference} Ollama (n.d.) Ollama. Available at: https://example.invalid (Accessed: 1 January 2026).
"""


@pytest.fixture()
def fixture_files(tmp_path: Path) -> tuple[Path, Path]:
    md = tmp_path / "ch9.md"
    refs = tmp_path / "references.md"
    md.write_text(_CHAPTER, encoding="utf-8")
    refs.write_text(_REFS, encoding="utf-8")
    assert len(_CHAPTER.splitlines()) == 20
    return md, refs


def test_author_key_normalises_persons_and_organisations() -> None:
    assert cc.author_key("Lees et al.") == "lees"
    assert cc.author_key("Li, L.H. et al.") == "li"
    assert cc.author_key("Gorwa, R., Binns, R. and Katzenbach, C.") == "gorwa"
    assert cc.author_key("Gorwa, Binns and Katzenbach") == "gorwa"
    assert cc.author_key("Hanu, L. and Unitary team") == cc.author_key("Hanu and Unitary team")
    assert cc.author_key("Llama Team, AI@Meta") == "llama team"
    assert cc.author_key("European Parliament and Council") == "european parliament"
    assert cc.author_key("RapidAI") == "rapidai"


def test_three_lists_on_fixture(fixture_files: tuple[Path, Path]) -> None:
    md, refs = fixture_files
    report = cc.check(md.read_text(encoding="utf-8").splitlines(),
                      refs.read_text(encoding="utf-8").splitlines())
    cited = {c.key for c in report.citations}
    # organisation authors, n.d., 'et al.', 'and', initials, table cell
    for key in [("hanu", "2020"), ("llama team", "2024"), ("ollama", "n.d."),
                ("european parliament", "2022"), ("lees", "2022"), ("li", "2019"),
                ("gorwa", "2020"), ("kiela", "2020"), ("nobody", "2001")]:
        assert key in cited, key
    assert [(c.key, c.line) for c in report.cited_not_referenced] == [(("nobody", "2001"), 13)]
    assert [(e.key, e.line) for e in report.referenced_not_cited] == [(("lazar", "2023"), 11)]
    bare = {(b.name, b.line) for b in report.bare_names}
    assert bare == {("VisualBERT", 7), ("toxic-bert", 20)}
    assert not report.ok


def test_sentence_protection_and_document_coverage(fixture_files: tuple[Path, Path]) -> None:
    md, refs = fixture_files
    lines = md.read_text(encoding="utf-8").splitlines()
    # 'e.g.' and '0.5' do not split line 20 into several sentences
    assert len(cc.split_sentences(cc.clean_line(lines[19]))) == 1
    # Faster-RCNN shares a sentence with Li, L.H. et al. (2019) -> covered
    report = cc.check(lines, refs.read_text(encoding="utf-8").splitlines())
    assert "Faster-RCNN" not in {b.name for b in report.bare_names}
    # strict mode reports every uncited sentence; it keeps the two bare names
    strict = cc.check(lines, refs.read_text(encoding="utf-8").splitlines(), every_mention=True)
    assert {b.name for b in strict.bare_names} >= {"VisualBERT", "toxic-bert"}
    # proper names are case-sensitive: a lowercase search term is not a mention
    term = cc.check(["[p1] Search terms included hateful memes and llama farming."], [])
    assert term.bare_names == []


def test_names_file_mapping_demands_specific_citation(fixture_files: tuple[Path, Path], tmp_path: Path) -> None:
    md, refs = fixture_files
    names_file = tmp_path / "names.txt"
    names_file.write_text("# custom list\nFaster-RCNN | Ren, 2015\nDetoxify\n", encoding="utf-8")
    names = cc.load_names_file(names_file)
    assert names == {"Faster-RCNN": ("ren", "2015"), "Detoxify": None}
    report = cc.check(md.read_text(encoding="utf-8").splitlines(),
                      refs.read_text(encoding="utf-8").splitlines(), names)
    assert {(b.name, b.line) for b in report.bare_names} == {("Faster-RCNN", 7)}


def test_main_exit_codes(fixture_files: tuple[Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    md, refs = fixture_files
    assert cc.main([str(md), "--refs", str(refs)]) == 1
    out = capsys.readouterr().out
    assert "== cited-not-referenced (1) ==" in out
    assert "== referenced-not-cited (1) ==" in out
    assert "== bare-name-without-citation (2;" in out
    # clean document with an in-file reference list -> 0
    clean = tmp_path / "clean.md"
    clean.write_text(
        "[p1] A sentence with a source (Ollama, n.d.).\n\n# References\n\n"
        "Ollama (n.d.) Ollama. Available at: https://example.invalid.\n",
        encoding="utf-8")
    assert cc.main([str(clean)]) == 0
    assert cc.main([str(tmp_path / "missing.md")]) == 2
