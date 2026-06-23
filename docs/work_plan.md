# Work Plan — TriGuard

CLAUDE.md §15 format. Gantt-style table; live document.

## Gantt-style table

Legend: **[done]** complete · **[active]** in progress · **[next]** upcoming · *(empty)* future.

| Wk | Focus | Main tasks | Deliverable | Status | Risk / contingency |
|---:|---|---|---|---|---|
| 1 | Concept | Choose template, set up repo + journal | Pitch deck skeleton, JOURNAL.md | **[done]** | — |
| 2 | Pitch | 3–5 min video pitch script + slides | `TriGuard_Pitch_Deck.pptx` + `Video_Script_TriGuard.md` | **[done]** | User records voiceover |
| 3 | Ethics + Proposal | Ethics quiz; formative Project Proposal | Quiz submitted; Proposal submitted | **[done]** | — |
| 4 | Literature review | 8 sources, referencing notes, matrix, lit review draft | `TriGuard_Literature_Review.pdf` (5 pages, 2040 words) | **[done]** | — |
| 5 | Project design | Design draft, architecture diagram, evaluation protocol, work plan, inclusive design, ethics, risk register | `TriGuard_Project_Design.pdf` (6 pages, 1783 words) + supporting `docs/*.md` | **[done]** | — |
| 6 | Preliminary Report | Assemble Preliminary Report from lit review + design + plan + risk register; check tutor for prototype requirement | **Preliminary Report (10 %)** | **[next — 2–3 weeks out]** | R12: confirm prototype-evidence requirement before submission |
| 7 | Mock pipeline | Repo skeleton (`src/triguard/`), Pydantic schemas, mock text/image/audio wrappers, orchestrator, unit tests | Tier-A prototype (M3–M5) | *Starts after Wk 6 submission* | If schemas unclear → use minimal `dict` outputs first |
| 8 | Real text wrapper | HF toxicity classifier wrapper + tests | Text wrapper + tests (M6) | | If HF model heavy → quantised fallback |
| 9 | Real image wrapper | BLIP captioning + visual cue heuristics + tests | Image wrapper + tests | | If BLIP heavy → MobileNet captioner |
| 10 | Real audio wrapper | Whisper + YAMNet wrappers + tests | Audio wrapper + tests (M7) | | If Whisper slow → Whisper-tiny |
| 11 | LLM judge — real | Ollama integration; prompt; Pydantic validation | LLM judge + retry logic | | If Ollama slow → 3 B quantised model |
| 12 | End-to-end smoke run | Wire it all together; first 10 multimodal samples | Smoke-test output JSONs | | If pipeline breaks → mock judge |
| 13 | Evaluation harness | T1, T2, T5 implemented | metrics scripts | | — |
| 14 | T3 + T4 evaluations | Hateful Memes (or fallback) + AudioSet eval | results JSONs + failure logs | | Dataset access fallback |
| 15 | Build T6 eval set | Hand-label 50 synthetic items | `data/sample_inputs/triguard_eval_v1` | | — |
| 16 | T6 run + iterate prompt | Full pipeline eval; tune judge prompt | per-class F1, confusion matrix | | If F1 poor → revise prompt only, no model swap |
| 17 | FastAPI demo + T7 | Demo endpoint; rationale review form | Demo URL + T7 ratings | | If peer review blocked → self-only T7 |
| 18 | Formative draft report | ~ 6 000 words covering all sections | **Draft Report (formative)** | | Reuse `docs/` markdown |
| 19 | Apply feedback | Tighten lit review; expand discussion; T8 measurement | revised report | | — |
| 20 | Portfolio polish | README, demo video, repo cleanup | Public-ready repo | | — |
| 21 | Exam revision | Pure exam prep; coding hard-stop | — | | — |
| 22 | Exam | **Sit written exam (20 %)** | — | | — |
| 23 | Final demo video | Record TriGuard demo (different from Wk 2 pitch) | demo video | | — |
| 24 | Final submission | Final Report + code + video upload | **Final Report (60 %) + Project Presentation Video (5 %)** | | Submit 24 h early; backup on Drive + USB |

## Milestone alignment (CLAUDE.md §35)

| Milestone | Weeks | Status |
|---|---|---|
| M1 Literature Review foundation | 4 | **Done** |
| M2 Project Design | 5 | **Done** |
| M3 Repository Setup | 7 | Pending — starts after Preliminary Report |
| M4 Schemas | 7 | Pending |
| M5 Mock Pipeline | 7 | Pending |
| M6 First Real Model | 8 | Pending |
| M7 Multimodal Prototype | 9–10 | Pending |
| M8 Evaluation Prototype | 13–14 | Pending |
| M9 Demo API | 17 | Pending |
| M10 Preliminary Report Preparation | 6 | **Next — 2–3 weeks out** |

## Time budget

Plan totals ~ 230 hours across 24 weeks ≈ 9–10 h/wk. Heavier weeks: 10 (Preliminary Report), 18 (formative draft), 24 (final submission).
