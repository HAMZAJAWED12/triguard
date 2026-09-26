# Final video — shot list (P1)

Status: plan only. Facts and pointers; NO narration text anywhere in this file
(the student writes and speaks every sentence). Companion files:
`scripts/video_preflight.sh` (read-only go/no-go check),
`docs/video_number_card.md` (every number visible in shots 7-8, verbatim),
`docs/figures/video/{title_card,tiers_card,close_card}.svg` (1920x1080 cards).
The preliminary-era script stays as the historical record at
`docs/Video_Script_Prototype_Demo.md`.

## Constraints from the FINAL brief

Facts as supplied to this task; [STUDENT] re-check each line against the
brief document before recording (this repo holds no copy of the brief).

- Length: 3-5 minutes.
- Must demonstrate the project WORKING and show all important features;
  explain a little how they work / justify the approaches taken.
- Appropriate visuals.
- Audio must be the student's own voice — no AI-generated voice; not sped up.
- The student need not appear on camera.
- Videos outside the length or the other constraints are penalised.
- Marked by criterion 17 (appropriate video demonstrating the working
  program, the achievements and the student's understanding) and
  criterion 18 (well thought through, well structured, impactful).
- Earlier criteria used in this plan follow the numbering already in
  `docs/report_skeleton.md:33-37` (crit 2 diagrams/figures; crit 4 critical
  evaluation of literature; crit 10-13 evaluation coverage / critical
  analysis; crit 16 originality). [STUDENT] confirm those numbers against
  the brief.

## Budget

9 shots, 260 s = 4:20 — 40 s under the 5:00 cap, 80 s over the 3:00 floor.
Measure the export in VLC (pre-record checklist item 9); the budget is the
recording target, not a claim about the file.

| # | shot | s | running total |
|---|---|---|---|
| 1 | Title card | 10 | 0:10 |
| 2 | Problem + as-built architecture | 35 | 0:45 |
| 3 | Pre-flight proof | 20 | 1:05 |
| 4 | Preset "Real committed media" — single verdict | 30 | 1:35 |
| 5 | Compare mode with uploads | 40 | 2:15 |
| 6 | Stream mode | 35 | 2:50 |
| 7 | /dashboard | 40 | 3:30 |
| 8 | Critical evaluation on screen | 35 | 4:05 |
| 9 | Close card | 15 | 4:20 |
| | total | 260 | 4:20 |

## Shot table

Server = the real-backend server booted by `scripts/demo_up.sh` on
`http://127.0.0.1:8006` (`scripts/demo_up.sh:13` default port). Frame
references from the committed screenshots (commit a8f2bb2 per
`docs/SESSION_HANDOFF.md:15`): `docs/figures/screenshots/S1_ui_presets.png`,
`S2_compare.png`, `S3_stream_tokens.png`, `S3_stream_final.png`,
`S4_dashboard.png`, `S4_dashboard_full.png`.

| # | shot | s | on screen (exact URL / preset / file) | evidence it demonstrates (file:line or results.json key) | criterion | facts to mention (pointers only) |
|---|---|---|---|---|---|---|
| 1 | Title card | 10 | `docs/figures/video/title_card.svg` opened full-screen in the browser (fill the `[STUDENT: name]` slot first) | project identity `CLAUDE.md:8-14`; decision-support wording `CLAUDE.md:91-94`, `src/triguard/api/static/index.html:76-77` | 18 | title; module CM3070; template CM3020 Project Idea 1; "decision-support prototype" |
| 2 | Problem + as-built architecture | 35 | `docs/figures/fig1_architecture.svg` full-screen (NOT `docs/architecture.png` — that is the preliminary six-layer drawing); optional second frame `docs/figures/video/tiers_card.svg` | pipeline wiring `src/triguard/orchestrator/`; frozen schemas `CLAUDE.md:36-37`; real-vs-mock tiers `CLAUDE.md:60-71`; perception-once design `src/triguard/api/main.py:277-282` | 2, 4, 17, 18 | three wrappers -> Pydantic evidence -> judge -> `TriGuardResult`; rule judge default, llama3 opt-in, `ollama->rule` fallback label (`CLAUDE.md:66-67`); regulatory motivation pointers in `docs/chapter1_introduction.md` [STUDENT picks the one-liner] |
| 3 | Pre-flight proof | 20 | terminal: `wsl -e bash /mnt/c/dev/triguard/scripts/demo_up.sh` — the six `[OK]` lines and `ALL GREEN — open http://127.0.0.1:8006/ui`; then browser `http://127.0.0.1:8006/ui` with the banner line `server backends: text=hf · image=blip · audio=real · OCR on · default judge=rule` | `[OK]` lines `scripts/demo_up.sh:40,45,61,63,70,77`; ALL GREEN `scripts/demo_up.sh:82`; banner `src/triguard/api/static/index.html:305-308` fed by health keys `src/triguard/api/main.py:85-100` | 17 | banner values are read from the health endpoint keys (`main.py:85-100`, `index.html:305-308`), not hard-coded; `USE_TF=0` mandatory (`scripts/demo_up.sh:47-51`, D-016); MOCK MODE suffix would appear if all three were mock (`index.html:303,308`) |
| 4 | Preset "Real committed media" — single verdict | 30 | `/ui` -> preset button titled `Real committed media` (`src/triguard/api/main.py:67-73`); result block: badge + `recommended action:` + rationale + uncertainties + risk score, then cards `Text` / `Image` / `Audio` / `Models used`, `latency:` line | preset POST `index.html:273-277` -> `main.py:217-251` (`judge_mode=None`, default judge); render `index.html:171-178`; verdict fields `index.html:160-168`; evidence cards `index.html:133-158`; inputs `data/sample_inputs/sample_multimodal_real.json` (text + `blip_test.png` + `audio_test.wav`) | 17 | `Models used` card is `model_versions` (real-hf / real-blip / real-audio expected — `demo_up.sh:69-70` greps `real-hf`); the word "recommended" (`index.html:163`); uncertainties list when present (`index.html:165-166`) |
| 5 | Compare mode with uploads | 40 | `/ui` form: Text = [STUDENT: own sentence or the sample text], Image = `data/sample_inputs/blip_test.png`, Audio = `data/sample_inputs/audio_test.wav`, Judge mode = `Compare rule vs llama3` (`index.html:100-101`) -> `Analyse`; two cards `Rule judge (N ms, incl. perception)` and `llama3 judge — ollama (N ms)`; note line `perception ran once; the same evidence was judged twice`; `Models used (perception)` card | endpoint `src/triguard/api/main.py:271-325` (note string `:305`; same `JudgeInput` re-judged `:292-298`; label `:321`); render `index.html:180-195` | 16, 17 | one perception pass, two judges on identical evidence; `judge_label` is `ollama` only when llama3 answered (`main.py:321`), otherwise `ollama->rule` with the on-screen warning (`index.html:186-188`); llama3 latency shown next to the rule latency |
| 6 | Stream mode | 35 | same inputs, Judge mode = `Stream llama3` (`index.html:102-103`) -> `Running perception…` -> card `Rule judge (instant, N ms incl. perception)` + evidence cards -> `llama3 judge (streaming)` token box filling -> `Final schema-validated verdict (judge label ollama):` + badge | endpoint `src/triguard/api/main.py:333-395` (event types `:341-346`; final label `:387-392`); client `index.html:198-255` (token path `:239-240`; final `:241-251`) | 17, 18 | tokens are presentation-only; the final verdict is the schema-validated one (`main.py:344-346`); if the final event is not from ollama the warning at `index.html:243-246` appears and the streamed draft is NOT the verdict |
| 7 | /dashboard | 40 | `http://127.0.0.1:8006/dashboard`; banner paragraph (`dashboard.html:45-50`); sections T2, T3, T4, T6, T7, T8 in that order; each section's `source:` and `config:` lines | banner `src/triguard/api/static/dashboard.html:45-50`; per-section source/config lines `dashboard.html:73-79`; `/eval/summary` `src/triguard/api/main.py:463-528`; newest-run rule `main.py:469`, sorted scan `:481`, `tracks[track] = entry` `:515`; all numbers listed in `docs/video_number_card.md` | 10-13, 17 | every number is copied verbatim from a `results.json`; T6 on screen is run `20260725-191055` (`config.judge` = `ollama`, multimodal accuracy `0.4583`) — newest-run rule `main.py:469,481,515`; Table E6 (`docs/report_evidence_tables.md:108-119`) cites the rule run `20260705-160858` (`0.625`) and Table E6c (`:160-161`) holds both — [STUDENT] decides how the on-screen run id is handled; `verify the run ids against the committed evidence` (`dashboard.html:48-49`) |
| 8 | Critical evaluation on screen | 35 | stay on `/dashboard` and scroll: T6 provenance box (`dashboard.html:151-152`), `cross-modal confounder items: 0` box (`:160-162`), T7 note box (`:173`), T3 OCR note (`:125`), each section's limitations list (`:68-71`); optional second frame: the committed `docs/report_evidence_tables.md` E6c caveats (`:172-195`) and E7 caveats (`:207-245`) — that file is modified in the working tree (git `M`), so show `git show HEAD:docs/report_evidence_tables.md` or commit first (checklist item 6) | T6 `limitations[]`, `manifest_provenance`, `cross_modal_ablation.n_cross_modal_harmful` (both T6 files); T7 `note`; T3 `ocr_ablation.note`, `limitations[2]`; E6c `docs/report_evidence_tables.md:142-195`; E7 `:196-245`; T7/T8 on v1 n=18 vs T6 on v2 n=24 `docs/feedback_traceability.md:45` | 10-13, 17, 18 | rule vs llama3 multimodal accuracy `0.625` vs `0.4583`, single llama3 run (`report_evidence_tables.md:160-161,173-176`); T7 `18/18 grounded; 17 native + 1 suspected rule-fallback (MB1)` (`:223-224`), floor metric (`:237-238`); confounder rows empty (`n_cross_modal_harmful` = 0); T2 toxic recall `0.2812` (`:54`); T3 F1 is a flag-vs-label decision measure, not a classifier F1 (T3 `limitations[2]`) |
| 9 | Close card | 15 | `docs/figures/video/close_card.svg` with the `Achieved` / `To improve` slots filled by the student from the candidate list below | candidate facts below, each with its pointer | 17, 18 | [STUDENT] picks 3-4 per column; nothing is pre-selected in the SVG |

## Fallback if Ollama is down at recording time

- Shot 3: `scripts/demo_up.sh` prints `[FAIL] Ollama unreachable (llama3
  segments will fall back to rule)` (`:40`) and ends with `SOMETHING RED`
  (`:84`), exit 1 (`:86`). The API can still be up (`[OK]` at `:61,63,70`);
  the compare warm-up at `:75-78` reports `[FAIL] compare fell back to rule`.
  [STUDENT] decides whether to show that terminal frame honestly or cut to
  the `/ui` banner only.
- Shot 5 becomes the honest-fallback shot: the right-hand card reads
  `llama3 judge — ollama->rule (N ms)` and shows the warning `Ollama was
  unavailable or returned invalid JSON — this column is the rule judge
  acting as fallback, honestly labelled ollama->rule`
  (`src/triguard/api/static/index.html:186-188`; label from
  `src/triguard/api/main.py:321`).
- Drop shot 6 (35 s) and give its seconds to shot 8 (35 + 35 = 70 s). Total
  stays 260 s.
- The stream path would also fall back (`index.html:243-246`) — do not use it
  to demonstrate llama3 when Ollama is down.

## Pre-record checklist (pointers; every item is a fact to verify, not a line to say)

0. [STUDENT] Measure the preliminary MP4's actual runtime (VLC / file
   properties) and note which side of the 3:00-5:00 window it fell on. The
   preliminary plan claimed ~3 min 23 s (`docs/Video_Script_Prototype_Demo.md`
   timing summary); the file's true runtime is not recorded in the repo.
1. `wsl -e bash /mnt/c/dev/triguard/scripts/demo_up.sh` -> `ALL GREEN`
   (`scripts/demo_up.sh:82`); six `[OK]` lines at `:40,45,61,63,70,77`.
2. `ollama ps` (WSL) shows `llama3:8b-instruct-q4_K_M`
   (`scripts/demo_up.sh:14`; `src/triguard/models/llm_judge.py:31`). keep_alive
   facts: demo_up warm-up sends `keep_alive 60m` (`scripts/demo_up.sh:44`)
   while its header comment says `30m` (`:8`, stale); the app judge sends
   `TRIGUARD_OLLAMA_KEEP_ALIVE` default `30m` on every call
   (`src/triguard/models/llm_judge.py:48-52`, used at `:244,269`) — so
   after the first in-app judgement the residency window is 30 m from that
   call; re-run demo_up.sh or keep judging if the gap before shot 5 is long.
3. `/ui` banner shows `text=hf · image=blip · audio=real · OCR on`, not
   `MOCK MODE` (`src/triguard/api/static/index.html:305-308`).
4. Media decision [STUDENT]: presets `safe` / `borderline` / `harmful` point
   at gitignored `data/local_demo/` files (`data/sample_inputs/sample_safe.json`,
   `sample_borderline.json`, `sample_harmful.json`; names listed in
   `data/local_demo/README.txt`; ignore rule `.gitignore:27`). Without those
   files the presets run the mock wrappers for image/audio (README.txt lines
   "Missing files are fine"). Either drop self-made benign files with exactly
   those names into `data/local_demo/` (ethics rules at the foot of
   README.txt) or record only with preset `multimodal_real` + the committed
   uploads `data/sample_inputs/blip_test.png` and `audio_test.wav`.
5. `git status --porcelain -- outputs/evaluation` prints nothing. The
   dashboard flags any uncommitted `results.json` with `UNCOMMITTED RUN`
   (`src/triguard/api/main.py:442-460`, `dashboard.html:80-83`). At the time
   this plan was written the command printed two untracked
   `derived_intervals.json` files (runs `20260623-074102`, `20260623-124802`,
   `t2/`) — not `results.json`, so no badge, but `scripts/video_preflight.sh`
   check (d) still FAILs until they are committed or removed (owned by the
   Integrate stage; do not delete from this task).
6. Keep WIP off screen: `git status --porcelain` (whole repo) lists modified
   and untracked files; do not open them in the editor during recording.
   `scripts/video_preflight.sh` prints them as INFO.
7. Browser zoom >= 125 %; terminal font >= 14 pt (preliminary checklist
   `docs/Video_Script_Prototype_Demo.md`, "Recording checklist").
8. One take per shot; own voice; no speed change (brief constraints above).
9. Export MP4 H.264 + AAC; measure the runtime in VLC; must be 3:00-5:00.
10. Stop servers afterwards: `study/commands_reference.md:43-47`
    (`wsl -e bash -lc "pkill -f 'uvicorn triguard.api.main'; pkill -f 'ollama serve'"`).

Run `wsl -e bash /mnt/c/dev/triguard/scripts/video_preflight.sh` after step 1;
it covers items 1 (health keys), 2 (`ollama ps`), 4 (media presence), 5 and 6
(git status) and prints the run ids the dashboard will show.

## Candidate facts for the close card (student selects; none pre-filled)

Achieved — candidates (pointer each):
- Real tiers behind flags: toxic-bert / BLIP+RapidOCR / Whisper+YAMNet /
  llama3 via Ollama, mock defaults intact (`CLAUDE.md:63-67`).
- Honest fallback labelling `ollama->rule` in `model_versions`
  (`CLAUDE.md:67`; `src/triguard/api/main.py:321,387-392`).
- Perception-once compare and SSE streaming demo (`main.py:271-325,333-395`).
- Dashboard that only copies committed `results.json` values
  (`dashboard.html:45-50`; `main.py:403-404`).
- Evaluation tracks T2-T8 with committed envelopes (`outputs/evaluation/`;
  Tables E3-E8 in `docs/report_evidence_tables.md`).
- Fast suites green on 2026-09-24: Windows offline 83 passed / 11 skipped;
  WSL 95 passed / 10 skipped (run on the uncommitted working tree, which
  sibling tasks were still adding tests to — re-measure before recording; see
  `docs/Video_Script_Prototype_Demo.md:5`).
- Student-owned v2 evaluation set, n=24 (T6 `manifest_provenance`).

To improve — candidates (pointer each):
- Cross-modal confounder rows empty: `cross_modal_ablation.n_cross_modal_harmful`
  = 0 in both T6 runs (`docs/report_evidence_tables.md:183-185`).
- Single llama3 run, non-deterministic judge (T6 ollama `limitations[4]`;
  `report_evidence_tables.md:173-176`).
- llama3 multimodal accuracy `0.4583` below the rule judge's `0.625` on the
  same set (`report_evidence_tables.md:160-161`).
- T7 grounding is a floor metric; human `usefulness_1to5` column null for
  all 18 (`report_evidence_tables.md:237-241`; `docs/feedback_traceability.md:42`).
- T7/T8 ran on the v1 18-item set, T6 on v2 n=24 (`docs/feedback_traceability.md:45`).
- toxic-bert toxic recall `0.2812` at threshold 0.5 (`report_evidence_tables.md:54`).
- Borderline F1 `0.0` for the rule judge in every T6 condition
  (`report_evidence_tables.md:116-119`).
- Real-backend cold start `4075.1` ms, peak RSS `2873.7` MB
  (`report_evidence_tables.md:275`).

## For integration

Skeleton checklist lines (for `docs/report_skeleton.md`, "Pre-submission
checklist", next to the existing runtime line at `:369-370`):

```
- [ ] Preliminary MP4 runtime measured (VLC) and recorded [STUDENT]; final
      MP4 runtime measured in VLC and within 3:00-5:00 (plan budget 4:20,
      `docs/Video_Shot_List_Final.md`).
- [ ] `wsl -e bash /mnt/c/dev/triguard/scripts/video_preflight.sh` exits 0
      immediately before recording (health hf/blip/real/OCR, `ollama ps`,
      local_demo media, `outputs/evaluation` clean, `/eval/summary` run ids).
```

DECISIONS draft (number assigned by the Integrate stage; fields as in
Decision 034):

```
## Decision 0NN: P1 — final video shot list + preflight; dashboard newest-run rule surfaced
Date: 2026-09-24
Status: draft — Options/Decision/Reason to be completed by the author
Source draft: `docs/Video_Shot_List_Final.md` '## For integration'.

Context: the FINAL brief's video constraints (3-5 min, own voice, not sped
up, working program + features + understanding; criteria 17/18) replace the
preliminary plan in `docs/Video_Script_Prototype_Demo.md` (now banner-marked
historical). A 9-shot, 260 s plan was written with file:line evidence per
shot and an Ollama-down fallback (`index.html:186-188`). `scripts/video_preflight.sh`
(WSL, read-only: health keys `main.py:85-100`, `ollama ps`, `data/local_demo`
presence, `git status --porcelain -- outputs/evaluation`, `/eval/summary`
run ids) gives a go/no-go before recording. `docs/video_number_card.md`
lists every dashboard number verbatim with its results.json key.
Fact surfaced: `/eval/summary` keeps the newest run per track
(`main.py:469,481,515`), so `/dashboard` shows T6 run 20260725-191055
(ollama judge, multimodal accuracy 0.4583) while Table E6 cites the rule run
20260705-160858 (0.625) and E6c holds both runs; [STUDENT] decides how the
on-screen run id is handled. Suite counts measured 2026-09-24 on the working tree:
Windows 83 passed / 11 skipped, WSL 95 passed / 10 skipped (re-measure at
integration; sibling tasks were adding tests during the measurement).
Options considered: [STUDENT]
Decision: [STUDENT]
Reason: [STUDENT]
Impact: files added — `docs/Video_Shot_List_Final.md`, `scripts/video_preflight.sh`,
`docs/video_number_card.md`, `docs/figures/video/title_card.svg`,
`tiers_card.svg`, `close_card.svg`; `docs/Video_Script_Prototype_Demo.md`
banner lines only (counts, pointer, architecture figure path). No change
under `src/`, `outputs/` or `scripts/demo_up.sh`.
```
