# TriGuard — Final Report Skeleton (CM3070, 6 chapters, 10,500-word strict cap)

How to use this file: each chapter below gives (a) word budget, (b) section
plan with content pointers, (c) exactly what to fix from the submitted draft,
(d) evidence/figure hooks. YOU write the prose in your own voice; copy
numbers only from `docs/report_evidence_tables.md` (E-tables). This file is
pointers-only: no sentence here is report prose.

Final brief facts (word count):
- Chapter caps: Ch1 1000 / Ch2 2500 / Ch3 2000 / Ch4 2500 / Ch5 2500 /
  Ch6 1000. Strict total 10,500.
- Excluded from the count by the brief: references, table/figure LEGENDS,
  chapter titles. The brief does NOT explicitly exclude table CELLS — the
  word ledger therefore reports BOTH totals (prose-only, prose + table cells)
  and both must be <= cap.
- Appendices: "additional pages of images and references" only — no prose
  appendices.
- A public repository link is REQUIRED in the report.

Proposed budget (sums to 10,200; 300 slack against the 10,500 strict total;
every chapter maximum respected):

| ch | title | cap | budget |
|---|---|---|---|
| 1 | Introduction | 1000 | 800 |
| 2 | Literature Review | 2500 | 2300 |
| 3 | Design | 2000 | 1600 |
| 4 | Implementation | 2500 | 2400 |
| 5 | Evaluation | 2500 | 2400 |
| 6 | Conclusion | 1000 | 700 |
| | total | 10,500 | 10,200 |

Marker-criteria coverage note: diagrams/figures (crit 2) -> Fig list below;
critical eval of literature (crit 4) -> Ch2 §comparative + gap; evaluation
coverage/critical analysis (crit 10-13) -> Ch5 structure; originality
(crit 16) -> owned v2 eval set, honest-eval methodology, tri-modal
orchestration with honest fallback labelling, OCR-routing finding.

Marker-feedback traceability (P1-P3, F1-F6 -> root cause -> section ->
deliverable -> wording constraint): `docs/feedback_traceability.md`.

---

## Chapter 1 — Introduction (budget 800; source: docs/chapter1_introduction.md, ~890 words)

Keep §1.1 concept + output contract (fix "one model per modality" — audio =
Whisper+YAMNet, image = BLIP + opt-in OCR), keep §1.2 two-gap motivation
verbatim-ish (upgrade locality gap from "planned" to demonstrated), keep
§1.3 template statement (CM3020 Project Idea 1 — REQUIRED by the brief) with
concrete model names (toxic-bert, BLIP, RapidOCR, Whisper, YAMNet,
llama3-8B via Ollama) and DELETE the "only a small text classifier is
trained from scratch" sentence (stale; the 30-sentence corpus is now
documented in Ch4 §4.2 / Table E11 instead). REWRITE §1.4 wholly:
six-chapter preview, no "preliminary report", no video sentence.

## Chapter 2 — Literature Review (budget 2300 target / 2500 cap; submitted draft 1,814 words)

Source of record = the submitted draft's Ch2, sections 2.1-2.7:
`docs/draft_as_submitted/ch2.md` — local-only, gitignored; regenerate with
`scripts/docx_to_md.py <draft.docx> --out docs/draft_as_submitted` (re-key every pointer below to THAT file's
section numbers; do not use the old .md §1-§11 numbering). Word budget:
1,814 (submitted-draft count, orchestrator-supplied) -> 2,300 target /
2,500 cap (~486 words headroom for the F1 cohesion work + citations).

Feedback F1 (cohesion) fixes — pointers only:
- Five hand-off boundaries need one linking sentence each: 2.2->2.3,
  2.3->2.4, 2.4->2.5, 2.5->2.6, 2.6->2.7. Each exit sentence names the
  property the section contributes to the gap (multimodal / audio-aware /
  explainable / local) so 2.7 does not introduce the four properties cold.
- The unfulfilled "organised by design question" promise: either organise
  2.3-2.6 by the design questions actually asked (text? image+text? audio?
  judge?) with those questions in the sub-headings, or delete the promise.
- Table 2.1 replacement body = **Table E12** (pending): five property
  columns (multimodal, audio-aware, explainable/rationale, local/offline,
  end-to-end decision) + a TriGuard row; caption numbered (P2); cells are
  facts from the cited papers only.
- Align 2.7 with Ch5: 2.7 currently says the cross-modal evidence is "weak";
  the Figure 5 (T6) caption says the confounder table is "empty". Use
  "empty" in both places (the metric was not measured, not measured-and-low;
  D-029: `n_cross_modal_harmful: 0`).
- ADD citations: Hanu & Unitary (2020) Detoxify (toxic-bert lineage);
  AI@Meta (2024) Llama 3 (deployed judge currently uncited); decide ViLBERT:
  cite Lu et al. (2019) or drop the name; verify or drop the Gemmeke 2017 ->
  YAMNet attribution (F4; repo cannot support it).
- Image-text section: 1-2 sentences on OCR-as-text-recovery (T3 finding
  echoes Kiela's confounder design); note T3 was measured on Memotion, not
  Hateful Memes (D-018).
- Audio section: "not packaged together" gap -> "this project packages them"
  (Whisper+YAMNet tier).
- Judge section (Zheng): hallucination risk partially checked by a floor
  metric — cross-reference 5.7 / Table E7 and its caveats (grounding =
  >=1 evidence token cited; not completeness, correctness or usefulness).
  Soften the unevidenced fixed-format-bias sentence or back it with the
  rule-vs-llama3 agreement data (E6c).

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
- **§3.4 hook — component selection (F4).** For EACH model (toxic-bert,
  BLIP, RapidOCR, Whisper, YAMNet, llama3-8B/Ollama): what it is + why it
  was chosen over an alternative. Facts-only **Table M1** (pending): model,
  hub id / pinned revision, input -> output, config values, file:line,
  source decision. Repo status of alternatives: D-012 (text), D-013 (image),
  D-023 (OCR: easyocr rejected, torch ABI), D-015 (judge) record options;
  **D-014 lists NO alternative for YAMNet** — the student must name and
  justify one themselves (cannot be sourced from the repo). Introduce YAMNet
  before the schema field `yamnet_tags` is presented.
- Figure: **Fig 1** (new as-built architecture SVG) replaces the stale
  architecture.png.

## Chapter 4 — Implementation (budget 2400; source: docs/chapter4_prototype.md, fully reframed)

The brief wants: major algorithms/techniques, most important code, visual
results. Suggested sections (~words):
- 4.1 Orchestration core (350): pipeline.run keyword-only contract,
  per-wrapper exception shielding, honest model_versions derived from
  raw["mode"] incl. "ollama->rule" fallback label (D-019/D-021) — show the
  `_version()`/`judge_label()` snippet.
- 4.2 Perception tiers (500): per modality — mock default + real tier +
  feature flag; toxic-bert pinned revision, multi-label sigmoid; BLIP
  caption + keyword cues + opt-in RapidOCR (why easyocr failed: torch ABI);
  Whisper chunking + YAMNet top-5>0.2 + per-component fallback. Lazy
  imports, lru_cache.
  **§4.2 hook (F2):** name the 30-sentence bundled training corpus —
  **Table E11** corpus card (pending). Facts: `src/triguard/models/
  text_model.py:48-81` `_TRAIN`; role = training data for the offline
  sklearn floor ONLY (never an evaluation set); 30 sentences, 15 toxic /
  15 non-toxic (counted from `_TRAIN`, 2026-09-24); hard-token override
  (`_HARD_TOXIC_TOKENS`, text_model.py:176-179: probability floored at 0.6
  when a hard token is present); overlap note = state whether any corpus
  sentence overlaps the T1 smoke set / T6 manifest (E11 records the check).
- 4.3 LLM judge (500): prompt with embedded JSON schema + consistency
  rules; parse-validate-retry-fallback ladder with distinguishable tags;
  judge_stream NDJSON generator — token stream presentation-only, terminal
  event schema-validated (show the fallback tags snippet). SSE endpoint;
  temp-file lifecycle.
  **§4.3 hook (F6):** (i) verbatim prompt as a numbered figure
  (`llm_judge.py:55-76` template; retry suffix and evidence-block format
  cited by line); (ii) non-stream ladder figure (parse -> validate -> one
  stricter retry -> rule fallback, tags `judge_output_invalid` /
  `ollama_unavailable:<reason>`; streaming path has no retry); (iii)
  **Table E13a** prompt revision log (pending) — prompt template
  byte-identical across commits 1373e06 / 4f10803 / e866541 / daae032 /
  HEAD (sha256 of the template string compared 2026-09-24); (iv) **Table
  E13b** validation log (pending: D-015 sample, T7 n=18, T6 v2 n=24);
  (v) honest statement to make: designed once, validated, never revised.
  Own the design-vs-shipped deviations (borderline-on-failure, system/user
  split, regex guardrail in system_architecture.md:107-116 — none shipped)
  via Table E9.
- 4.4 Demo + dashboard (300): presets whitelist, perception-once compare,
  /eval/summary verbatim-copy design (honesty mechanically enforced),
  self-contained no-CDN pages. **Fig 2** (streaming sequence), screenshots
  S1-S4.
- 4.5 Environment + tests (100 — ~100 words donated to §5.2): WSL py3.12
  combined venv, USE_TF=0 segfault guard, TRIGUARD_MOCK offline lane; one
  forward pointer to Table E1 in §5.2. Kill stale claims: "<1000 LOC",
  "23 tests", all mock-era numbers.
- 4.6 One honest implementation struggle (250): pick 1-2 of: torch/TF
  segfault (env-only fix), easyocr ABI failure -> RapidOCR, Ollama no-sudo
  install, **or the D-027 latch bug** (DECISIONS.md:667-707: a per-file
  decode failure latched the real BLIP/Whisper/YAMNet tier off for the whole
  server session; reproduced live; fix = split model-load from per-request
  work; 4 offline regression tests `tests/test_wrapper_latch.py`). Markers
  reward real debugging narrative.

## Chapter 5 — Evaluation (budget 2400; strongest chapter — this is where the project wins)

Suggested sections:
- 5.1 Strategy (300): tracks T1-T8 mapped to project aims; unimodal
  baseline beside every multimodal claim; numbers only from committed
  results.json envelopes (mention the 195-claim audit, commit 33ade3d);
  **Table E10** datasets & tracks at a glance (pending: dataset, role
  train/eval, n, selection, licence, evidence path). **Table E9**
  protocol-vs-actual deviations — own them openly (criterion 13 gold).
  **Single scope statement for user testing** (facts): no user testing with
  participants was done or planned (`docs/ethics.md:12-14`; DECISIONS.md:58
  — T7 peer review contingent on tutor approval); the only human element is
  the author's own single-rater T7 usefulness rating (`scripts/rate_t7.py`);
  the contingent peer review was not pursued.
- 5.2 Testing (300; +~100 words from §4.5, +~50 from §5.8) — restructure to
  <= 3 sub-sections:
  (a) automated layers via **Table E1** (unit / integration / regression /
      real-backend slow lane; fast-vs-slow design `tests/conftest.py`;
      honesty properties asserted by tests, e.g. model_versions);
  (b) protocol-claim discharge + coverage via **Table E1b** (pending:
      protocol claim -> discharging test) and **Table E9** rows: T1 "200
      synthetic inputs" planned vs n_samples=14 run
      (`outputs/evaluation/20260623-063735/results.json`); T5 branch
      coverage NOT measured (pytest-cov absent); judge retry: protocol
      borderline-on-failure (evaluation_protocol.md:58) vs actual
      rule-judge fallback tagged `judge_output_invalid` (D-015);
  (c) what is NOT tested (**Table E1c** manual functional checks, pending:
      CLI, README quick-start, `scripts/demo_up.sh` checklist) + the user
      testing scope statement cross-ref to 5.1.
- 5.3 Text track (300): **Tables E3a** (pending: sampling facts) **+ E3**
  + Fig 3; precision/recall trade; threshold + tiny-positive-class caveats.
  Sampling paragraph pointers (F3): HOW = `src/triguard/data/datasets.py:
  190-218` (streaming `test` split, seeded (42) shuffle over a bounded
  buffer, first 500 non-empty rows kept, cached locally, dataset revision
  unpinned); WHY 500 = NOT in the repo (CLI default `run_t2.py:74`;
  D-011 gives "small, reproducible, offline-after-first-run" but no number)
  — the reason is the student's own statement; CONSEQUENCE = 32 positives
  / 468 negatives (E3), so toxic-F1 is noisy.
- 5.4 Image-text track (350): Table E4 + E4b + **Figure 4** (OCR ablation);
  the OCR-routing finding (+0.3742 F1) vs dead keyword-cue route;
  near-chance AUROC honesty.
- 5.5 Audio track (250): Table E5; proxy-dataset reasoning; best-case WER
  framing.
- 5.6 Tri-modal ablation (400): Table E6 (+E6b as method evolution) +
  **Figure 5** (T6); multimodal >= unimodal; borderline F1 = 0 finding ->
  threshold analysis; empty confounder table = honest unmet thesis metric
  -> future work. **Table E6c** (T6 v2 two-judge comparison, D-029: rule
  run 20260725-191000 vs ollama run 20260725-191055, n=24): quote with the
  D-029 caveats — unimodal conditions degenerate for BOTH judges (constant
  answers), only the multimodal row is substantive, single llama3 run.
- 5.7 Judge quality (300) — five-slot map:
  1. PURPOSE: rationale = the explainability artefact (Ch1 aim; Zheng
     hallucination risk); the prompt itself requires it — `llm_judge.py:70`
     "Reference at least one piece of evidence in the rationale."
  2. DEFINITION + **Table E7**: grounded = rationale contains >=1 token from
     the evidence vocabulary (`grounding.py`); invented modality = names a
     modality not supplied. Floor metric, not hallucination-free.
  3. RESULT + CONFIG: E7 values with run id 20260705-113456 and its config
     block (hf / blip / real, WSL); rule judge ~1.0 by construction, not
     separately measured.
  4. LIMITS (-> E9 rows): 3/18 rationales grounded ONLY by generic tokens
     (S4, MS1, MS2: `cited` is a subset of {toxicity, that}; counted from
     `per_item[].cited`, 2026-09-24); item MB1's rationale has the rule-judge
     template form ("the text classifier flagged toxicity at 0.63 (toxic).
     the image caption '...' showed no obvious risk cues") — suspected
     fallback, cause unrecorded (per-item judge provenance not persisted);
     6/18 rationales stored truncated at 200 chars (`run_t7.py:60`; items
     B2, H3, I1, A1, MS1, MH1 have len == 200); T7 ran on the v1 AI-drafted
     18-item set (superseded by v2, D-026) — disclose in 5.7 and in the
     AI-use declaration; protocol unit/rater/scale deviations (E9).
     **Table E7b** citation-type summary (pending, 4 rows).
  5. USEFULNESS COLUMN: status = `usefulness_1to5` null for all 18 in the
     committed run; if rated, cite the new `t7_human/results.json` envelope
     (single rater = author, no kappa). D-015 rationale observation
     (llama3 more conservative than rule on one sample; omitted audio) with
     its caveat: single sample, single run.
- 5.8 Performance (100 — ~50 words donated to §5.2): Table E8 + Fig 6;
  8GB-laptop viability argument; llama3 seconds-per-item -> streaming
  rationale. State T8 (and T7) ran on the v1 18-item manifest, E6 on v2.
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

Numbering decision (student decision A): the report keeps ONE sequential
Figure list (Figure 1-6, plus pending 7/8) and a SEPARATE Screenshot list
(S1-S4). Every caption is standalone and every figure/table is referenced
from body text (P2).

Repo file vs report number (recorded, NOT renamed yet):
- `docs/figures/fig4_t6_ablation.svg` = report **Figure 5** (T6 ablation).
- `docs/figures/fig5_t3_ocr_ablation.svg` = report **Figure 4** (OCR ablation).
- Rename the files (and the baked "see Table E6" text in fig4_t6_ablation.svg)
  only in a dedicated pass; until then cite by report number.

| id | asset | where | status |
|---|---|---|---|
| Fig 1 | docs/figures/fig1_architecture.svg (as-built architecture) | Ch3 | exists |
| Fig 2 | docs/figures/fig2_streaming_flow.svg (SSE protocol) | Ch4.4 | exists |
| Fig 3 | docs/figures/fig3_t2_text_track.svg (sklearn vs toxic-bert; runs 20260623-074102, 20260623-124802) | Ch5.3 | exists |
| Fig 4 | docs/figures/fig5_t3_ocr_ablation.svg (OCR routes; run 20260705-111002) | Ch5.4 | exists (file name says fig5) |
| Fig 5 | docs/figures/fig4_t6_ablation.svg (v2 four conditions; run 20260705-160858) | Ch5.6 | exists (file name says fig4) |
| Fig 6 | docs/figures/fig6_t8_perf.svg (mock vs real latency/RSS; runs 20260705-113354, 20260705-113639) | Ch5.8 | exists |
| Fig 7 | §4.3 verbatim judge prompt (llm_judge.py:55-76) as a numbered figure | Ch4.3 | pending; if inserted before Figure 6, renumber Figure 6 -> 8 and every Ch5 reference to it |
| Fig 8 | §4.3 non-stream judge ladder (parse -> validate -> retry -> rule fallback, tags) | Ch4.3 | pending; same renumbering rule |
| S1-S4 | docs/figures/screenshots/ (S1 presets, S2 compare, S3 stream, S4 dashboard) | Ch4.4 | exist; S2/S3 need separate standalone captions |
| E1 | test suite facts (two dated rows added 2026-09-24) | Ch5.2 | exists |
| E1b | protocol claim -> discharging test | Ch5.2 | pending (P3) |
| E1c | manual functional checks (CLI, quick-start, demo_up.sh) | Ch5.2 | pending (P3) |
| E2 | T1/T5 smoke run (quote only with limitations) | Ch5.2 | exists |
| E3 | T2 sklearn vs toxic-bert | Ch5.3 | exists |
| E3a | T2 sampling facts (how / why-500-unrecorded / 32 positives) | Ch5.3 | pending (F3) |
| E4 / E4b | T3 image-text + OCR ablation | Ch5.4 | exist |
| E5 | T4 audio proxies | Ch5.5 | exists |
| E6 / E6b | T6 v2 rule run 20260705-160858 / v1 method evolution | Ch5.6 | exist |
| E6c | T6 v2 two-judge comparison (D-029): rule 20260725-191000 vs ollama 20260725-191055 | Ch5.6 | NEW |
| E7 | T7 grounding (run 20260705-113456) — caption/caveat rewrite: floor metric | Ch5.7 | exists; caption rewrite pending |
| E7b | T7 citation-type summary (4 rows) | Ch5.7 | NEW |
| E8 | T8 latency & memory | Ch5.8 | exists |
| E9 | protocol-vs-actual deviations — add/rewrite rows: T7 (unit, rater, scale wording), T1 (200 planned vs n=14), T5 (coverage not measured), judge retry (borderline-on-failure vs rule fallback tagged) | Ch5.1 / 5.2 | exists; rows pending |
| E10 | datasets & tracks at a glance | Ch5.1 | pending (F2/F3) |
| E11 | 30-sentence corpus card | Ch4.2 | pending (F2) |
| E12 | Table 2.1 replacement body (five property columns + TriGuard row) | Ch2 | pending (F1/P2) |
| E13a / E13b | prompt revision log / validation log | Ch4.3 | pending (F6) |
| M1 | models composed (facts-only) | Ch3.4 | pending (F4) |

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
- T6 evaluation set: AI-assisted draft (v1), then reviewed, edited and
  approved by the author (v2), who owns the ground-truth labels (manifest
  provenance field records this). T7/T8 numbers were produced on the v1
  set — say so.
- Report prose and critical analysis: the author's own work; AI used for
  structure suggestions, figures/tables preparation, and number/citation
  checking (policy-permitted supportive uses).

## References to ADD to the existing 8 (Harvard)

- Hanu, L. and Unitary team (2020) Detoxify. github.com/unitaryai/detoxify.
- AI@Meta (2024) 'The Llama 3 herd of models'. arXiv:2407.21783.
- (decide) Lu, J. et al. (2019) 'ViLBERT'. NeurIPS 32 — or drop the name
  from the image-text section.
- Piczak, K.J. (2015) 'ESC: Dataset for environmental sound
  classification'. ACM MM — if ESC-50 is discussed in Ch5 (it is).
- Panayotov, V. et al. (2015) 'LibriSpeech'. ICASSP — same reason.
- YAMNet / TF-Hub model card and RapidOCR — student to verify and add (F4);
  the repo holds no citable entry for either.

## Pre-submission checklist

- [ ] Every number traced to an E-table (which traces to a results.json);
      every E-table number (E1-E13, M1) traced — none retyped by hand.
- [ ] Word ledger: BOTH totals (prose-only; prose + table cells) <= chapter
      caps AND <= 10,500 strict total.
- [ ] Run `scripts/check_report_refs.py` (pending) on the final .docx:
      every Figure/Table/Screenshot caption referenced in body text,
      numbering sequential, no dangling references, no repo-only ids
      (E1/E9/E4b) left in captions.
- [ ] Every figure referenced from body text (brief demands linkage).
- [ ] Public repository URL present in the report.
- [ ] Video runtime measured (VLC / file properties) and within 3:00-5:00
      before upload.
- [ ] Careful-language sweep: "supports/assists/demonstrates feasibility";
      never "automatically detects / achieves perfect / replaces".
- [ ] Harvard consistency; every in-text cite has a reference entry and
      vice versa.
- [ ] AI-use declaration section present; name/SRN + integrity declaration
      present.
- [ ] T1 "200 inputs" and T5 "coverage >80%" claims either verified by a
      fresh run or removed (E9 rows own the deviation).
- [ ] Optional before submission: rate T7 usefulness_1to5 (18 items) and
      merge (`scripts/rate_t7.py --merge`) to fill the human-eval gap.
