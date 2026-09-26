# Prototype Demonstration Video — Script & Shot List

> **HISTORICAL (preliminary-report video, Tier-A era).** Counts and shots below
> describe the mock-pipeline prototype as submitted then (e.g. "23 passed" —
> the suite is now 95 passed / 10 skipped WSL, 83 passed / 11 skipped offline, measured 2026-09-24 on the uncommitted working tree). The FINAL demo flows through the
> server UI instead: boot with `bash scripts/demo_up.sh`, then /ui presets →
> rule-vs-llama3 compare → llama3 streaming → /dashboard. Write a new shot list
> for the final video; keep this file as the preliminary record.
> Final shot list: docs/Video_Shot_List_Final.md (pre-flight: scripts/video_preflight.sh; numbers: docs/video_number_card.md).

**Project:** CM3070 Preliminary Report — TriGuard
**Length target:** 3–5 minutes (script ≈ 600 words ≈ 4 min 15 s at 140 wpm)
**Voiceover:** Hamza (own voice, no AI/speed manipulation per brief)
**Output format:** MP4

---

## How to record

- Screen-capture the terminal, the project tree in your editor and the JSON outputs.
- Use a single take per shot where possible.
- Speak in calm sentences, pause at line breaks.
- Final assembly: stitch the shots in order, normalise audio, export as MP4 (H.264 + AAC) at 1080p or 720p.
- Do not speed up or slow the audio.

---

## SCRIPT (with shot directions)

### Shot 1 — Title card (8 s)

*Static slide on screen: "TriGuard — Preliminary Report Prototype Demo · Hamza · CM3070".*

> "Hi, I'm Hamza. This is the prototype-demonstration video for my CM3070 Preliminary Report. The project is **TriGuard** — a multimodal, explainable, locally deployable content-moderation pipeline."

### Shot 2 — Motivation (35 s)

*Slide with three bullets:*
- *Harmful content increasingly crosses modalities*
- *Existing tools are usually single-modality or closed-cloud*
- *Regulators now expect rationales (DSA, UK Online Safety Act)*

> "The motivation is short. Harmful content increasingly crosses modalities — a meme combines image and text, a voice note layers over a violent visual. But the strongest moderation tools today are usually single-modality, like Google's Perspective API, or closed cloud services that platforms cannot self-host. At the same time, the EU Digital Services Act and the UK Online Safety Act now expect moderation decisions to come with a statement of reasons that a human can audit. TriGuard is my attempt to address all three of those gaps at once, by orchestrating several pre-trained models with a local LLM judge that emits a written rationale."

### Shot 3 — Architecture recap (20 s)

*Show `docs/figures/fig1_architecture.svg` full-screen (as-built figure; the preliminary take used `docs/architecture.png`).*

> "The architecture is six layers. An input handler validates the payload; a dispatcher routes each modality to a wrapper; the wrappers return normalised Pydantic evidence; the judge reads the evidence and emits a structured decision with a rationale; and a side branch sends the same result into the evaluation harness."

### Shot 4 — Repo tour (25 s)

*Show `tree src/triguard` and the `tests/` folder.*

> "This is the Tier-A prototype I have built. Pydantic schemas are in `orchestrator/schemas.py`. The text wrapper in `models/text_model.py` is a real scikit-learn TF-IDF plus logistic-regression classifier trained on a small bundled corpus. The image and audio wrappers are mocks. The judge in `models/llm_judge.py` has two paths — a deterministic rule-based judge for this demo, and an Ollama path with retry-on-invalid-JSON and a graceful fallback to the rule judge. The orchestrator wires it together."

### Shot 5 — Run the tests (20 s)

*Run `PYTHONPATH=src python -m pytest -q`.*

> "First the test suite. Twenty-three pytest cases run in about four seconds, covering schema bounds, the safe-cannot-block invariant, harmful-cannot-allow, partial-modality input, the orchestrator's missing-input rejection and the Ollama-unavailable fallback path."

### Shot 6 — Run a harmful sample (35 s)

*Run `PYTHONPATH=src python -m triguard.cli run data/sample_inputs/sample_harmful.json`. Highlight the key fields in the JSON output.*

> "Now the pipeline. I'll feed it a deliberately harmful payload — a threatening text, a photo described as containing a weapon, and an audio clip tagged as shouting. The system returns a risk score of 0.87, a risk label of *harmful*, all three modalities flagged, a recommended action of *block*, and a rationale that names the evidence: the text classifier's score, the image caption and the audio event. Everything is schema-valid by construction because the Pydantic models reject inconsistent output."

### Shot 7 — A real failure case (25 s)

*Run on `sample_safe.json` and pause on the borderline output + uncertainties.*

> "It is more interesting to look at a failure case. On a perfectly benign sample the text classifier scores 0.37, the pipeline labels it *borderline* and recommends *review*. The label is wrong — the text is plainly safe — but notice that the system tags `low_text_classifier_confidence` in the uncertainties list and chooses *review* rather than *block*. That is the conservative behaviour the design asks for. The chapter explains that the root cause is a very small training corpus, and the fix is to swap in a Hugging Face toxicity model in the next iteration."

### Shot 8 — Evaluation results (20 s)

*Run `python -m triguard.evaluation.run_eval`; show the printed metrics and the saved JSON envelope in `outputs/evaluation/<timestamp>/results.json`.*

> "The evaluation harness drives fourteen hand-built tri-modal samples through the pipeline, reports per-class precision, recall and F1, plus p50 and p95 latency, and saves a full results envelope to disk. On this constructed set the orchestration combines evidence into the intended label every time. I am very careful to flag in the chapter that this is a *consistency check* on the engineering, not a generalisation claim."

### Shot 9 — Close (15 s)

*Back to the title slide.*

> "That is the Tier-A prototype: schemas, a real text classifier, mock image and audio wrappers, a working judge, twenty-three tests and a small reproducible evaluation. Replacing the mocks with BLIP, Whisper and Ollama is the work of the next phase. Thank you."

---

## Timing summary

| Shot | Length |
|---|---|
| 1 Title | 8 s |
| 2 Motivation | 35 s |
| 3 Architecture | 20 s |
| 4 Repo tour | 25 s |
| 5 Tests | 20 s |
| 6 Harmful sample | 35 s |
| 7 Failure case | 25 s |
| 8 Evaluation | 20 s |
| 9 Close | 15 s |
| **Total** | **~ 3 min 23 s** |

Inside the 3–5 minute window with room for natural pauses and one slow re-read.

## Marking-rubric check

1. **Demonstration of prototype effective and impactful** — Shots 5, 6, 7, 8 each show concrete output, not slides about it.
2. **Knowledge of area + previous work** — Shot 2 + 3 reference Perspective API, DSA, OSA and the architecture from the report.
3. **Critical evaluation of prototype** — Shot 7 deliberately surfaces the prototype's failure mode and the planned fix.
4. **Successful evaluation + improvements** — Shot 8 shows real numbers; Shot 7 + closing line name the next iteration (real HF text model, BLIP, Whisper, Ollama).
5. **Format** — MP4, own voiceover, no speed manipulation.

## Recording checklist

- [ ] Title slide image prepared
- [ ] Terminal font ≥ 14 pt, dark background for legibility
- [ ] All three sample JSONs runnable end-to-end before recording
- [ ] `python -m pytest -q` returns *23 passed* before recording
- [ ] Microphone test; quiet room
- [ ] Export as MP4 (H.264 + AAC) and verify in VLC before upload
