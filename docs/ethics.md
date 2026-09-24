# Ethics — TriGuard

CLAUDE.md §20 + §21. Project deals with potentially harmful content, so ethics is treated as a design constraint, not an afterthought.

## Ethics quiz outcome (planned)

Expected outcome: **pass** with the following declared conditions:

- No human-subjects data is collected.
- No real user-generated content is scraped.
- All datasets used are public and properly licensed.
- Any peer review of LLM rationales (Track T7) is low-risk: the reviewer rates the *explanation*, not the harmful content itself, and may opt out at any time.

If the tutor flags any concern, the T7 peer review will be removed from scope and replaced with self-only review.

As run: no peer reviewer was recruited; the T7 usefulness ratings are the author's own single-rater judgement (`scripts/rate_t7.py`), and the deviation is recorded in Table E9 of `docs/report_evidence_tables.md`.

## Data handling

| Concern | Mitigation |
|---|---|
| Unnecessary exposure to harmful content | Hand-built T6 set deliberately uses *mild* examples; no extreme imagery; reviewer-warned before opening folder |
| Collecting personal data | Not collected. The prototype processes inputs the user voluntarily provides via demo upload |
| Using real participant data | Not used. All evaluation inputs are public datasets or synthetic |
| Public datasets | As used: Civil Comments (CC0-1.0), Memotion / SemEval-2020 Task 8 (research use), LibriSpeech test-clean (CC BY 4.0), ESC-50 (CC BY-NC 3.0). Hateful Memes (gated) and AudioSet (YouTube ids only) were planned but not used — see Table E9. Licences and attributions logged in `data/README.md` |
| Secure storage | Datasets stored locally only; `.gitignore` excludes raw harmful samples from the repo |
| Third-party services | None. The whole pipeline runs locally. No outbound API calls except for downloading model weights from HuggingFace at first run |
| Scraping social media | Not done. Project does not crawl any platform |
| Retaining harmful content | Hand-built T6 set kept in a single folder, deleted after final report submission |

## LLM judge ethical considerations

- The judge can hallucinate reasons. The system never presents the judge's output as autonomous truth: it is always tagged as "supporting human review".
- The judge is constrained by a JSON schema to keep its rationale short and tied to the evidence; the orchestrator runs a regex check that the rationale references at least one piece of evidence.
- The recommended action is advisory; downstream actions are taken by humans.

## Consent

No participant consent is required because no participants are involved at the prototype stage. If a future user study is approved, the Goldsmiths participant information sheet and consent form templates (provided with the module materials) will be used.

## Language used in the report

Per CLAUDE.md §11 the report uses careful, non-claiming language:

- "supports moderation" / "assists human review" / "demonstrates feasibility" / "provides structured evidence" / "highlights limitations" / "prototype system" — yes.
- "automatically detects hate", "achieves perfect accuracy", "replaces moderators" — no.

## What I will not do

- I will not collect real user data.
- I will not scrape any platform.
- I will not retain extreme harmful content beyond the evaluation period.
- I will not use the system to make autonomous moderation decisions.
- I will not claim improvements that the evaluation does not show.
