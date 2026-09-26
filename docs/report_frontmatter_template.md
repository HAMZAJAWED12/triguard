# Front-matter templates (fill the [brackets]; paste into the report document)

## Title page

---

**TriGuard: An Explainable, Locally Deployable Multimodal
Content-Moderation Pipeline Orchestrating Pre-Trained Text, Image and
Audio Models with a Local LLM Judge**

CM3070 Computer Science Final Project — Draft Report

Template: CM3020 Artificial Intelligence — Project Idea 1:
*Orchestrating AI Models to Achieve a Goal*

[Your full name]
Student number: [SRN]
University of London — BSc Computer Science

[Month Year of submission]

Word count: [fill after final count — prose only; tables, figures,
captions, references and this page excluded]

---

## Declaration of AI use (REQUIRED — UoL Generative AI policy: "declare how and where"; word it yourself, these are the facts)

Facts to cover, in your own sentences:

- Generative AI (Anthropic Claude, via Claude Code) was used, under my
  direction, to assist development of the project's source code: model
  wrapper integration, the orchestrator, the judge integration and its
  streaming variant, the FastAPI demo surface, the evaluation harnesses
  (tracks T1–T8) and the automated test suite. Design decisions and their
  rationale are logged in the repository's DECISIONS.md.
- All evaluation figures were produced by those committed harnesses running
  on public datasets; every number quoted in this report is traceable to a
  committed results file in the repository (`outputs/evaluation/`), and a
  claim-by-claim audit of report-vs-evidence consistency was performed.
- The T6 evaluation set was drafted with AI assistance and then reviewed,
  edited and approved by me; I own its ground-truth labels (the manifest's
  provenance field records this).
- AI tools were also used for permitted supportive tasks: suggesting
  report structure, preparing figures and tables, and checking numbers,
  citations and word counts.
- The prose and critical analysis of this report are my own work.

## Standard academic-integrity declaration

Use the exact declaration wording required by your submission portal /
programme handbook (do not invent it). Typical form: "I declare that this
report is my own work except where otherwise acknowledged…" — copy the
official sentence from the VLE submission page.

## Figure/screenshot files ready for embedding

- docs/figures/fig1_architecture.svg … fig6_t8_perf.svg: insert the SVG
  files directly (Word accepts SVG); no rasteriser dependency; the embedded
  figure is then byte-identical to the repo asset
- docs/figures/screenshots/S1_ui_presets.png (demo UI with presets)
- docs/figures/screenshots/S4_dashboard.png
  (evaluation dashboard, verbatim numbers + limitations visible)
- committed but unused in the submitted draft (not among its word/media/
  parts): docs/figures/screenshots/S3_stream_tokens.png,
  docs/figures/screenshots/S4_dashboard_full.png
- S2 (rule-vs-llama3 compare) and S3 (live token stream) — capture
  yourself, 60 seconds, see recipe in the chat / skeleton shot list.
