# Report crosswalk — figure / table / listing ids to repository evidence (P2)

Purpose: one lookup from every numbered item in the submitted draft to the
repository asset or evidence table it is built from, the committed
`results.json` and the JSON key paths that hold its numbers, and the chapter
where it lives. Numbering is read from the front-matter lists of the read-only
mirror `docs/draft_as_submitted/full.md` (List of Figures and Screenshots,
lines 99-117; List of Tables, 119-147; List of Code Listings, 149-153).
E-table sources are the `Source:` lines under each header of
`docs/report_evidence_tables.md`. Line numbers below are `full.md` lines of
the body mention / body caption. Nothing here is report prose.

Checker: `scripts/check_report_refs.py <path.docx>` (stdlib; see its module
docstring for the checks). Provenance test for the data figures:
`tests/test_figures_provenance.py`.

## 1. Report id -> asset / E-table -> results.json + key paths -> chapter

Repo-file-vs-report swap (recorded in `docs/report_skeleton.md` "Figure &
table manifest", NOT renamed): `docs/figures/fig4_t6_ablation.svg` is report
**Figure 5**; `docs/figures/fig5_t3_ocr_ablation.svg` is report **Figure 4**.

Docx media check (md5 of `word/media/*.png` in the submitted draft vs
`docs/figures/screenshots/*.png`): S1_ui_presets.png = image3.png,
S2_compare.png = image4.png, S3_stream_final.png = image5.png,
S4_dashboard.png = image6.png; S3_stream_tokens.png and S4_dashboard_full.png
match no media part (committed but unused). image1/2 and image7-10 are PNG
rasterisations of the six SVGs (not byte-identical to the repo assets).

| report id | asset / E-table | results.json (under `outputs/evaluation/`) | JSON key paths used | chapter (mention / caption line) |
|---|---|---|---|---|
| Figure 1 | `docs/figures/fig1_architecture.svg` | none | — (as-built architecture drawing) | Ch3 §3.2 (287 / 291) |
| Figure 2 | `docs/figures/fig2_streaming_flow.svg` | none | — (SSE protocol drawing; code: `src/triguard/models/llm_judge.py` `judge_stream()`, def line 290) | Ch4 §4.3 (394 / 396) |
| Screenshot S1 | `docs/figures/screenshots/S1_ui_presets.png` | none | — (`/ui` presets) | Ch4 §4.4 (408 / 410) |
| Screenshot S2 | `docs/figures/screenshots/S2_compare.png` | none | — (`POST /analyse/compare`) | Ch4 §4.4 (412 / 418, merged caption with S3) |
| Screenshot S3 | `docs/figures/screenshots/S3_stream_final.png` | none | — (`POST /analyse/stream`) | Ch4 §4.4 (412 / 418, merged caption with S2) |
| Screenshot S4 | `docs/figures/screenshots/S4_dashboard.png` | indirect: `/eval/summary` copies whitelisted keys from the newest run per configuration | — (dashboard page) | Ch4 §4.4 (420 / 422) |
| Figure 3 | `docs/figures/fig3_t2_text_track.svg` -> Table E3 | `20260623-074102/t2/results.json` (sklearn), `20260623-124802/t2/results.json` (hf) | `accuracy`, `macro_f1`; title n from `n_samples` | Ch5 §5.3 (497 / 499) |
| Figure 4 | `docs/figures/fig5_t3_ocr_ablation.svg` (file name says fig5) -> Table E4b | `20260705-111002/t3/results.json` | `ocr_ablation.image_only_noocr.f1`, `ocr_ablation.image_only_ocr_cues.f1`, `ocr_ablation.image_only_ocr_to_text.f1`, `ocr_ablation.delta_f1_ocr_to_cues`, `ocr_ablation.delta_f1_ocr_to_text`; n from `n_samples` | Ch5 §5.4 (532 / 534) |
| Figure 5 | `docs/figures/fig4_t6_ablation.svg` (file name says fig4) -> Table E6 | `20260705-160858/t6/results.json` | `conditions.{text_only,image_only,audio_only,multimodal}.{n,accuracy,macro_f1}`, `conditions.*.per_class.borderline.f1` (= 0.0), `cross_modal_ablation.n_cross_modal_harmful` (= 0); `n_items` | Ch5 §5.6 (570 / 572) |
| Figure 6 | `docs/figures/fig6_t8_perf.svg` -> Table E8 | `20260705-113354/t8/results.json` (mock), `20260705-113639/t8/results.json` (real) | `latency_ms.p50`, `latency_ms.p95`, `latency_ms.cold_start_ms`, `peak_rss_mb` | Ch5 §5.8 (613 / 615) |
| Table 2.1 | no results.json; source = literature (References list; replacement body = Table E12 in `docs/report_evidence_tables.md`) | none | — | Ch2 §2.7 (245 / 247) |
| Table 3.1 | no results.json; source = `docs/project_design_draft.md` §4 needs table + DECISIONS | none | — | Ch3 §3.1 (271 / 273) |
| Table 3.2 | no results.json; source = DECISIONS / `docs/implementation_notes.md` (facts card: Table M1) | none | — | Ch3 §3.4 (305 / 307) |
| Table 3.3 | no results.json; source = DECISIONS (plan-to-build changes) | none | — | Ch3 §3.6 (336 / 338) |
| Table 4.1 | no results.json; source = `docs/implementation_notes.md` (perception tiers) | none | — | Ch4 §4.2 (371 / 373) |
| Table 4.2 | Table E1 (facts, not results.json): pytest fast-lane runs dated 2026-07-06; `tests/` inventory | none | — | Ch4 §4.6 (436 / 438); source line 449 cites `Table E1` |
| Table 5.1 | Table E9 (protocol-vs-actual) | row pointers only: `20260623-063735/results.json` `n_samples`; `20260705-113456/t7/results.json` `per_item[*].usefulness_1to5` | see E9 rows | Ch5 §5.1 (461 / 463); source line 475 cites `Table E9` |
| Table 5.2 | Table E3 | `20260623-074102/t2/results.json`, `20260623-124802/t2/results.json` | `accuracy`, `macro_f1`, `per_class.toxic.precision`, `per_class.toxic.recall`, `per_class.toxic.f1`; caption counts `n_samples`, `class_balance.non-toxic`, `class_balance.toxic` | Ch5 §5.3 (485 / 487) |
| Table 5.3 | Table E4 | `20260705-111002/t3/results.json` | `metrics_pipeline.{precision,recall,f1,accuracy,auroc}`, `metrics_text_only_baseline.{precision,recall,f1,accuracy}` (no `auroc` key -> "Not reported"); caption counts `n_samples`, `class_balance.{not_offensive,offensive}` | Ch5 §5.4 (505 / 507) |
| Table 5.4 | Table E4b | `20260705-111002/t3/results.json` | `ocr_ablation.image_only_noocr.{precision,recall,f1}`, `ocr_ablation.image_only_ocr_cues.{precision,recall,f1}`, `ocr_ablation.image_only_ocr_to_text.{precision,recall,f1}`, `ocr_ablation.delta_f1_ocr_to_cues`, `ocr_ablation.delta_f1_ocr_to_text` | Ch5 §5.4 (519 / 521); source line 530 cites `Table E4b` |
| Table 5.5 | Table E5 | `20260704-153729/t4/results.json` | `whisper_wer.wer_corpus`, `whisper_wer.wer_mean_per_clip`, `yamnet_events.top1_rate`, `yamnet_events.top5_rate`; n from `whisper_wer.n`, `yamnet_events.n`; "29 mapped categories" = `len(yamnet_events.categories_used)` | Ch5 §5.5 (538 / 540) |
| Table 5.6 | Table E6 | `20260705-160858/t6/results.json` | `conditions.<c>.{n,accuracy,macro_f1}`, `conditions.<c>.per_class.{safe,borderline,harmful}.f1`, `conditions.<c>.latency_ms.{p50,p95}` for `<c>` in text_only / image_only / audio_only / multimodal; source line: `class_balance.{safe,borderline,harmful}` | Ch5 §5.6 (556 / 558) |
| Table 5.7 | Table E7 | `20260705-113456/t7/results.json` | `grounding_rate`, `n`, `invented_modality_count`, `per_item[*].usefulness_1to5` (all `null` -> "Not completed") | Ch5 §5.7 (582 / 584) |
| Table 5.8 | Table E8 | `20260705-113354/t8/results.json`, `20260705-113639/t8/results.json` | `latency_ms.p50`, `latency_ms.p95`, `latency_ms.cold_start_ms`, `peak_rss_mb`; n from `n` | Ch5 §5.8 (601 / 603) |
| Listing 1 | `src/triguard/orchestrator/pipeline.py` — `_version()` helper (docstring line 60) and the judge label in `run()` (def line 71) | none | — | Ch4 §4.1 (359 / 361) |
| Listing 2 | `src/triguard/models/llm_judge.py` — terminal branch of `judge_stream()` (def line 290) | none | — | Ch4 §4.3 (398 / 400) |

## 2. The three source lines citing repository-only ids

Anchor = first six words of the `TableSource` paragraph text (as printed by
the checker), not a paragraph index. Replacement pointers are facts from the
named files; wording is the author's.

| anchor (first six words) | mirror anchor / line | under | repo-only id | factual replacement pointer |
|---|---|---|---|---|
| `Source: test runs and repository test` | `[p923b8e67]` / full.md 449 | Table 4.2 | `Table E1` | pytest fast-lane runs dated 2026-07-06 (`docs/report_evidence_tables.md` E1 rows, lines 18-19: full WSL venv 45 passed / 10 skipped; minimal offline venv 33 passed / 11 skipped) and the `tests/` inventory (E1 line 24: 10 slow-marked real-path tests, `--run-slow`) |
| `Source: Table E9; decisions D-011, D-017,` | `[pf8a3fed6]` / full.md 475 | Table 5.1 | `Table E9` | `DECISIONS.md` entries D-011 (line 97), D-017 (297), D-018 (334), D-022 (448), D-024 (522), D-026 (635); planned column from `docs/evaluation_protocol.md` |
| `Source: run 20260705-111002, Table E4b.` | `[pb9216774]` / full.md 530 | Table 5.4 | `Table E4b` | run `20260705-111002`, `t3/results.json`, `ocr_ablation` block (keys listed in section 1, Table 5.4 row) |

Checker output on the submitted draft (2026-09-24, before any docx edit):
3 errors (all `repo-only-id`, the three lines above), 8 warnings
(1 `merged-caption` Screenshot S2/S3; 7 `not-standalone` at the default
`--min-words 8`: Listing 1, Listing 2, Table 3.2, Table 4.1, Table 4.2,
Table 5.1, Table 5.4), 0 `missing-reference`, 0 `dangling-reference`,
0 `non-sequential`, 0 `duplicate-caption`, 0 `list-drift`,
0 `not-near-anchor`; captions Figure 6 / Table 14 / Screenshot 4 /
Listing 2, every one referenced; exit code 1. `--allow-ids E1 E9 E4b` gives
exit 0 for the current file (the ids are then tolerated, not fixed).

## 3. Durable fix pointer and the numbering decision on record

Durable fix (Word): References > Insert Caption for every figure, table and
listing so the number is a `SEQ` field; Insert Cross-reference for every
in-text mention so it is a `REF` field; then select all, F9 (update fields),
save, and re-run `scripts/check_report_refs.py` on the saved file. The checker
reads cached field results and prints the notice `SEQ/REF fields present —
update fields (F9) before checking` whenever such fields exist, so an
un-updated file is visible.

Numbering decision on record (`docs/report_skeleton.md` "Figure & table
manifest", student decision A): Figures 1-6 sequential in one list and
Screenshots S1-S4 in a separate list. Open item under the same decision:
split the merged S2/S3 caption (`[p1c8e8375-2]`, full.md 418) into two
standalone captions, one per screenshot, each referenced from body text
(the body mention at full.md 412 already reads "Screenshots S2 and S3").

Related file-level change (this pass): the trailing text of
`docs/figures/fig4_t6_ablation.svg` no longer says "(see Table E6)", so the
figure no longer bakes a repo-only id into the report;
`tests/test_figures_provenance.py::test_no_repo_table_ids_baked_into_figure_text`
guards all six SVGs.

## For integration

### Skeleton checklist line (docs/report_skeleton.md "Pre-submission checklist")

- [ ] `scripts/check_report_refs.py <final.docx>` exits 0 (3 `repo-only-id`
      lines replaced per `docs/report_crosswalk.md` §2; S2/S3 caption split);
      `tests/test_figures_provenance.py` green; crosswalk §1 consulted for
      every figure/table number.

### DECISIONS draft — P2: report reference checker + crosswalk; SVG text de-coupled from table ids

Date: 2026-09-24
Status: draft — Decision/Reason to be completed by the author

Context: The pre-submission checklist required a reference checker for the
report (skeleton line "Run `scripts/check_report_refs.py` (pending)"). Added
`scripts/check_report_refs.py` (stdlib zipfile + ElementTree; field-aware
text; checks: missing / dangling references, per-kind sequence, duplicates,
repo-only `Table E*` ids, standalone caption length, front-matter list
drift, drawing/table proximity, header/footer captions) with
`tests/test_check_report_refs.py` (7 tests on generated minimal .docx files),
`docs/report_crosswalk.md` (report id -> asset / E-table -> results.json key
paths -> chapter), and `tests/test_figures_provenance.py` (5 tests: every
number printed on fig3/fig4/fig5/fig6 SVG text exists in the cited
results.json; no `Table E*` id in any SVG). Run on the submitted draft: 3
errors, all `repo-only-id` on the Table 4.2 / 5.1 / 5.4 source lines; 0
missing, 0 dangling, 0 sequence errors; 1 merged S2/S3 caption. One text edit:
`docs/figures/fig4_t6_ablation.svg` trailing label dropped "(see Table E6)".
`docs/report_frontmatter_template.md` embedding recipe now says insert the
SVG directly (Word accepts SVG; byte-identical asset) and lists
S3_stream_tokens.png / S4_dashboard_full.png as committed-but-unused
(md5 check against the draft's `word/media/`).
Options considered: [STUDENT]
Decision: [STUDENT]
Reason: [STUDENT]
Impact: two new scripts/tests in the fast lane (+12 tests); no change under
`src/`; no change to any file under `outputs/`; report edits (E-id source
lines, S2/S3 split, SEQ/REF fields) remain the author's to make in Word.
