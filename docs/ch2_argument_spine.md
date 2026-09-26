# Chapter 2 argument spine (F1 cohesion) — structure map, no prose

Task W4. Structure map for the literature review: opener/closer audit,
hand-off facts, source-to-code links, wording constraints, Table E12 body.
No sentence in this file is report prose; every "why" is a `[STUDENT]` slot.

Sources read: `docs/draft_as_submitted/ch2.md` (local mirror, gitignored;
paragraph anchors `[pXXXXXXXX]`, line numbers are that file's),
`docs/draft_as_submitted/references.md`, `docs/draft_as_submitted/ch5.md`,
`docs/draft_as_submitted/wordcount.json`, `docs/literature_matrix.md`,
`docs/referencing_notes.md`, `docs/report_skeleton.md` lines 56-95,
`docs/report_evidence_tables.md`, `DECISIONS.md`, `src/triguard/**`.
Code line numbers verified at commit `908b1e5` (2026-09-24).

Quoting rule: at most six words per anchor; the student's sentences are
not reproduced here.

The five properties named in the 2.7 gap sentence `[pb04b4da4]`
(ch2.md:67) and the short tags used below:

| tag | property as listed in [pb04b4da4] |
|---|---|
| TRIMODAL | text, image and audio evidence (one list item in the sentence) |
| LOCAL | local execution |
| RATIONALE | human-readable rationale |
| PROVENANCE | backend provenance |
| WORKFLOW | reviewer-facing workflow |

Note: `docs/report_skeleton.md:73-75` describes the E12 columns as
"multimodal, audio-aware, explainable/rationale, local/offline, end-to-end
decision" — a different five from the mirror's own gap sentence. Section F
below uses the column set fixed by the W4 task (Text / Image / Audio /
Local / Rationale / Provenance & workflow), which covers both lists.

---

## A. Opener / closer audit, sections 2.2-2.7

| section (heading anchor) | opener anchor + <=6 quoted words | closer anchor + <=6 quoted words | opens with a source name? | closes with a hand-off to the next section? | design-question slot | property deposited | consumed by |
|---|---|---|---|---|---|---|---|
| 2.2 Text `[p9b7f009c]` (ch2.md:7) | `[pae27b7aa]` (:9) "Lees et al. (2022) describe the" | `[pbdb75761]` (:13) "deployment requires more than a headline" | yes (Lees et al.) | no — closer is a text-only verdict; no pointer to image/OCR | [STUDENT] (heading is a topic label: "strong classifiers, narrow evidence") | TRIMODAL (text third); LOCAL (Perspective closed-cloud contrast, :9); PROVENANCE seed ("evidence rather than ... verdict", :11) | 2.3 `[p3bace98d]` (:23) OCR text routed to toxic-bert; 2.7 `[pb04b4da4]`; Ch5 T2 (E3) |
| 2.3 Image-text `[p4cf2e54c]` (:15) | `[p08bcbe97]` (:17) "Kiela et al. (2020) provide the" | `[p3bace98d]` (:23) "evidence routing are separate design problems" | yes (Kiela et al.) | no — closer states the routing principle; audio is not mentioned | [STUDENT] (heading names three topics, no question) | TRIMODAL (image third); RATIONALE seed (caption "inspectable language", :21); "evidence routing" principle (:23) | 2.4 (transcript is the audio analogue of OCR text — see B); 2.7 `[pb04b4da4]` "correct evidence route"; Ch5 T3 (E4/E4b) |
| 2.4 Audio `[pcc12378d]` (:25) | `[p7f25d85a]` (:27) "AudioSet established a broad ontology" | `[p5b352c47]` (:31) "weak evidence of real moderation capability" | partly — opens on a dataset name (AudioSet); author citation arrives at the sentence end | no — closer is about proxy datasets; the judge is not introduced. Mid-paragraph "does not package them" (:31) is the only forward pointer | [STUDENT] (heading: "complementary speech and event evidence") | TRIMODAL (audio third); LOCAL ("local feasibility", :29) | 2.5 (evidence packet = JudgeInput, see B); 2.7; Ch5 T4 (E5) |
| 2.5 Judge `[peb750438]` (:33) | `[pdeee25b3]` (:35) "Zheng et al. (2023) investigate language" | `[pf6323324]` (:39) "inter-rater comparison remain incomplete" | yes (Zheng et al.) | no — closer is a T7 caveat; governance not signalled | [STUDENT] (heading: "Orchestration and LLM-as-judge") | RATIONALE; LOCAL ("Local weights ... privacy", :37); PROVENANCE ("explicitly labelled rule fallback", :37) | 2.6 `[p6ec93d91]` (:45) rationale vs statement of reasons; 2.7; Ch5 T7 (E7/E7b), E6c |
| 2.6 Governance `[p1f497aaa]` (:41) | `[p981b31bf]` (:43) "Gorwa, Binns and Katzenbach (2020) argue" | `[p9c7d170d]` (:47) "automatically private or fair" | yes (Gorwa, Binns and Katzenbach) | no — closer qualifies LOCAL; 2.7's table is not announced | [STUDENT] (heading: "Explainability, privacy and governance") | WORKFLOW ("human review", :45); PROVENANCE ("provenance", :45); LOCAL (limits, :47); RATIONALE requirement (:43) | 2.7 `[pb04b4da4]` (:67) — the requirement list in :45 (auditability, provenance, human review, local processing) is the nearest antecedent of the five properties |
| 2.7 Synthesis `[pdce0d98f]` (:49) | `[p0e29a958]` (:51) "Table 2.1 makes the comparison" | `[pac82fdae]` (:69) "narrower but more defensible contribution" | no (table pointer) | partial — `[pb04b4da4]` (:67) names Chapters 3, 4 and 5; the closing paragraph itself does not | [STUDENT] | all five stated cold in `[pb04b4da4]` (:67); Table 2.1 `[tadb2d13b]` (:55-65) has no column for any of the five | Ch3 §3.4 (M1), Ch4, Ch5 (E4b "correct evidence route" claim, E6/E6c "confounders" claim) |

Facts behind the "no" column: none of the six closing paragraphs contains
the next section's number, heading word or first source name (checked by
reading ch2.md:13, :23, :31, :39, :47, :69).

---

## B. The five hand-off boundaries — the FACT each transition must carry

Facts only (file:line); the linking sentence is `[STUDENT]`.

### 2.2 -> 2.3 (text evidence is reused by the image section)
- Deployed text tier: `src/triguard/models/text_model.py:39-40`
  (`unitary/toxic-bert`, revision `4d6c22e7...`); offline floor
  `text_model.py:87-95` (TF-IDF + LogisticRegression); `_TRAIN` has 30
  entries (`text_model.py:48`; `len(text_model._TRAIN) == 30` run this
  session).
- Text output is stored as evidence, not a verdict: `schemas.py:20-21`
  (`TextEvidence.toxicity_score`); `pipeline.py:95` (`text_model.analyse`).
- The image section's headline finding depends on this route: OCR text ->
  toxic-bert delta F1 0.3742 vs keyword-cue route 0.0
  (`docs/report_evidence_tables.md:75-83`, Table E4b, source run
  `outputs/evaluation/20260705-111002/t3/results.json`, :63).
- Dataset for T2: `google/civil_comments` (`src/triguard/data/datasets.py:78`);
  E3 runs `20260623-074102` (sklearn) / `20260623-124802` (hf)
  (`report_evidence_tables.md:46-47`).

### 2.3 -> 2.4 (a second extraction-then-route modality)
- Image evidence = BLIP caption (`image_model.py:30-31`, pinned
  `Salesforce/blip-image-captioning-base` @ `82a37760...`) + opt-in OCR
  (`image_model.py:119` env `TRIGUARD_IMAGE_OCR`; `:126` `RapidOCR`).
- T3 was measured on Memotion, not Hateful Memes: `DECISIONS.md:334-374`
  (D-018; Hateful Memes gated; `Ahren09/MMSoc_Memotion`,
  `src/triguard/data/image_datasets.py:40`).
- Audio evidence has two fields: `schemas.py:35` (`transcript`) and
  `schemas.py:37` (`yamnet_tags`); Whisper loader `audio_model.py:111-114`,
  default model `tiny` (`audio_model.py:122`); YAMNet URL
  `audio_model.py:35` (`tfhub.dev/google/yamnet/1`).
- Routing fact that constrains the analogy (see E.4): the rule judge scores
  audio from `yamnet_tags` only (`llm_judge.py:160-161`); the transcript
  is not passed to the text model (`pipeline.py:95` analyses the input
  text only) and appears only in the Ollama evidence block
  (`llm_judge.py:361`).

### 2.4 -> 2.5 (all evidence becomes one packet for one judge)
- Packet type `JudgeInput` (`schemas.py:46`); judge default is `rule`
  (`llm_judge.py:94`, env `TRIGUARD_JUDGE`).
- Rule judge thresholds `>= 0.65` harmful / `>= 0.35` borderline
  (`llm_judge.py:185,188`); +0.15 boost only when two modalities already
  fired (`llm_judge.py:182-183`) — the structural reason the confounder
  experiment needs both judges (`DECISIONS.md:713-718`, D-028).
- Ollama prompt `llm_judge.py:55-76`; the cite-evidence rule is
  `llm_judge.py:70`; model tag `llama3:8b-instruct-q4_K_M`
  (`llm_judge.py:31`); host `localhost:11434` (`llm_judge.py:30`).
- T4 evidence: run `20260704-153729` (`report_evidence_tables.md:92`;
  Whisper WER 0.0971 corpus, YAMNet top-5 0.66, D-017 `DECISIONS.md:297-333`
  proxies LibriSpeech / ESC-50, AudioSet unobtainable).

### 2.5 -> 2.6 (rationale and provenance are contract fields; "statement of reasons" is not)
- `JudgeOutput.rationale` bounded 1-600 chars (`schemas.py:67`);
  `recommended_action` (`schemas.py:69`); `TriGuardResult.model_versions`
  (`schemas.py:91`).
- Fallback label `"ollama->rule"` (`pipeline.py:48,55`); fallback paths
  `llm_judge.py:99-113` (invalid JSON twice / unreachable / timeout).
- T7 floor metric 1.0 (18/18), 0 invented modalities, run
  `20260705-113456` (`report_evidence_tables.md:194-204`); caveats
  :205-243 (rationale-level binary; 17 native + 1 suspected fallback;
  6 rationales truncated at 200 chars; `usefulness_1to5` null).
- The 2.6 paragraph `[p6ec93d91]` (:45) already contains the requirement
  list (auditability, provenance, human review, local processing).

### 2.6 -> 2.7 (requirements become the five gap properties)
- Requirement list `[p6ec93d91]` (:45) <-> gap sentence `[pb04b4da4]` (:67):
  tags PROVENANCE, WORKFLOW, LOCAL map directly; RATIONALE and TRIMODAL are
  deposited earlier (2.5 / 2.2-2.4).
- What Table 2.1 `[tadb2d13b]` (:55-65) shows per row: modality/role,
  output, open/local path, limitation — none of the five properties is a
  column (E12 in section F fixes this).
- Cross-modal confounder table is EMPTY, not weak: `n_cross_modal_harmful`
  = 0 in both D-029 runs (`DECISIONS.md:783-784`;
  `report_evidence_tables.md:181-183`; runs `20260725-191000` rule /
  `20260725-191055` ollama, n=24).

---

## C. The 2.1 promise vs the actual openers (one line)

`[p80c90bf5]` (ch2.md:5) promises "organised by the design question"
(per source); the actual openers are author-name-first in 2.2, 2.3, 2.5,
2.6 (`[pae27b7aa]`, `[p08bcbe97]`, `[pdeee25b3]`, `[p981b31bf]`),
dataset-name-first in 2.4 (`[p7f25d85a]`) and table-pointer-first in 2.7
(`[p0e29a958]`), and none of the six section headings (:7, :15, :25, :33,
:41, :49) is phrased as a question. [STUDENT] to decide whether the
promise stands, is reworded, or is deleted (see [STUDENT] item 1).

---

## D. Source -> deployed component -> evidence track -> E-table -> run id

| source (references.md line) | deployed component (file:line) | evidence track | E-table (report_evidence_tables.md line) | run id(s) |
|---|---|---|---|---|
| Hanu and Unitary team (2020) Detoxify (:11) | `text_model.py:39-40` `unitary/toxic-bert` @ `4d6c22e7` | T2, T3 (OCR route), T6 | E3 (:44), E4b (:75), E6 (:106), E6c (:140) | `20260623-124802`; `20260705-111002`; `20260705-160858`; `20260725-191000` / `-191055` |
| Borkan et al. (2019) Civil Comments (:3) | dataset loader `data/datasets.py:78` `google/civil_comments` (not a model) | T2 | E3 (:44) | `20260623-074102`, `20260623-124802` |
| Lees et al. (2022) Perspective API (:17) | none — closed cloud service; contrast only | — | — | — |
| Kiela et al. (2020) Hateful Memes (:13) | none — gated; NOT the T3 dataset (D-018 `DECISIONS.md:334-374`) | design of the confounder set only (`DECISIONS.md:727`, D-028 README) | E6/E6c confounder rows: `n_cross_modal_harmful` 0 (:119, :181-183) | `20260725-191000` / `-191055` (both 0) |
| Sharma et al. (2020) Memotion (:35) | dataset loader `data/image_datasets.py:40` `Ahren09/MMSoc_Memotion` | T3 | E4 (:61), E4b (:75) | `20260705-111002` (E4 source :63); D-018 first run `20260704-172017` (`DECISIONS.md:363`) |
| Li, L.H. et al. (2019) VisualBERT (:21) | none — contrast (composition vs learned fusion) | — | — | — |
| Li, J. et al. (2022) BLIP (:19) | `image_model.py:30-31` `Salesforce/blip-image-captioning-base` @ `82a37760` | T3, T6 | E4 (:61), E4b (:75), E6 (:106), E6c (:140) | `20260705-111002`; `20260705-160858`; `20260725-191000` / `-191055` |
| RapidAI (n.d.) RapidOCR (:33) | `image_model.py:126` (`rapidocr_onnxruntime`), opt-in `image_model.py:119` | T3 OCR ablation | E4b (:75-83) | `20260705-111002` (D-023 `DECISIONS.md:478-520`) |
| Gemmeke et al. (2017) AudioSet (:7) | none directly — AudioSet audio unobtainable (D-017 `DECISIONS.md:297-306`); ontology labels only via YAMNet | T4 (ESC-50 proxy, approximate map) | E5 (:90) | `20260704-153729` |
| TensorFlow Hub (2024) YAMNet (:37) | `audio_model.py:35` `tfhub.dev/google/yamnet/1`; rule judge reads tags `llm_judge.py:160-161` | T4, T6 | E5 (:90), E6 (:106), E6c (:140) | `20260704-153729`; `20260705-160858`; `20260725-191000` / `-191055` |
| Radford et al. (2023) Whisper (:31) | `audio_model.py:111-114`; default `tiny` `audio_model.py:122` | T4 (LibriSpeech proxy), T6 | E5 (:90), E6, E6c | `20260704-153729`; `20260705-160858`; `20260725-191000` / `-191055` |
| Panayotov et al. (2015) LibriSpeech (:27); Piczak (2015) ESC-50 (:29) | dataset loaders `data/audio_datasets.py:6-10` (`openslr/librispeech_asr`, `ashraq/esc50`) | T4 | E5 (:90) | `20260704-153729` |
| Zheng et al. (2023) LLM-as-judge (:41) | prompt `llm_judge.py:55-76`; cite rule `:70`; fallback `:99-113` | T7 grounding; T6 two-judge | E7 (:194), E7b (:245), E6c (:140) | `20260705-113456`; `20260725-191000` / `-191055` |
| Llama Team, AI@Meta (2024) Llama 3 (:23); Ollama (n.d.) (:25) | `llm_judge.py:31` `llama3:8b-instruct-q4_K_M`; `llm_judge.py:30` localhost host | T7, T6 (ollama) | E7, E6c | `20260705-113456`; `20260725-191055` |
| Gorwa, Binns and Katzenbach (2020) (:9) | contract fields: `schemas.py:67` rationale, `:69` recommended_action, `:91` model_versions; label `pipeline.py:55` | none (design requirement); deviations E9 (:279) | E9 | — |
| European Parliament and Council (2022) (:5); UK Parliament (2023) (:39) | none — design requirement only (`[p6ec93d91]` :45) | — | — | — |

Confounder status for any "cross-modal" claim: D-028 infrastructure only
(`DECISIONS.md:709-753`), D-029 baseline with the table empty
(`DECISIONS.md:754-787`).

---

## E. Wording constraints (anchors + facts)

1. **"weak" vs "empty".** `[pb04b4da4]` (ch2.md:67) closes with
   cross-modal confounders "remain weak"; the Figure 5 caption
   `[pa9771d78-2]` (ch5.md:120) says the confounder subset is "empty";
   `[p9f914552]` (ch5.md:185) also says "empty". Fact:
   `cross_modal_ablation.n_cross_modal_harmful` = 0 in both runs
   (`report_evidence_tables.md:181-183`; `DECISIONS.md:783-784`); no
   committed run scores any confounder item, so no strength measurement
   exists. [STUDENT] to choose one word and use it in both chapters; facts
   to draw on: zero items in the table, zero measurements.
2. **Hallucination check = a floor metric.** `[pf6323324]` (ch2.md:39)
   already frames T7 as a floor test. Wording constraint: the facts below
   support a floor-metric description only; no committed evidence exists
   for a stronger claim (e.g. "empirically addressed"). [STUDENT] chooses
   the phrasing. Facts to hold it to:
   rationale-level binary >= 1 token (`grounding.py:37-48` per
   `report_evidence_tables.md:235-236`); 17 native + 1 suspected
   rule-fallback rationale (:217-225); six rationales truncated at 200
   chars (:232-234); `usefulness_1to5` null for all 18 (:237-238).
3. **D-029 counts only with the single-run caveat.** Any use of the E6c
   rule-vs-llama3 numbers (`report_evidence_tables.md:152-159`) carries:
   single llama3 run, n=24, temperature 0 but not bit-reproducible
   (`DECISIONS.md:779-781`); unimodal rows degenerate in both judges
   (`DECISIONS.md:766-771`; `report_evidence_tables.md:190-193`).
4. **Transcript route claim.** `[p03ba2449]` (ch2.md:29) states the
   transcript enters "the existing text reasoning path". Code: the text
   model scores only the submitted text (`pipeline.py:95`); the rule judge
   scores audio from `yamnet_tags` alone (`llm_judge.py:160-161`); the
   transcript is read only by the Ollama prompt (`llm_judge.py:361`).
   [STUDENT] to reconcile (either qualify as "LLM path only" or describe
   the actual route).
5. **YAMNet attribution.** Table 2.1 row `[tadb2d13b]` (ch2.md:62) attaches
   "Audio events ... Open model path" to Gemmeke et al. (2017); the code
   pins TensorFlow Hub's `yamnet/1` (`audio_model.py:35`), cited as
   TensorFlow Hub (2024) in `[p7f25d85a]` (:27). `report_skeleton.md:83-84`
   (F4) asks to verify or drop the Gemmeke -> YAMNet attribution.
6. **Retry wording.** `[p17674d15]` (ch2.md:37) "stricter retry on the
   non-streaming path" — consistent with `llm_judge.py:224` (retry once
   with a stricter prompt) and `:303` (no retry on the streaming variant).
7. **"thirty-example TF-IDF baseline"** `[p3d7920ab]` (ch2.md:11) —
   `_TRAIN` length 30 (`text_model.py:48`; counted this session). Consistent;
   Table E11 (owned by another task) is the corpus card to cite.
8. **Use of "packages"**: `[p5b352c47]` (:31) says prior work "does not
   package them"; `report_skeleton.md:88` asks for the mirror-image fact
   — the packaging exists: `audio_model.py` real tier (D-014
   `DECISIONS.md:180-203`), evidence fields `schemas.py:35,37`.

---

## F. For integration

### Table E12 — Table 2.1 replacement body (Ch2 §2.7)

Cell source: `docs/literature_matrix.md:7-14` (matrix columns Method /
Limitation / Gap Identified), reduced to yes / no / partial. The
reduction is this task's reading of those cells; each "partial" is
flagged for the student's confirmation in the notes below. Limitation
cells are the student's own table content and stay `[keep existing]` with
the row anchor. TriGuard row = verified code facts (file:line in the
notes). Caption slot: `[STUDENT]` (numbered caption per P2).

| Source | Text | Image | Audio (speech / events) | Local execution | Human-readable rationale | Backend provenance & reviewer workflow | Limitation for TriGuard's goal |
|---|---|---|---|---|---|---|---|
| Lees et al. (2022) | yes | no | no / no | no | no | no | [keep existing] `[tadb2d13b]` row 1 (ch2.md:58) |
| Kiela et al. (2020) | yes | yes | no / no | partial (n1) | no | no | [keep existing] `[tadb2d13b]` row 2 (ch2.md:59) |
| Li, L.H. et al. (2019) | yes | yes | no / no | partial (n2) | no | no | [keep existing] `[tadb2d13b]` row 3 (ch2.md:60) |
| Li, J. et al. (2022) | partial (n3) | yes | no / no | yes | no | no | [keep existing] `[tadb2d13b]` row 4 (ch2.md:61) |
| Gemmeke et al. (2017) | no | no | no / yes | yes (n4) | no | no | [keep existing] `[tadb2d13b]` row 5 (ch2.md:62) |
| Radford et al. (2023) | no (n5) | no | yes / no | yes | no | no | [keep existing] `[tadb2d13b]` row 6 (ch2.md:63) |
| Zheng et al. (2023) | yes | no | no / no | partial (n6) | yes | no | [keep existing] `[tadb2d13b]` row 7 (ch2.md:64) |
| Gorwa, Binns and Katzenbach (2020) | no | no | no / no | no | no (n7) | no (n7) | [keep existing] `[tadb2d13b]` row 8 (ch2.md:65) |
| TriGuard (this project) | yes | yes | yes / yes | yes | yes | yes | [STUDENT] — facts: E3 toxic recall 0.2812 (`report_evidence_tables.md:53`); E4 AUROC 0.566 (:69); E6c confounder rows empty (:181-183); T7 floor metric only (:235-236); single llama3 run (D-029) |

Notes (facts behind the reduced cells):
- n1 Kiela: `literature_matrix.md:8` "Benchmark only — not a deployable
  system; ... gated access"; baselines are research code — mark "partial"
  or "no" [STUDENT].
- n2 Li, L.H.: `literature_matrix.md:9` "Reproducible; widely used as a
  baseline" and "Depends on pre-extracted Faster-RCNN regions" — research
  implementation (`[tadb2d13b]` row 3 "Research implementation").
- n3 Li, J. (BLIP): `literature_matrix.md:13` lists image captioning +
  VQA (text is the caption output / question input of an image model); the
  matrix has no text-moderation cell for this row — reduced to "partial";
  [STUDENT] to confirm.
- n4 Gemmeke: `literature_matrix.md:10` "pretrained weights freely
  available" refers to the YAMNet line, not the AudioSet paper itself — see
  E.5 before keeping "yes" against Gemmeke.
- n5 Radford: `literature_matrix.md:11` "Transcription only — no toxicity
  classification".
- n6 Zheng: `literature_matrix.md:12` "Closed-source judge models"; the
  pattern is model-dependent (`[tadb2d13b]` row 7 "Model-dependent").
- n7 Gorwa: `literature_matrix.md:14` "No empirical model evaluation" —
  requirements source, not an implementation.
- TriGuard row code facts: Text `text_model.py:39-40`; Image
  `image_model.py:30-31` (+ OCR `:126`); Audio speech `audio_model.py:111-114`,
  events `audio_model.py:35`; Local — all backends resolve to local
  processes, Ollama host `llm_judge.py:30` (`localhost:11434`), mock/offline
  defaults `text_model.py:15`, `image_model.py:11`, `audio_model.py:12`;
  Rationale `schemas.py:67`; Provenance `schemas.py:91` `model_versions` +
  `pipeline.py:55` `"ollama->rule"`; Workflow `schemas.py:69`
  `recommended_action` + `/ui` compare and `/dashboard` (`CLAUDE.md`
  status table row "FastAPI demo").

### DECISIONS entry candidate (for the Integrate stage to place)

- Title: check_citations tool + Ch2 argument spine (F1).
- Facts: `scripts/check_citations.py` (stdlib), `tests/test_check_citations.py`
  (5 tests); run on `docs/draft_as_submitted/ch2.md --refs
  docs/draft_as_submitted/references.md` -> cited-not-referenced 0,
  referenced-not-cited 1 (Lazar 2023 — cited in another chapter; full.md
  run gives 0), bare-name-without-citation 2 (Hateful Memes ch2.md:17,
  VisualBERT ch2.md:19); strict `--every-mention` mode: 9 uncited-sentence
  mentions (ch2.md:5, 11, 17, 19, 23, 31 x3, 39). The audit expectation
  "Faster-RCNN + MobileNet" is NOT reproduced: both names sit in sentences
  that carry a citation (ch2.md:19 Li, L.H. et al.; ch2.md:27 TensorFlow
  Hub); a names-file mapping (`Faster-RCNN | Ren, 2015`) would flag them —
  the reference targets are UNVERIFIED-EXTERNAL (see H).

---

## G. Budget line

Ch2 prose words 1,762 / prose + table cells 1,905
(`docs/draft_as_submitted/wordcount.json` `chapters.ch2.prose_words`,
`.prose_plus_table_words`) vs target 2,300 / cap 2,500 -> headroom 538
(prose) / 595 (with table cells). Note `docs/report_skeleton.md:56` states
"submitted draft 1,814 words" (orchestrator-supplied count, different
basis) — re-key to wordcount.json.

---

## [STUDENT]

Questions and pointers only.

1. Design question per section (to honour or delete the promise in
   `[p80c90bf5]`, ch2.md:5): 2.2 — what can a text classifier decide on its
   own? 2.3 — when does image+text meaning need fusion, and which route
   carries recovered text? 2.4 — which two audio questions (what was said /
   what sounded) does moderation need? 2.5 — can a judge explain without
   inventing? 2.6 — what must a decision expose to be reviewable? Draft
   phrasing is yours; sub-heading slots are the six headings at :7, :15,
   :25, :33, :41, :49.
2. Five hand-off sentences (one each at the closers `[pbdb75761]`,
   `[p3bace98d]`, `[p5b352c47]`, `[pf6323324]`, `[p9c7d170d]`), each naming
   the tag it deposits (section B facts). Budget: 538 words headroom
   (section G).
3. 2.7 alignment: replace "weak" in `[pb04b4da4]` with the word used in
   `[pa9771d78-2]` / `[p9f914552]` (E.1); decide whether `[pac82fdae]`
   "OCR routing into a testable ablation" needs "on Memotion" (D-018).
4. Transcript route sentence `[p03ba2449]` (E.4): qualify or re-describe.
5. YAMNet attribution row (E.5): keep Gemmeke as the ontology source and
   TensorFlow Hub (2024) as the model source, or drop the "Open model path"
   cell from the Gemmeke row.
6. DSA article numbers to reconcile: the draft cites **Article 17** only
   (`[p6ec93d91]`, ch2.md:45; ch1.md:13 `[p3d95ce74]` gives no number);
   `docs/referencing_notes.md:164` lists Articles 14, 17, 27. Which
   articles actually carry the statement-of-reasons and transparency duties
   in Regulation (EU) 2022/2065 is UNVERIFIED-EXTERNAL in this session —
   VERIFY against the eur-lex text at `references.md:5` before adding 14 /
   27.
7. Bare names printed by the checker: "Hateful Memes" (ch2.md:17) and
   "VisualBERT" (ch2.md:19) never share a sentence with a citation — move
   or add the Kiela / Li, L.H. citation into those sentences, or accept.
   Faster-RCNN (ch2.md:19) and MobileNet (ch2.md:27) have no reference of
   their own: cite (Ren et al. — VERIFY year / venue; Howard et al. —
   VERIFY year / venue) or reword to avoid the bare model names. ViLBERT
   does not appear in ch2.md (grep this session), so
   `report_skeleton.md:82-83` / `:342` "decide ViLBERT" is moot for the
   mirror text.
8. Lazar (2023) `references.md:15` is not cited in Ch2 — confirm it is
   cited elsewhere (full.md run: 0 referenced-not-cited).
9. Strict-mode list (9 mentions, section F DECISIONS candidate) is
   informational: each is a repeat mention in a sentence without a
   citation, after an earlier cited mention. [STUDENT] to decide whether
   any of them needs a citation; items 6-7 above list the bare names and
   uncited model names separately.
