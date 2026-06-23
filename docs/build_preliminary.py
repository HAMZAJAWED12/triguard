"""
Build TriGuard Preliminary Report (single PDF, 4 chapters, title page + ToC + references).
"""
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
OUT = HERE / "TriGuard_Preliminary_Report.pdf"


def strip_yaml_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5:].lstrip()
    return text


def strip_section(text: str, header_re: str) -> str:
    """Cut from `# header_re` until end of file (or next top-level marker)."""
    m = re.search(header_re, text, flags=re.MULTILINE)
    if not m:
        return text
    return text[: m.start()].rstrip() + "\n"


def renumber_top_headings(text: str, ch: int) -> str:
    """Rewrite '# 1.', '# 2.' ... in standalone chapter files to '## <ch>.N'.
    Standalone files use '# N. Title' as their section headers; in the combined
    report we want the chapter to be a single top-level heading and the sections
    to drop one level."""
    out_lines: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^# (\d+)\.\s+(.+)$", line)
        if m:
            n, title = m.groups()
            out_lines.append(f"## {ch}.{n} {title}")
        else:
            out_lines.append(line)
    return "\n".join(out_lines)


def main() -> int:
    ch1 = (HERE / "chapter1_introduction.md").read_text(encoding="utf-8")
    ch2 = (HERE / "literature_review_draft.md").read_text(encoding="utf-8")
    ch3 = (HERE / "project_design_draft.md").read_text(encoding="utf-8")
    ch4 = (HERE / "chapter4_prototype.md").read_text(encoding="utf-8")

    ch2 = strip_yaml_frontmatter(ch2)
    ch3 = strip_yaml_frontmatter(ch3)

    # Strip the standalone reference sections from Ch2 and Ch3 — refs go at the end of the report.
    ch2 = strip_section(ch2, r"^# 11\. References")
    ch3 = strip_section(ch3, r"^# 14\. References")

    # Convert standalone numeric headings to chapter-scoped ones.
    ch2 = renumber_top_headings(ch2, 2)
    ch3 = renumber_top_headings(ch3, 3)

    # Build references section (deduplicated; Lazar from Ch3 included).
    refs = """
# References

Gemmeke, J.F., Ellis, D.P.W., Freedman, D., Jansen, A., Lawrence, W., Moore, R.C., Plakal, M. and Ritter, M. (2017) 'Audio Set: An ontology and human-labeled dataset for audio events', *Proceedings of the 2017 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)*. New Orleans: IEEE, pp. 776–780. https://doi.org/10.1109/ICASSP.2017.7952261

Gorwa, R., Binns, R. and Katzenbach, C. (2020) 'Algorithmic content moderation: Technical and political challenges in the automation of platform governance', *Big Data & Society*, 7(1), pp. 1–15. https://doi.org/10.1177/2053951719897945

Kiela, D., Firooz, H., Mohan, A., Goswami, V., Singh, A., Ringshia, P. and Testuggine, D. (2020) 'The Hateful Memes Challenge: Detecting hate speech in multimodal memes', in *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)*. La Jolla: NeurIPS Foundation, pp. 2611–2624. arXiv:2005.04790.

Lazar, J. (2023) 'A framework for born-accessible development of software and digital content', in *Human-Computer Interaction – INTERACT 2023*. Lecture Notes in Computer Science, vol. 14145. Cham: Springer, pp. 333–338.

Lees, A., Tran, V.Q., Tay, Y., Sorensen, J., Gupta, J., Metzler, D. and Vasserman, L. (2022) 'A new generation of Perspective API: Efficient multilingual character-level transformers', *Proceedings of the 28th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD '22)*. New York: ACM, pp. 3197–3207. https://doi.org/10.1145/3534678.3539147

Li, J., Li, D., Xiong, C. and Hoi, S. (2022) 'BLIP: Bootstrapping language–image pre-training for unified vision–language understanding and generation', in *Proceedings of the 39th International Conference on Machine Learning (ICML 2022)*. PMLR vol. 162, pp. 12888–12900. arXiv:2201.12086.

Li, L.H., Yatskar, M., Yin, D., Hsieh, C.J. and Chang, K.W. (2019) 'VisualBERT: A simple and performant baseline for vision and language', *arXiv preprint* arXiv:1908.03557.

Radford, A., Kim, J.W., Xu, T., Brockman, G., McLeavey, C. and Sutskever, I. (2023) 'Robust speech recognition via large-scale weak supervision', in *Proceedings of the 40th International Conference on Machine Learning (ICML 2023)*. PMLR vol. 202, pp. 28492–28518. arXiv:2212.04356.

Zheng, L., Chiang, W.L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E.P., Zhang, H., Gonzalez, J.E. and Stoica, I. (2023) 'Judging LLM-as-a-judge with MT-Bench and Chatbot Arena', in *Advances in Neural Information Processing Systems 36 (NeurIPS 2023)*. La Jolla: NeurIPS Foundation. arXiv:2306.05685.
""".strip()

    # Wrap chapters: each chapter file's top heading is renamed to be `# Chapter N — Title`.
    ch1 = ch1.replace("# Chapter 1 — Introduction", "# Chapter 1 — Introduction", 1)
    ch2 = "# Chapter 2 — Literature Review\n\n" + ch2
    ch3 = "# Chapter 3 — Project Design\n\n" + ch3
    # ch4 already starts with `# Chapter 4 — Feature Prototype`.

    yaml = (
        "---\n"
        "title: 'Preliminary Project Report — TriGuard'\n"
        "subtitle: 'A Multimodal Explainable Content-Moderation Pipeline'\n"
        "author: 'Hamza — BSc Computer Science, University of London'\n"
        "date: 'June 2026'\n"
        "geometry: margin=2cm\n"
        "fontsize: 11pt\n"
        "mainfont: 'Liberation Serif'\n"
        "colorlinks: true\n"
        "linkcolor: 'blue'\n"
        "urlcolor: 'blue'\n"
        "toc: true\n"
        "toc-depth: 2\n"
        "numbersections: false\n"
        "---\n\n"
    )

    body = "\n\n".join([ch1, ch2, ch3, ch4, refs])

    combined = (HERE / "_preliminary_combined.md")
    combined.write_text(yaml + body, encoding="utf-8")

    # Strip null bytes if any
    raw = combined.read_bytes()
    combined.write_bytes(raw.replace(b"\x00", b""))

    cmd = [
        "pandoc",
        str(combined),
        "-o", str(OUT),
        "--pdf-engine=xelatex",
        "-V", "papersize=a4",
        "-V", "geometry:margin=2cm",
        "-V", "fontsize=11pt",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr[-800:] if res.stderr else "")
    if res.returncode != 0:
        return res.returncode
    print(f"OK  {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
