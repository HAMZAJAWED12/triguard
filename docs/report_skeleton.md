# TriGuard — Draft Report Skeleton (CM3070, 6 chapters, 9,500-word hard cap)

How to use this file: each chapter below gives (a) word budget, (b) section
plan with content pointers, (c) exactly what to fix from the preliminary
version, (d) evidence/figure hooks. YOU write the prose in your own voice;
copy numbers only from `docs/report_evidence_tables.md` (E-tables). Tables,
figures, captions, references and the title page are outside the word count.

Proposed budget (sums to the 9,500 cap; section maxima all respected):

| ch | title | max | budget |
|---|---|---|---|
| 1 | Introduction | 1000 | 800 |
| 2 | Literature Review | 2500 | 2200 |
| 3 | Design | 2000 | 1600 |
| 4 | Implementation | 2000 | 1900 |
| 5 | Evaluation | 2500 | 2300 |
| 6 | Conclusion | 1000 | 700 |

Marker-criteria coverage note: diagrams/figures (crit 2) -> Fig list below;
critical eval of literature (crit 4) -> Ch2 §comparative + gap; evaluation
coverage/critical analysis (crit 10-13) -> Ch5 structure; originality
(crit 16) -> owned v2 eval set, honest-eval methodology, tri-modal
orchestration with honest fallback labelling, OCR-routing finding.

---

## Chapter 1 — Introduction (budget 800; source: docs/chapter1_introduction.md, ~890 words)

Keep §1.1 concept + output contract (fix "one model per modality" — audio =
Whisper+YAMNet, image = BLIP + opt-in OCR), keep §1.2 two-gap motivation
verbatim-ish (upgrade locality gap from "planned" to demonstrated), keep
§1.3 template statement (CM3020 Project Idea 1 — REQUIRED by the brief) with
concrete model names (toxic-bert, BLIP, RapidOCR, Whisper, YAMNet,
llama3-8B via Ollama) and DELETE the "only a small text classifier is
trained from scratch" sentence (stale). REWRITE §1.4 wholly: six-chapter
preview, no "preliminary report", no video sentence.

## Chapter 2 — Literature Review (budget 2200; source: docs/literature_review_draft.md, ~1815 words)

Structure survives (8 sources, 6 themes, comparative table, gap statement).
Revisions:
- Tense: "plans to / will" -> built + measured; §9 gap now FILLED at the
  intersection — cross-reference Ch4/Ch5 instead of promising.
- ADD citations: Hanu & Unitary (2020) Detoxify (toxic-bert lineage —
  bridges Perspective critique to your deployed model); AI@Meta (2024)
  Llama 3 (deployed judge currently uncited — examiners notice); decide
  ViLBERT: cite Lu et al. (2019) or drop the name.
- §4: add 1-2 sentences on OCR-as-text-recovery (your T3 finding directly
  echoes Kiela's confounder design).
- §5: "not packaged together" gap -> "this project packages them" (Whisper+
  YAMNet tier).
- §6 Zheng: hallucination risk now empirically addressed — point to T7
  grounding 1.0 in Ch5; soften the unevidenced fixed-format-bias sentence
  or back it with the rule-vs-llama3 agreement data.
- ~385 words headroom for the additions.

## Chapter 3 — Design (budget 1600; source: docs/project_design_draft.md + system_architecture.md)

Keep: layered architecture, frozen pydantic contract, decision-support
stance, user groups, ethics-by-design. Update to AS-BUILT:
- Judge: rule-based is the shipped DEFAULT, llama3/Ollama opt-in
  (design implied inverse); note streaming variant exists (detail in Ch4).
- Thresholds are now load-bearing design: risk_score >=0.65 harmful,
  >=0.35 borderline (cite file), Civil Comments binarised at 0.5.
- Whisper default tiny (not small); env = WSL py3.12 combined venv (not
  py3.11 laptop) — one sentence, detail in Ch4.
- OCR extension point (raw["ocr_text"], no schema change) as an example of
  the frozen-schema design paying off.
- Latency contingency: planned "swap to 3B model" replaced by SSE streaming
  + rule default — a DESIGN decision, justify it here.
- Figure: **Fig 1** (new as-built architecture SVG) replaces the stale
  architecture.png.

## Chapter 4 — Implementation (budget 1900; source: docs/chapter4_prototype.md, fully reframed)

The brief wants: major algorithms/techniques, most important code, visual
results. Suggested sections (~words):
- 4.1 Orchestration core (350): pipeline.run keyword-only contract,
  per-wrapper exception shielding, honest model_versions derived from
  raw["mode"] incl. "ollama->rule" fallback label (D-019/D-021) — show the
  `_version()`/`judge_label()` snippet.
- 4.2 Perception tiers (450): per modality — mock default + real tier +
  feature flag; toxic-bert pinned revision, multi-label sigmoid; BLIP
  caption + keyword cues + opt-in RapidOCR (why easyocr failed: torch ABI);
  Whisper chunking + YAMNet top-5>0.2 + per-component fallback. Lazy
  imports, lru_cache.
- 4.3 LLM judge (400): prompt with embedded JSON schema + consistency
  rules; parse-validate-retry-fallback ladder with distinguishable tags;
  judge_stream NDJSON generator — token stream presentation-only, terminal
  event schema-validated (show the fallback tags snippet). SSE endpoint;
  temp-file lifecycle.
- 4.4 Demo + dashboard (300): presets whitelist, perception-once compare,
  /eval/summary verbatim-copy design (honesty mechanically enforced),
  self-contained no-CDN pages. **Fig 2** (streaming sequence), screenshots
  S1-S4.
- 4.5 Environment + tests (200): WSL py3.12 combined venv, USE_TF=0
  segfault guard, TRIGUARD_MOCK offline lane; Table E1. Kill stale claims:
  "<1000 LOC", "23 tests", all mock-era numbers.
- 4.6 One honest implementation struggle (200): pick 1-2 of: torch/TF
  segfault (env-only fix), easyocr ABI failure -> RapidOCR, Ollama no-sudo
  install. Markers reward real debugging narrative.

## Chapter 5 — Evaluation (budget 2300; strongest chapter — this is where the project wins)

Suggested sections:
- 5.1 Strategy (250): tracks T1-T8 mapped to project aims; unimodal
  baseline beside every multimodal claim; numbers only from committed
  results.json envelopes (mention the 195-claim audit, commit 33ade3d);
  **Table E9** protocol-vs-actual deviations — own them openly (criterion
  13 gold).
- 5.2 Unit/integration testing (150): Table E1; schema validity by
  construction; T1/T5 smoke (Table E2) with its limitations stated.
- 5.3 Text track (300): Table E3 + Fig 3; precision/recall trade;
  threshold + tiny-positive-class caveats.
- 5.4 Image-text track (350): Table E4 + E4b + Fig 5; the OCR-routing
  finding (+0.3742 F1) vs dead keyword-cue route; near-chance AUROC
  honesty.
- 5.5 Audio track (250): Table E5; proxy-dataset reasoning; best-case WER
  framing.
- 5.6 Tri-modal ablation (400): Table E6 (+E6b as method evolution) +
  Fig 4; multimodal >= unimodal; borderline F1 = 0 finding -> threshold
  analysis; empty confounder table = honest unmet thesis metric -> future
  work.
- 5.7 Judge quality (300): T7 Table E7 (floor-metric caveat, blank human
  column); rule-vs-llama3 compare observations (D-015: llama3 more
  conservative, omitted audio once); grounding as explainability evidence.
- 5.8 Performance (150): Table E8 + Fig 6; 8GB-laptop viability argument;
  llama3 seconds-per-item -> streaming rationale.
- 5.9 Critical synthesis (150): achieved vs improve list — explicitly
  answer "what you have achieved and what you can improve" from the brief.

## Chapter 6 — Conclusion (budget 700)

Pointers: restate template fit + what was demonstrated (local, explainable,
schema-valid multimodal decision support); themes — honest evaluation as a
methodology (audit, provenance, verbatim dashboard), regulation alignment
(OSA/DSA rationale requirement), limits of pretrained composition (mild
incivility miss). Further work: student-authored cross-modal confounder
set (the empty table), human usefulness ratings for T7, threshold
sensitivity on a dev split, toxic-bert recall tuning alternatives.

---

## Figure & table manifest

| id | asset | where |
|---|---|---|
| Fig 1 | docs/figures/fig1_architecture.svg (as-built architecture) | Ch3 |
| Fig 2 | docs/figures/fig2_streaming_flow.svg (SSE protocol) | Ch4 |
| Fig 3 | docs/figures/fig3_t2_text_track.svg (sklearn vs toxic-bert) | Ch5.3 |
| Fig 4 | docs/figures/fig4_t6_ablation.svg (v2 four conditions) | Ch5.6 |
| Fig 5 | docs/figures/fig5_t3_ocr_ablation.svg (OCR routes) | Ch5.4 |
| Fig 6 | docs/figures/fig6_t8_perf.svg (mock vs real latency/RSS) | Ch5.8 |
| S1-S4 | screenshots YOU capture (see shot list) | Ch4 |
| E1-E9 | docs/report_evidence_tables.md | Ch4/Ch5 |

Screenshot shot list (server: `uvicorn triguard.api.main:app` per README):
- S1 /ui with preset buttons + a rendered verdict (mock mode fine).
- S2 compare view: rule vs llama3 columns (run with Ollama up; if down, the
  ollama->rule warning view is itself worth showing — honest fallback).
- S3 stream view mid-tokens, and/or final validated verdict card.
- S4 /dashboard T6 section (provenance line + config visible).

## AI-use declaration — facts to state (wording yours; UoL policy: "declare how and where")

- Code (wrappers, orchestrator, judge integration, demo surface, evaluation
  harnesses, tests) developed with AI assistance (Claude) under the
  author's direction; all design decisions logged in DECISIONS.md.
- Evaluation numbers produced by the committed harnesses on public
  datasets; a claim-by-claim audit verified every documented number against
  its evidence file.
- T6 evaluation set: AI-assisted draft, then reviewed, edited and approved
  by the author, who owns the ground-truth labels (manifest provenance
  field records this).
- Report prose and critical analysis: the author's own work; AI used for
  structure suggestions, figures/tables preparation, and number/citation
  checking (policy-permitted supportive uses).

## References to ADD to the existing 8 (Harvard)

- Hanu, L. and Unitary team (2020) Detoxify. github.com/unitaryai/detoxify.
- AI@Meta (2024) 'The Llama 3 herd of models'. arXiv:2407.21783.
- (decide) Lu, J. et al. (2019) 'ViLBERT'. NeurIPS 32 — or drop the name
  from §4.
- Piczak, K.J. (2015) 'ESC: Dataset for environmental sound
  classification'. ACM MM — if ESC-50 is discussed in Ch5 (it is).
- Panayotov, V. et al. (2015) 'LibriSpeech'. ICASSP — same reason.

## Pre-submission checklist

- [ ] Every number traced to an E-table (which traces to a results.json).
- [ ] Word counts per chapter <= caps AND total <= 9500 (count prose only).
- [ ] Every figure referenced from body text (brief demands linkage).
- [ ] Careful-language sweep: "supports/assists/demonstrates feasibility";
      never "automatically detects / achieves perfect / replaces".
- [ ] Harvard consistency; every in-text cite has a reference entry and
      vice versa.
- [ ] AI-use declaration section present.
- [ ] T1 "200 inputs" and T5 "coverage >80%" claims either verified by a
      fresh run or removed.
- [ ] Optional before submission: rate T7 usefulness_1to5 (18 items) to
      fill the human-eval gap.
