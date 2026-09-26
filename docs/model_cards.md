# Model cards — TriGuard (facts only; W3 / F4)

Working document for Ch3 §3.4 (component selection) and the Ch2 audio
paragraph. Every cell is a repo fact with a pointer (file:line, results.json
key path, git/WSL command output) or is marked `UNVERIFIED-EXTERNAL` /
`VERIFY` / `MISSING`. No cell is report prose; where a justification is needed
the cell says `[STUDENT]`. Line numbers are as of commit `908b1e5`.

Machine-checked tokens (see `scripts/verify_model_cards.py`; test
`tests/test_verify_model_cards.py`):

- inline-code span with prefix **code:** — `_NAME` `=` python literal;
  compared with the live module attribute (wrappers imported mock-safe, no
  weights).
- prefix **t4:** — key path `=` literal; compared with
  `outputs/evaluation/20260704-153729/t4/results.json`.
- prefix **pin:** — package `==` version; compared with
  `requirements-full.txt`; package `=MISSING` asserts the package is absent
  from that file.

Draft-report anchors (`docs/draft_as_submitted/`, local-only) are given as
`[pXXXXXXXX]`; no student prose is reproduced here.

---

## 1. External-verification checklist (all UNVERIFIED-EXTERNAL)

Nothing in this table was opened in-session. No publisher, year, licence,
DOI or page number is asserted here beyond what a named repo line already
contains; those repo lines are themselves unverified against the sources.

| # | Item | What to verify (at submission) | Where it lands | Which repo sentence changes if false |
|---|---|---|---|---|
| 1 | TF-Hub `google/yamnet/1` model card | Publisher; input spec (code assumes 16 kHz mono float32 waveform — `audio_model.py:36`, `:92`, `:106`); output spec (code unpacks three outputs `scores, _, _ = model(c)` `:179` and reads the class-map CSV column `display_name` `:153-155`); class count (submitted ch2 `[p7f25d85a]` says 521; `docs/referencing_notes.md:79` says 632 — the two repo statements disagree; which count is the model's output size and which is the AudioSet ontology size is UNVERIFIED-EXTERNAL, so at least one of the two lines changes once the card is read); backbone (repo says MobileNet: `docs/literature_matrix.md:10`, ch2 `[p7f25d85a]`); licence (stated nowhere in the repo — grep for "yamnet" + "licen" returns nothing); whether `https://tfhub.dev/google/yamnet/1` (`audio_model.py:35`; `hub.load` `:151`) still resolves (tfhub.dev has been redirecting to Kaggle Models — UNVERIFIED) and what year the card should carry | Ch2 audio paragraph; Ch3 Table M1; Ch4 `[pe2f09a93]`; reference entry `[p47fe03b3]` (TensorFlow Hub, 2024) | ch2 `[p7f25d85a]` (class count, backbone, year); `[p47fe03b3]` (URL, year); `docs/referencing_notes.md:79` (632 vs 521) |
| 2 | Does Gemmeke et al. (2017) describe YAMNet at all? | The AudioSet paper title is an ontology + dataset paper (`docs/referencing_notes.md:73`). Whether it introduces the YAMNet model, its weights, or any "MobileNet-style CNN baselines" is UNVERIFIED. Repo lines that assume it does: `docs/referencing_notes.md:79` ("YAMNet/MobileNet-style CNN baselines"), `:82` ("YAMNet (the model TriGuard plans to use) is trained on AudioSet"), `docs/literature_review_draft.md:38` ("of which YAMNet is the most reused"), `:88` ("supplies YAMNet weights and the event ontology"), `docs/literature_matrix.md:10` ("AudioSet (YAMNet line)"), `docs/project_design_draft.md:64` (cites Gemmeke for "Whisper (small) + YAMNet"). Submitted draft status: ch2 `[p7f25d85a]` already separates the two — AudioSet -> Gemmeke et al. (2017), YAMNet -> TensorFlow Hub (2024); but Table 2.1 row `[tadb2d13b]` line 62 still gives Gemmeke et al. (2017) the "Open model path" cell, which attributes a model to the dataset paper | Ch2 `[p7f25d85a]`, Table 2.1 `[tadb2d13b]` row 62; Ch3 M1 citation column | If false: `referencing_notes.md:79,82`; `literature_review_draft.md:38,88`; `literature_matrix.md:10` (title + "pretrained weights freely available" cell); `project_design_draft.md:64`; Table 2.1 row-62 cell "Open model path" |
| 3 | Hershey et al. (2017), CNN architectures for large-scale audio classification | Not cited anywhere in the repo (`grep -rni hershey docs DECISIONS.md README.md`, re-run 2026-09-24 -> hits only in this file and in the two docs that copy Table M1 / this checklist: `docs/ch2_argument_spine.md`, `docs/report_evidence_tables.md`). Verify: authors/venue/year; whether it is the source of the AudioSet CNN baselines (VGGish line) and whether the YAMNet card cites it | Ch2 audio paragraph (optional architecture citation); Ch3 M1 | Currently MISSING — nothing changes if false; adding it changes ch2 `[p7f25d85a]` only |
| 4 | Howard et al. (2017), MobileNets | Not cited anywhere in the repo (0 hits). ch2 `[p7f25d85a]` and `literature_matrix.md:10` say "MobileNet" without a citation. Verify: YAMNet backbone is MobileNet-v1 (per the TF-Hub card, row 1); authors/venue/arXiv id | Ch2 `[p7f25d85a]`; Ch3 M1 architecture column | MISSING; if the backbone claim is false, ch2 `[p7f25d85a]` and `literature_matrix.md:10` change |
| 5 | Detoxify (`unitary/toxic-bert`) | Submitted reference `[pc1239dbf]` "Hanu, L. and Unitary team (2020)", GitHub URL, accessed 25 July 2026; cited at ch2 `[p3d7920ab]`. Verify: authorship/year as the repo README states them; that the HF repo `unitary/toxic-bert` (`text_model.py:39`) is the Detoxify "original" checkpoint; training data (Jigsaw challenge data — UNVERIFIED, not stated in the repo); base model (BERT — implied by the name only); licence; the six head names in `docs/implementation_notes.md:62` (toxic, severe_toxic, obscene, threat, insult, identity_hate — recorded from observed output, not from the card). Not in `docs/referencing_notes.md` (S1–S8 has no Detoxify block) | Ch2 `[p3d7920ab]`; Ch3 M1; Ch4 `[p51b012ed]` | ch2 `[p3d7920ab]` (distribution/authorship clause); `[pc1239dbf]`; `implementation_notes.md:62` head list if the card lists different heads |
| 6 | Llama 3 paper vs deployed `llama3` Ollama tag | Submitted reference `[pedd4c0e5]` = 'The Llama 3 herd of models', arXiv:2407.21783 (2024); deployed tag `llama3:8b-instruct-q4_K_M` (`llm_judge.py:31`; WSL cache manifest `~/.ollama/models/manifests/registry.ollama.ai/library/llama3/8b-instruct-q4_K_M`, observed 2026-09-24). Verify: which Meta release the Ollama library name `llama3` maps to (Ollama publishes `llama3` and `llama3.1` as separate libraries — UNVERIFIED which weights each carries); whether arXiv:2407.21783 describes the April-2024 Llama 3 release or the July-2024 Llama 3.1 release (if the latter, the citation and the deployed weights may differ); licence name (Meta Llama 3 Community License — UNVERIFIED); that `q4_K_M` is a GGUF/llama.cpp quantisation scheme (UNVERIFIED); parameter count "8B" | Ch2 `[p17674d15]`; Ch3 table row line 52 and `[p09c59592]`; Ch1 `[p04dab7f7]`; Ch4 `[p3245e8cd]`; M1 | ch2 `[p17674d15]` (family/citation clause); `[pedd4c0e5]`; `docs/implementation_notes.md:169-170` ("Llama-3-8B-Instruct, 4-bit K-quant q4_K_M"); `docs/system_architecture.md:112` (already stale tag, see §4) |
| 7 | RapidOCR project + model lineage | Submitted reference `[pc4f1814e]` "RapidAI (n.d.) RapidOCR", GitHub URL; cited ch2 `[p3bace98d]`, ch4 `[p2ff8e331]`. Package `rapidocr-onnxruntime>=1.3,<2` (`requirements.txt:28`, `pyproject.toml:32`, `scripts/build_venv_tri.sh:37`); installed in `~/.venv-tri`: `rapidocr-onnxruntime 1.4.4`, `onnxruntime 1.27.0` (WSL `pip show`, 2026-09-24 — not in any tracked file). Code constructs `RapidOCR()` with defaults (`image_model.py:128`) which "Downloads small ONNX models on first use" (`:125`). Verify: project year/version for the citation; which detection/recognition/classification ONNX models the 1.4.x default bundle ships and their origin (PaddleOCR PP-OCR conversions — UNVERIFIED); licence of the package and of the models; whether "first use" download still applies in 1.4.4 or models ship in the wheel | Ch2 `[p3bace98d]`; Ch3 M1; Ch4 `[p2ff8e331]`; D-023 | `[pc4f1814e]` (year/version); ch2 `[p3bace98d]` ("optional local OCR component" attribution); `image_model.py:125` docstring if models ship in-wheel |
| 8 | Piczak (2015) ESC-50; Panayotov et al. (2015) LibriSpeech | Submitted references `[pd6d56b06]` (ACM MM 2015, pp. 1015-1018, DOI 10.1145/2733373.2806390) and `[p47c1a59b]` (ICASSP 2015, pp. 5206-5210, DOI 10.1109/ICASSP.2015.7178964); cited ch2 `[p5b352c47]`, ch5 table lines 93-96. Verify: DOIs resolve; pages; licence strings written into the committed T4 file — `t4:datasets.esc50.licence` = "CC BY-NC 3.0 (Piczak 2015; non-commercial, academic use)" and `t4:datasets.librispeech.licence` = "CC BY 4.0" (`outputs/evaluation/20260704-153729/t4/results.json`, not editable) against the dataset pages; HF mirrors `ashraq/esc50` and `openslr/librispeech_asr` (`t4:datasets.*.hub_id`) carry the same licence | Ch2 `[p5b352c47]`; Ch5 T4 table + `[pe829517b]`; D-017 | If a licence string is wrong: the results.json cannot be edited (rule 3) — Ch5 must carry a correction note; `DECISIONS.md` D-017 and `docs/implementation_notes.md:307` repeat the ESC-50 licence |

Also unverified but not in the task list: Radford et al. (2023) and Li, J. et al. (2022) bibliographic fields are copied from `docs/referencing_notes.md` S5/S7 (the notes claim "Access date: 2026-06-08"); they are not re-checked here.

---

## 2. Cards (12 rows each)

Row key: (1) what it is · (2) architecture family · (3) training data ·
(4) variant/size used · (5) pinned identifier · (6) role / evidence field ·
(7) config values from code · (8) feature flag / env · (9) fallback behaviour ·
(10) downstream consumer · (11) evidence track + run id + verbatim numbers ·
(12) citation status.

### Card A — `unitary/toxic-bert` (text, real tier)

| # | Fact |
|---|---|
| 1 | Repo text: "real Hugging Face toxicity classifier (unitary/toxic-bert), multi-label sigmoid heads" (`src/triguard/models/text_model.py:9-10`). Submitted: ch2 `[p3d7920ab]`. Anything beyond that: UNVERIFIED-EXTERNAL (checklist row 5). |
| 2 | BERT family — implied by the checkpoint name only; the repo never states the base model. UNVERIFIED-EXTERNAL. |
| 3 | Not stated in the repo. UNVERIFIED-EXTERNAL (Jigsaw data per Detoxify README — VERIFY). |
| 4 | Single checkpoint; "~440 MB weights" (`text_model.py:10`; `docs/implementation_notes.md:62`). |
| 5 | `code:_HF_MODEL="unitary/toxic-bert"` (`text_model.py:39`); `code:_HF_REVISION="4d6c22e74ba2fdd26bc4f7238f50766b045a0d94"` (`:40`); both passed to `transformers.pipeline(...)` (`:112-119`). Library pins: `pin:transformers==4.57.6` (`requirements-full.txt:104`), `pin:torch==2.12.1+cpu` (`:102`); ranges `transformers>=4.40,<5`, `torch>=2.2,<3` (`requirements.txt:11-12`). |
| 6 | `TextEvidence.toxicity_score` = `toxic` head (`:216`, rounded 4 dp `:220`); `top_labels` = sorted heads with score >= 0.5 (`:217`); `confidence` = `abs(tox - 0.5) * 2` (`:222`); `raw` = `{"mode": "real-hf", "model_name", "model_revision", "scores"}` (`:223-229`). |
| 7 | `pipeline("text-classification", model=_HF_MODEL, revision=_HF_REVISION, top_k=None, function_to_apply="sigmoid", truncation=True)` (`:112-119`); label threshold `0.5` (`:217`); `lru_cache(maxsize=1)` (`:103`). |
| 8 | `TRIGUARD_TEXT_BACKEND=hf` (`:132-133`) or `force_mode="hf"`; `TRIGUARD_MOCK=1` forces mock (`:123`, `:130-131`); default tier is `sklearn` (`:133`). |
| 9 | Import/load failure -> `_HF_BROKEN = True` (`:206`, latched per process) -> `_mock_analyse` (`raw["mode"]="mock"`, `:159`), warning "toxic-bert unavailable" (`:207`). `model_versions` token on success: `real-hf:unitary/toxic-bert@4d6c22e74ba2` (`pipeline.py:59-68`; `docs/implementation_notes.md:286`). |
| 10 | Rule judge: `ts >= 0.5` flags `text` (`llm_judge.py:134-135`), rationale template `:137-142`; `confidence < 0.4` -> uncertainty `low_text_classifier_confidence` (`:197-198`). LLM judge: evidence line `TEXT — toxicity=…, labels=…, confidence=…` (`:348-352`). T3 OCR route: `run_t3.py:75-98` (`_ocr_to_text`) feeds `raw["ocr_text"]` through this tier via `text_model` (harness only, not the pipeline). |
| 11 | T2 run `20260623-124802` (`outputs/evaluation/20260623-124802/t2/results.json`): `model_versions.text_model` = `unitary/toxic-bert`, `model_versions.text_model_revision` = `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94`; `config.wrapper_mode` = `real-hf`, `config.run_env` = `wsl-ubuntu`, `n_samples` 500, `class_balance` non-toxic 468 / toxic 32, `config.threshold` 0.5; `accuracy` 0.928; `macro_f1` 0.6476; `per_class.toxic` precision 0.4091 / recall 0.2812 / f1 0.3333; `confusion_matrix` non-toxic->non-toxic 455, non-toxic->toxic 13, toxic->non-toxic 23, toxic->toxic 9. T3 run `20260705-111002` (text via the dataset `text` field, `model_versions.text_mode` = `real-hf`): `metrics_text_only_baseline.f1` 0.3636; `ocr_ablation.image_only_ocr_to_text.f1` 0.4348. |
| 12 | Cited in the submitted draft as Detoxify `[pc1239dbf]` (ch2 `[p3d7920ab]`). Absent from `docs/referencing_notes.md` (no S-block) — MISSING there. Bibliographic fields: VERIFY (checklist row 5). |

### Card B — `Salesforce/blip-image-captioning-base` (image, real tier)

| # | Fact |
|---|---|
| 1 | Repo text: "real Salesforce/blip-image-captioning-base captioning" (`src/triguard/models/image_model.py:7`); S7 key idea `docs/referencing_notes.md:139`. |
| 2 | Vision–language model with captioning head (repo text `referencing_notes.md:139`, `literature_review_draft.md:32`). Encoder/decoder details: UNVERIFIED-EXTERNAL. |
| 3 | Not stated in the repo (S7 mentions COCO only as an evaluation set, `referencing_notes.md:139`). UNVERIFIED-EXTERNAL. |
| 4 | "base" captioning checkpoint; "~990 MB weights" (`image_model.py:8`; `implementation_notes.md:65`). |
| 5 | `code:_BLIP_MODEL="Salesforce/blip-image-captioning-base"` (`image_model.py:30`); `code:_BLIP_REVISION="82a37760796d32b1411fe092ab5d4e227313294b"` (`:31`); used in both `from_pretrained` calls (`:98-101`). Library pins as Card A row 5; `pin:transformers==4.57.6`. |
| 6 | `ImageEvidence.caption` (`:207-208`, fallback string "an unrecognised image"); `visual_risk_cues` = `_RISK_KEYWORDS` substring scan (`:39-56`) over `caption` (+ OCR text when present, `:193-194`, `:209`); `confidence` = mean over generation steps of max softmax prob (`:179-188`); `raw` = `{"mode": "real-blip", "model_name", "model_revision", "caption"[, "ocr_text"][, "confidence_fallback"]}` (`:196-205`). |
| 7 | `code:_MAX_EDGE=1024` (`:33`; `img.thumbnail((_MAX_EDGE, _MAX_EDGE))` `:114`); `code:_BLIP_CONF_FALLBACK=0.6` (`:32`); `max_new_tokens=30`, `output_scores=True`, `return_dict_in_generate=True`, no sampling arguments (greedy) (`:171-176`); `model.eval()` (`:102`); `torch.no_grad()` (`:170`); RGB conversion (`:113`); `lru_cache(maxsize=1)` (`:93`). |
| 8 | `TRIGUARD_IMAGE_BACKEND=blip` (`:64-65`) or `force_mode="blip"`; `TRIGUARD_MOCK=1` -> mock (`:62-63`); default `mock`. |
| 9 | Load failure -> `_BLIP_BROKEN = True` (`:153`, latched) -> mock. Per-image decode failure -> mock for that file only with `raw["decode_error"]` (`:158-165`), model stays live. `model_versions` token `real-blip:Salesforce/blip-image-captioning-base@82a37760796d` (`implementation_notes.md:287`). |
| 10 | Rule judge: any cue -> `img_score 0.6` and flag `image`, else `0.1` (`llm_judge.py:146-150`); rationale quotes the caption (`:151-157`); `confidence < 0.5` -> `low_image_caption_confidence` (`:201-202`). LLM judge line `IMAGE — caption='…', visual_risk_cues=…, confidence=…` (`:353-358`); `raw["ocr_text"]` is not in that line. |
| 11 | T3 run `20260705-111002` (`model_versions.image_mode` = `real-blip`, `config.judge` = `rule`, `n_samples` 50, `class_balance` not_offensive 18 / offensive 32): `metrics_pipeline` precision 0.6923 / recall 0.2812 / f1 0.4 / accuracy 0.46 / auroc 0.566; `metrics_text_only_baseline` 0.6667 / 0.25 / 0.3636 / 0.44; `confusion_matrix_pipeline` not_offensive 14 / 4, offensive 23 / 9; `ocr_ablation.image_only_noocr` precision 1.0 / recall 0.0312 / f1 0.0606 / accuracy 0.38 / auroc 0.5156. T6 run `20260725-191000` (rule): `conditions.image_only` n 8, accuracy 0.5, macro_f1 0.2222. |
| 12 | Cited: S7 Li, J. et al. (2022) (`docs/referencing_notes.md:130-146`); submitted `[pd2976f51]`. The HF model card / revision hash is not cited (`referencing_notes.md:175` treats model cards as supporting material only). |

### Card C — RapidOCR (`rapidocr-onnxruntime`) (image, opt-in OCR)

| # | Fact |
|---|---|
| 1 | Repo text: "Lazy RapidOCR engine (ONNX runtime; no torch/torchvision …). Downloads small ONNX models on first use." (`image_model.py:124-125`); D-023 (`DECISIONS.md:478-521`). |
| 2 | UNVERIFIED-EXTERNAL (text detection + recognition ONNX models; PaddleOCR lineage — VERIFY, checklist row 7). |
| 3 | UNVERIFIED-EXTERNAL; not in the repo. |
| 4 | Default constructor `RapidOCR()` with no model arguments (`:128`). Package range `rapidocr-onnxruntime>=1.3,<2` (`requirements.txt:28`, `pyproject.toml:32`, `scripts/build_venv_tri.sh:37`). Installed in `~/.venv-tri` (WSL, observed 2026-09-24, untracked): `rapidocr-onnxruntime 1.4.4`, `onnxruntime 1.27.0`. |
| 5 | Exact pin MISSING in `requirements-full.txt`: `pin:rapidocr-onnxruntime=MISSING`, `pin:onnxruntime=MISSING` (grep, 0 hits). No model-file revision pinned in code. |
| 6 | `ImageEvidence.raw["ocr_text"]` (`:202-203`; key absent when OCR is off, fails or reads nothing); folded into `visual_risk_cues` via `cue_source = f"{caption} {ocr}"` (`:193-194`, `:209`). No schema field of its own (D-023 "NO schema change"). |
| 7 | `_ocr_enabled()` reads `TRIGUARD_IMAGE_OCR` in `{"1","true","yes"}` (`:118-119`); runs only inside the blip tier after `_open_image` (`:193`), i.e. on the RGB image already downscaled to `_MAX_EDGE` (`:114`); output = `" ".join(item[1])` over result rows (`:139-140`); `lru_cache(maxsize=1)` engine (`:122`). |
| 8 | `TRIGUARD_IMAGE_OCR=1` (`:119`); requires the blip backend (`:193`) — the mock tier never OCRs. |
| 9 | Any exception -> returns `""` with warning "OCR unavailable" (`:141-143`); no raw flag records the failure; not latched. |
| 10 | Keyword-cue route (pipeline): cues -> rule judge as Card B row 10. Text route (harness only): `run_t3.py:75-98` sends `raw["ocr_text"]` to `text_model` (`image_only_ocr_to_text`). LLM judge never receives `raw["ocr_text"]` (`llm_judge.py:353-358`). |
| 11 | T3 run `20260705-111002` `ocr_ablation` (`measured_on` = "image track alone (dataset text dropped)"): `image_only_ocr_cues` f1 0.0606 (`delta_f1_ocr_to_cues` 0.0, `n_with_ocr_text` 50); `image_only_ocr_to_text` precision 0.7143 / recall 0.3125 / f1 0.4348 / accuracy 0.48 / auroc 0.5964 (`delta_f1_ocr_to_text` 0.3742, `n_with_ocr_text` 50); `headline` = `ocr_to_text`. |
| 12 | Submitted reference `[pc4f1814e]` RapidAI (n.d.) — cited ch2 `[p3bace98d]`, ch4 `[p2ff8e331]`. Absent from `docs/referencing_notes.md` — MISSING there. VERIFY (checklist row 7). |

### Card D — Whisper `tiny` (audio, transcription)

| # | Fact |
|---|---|
| 1 | Repo text: "OpenAI Whisper transcription" (`src/triguard/models/audio_model.py:7`); S5 key idea `docs/referencing_notes.md:99`. Submitted ch2 `[p03ba2449]`. |
| 2 | Encoder–decoder transformer (repo text `referencing_notes.md:99`; `literature_review_draft.md:40`). UNVERIFIED-EXTERNAL as a fact. |
| 3 | "680 000-hour multilingual … weak supervision" (repo text `referencing_notes.md:99`). UNVERIFIED-EXTERNAL. |
| 4 | `tiny` = default of `os.getenv("TRIGUARD_WHISPER_MODEL", "tiny")` (`audio_model.py:122`); cached checkpoint `~/.cache/whisper/tiny.pt`, 75,572,083 bytes (WSL `ls -la`, observed 2026-09-24, untracked); `docs/CLAUDE_CODE_PROMPTS.md:133` "≈ 75 MB". `small` is the documented alternative (`audio_model.py:13-14`; D-014). |
| 5 | Library pin `pin:openai-whisper==20250625` (`requirements-full.txt:64`); `[audio]` extra `openai-whisper>=20231117` (`pyproject.toml:40`). Model identifier is the name string `"tiny"` passed to `whisper.load_model` (`:114`) — no checkpoint hash pinned in code. |
| 6 | `AudioEvidence.transcript` (`:222`, fallback "(no speech detected)"); `transcript_confidence` = mean over segments of `exp(avg_logprob)`, clamped [0,1], rounded 4 dp (`:136-141`); `raw["whisper_model"]` (`:210`). |
| 7 | `code:_SR=16000` (`:36`); decode `librosa.load(..., sr=_SR, mono=True)` (`:106`); only the first `_SR * _MAX_SECONDS` samples are transcribed — `clip = wav[: _SR * _MAX_SECONDS]` (`:130`), `code:_MAX_SECONDS=60` (`:37`); `fp16=False` (`:131`); `lru_cache(maxsize=2)` (`:110`). |
| 8 | `TRIGUARD_AUDIO_BACKEND=real` (`:59-60`) or `force_mode="real"`; `TRIGUARD_WHISPER_MODEL` (`:122`); `TRIGUARD_MOCK=1` -> mock (`:57-58`); default `mock`. |
| 9 | Load failure -> `_WHISPER_BROKEN = True` (`:126`, latched) -> mock transcript + `raw["whisper_fallback"]=True` (`:204-207`) and `raw["mode"]="real-audio-partial"` (`:218-219`). Per-clip transcription failure -> mock transcript for that clip only (`:132-134`). Waveform decode failure -> whole evidence from `_mock_analyse` (`:194-198`). |
| 10 | Rule judge: only `transcript_confidence < 0.5` is used (-> `low_audio_transcript_confidence`, `llm_judge.py:199-200`); the transcript text is never scored by the rule judge (its audio signal reads `yamnet_tags` only, `:161-162`). LLM judge: `AUDIO — transcript='…', tags=…, transcript_confidence=…` (`:359-363`). |
| 11 | T4 run `20260704-153729`: `t4:model_versions.whisper_model="tiny"`; `t4:whisper_wer.n=50`; `t4:whisper_wer.wer_corpus=0.0971`; `t4:whisper_wer.wer_mean_per_clip=0.1314`; `whisper_wer.wrapper_modes` = ["real-audio"]; `t4:datasets.librispeech.hub_id="openslr/librispeech_asr"`, config `clean`, split `test`, licence "CC BY 4.0"; `config` sample_size 50 / seed 42 / run_env `wsl-ubuntu-py312-tri`; `failures.asr_worst_wer` 10 entries, worst `wer` 0.6667. |
| 12 | Cited: S5 Radford et al. (2023) (`docs/referencing_notes.md:90-106`); submitted `[p4b78a00c]`. |

### Card E — YAMNet (`google/yamnet/1`, TF-Hub) (audio, event tags)

| # | Fact |
|---|---|
| 1 | Repo text: "YAMNet (TF-Hub) audio-event tagging" (`audio_model.py:7-8`). Submitted ch2 `[p7f25d85a]`, ch4 `[pe2f09a93]`. |
| 2 | MobileNet (repo text: `docs/literature_matrix.md:10`; ch2 `[p7f25d85a]`) — UNVERIFIED-EXTERNAL (checklist rows 1, 4). |
| 3 | AudioSet (repo text `docs/referencing_notes.md:82`) — UNVERIFIED-EXTERNAL (checklist row 2). Class count 521 vs 632: see checklist row 1. |
| 4 | TF-Hub handle version `/1`; `raw["yamnet"]="yamnet/1"` (`:216`). |
| 5 | `code:_YAMNET_URL="https://tfhub.dev/google/yamnet/1"` (`:35`), loaded by `hub.load` (`:151`) — the `/1` suffix is the only version pin. Library pins `pin:tensorflow-hub==0.16.1` (`requirements-full.txt:96`), `pin:tensorflow==2.21.0` (`:94`); `[audio]` extra ranges `tensorflow>=2.15,<3`, `tensorflow-hub>=0.16` (`pyproject.toml:41-42`). |
| 6 | `AudioEvidence.yamnet_tags: list[(display_name, score)]` (`:183-187`, `:224`). |
| 7 | `code:_SR=16000` (`:36`); `code:_MAX_SECONDS=60` (`:37`); `code:_TAG_THRESHOLD=0.2` (`:38`); `code:_TOP_K=5` (`:39`); chunking `win = _SR * _MAX_SECONDS`, per-chunk frame-mean of `scores`, then mean over chunks (`:175-181`); strict `mean[i] > _TAG_THRESHOLD` (`:186`), top-`_TOP_K` after descending sort (`:182-187`); scores rounded 4 dp (`:184`); class names = column `display_name` of `model.class_map_path()` CSV (`:153-155`); empty waveform -> `[]` (`:173-174`); `lru_cache(maxsize=1)` (`:144`). |
| 8 | Same switch as Whisper: `TRIGUARD_AUDIO_BACKEND=real` / `force_mode="real"`; no YAMNet-only switch. Runtime note: `USE_TF=0` (`requirements-full.txt:11-15`) targets transformers; the audio wrapper imports TensorFlow directly (`:148-149`). |
| 9 | Load failure -> `_YAMNET_BROKEN = True` (`:169`, latched) -> `None` -> `tags = _mock_analyse(audio).yamnet_tags` with `raw["yamnet_fallback"]=True` (`:212-214`) and `raw["mode"]="real-audio-partial"` (`:218-219`). Per-clip tagging failure -> `None` for that clip only (`:188-190`). Mock vocabulary (filename token -> tag): shout->`shouting` 0.7, scream->`screaming` 0.8, gun->`gunshot` 0.75, siren->`siren` 0.6, calm/speech->`speech` 0.6/0.7 (`:44-51`). |
| 10 | Rule judge exact-matches lowercase `{"shouting", "screaming", "gunshot"}` (`llm_judge.py:161-162`; `aud_score 0.6` if any, else `0.1`, `:163`). Real display names observed capitalised: `Speech` (`docs/implementation_notes.md:146`, `:262`), `Siren` (`t4 yamnet_label_map.siren[0]`), `Vehicle`, `Aircraft`, `Silence`, `Bicycle` (`t4 failures.yamnet_mismatched[*].yamnet_top5`), `Laughter` (`t4 yamnet_label_map.laughing[0]`; also `failures.yamnet_mismatched[*].expected_any_of`, never in a `yamnet_top5`). On `yamnet_fallback` the lowercase mock tags reach the judge and can match (`audio_model.py:212-214`). LLM judge receives `tags=` verbatim (`llm_judge.py:359-363`). AudioSet display names for shout / scream / gunshot classes: UNVERIFIED — the committed `yamnet_label_map` (42 ESC-50 categories) contains none of them (grep on keys: 0 hits). |
| 11 | T4 run `20260704-153729`: `t4:model_versions.yamnet="yamnet/1"`; `t4:yamnet_events.n=50`; `t4:yamnet_events.top1_rate=0.32`; `t4:yamnet_events.top5_rate=0.66`; `yamnet_events.categories_used` 29 entries; `yamnet_events.wrapper_modes` ["real-audio"]; `t4:datasets.esc50.hub_id="ashraq/esc50"`, split `train`, licence "CC BY-NC 3.0 (Piczak 2015; non-commercial, academic use)"; `failures.yamnet_mismatched` 10 entries. T6 run `20260725-191000` (rule): `conditions.audio_only` n 6, accuracy 0.5, macro_f1 0.2222, `confusion_matrix` safe->safe 3, borderline->safe 1, harmful->safe 2 (all six predicted `safe`). T6 run `20260725-191055` (ollama): `conditions.audio_only` n 6, accuracy 0.1667, macro_f1 0.0952. |
| 12 | S4 Gemmeke et al. (2017) (`docs/referencing_notes.md:70-86`) is the AudioSet dataset paper; the TF-Hub card is cited only in the submitted draft (`[p47fe03b3]`, ch2 `[p7f25d85a]`) and is absent from `docs/referencing_notes.md`. VERIFY checklist rows 1-2; Hershey / Howard MISSING (rows 3-4). |

### Card F — `llama3:8b-instruct-q4_K_M` via Ollama (optional judge)

| # | Fact |
|---|---|
| 1 | Repo text: "a local Llama-3-8B-Instruct model served via Ollama" (`src/triguard/models/llm_judge.py:4`); `docs/implementation_notes.md:169-170`. Submitted ch2 `[p17674d15]`. |
| 2 | Instruction-tuned LLM (repo text `docs/chapter1_introduction.md:21`). Architecture details: UNVERIFIED-EXTERNAL. |
| 3 | Not in the repo. UNVERIFIED-EXTERNAL. |
| 4 | 8B parameters, instruct, "4-bit K-quant q4_K_M" (`implementation_notes.md:169-170`); observed "5.3 GB resident, 100% GPU" (`:170`); Ollama manifest model layer `size` 4,920,733,984 bytes (WSL `~/.ollama/models/manifests/registry.ollama.ai/library/llama3/8b-instruct-q4_K_M`, observed 2026-09-24, untracked). |
| 5 | `code:_DEFAULT_OLLAMA_MODEL="llama3:8b-instruct-q4_K_M"` (`llm_judge.py:31`); override order `TRIGUARD_OLLAMA_MODEL`, then `OLLAMA_MODEL` (`:39-45`). No weight digest pinned in code (the local manifest's model-layer digest `sha256:8d2bf441…` is untracked). |
| 6 | Entire `JudgeOutput` (`risk_score`, `risk_label`, `flagged_modalities`, `rationale`, `uncertainties`, `recommended_action`) parsed from the first `{…}` block (`:335-343`); provenance label `ollama` / `ollama->rule` in `model_versions.llm_judge` (`pipeline.py:43-56`). |
| 7 | `code:_DEFAULT_OLLAMA_HOST="http://localhost:11434"` (`:30`, env `OLLAMA_HOST` `:36`); `"options": {"temperature": 0.0}` (`:245`, `:270`); `keep_alive` default `"30m"` (`:52`, env `TRIGUARD_OLLAMA_KEEP_ALIVE`); `OLLAMA_TIMEOUT` default `60` s (`:252`, `:277`); endpoint `/api/generate` (`:248`); prompt `JUDGE_PROMPT_TEMPLATE` (`:55-76`); one stricter-prompt retry on the non-streaming path (`:232-234`); no retry on the streaming path (`:303-305`). |
| 8 | `TRIGUARD_JUDGE=ollama` (`:94`) or `force_mode="ollama"` (CLI `--judge ollama`, `docs/implementation_notes.md:249-250`); default `rule`. |
| 9 | Invalid JSON twice -> `JudgeFailure` -> rule judge + uncertainty `judge_output_invalid` (`:99-103`); `URLError` -> rule + `ollama_unavailable:<reason>` (`:104-108`); any other exception -> rule + `ollama_unavailable:<ExceptionName>` (`:109-113`); label `ollama->rule` when any uncertainty starts with those tags (`pipeline.py:35`, `:52-55`); streaming path terminal event `source: "rule_fallback"` (`:330-332`). |
| 10 | `TriGuardResult` copies the six judge fields (`pipeline.py:145-151`); demo endpoints compare/stream (`docs/implementation_notes.md:490`); T7 harness (`run_t7.py`, see `docs/report_evidence_tables.md` Table E7 for the provenance caveats). |
| 11 | T7 run `20260705-113456` (`outputs/evaluation/20260705-113456/t7/results.json`): `judge` = `ollama`, `n` 18, `grounding_rate` 1.0, `invented_modality_count` 0, `config` text `hf` / image `blip` / audio `real`, `run_env` `wsl-ubuntu-py312-tri`. T6 run `20260725-191055` (`config.judge` = `ollama`, n_items 24): `conditions.multimodal` accuracy 0.4583 / macro_f1 0.4722; `text_only` (n 22) 0.5909 / 0.4883; `image_only` (n 8) 0.25 / 0.1333; `audio_only` (n 6) 0.1667 / 0.0952; `limitations[4]` verbatim: "ollama/llama3 judge (non-deterministic; falls back to rule when unreachable — check model_versions in per-run logs)". Latency facts: `docs/implementation_notes.md:546` (compare: rule 0 ms vs llama3 5451 ms, one item, warm), `:275` (`latency_ms` 49421, cold all-real pass). |
| 12 | Submitted references `[pedd4c0e5]` (Llama Team, AI@Meta, 2024) and `[pf3a8bf6e]` (Ollama, n.d.). Absent from `docs/referencing_notes.md` (S6 Zheng et al. covers the judge *pattern*, not the model) — MISSING there. VERIFY (checklist row 6). |

### Card G — sklearn TF-IDF + logistic regression (text, offline floor)

| # | Fact |
|---|---|
| 1 | Repo text: "TF-IDF + logistic regression, trained on a small bundled corpus. Reproducible offline, no download. The offline default and a sanity-floor baseline." (`text_model.py:6-8`). Submitted ch4 `[p51b012ed]`. |
| 2 | Linear classifier over sparse n-gram features: `Pipeline([("tfidf", TfidfVectorizer(...)), ("lr", LogisticRegression(...))])` (`:93-98`). In-repo; nothing external. |
| 3 | `_TRAIN` (`:48-81`): 30 sentences, 15 label 0 / 15 label 1 (counted by importing the module, 2026-09-24); comment "Real deployment would use Civil Comments" (`:44`). Corpus card = Table E11 (another task). |
| 4 | No variants; trained at first call per process (`lru_cache(maxsize=1)`, `:84`). |
| 5 | No weights, no revision. Library `pin:scikit-learn==1.5.2` (`requirements-full.txt:87`); range `scikit-learn>=1.3,<2` (`requirements.txt:4`, `pyproject.toml:11`). |
| 6 | `toxicity_score` = `predict_proba[0, 1]` rounded 4 dp (`:174`, `:192`); `top_labels` rules: hard-token hit -> `insult`, kill/die/suffer -> `threat`, else `toxic` if prob >= 0.5 (`:183-189`); `confidence` = `abs(prob - 0.5) * 2` (`:194`); `raw` = `{"mode": "real", "classifier": "sklearn-tfidf-lr", "prob"}` (`:195`). |
| 7 | `TfidfVectorizer(ngram_range=(1, 2), min_df=1, lowercase=True)` (`:95`); `LogisticRegression(max_iter=500, C=4.0)` (`:96`); hard-token override `prob = max(prob, 0.6)` (`:179-181`); `_HARD_TOXIC_TOKENS` = 11 tokens (`:140-143`). |
| 8 | Default tier when `TRIGUARD_TEXT_BACKEND` is unset (`:133`); explicit `TRIGUARD_TEXT_BACKEND=sklearn`; `force_mode="real"` aliases it (`:134-135`); `TRIGUARD_MOCK=1` -> mock. |
| 9 | sklearn import/fit failure -> `_SKLEARN_BROKEN = True` (`:170`) -> mock. `model_versions` token `sklearn` (`pipeline.py:29`). |
| 10 | As Card A row 10 (same `TextEvidence` contract). |
| 11 | T2 run `20260623-074102`: `model_versions.text_model` = `sklearn-tfidf-lr`, `config.wrapper_mode` = `real`, `n_samples` 500, `class_balance` 468 / 32; `accuracy` 0.542; `macro_f1` 0.4149; `per_class.toxic` precision 0.0809 / recall 0.5938 / f1 0.1423; `confusion_matrix` non-toxic->non-toxic 252, non-toxic->toxic 216, toxic->non-toxic 13, toxic->toxic 19. |
| 12 | No model citation applies. scikit-learn library citation: MISSING (VERIFY if wanted). |

---

## For integration

### Table M1 — models composed (facts only)

Caption slot: `[STUDENT: justification sentence in Ch3 body]`. No "why"
column by design. Pointers: `file:line` at commit `908b1e5`.

| Modality / role | Model + variant | Pinned id (file:line) | Evidence field filled | Evidence track + run id | Citation status |
|---|---|---|---|---|---|
| Text, real tier | `unitary/toxic-bert` | `text_model.py:39-40` rev `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94` | `TextEvidence.toxicity_score`, `top_labels`, `confidence`, `raw.scores` | T2 `20260623-124802` (acc 0.928, macro-F1 0.6476); T3 `20260705-111002` OCR->text f1 0.4348 | Detoxify `[pc1239dbf]` in draft; not in referencing_notes.md; VERIFY |
| Text, offline floor | sklearn TF-IDF(1,2) + LR(C=4.0) on 30 bundled sentences | none (no weights); `text_model.py:48-81`, `:95-96` | same `TextEvidence` fields; `raw.classifier` = `sklearn-tfidf-lr` | T2 `20260623-074102` (acc 0.542, macro-F1 0.4149) | n/a (library citation MISSING) |
| Image, real tier | `Salesforce/blip-image-captioning-base` | `image_model.py:30-31` rev `82a37760796d32b1411fe092ab5d4e227313294b` | `ImageEvidence.caption`, `visual_risk_cues`, `confidence` | T3 `20260705-111002` (pipeline f1 0.4, auroc 0.566; caption-only f1 0.0606); T6 `20260725-191000` image_only acc 0.5 | S7 Li, J. et al. 2022; `[pd2976f51]` |
| Image, opt-in OCR | RapidOCR default engine (`rapidocr-onnxruntime`) | range only `requirements.txt:28`; exact pin MISSING in `requirements-full.txt`; no model revision | `ImageEvidence.raw["ocr_text"]` -> `visual_risk_cues` | T3 `20260705-111002` `ocr_ablation` (cues delta 0.0; ocr_to_text f1 0.4348, delta 0.3742) | `[pc4f1814e]` RapidAI (n.d.) in draft; not in referencing_notes.md; VERIFY |
| Audio, transcription | Whisper `tiny` (`openai-whisper`) | name string `audio_model.py:122`; lib `openai-whisper==20250625` `requirements-full.txt:64` | `AudioEvidence.transcript`, `transcript_confidence` | T4 `20260704-153729` (wer_corpus 0.0971, wer_mean_per_clip 0.1314) | S5 Radford et al. 2023; `[p4b78a00c]` |
| Audio, event tags | YAMNet TF-Hub `google/yamnet/1` | `audio_model.py:35` (URL `/1`); libs `tensorflow-hub==0.16.1` `:96`, `tensorflow==2.21.0` `:94` | `AudioEvidence.yamnet_tags` | T4 `20260704-153729` (top1_rate 0.32, top5_rate 0.66); T6 `20260725-191000` audio_only acc 0.5 (all `safe`) | S4 Gemmeke 2017 = dataset paper; TF-Hub card `[p47fe03b3]` in draft only; Hershey/Howard MISSING; VERIFY rows 1-4 |
| Judge, optional | `llama3:8b-instruct-q4_K_M` via Ollama | `llm_judge.py:31` (tag only; no digest) | whole `JudgeOutput`; `model_versions.llm_judge` = `ollama` / `ollama->rule` | T7 `20260705-113456` (grounding_rate 1.0, n 18, invented 0); T6 `20260725-191055` multimodal acc 0.4583 | `[pedd4c0e5]`, `[pf3a8bf6e]` in draft; not in referencing_notes.md; VERIFY row 6 |
| Judge, default | rule-based (`_rule_based_judge`) | `llm_judge.py:122-215` | whole `JudgeOutput`; label `rule` | every rule-judge run (T3, T6 `20260725-191000`, T8) | n/a |

### DECISIONS draft entry (for the Integrate stage to place; number TBD)

```
## Decision 0XX: Rule-judge audio flag matches mock tag vocabulary only
Date: 2026-09-24
Status: proposed

Context: The rule judge flags the audio modality when any yamnet_tags label
is exactly one of {"shouting", "screaming", "gunshot"} (lowercase,
src/triguard/models/llm_judge.py:161-162). Those three strings are the mock
wrapper's vocabulary (src/triguard/models/audio_model.py:44-51). The real
tier returns AudioSet display names read verbatim from the TF-Hub class map
(audio_model.py:153-155), which are capitalised in every committed
observation: "Speech" (docs/implementation_notes.md:146, :262); "Siren",
"Vehicle", "Aircraft", "Silence", "Laughter", "Bicycle"
(outputs/evaluation/20260704-153729/t4/results.json, yamnet_label_map and
failures.yamnet_mismatched). The exact AudioSet display names for the
shout / scream / gunshot classes are UNVERIFIED (not present in the
committed label map). Consequently, on the real tier the rule judge's audio
signal can only be 0.1 (llm_judge.py:163) unless a real display name happens
to equal one of the three lowercase strings; the lowercase mock tags can
still match when raw["yamnet_fallback"] is set (audio_model.py:212-214).
The LLM judge receives the tags verbatim (llm_judge.py:359-363) and is not
subject to the exact-match set.
Note on T6: the audio_only condition in run 20260725-191000 scores every
one of its 6 items as safe (conditions.audio_only.confusion_matrix: 3 + 1 +
2 all predicted safe). Related facts: every audio item in the v2 manifest
(A1, MS1, MS3, MB2, MH2, MH3 — `items[*].audio` non-null) references the
single committed clip data/sample_inputs/audio_test.wav
(data/sample_inputs/triguard_eval_v1/manifest.json); results.json
limitations[1] reads "no cross_modal confounder items yet (only two benign
committed media assets)"; the T6 envelope persists no per-item yamnet_tags
(top-level keys: track, run_at, manifest, manifest_provenance, config,
n_items, class_balance, conditions, cross_modal_ablation, limitations), so
the tags the rule judge saw for that clip in this run are not recorded.
[STUDENT] to attribute the all-safe outcome (clip content vs the vocabulary
mismatch above); the committed evidence does not separate the two causes.
Options considered: [STUDENT]
Decision: [STUDENT]
Reason: [STUDENT]
Impact: Facts the student can state — the rule-judge audio path has never
been exercised by a real capitalised risk tag in any committed run; the
mock-tag tests (tests/test_llm_judge.py, tests/test_orchestrator.py) exercise
the lowercase set; changing the match set or lower-casing tags in
llm_judge.py touches the rule-judge contract (CLAUDE.md "changing the LLM
judge contract" -> ask first) and would need a new slow test on the real
tier.
```


---

## [STUDENT]

Items that need the student's own decision or sentence; the repo supplies
only the facts listed.

1. **No alternative audio-event model is recorded anywhere.** D-014
   (`DECISIONS.md:180-202`) has no "Options considered" line, unlike D-012,
   D-013, D-015 and D-023. `docs/report_skeleton.md:115-117` already notes
   this. The student must name one alternative themselves (repo cannot
   supply it). Constraints citable from the repo when justifying the choice:
   - footprint: peak resident 2.98 GB for all four perception models in one
     process (`docs/implementation_notes.md:273-275`); YAMNet is loaded
     under TensorFlow (`audio_model.py:148-151`); repo statement
     `audio_model.py:16-17`: real audio needs Python <= 3.12 because
     TensorFlow / numba have no 3.14 wheels (also D-014 "Env");
   - no fine-tuning data: D-017 substituted public proxies because AudioSet
     ships only YouTube ids (`DECISIONS.md:297-333`); no safety-specific
     audio corpus exists in the repo;
   - ontology: `docs/literature_review_draft.md:38` (AudioSet ontology is
     broad, not safety-focused) and ch2 `[p7f25d85a]`;
   - the exact-match vocabulary issue in the DECISIONS draft above applies
     to any replacement whose labels are not lowercase `shouting` /
     `screaming` / `gunshot`.
2. **Stale sentences to reconcile** (each is a fact-level mismatch with the
   code at `908b1e5`):
   - `docs/referencing_notes.md:82` — "plans to use" (YAMNet is deployed:
     `audio_model.py:35`, T4 run `20260704-153729`).
   - `docs/project_design_draft.md:64` — "Whisper (small)" (default is
     `tiny`, `audio_model.py:122`; ch3 line 80 of the submitted draft already
     records the change). Same row cites Gemmeke et al. (2017) for YAMNet
     (checklist row 2). `docs/_preliminary_combined.md:182` repeats it.
   - `docs/system_architecture.md:112` — `llama3:8b-instruct-q4` (code tag is
     `llama3:8b-instruct-q4_K_M`, `llm_judge.py:31`).
   - `docs/chapter1_introduction.md:21` — "four established models" and
     "Only a small text classifier is trained from scratch" (as-built count
     per Table M1: toxic-bert, BLIP, RapidOCR, Whisper, YAMNet, llama3 = six
     external models plus the sklearn floor; `docs/report_skeleton.md:51`
     already flags the deletion).
   - `docs/referencing_notes.md:79` "632 sound event classes" vs ch2
     `[p7f25d85a]` 521 (checklist row 1).
   - `docs/literature_matrix.md:10` "AudioSet (YAMNet line)" and
     `docs/literature_review_draft.md:38,88` (checklist row 2).
3. **Citation blocks missing from `docs/referencing_notes.md`** for models
   that the submitted draft cites: Detoxify, TF-Hub YAMNet card, Llama 3,
   Ollama, RapidOCR (checklist rows 1, 5, 6, 7). Whether to add S9–S13
   blocks is the student's call; the fields must come from the sources.
4. **Whisper transcribes only the first 60 s** (`audio_model.py:130`) while
   YAMNet averages over all 60 s chunks (`:175-181`). Whether this
   asymmetry is stated in Ch4 `[pe2f09a93]` is for the student to decide.
