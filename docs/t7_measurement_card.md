# T7 measurement card — rationale grounding (definitions and mechanics only)

Scope: what the T7 number IS (formula, vocabulary, aggregation, inputs) and
what checks do and do not exist. No interpretation. Every value below is
copied from a named file + line, a `results.json` key path, or a git command.
Report-side prose is the student's ([STUDENT] questions at the end).

Working-tree note: line numbers for `scripts/smoke_ollama.py` are given at
commit `908b1e5` (HEAD at time of writing); the `--save` addition in the
working tree shifts later definitions (`_allowed_numbers` 74 -> 147,
`_grounding_report` 88 -> 161, `unmatched_numbers` 103 -> 176).

---

## 1. Metric identity

| field | value | source |
|---|---|---|
| Track | T7 | `outputs/evaluation/20260705-113456/t7/results.json` key `track` |
| Metric name (envelope key) | `grounding_rate` | `results.json` line 6; `src/triguard/evaluation/run_t7.py` line 70 |
| Companion count | `invented_modality_count` | `results.json` line 7; `run_t7.py` line 71 |
| Unit / range | fraction in [0, 1], rounded to 4 dp (`round(grounded / n, 4)`) | `run_t7.py` line 70 |
| Per-item value | boolean `grounded` | `src/triguard/evaluation/grounding.py` line 45 |
| Envelope `note` (verbatim) | "grounding_rate = fraction of rationales citing >=1 evidence token. The rule judge grounds ~1.0 by construction (it concatenates the evidence), so the meaningful headline is the ollama/llama3 rate. usefulness_1to5 is left blank for a human rater." | `results.json` line 14 |
| Module docstring self-description | "Heuristic (not proof)" | `grounding.py` line 3 |

## 2. Formula

In words: a rationale is *grounded* when its lower-cased text contains, as a
substring, at least one string from the evidence-token vocabulary built from
the same item's `JudgeInput`. `grounding_rate` = (number of grounded items) /
(number of items scored).

Code, `src/triguard/evaluation/grounding.py` lines 15-48 (verbatim):

```python
def evidence_tokens(ji: JudgeInput) -> list[str]:
    """Concrete strings a grounded rationale could legitimately cite."""
    toks: list[str] = []
    if ji.text:
        toks.append(f"{ji.text.toxicity_score:.2f}")
        toks += [lbl.lower() for lbl in ji.text.top_labels]
        toks.append("toxicity")
    if ji.image:
        toks += re.findall(r"[a-z]{4,}", ji.image.caption.lower())
        toks += [c.lower() for c in ji.image.visual_risk_cues]
    if ji.audio:
        toks += [t.lower() for t, _ in ji.audio.yamnet_tags]
        toks += re.findall(r"[a-z]{4,}", ji.audio.transcript.lower())
    seen: set[str] = set()
    out: list[str] = []
    for t in toks:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def grounding_report(ji: JudgeInput, rationale: str) -> dict:
    """Grounded (cites >=1 evidence token) + any invented (unsupplied) modality."""
    low = rationale.lower()
    cited = [t for t in evidence_tokens(ji) if t in low]
    present = {m for m, ev in (("text", ji.text), ("image", ji.image),
                               ("audio", ji.audio)) if ev is not None}
    claimed = {m for m in ("text", "image", "audio") if m in low}
    return {
        "grounded": bool(cited),
        "cited": cited,
        "invented_modalities": sorted(claimed - present),
    }
```

## 3. Evidence-token vocabulary, rule by rule

| # | condition | token(s) added | `grounding.py` line | mechanical note |
|---|---|---|---|---|
| 1 | text evidence present | `toxicity_score` formatted to 2 dp (e.g. `"0.85"`) | 19 | exact string; `0.8` or `0.850` do not match |
| 2 | text evidence present | each `top_labels` entry, lower-cased | 20 | e.g. `toxic`, `threat`, `insult`, `obscene` |
| 3 | text evidence present | the literal word `"toxicity"` | 21 | added unconditionally whenever text evidence exists |
| 4 | image evidence present | every run of >= 4 lower-case ASCII letters in the caption | 23 | regex `[a-z]{4,}`; includes function words (`that`, `with`, `middle`) |
| 5 | image evidence present | each `visual_risk_cues` entry, lower-cased | 24 | |
| 6 | audio evidence present | each YAMNet tag name, lower-cased (scores discarded) | 26 | `for t, _ in ji.audio.yamnet_tags` |
| 7 | audio evidence present | every run of >= 4 lower-case ASCII letters in the transcript | 27 | same regex as row 4 |
| 8 | all | de-duplicate, keep first-seen order, drop empty strings | 28-34 | |

Matching: `t in low` (substring test on the lower-cased rationale), line 40.
`cited` = the ordered list of vocabulary tokens found (line 40).

Invented-modality check (lines 41-47): `present` = modalities whose evidence
is not `None`; `claimed` = each of the literal words `"text"`, `"image"`,
`"audio"` found as a substring of the lower-cased rationale (line 43);
`invented_modalities` = `claimed - present`, sorted.

## 4. Aggregation (`src/triguard/evaluation/run_t7.py`)

| step | line(s) | code / value |
|---|---|---|
| items loaded from manifest | 41 | `_load_items(Path(args.manifest))` |
| condition run per item | 46 | `_inputs_for(item, "multimodal")` |
| pipeline call | 49 | `run_pipeline(judge_mode=args.judge, **kwargs)` |
| JudgeInput reconstructed from result evidence | 50-51 | `JudgeInput(text=r.text_evidence, image=r.image_evidence, audio=r.audio_evidence)` |
| per-item report | 52 | `grounding_report(ji, r.rationale)` |
| counters | 53-54 | `grounded += int(rep["grounded"])`; `invented += int(bool(rep["invented_modalities"]))` |
| per-item fields persisted | 55-62 | `id, grounded, cited, invented_modalities, rationale[:200], usefulness_1to5=None` |
| `grounding_rate` | 70 | `round(grounded / n, 4) if n else None` |
| `invented_modality_count` | 71 | `invented` |
| NOT persisted | — | `TriGuardResult.model_versions` (carries `judge_label`), `uncertainties`, latency, full rationale beyond 200 chars |

## 5. Computed over what

| field | value | source |
|---|---|---|
| Manifest | `data/sample_inputs/triguard_eval_v1/manifest.json` at commit `c8f22a8` (v1) | `run_t6.py` line 39 (`_MANIFEST`); `git show c8f22a8:data/sample_inputs/triguard_eval_v1/manifest.json` |
| Manifest `provenance` (verbatim, first clause) | "AI-DRAFTED STARTER SET (non-confounder)." | same `git show`, key `provenance` |
| n | 18 | `results.json` line 5 |
| Item ids | S1-S4, B1-B3, H1-H4, I1, A1, MS1, MS2, MB1, MH1, MH2 | manifest `items[*].id` |
| Modality mix (counted from manifest `text`/`image`/`audio` non-null) | 11 text-only; 1 image-only (I1); 1 audio-only (A1); 5 multimodal: MS1 t+i+a, MS2 t+i, MB1 t+i, MH1 t+i+a, MH2 t+a | manifest |
| Media reused | `data/sample_inputs/blip_test.png`, `data/sample_inputs/audio_test.wav` | manifest `description` |
| `judge` | `"ollama"` | `results.json` line 4 |
| `config.text_backend` | `"hf"` | `results.json` line 9 |
| `config.image_backend` | `"blip"` | line 10 |
| `config.audio_backend` | `"real"` | line 11 |
| `config.run_env` | `"wsl-ubuntu-py312-tri"` | line 12 |
| `run_at` | `2026-07-05T11:34:56.008277+00:00` | line 3 |
| Model tag / temperature | not in the envelope; code defaults at `c8f22a8`: `llama3:8b-instruct-q4_K_M`, `temperature 0.0` | `docs/report_evidence_tables.md` Table E7 bullet 4 |
| Manifest superseded | v2 24-item set, commit `6bfdfc3` (2026-07-05) | `git log -1 6bfdfc3` |

## 6. Prompt rule under test

`src/triguard/models/llm_judge.py` line 70 (verbatim):

```
- Reference at least one piece of evidence in the rationale.
```

Nothing in `llm_judge.py` checks this rule at judge time (no reference to
`grounding` or a regex over `rationale` in that file). The check runs only
post hoc in `run_t7.py` via `grounding.py`.

## 7. Rule-judge rationale strings vs vocabulary tokens (mechanics behind the envelope note "~1.0 by construction")

`_rule_based_judge`, `llm_judge.py` lines 122-215, builds `rationale` by
joining `rationale_parts` (line 204). Each part embeds evidence strings that
are themselves vocabulary tokens (the envelope `note`, Section 1, is the
only place the repo states the "by construction" reading; the table below
lists the string templates that reading rests on):

| branch | line(s) | rationale string built | vocabulary token(s) it necessarily contains |
|---|---|---|---|
| text, `ts >= 0.5` | 136-140 | `"the text classifier flagged toxicity at {ts:.2f}"` + optional `" ({top_labels})"` | `"toxicity"` (rule 3); `ts` at 2 dp (rule 1); labels (rule 2) |
| text, `ts < 0.5` | 142 | `"the text appeared benign (toxicity {ts:.2f})"` | `"toxicity"`; `ts` at 2 dp |
| image, cues present | 151-153 | `"the image caption '{caption}' mentioned {cues}"` | caption words (rule 4); cues (rule 5) |
| image, no cues | 155-157 | `"the image caption '{caption}' showed no obvious risk cues"` | caption words (rule 4) |
| audio, risky tags | 167-169 | `"audio analysis detected {risky_tags}"` | tag names (rule 6) |
| audio, no risky tags | 171-174 | `"audio events: {all tag names}"` or `"no salient events"` | tag names (rule 6) if any tags |
| no modalities | 205-206 | `"no modalities supplied; defaulting to safe"` | none (vocabulary is empty; `grounded` would be `False`) |

Rule-judge rate was not separately measured in the committed T7 run
(`results.json` `judge` = `"ollama"`; no rule-judge T7 envelope under
`outputs/evaluation/*/t7/`).

## 8. Checks that do NOT exist in `grounding.py`

| absent check | evidence of absence | where a version DOES exist |
|---|---|---|
| Number hallucination (decimals in the rationale that match no evidence value) | no `re.findall(r"\d+\.\d+", ...)` and no `_allowed_numbers` in `grounding.py` (file is 48 lines, all shown in Section 2) | `scripts/smoke_ollama.py` at `908b1e5` lines 74-85 (`_allowed_numbers`), 100-103 (`unmatched_numbers`) — manual smoke script only, not used by `run_t7.py` |
| Confidence values in the vocabulary | `grep -n confidence src/triguard/evaluation/grounding.py` -> no match; rules 1-7 add `toxicity_score`, labels, caption/transcript words, cues, tag names only | `smoke_ollama.py` `_allowed_numbers` adds `text.confidence`, `image.confidence`, `transcript_confidence`, YAMNet scores (lines 78-84 at `908b1e5`) — as allowed numbers, not as citation tokens |
| YAMNet tag scores | `for t, _ in ji.audio.yamnet_tags` discards the score, line 26 | none |
| Completeness (all modalities cited) | `grounded = bool(cited)`, line 45 — one token suffices | none |
| Correctness of the cited claim (e.g. "high toxicity" vs the actual score) | no comparison between rationale wording and score magnitude | none |
| Whole-word modality match | line 43 uses substring `m in low`; `"text"` matches inside `"context"`, `"image"` inside `"imagery"` | none |
| Stop-word exclusion | regex `[a-z]{4,}` (lines 23, 27) admits `that`, `they`, `with`, `near` | none |
| Native-vs-fallback provenance per item | `run_t7.py` lines 55-62 persist no `judge_label` / `model_versions` / `uncertainties` | `TriGuardResult.model_versions["llm_judge"]` at runtime (`pipeline.py` line 141) — not written to the T7 envelope |

Consequence recorded in `docs/report_evidence_tables.md` Table E7 bullet 3:
item MB1's stored rationale matches the rule-judge strings at `llm_judge.py`
lines 137 and 156.

## 9. Per-item cited arrays (all 18, from `results.json` `per_item`)

Columns: modalities from the c8f22a8 manifest; `grounded`, `cited`,
`invented_modalities` verbatim from the file; `len` = stored rationale length
(200 = truncated by `run_t7.py` line 60).

| id | modalities | grounded | cited | invented | len |
|---|---|---|---|---|---|
| S1 | text | true | `["0.00", "toxicity"]` | `[]` | 159 |
| S2 | text | true | `["0.00", "toxicity"]` | `[]` | 159 |
| S3 | text | true | `["0.00", "toxicity"]` | `[]` | 159 |
| S4 | text | true | `["toxicity"]` | `[]` | 116 |
| B1 | text | true | `["0.09", "toxicity"]` | `[]` | 162 |
| B2 | text | true | `["0.24", "toxicity"]` | `[]` | 200 |
| B3 | text | true | `["0.68", "toxic", "toxicity"]` | `[]` | 128 |
| H1 | text | true | `["insult", "obscene", "toxic", "toxicity"]` | `[]` | 159 |
| H2 | text | true | `["threat", "toxic"]` | `[]` | 136 |
| H3 | text | true | `["0.51", "toxic", "toxicity"]` | `[]` | 200 |
| H4 | text | true | `["insult", "obscene", "toxic", "toxicity"]` | `[]` | 117 |
| I1 | image | true | `["house", "middle", "field"]` | `[]` | 200 |
| A1 | audio | true | `["jump", "that", "they", "near", "river", "bank"]` | `[]` | 200 |
| MS1 | text+image+audio | true | `["toxicity", "that"]` | `[]` | 200 |
| MS2 | text+image | true | `["toxicity"]` | `[]` | 154 |
| MB1 | text+image | true | `["0.63", "toxic", "toxicity", "house", "middle", "field"]` | `[]` | 134 |
| MH1 | text+image+audio | true | `["0.69", "threat", "toxic", "toxicity"]` | `[]` | 200 |
| MH2 | text+audio | true | `["insult", "toxic"]` | `[]` | 136 |

Mechanical counts from the table: 18/18 `grounded`; 0 items with a non-empty
`invented` list; 6 rationales at length 200; 3 items whose only cited tokens
are `"toxicity"` and/or a function word (S4, MS1, MS2 — cf. E7b row 2); items
citing a 2-dp score: S1, S2, S3, B1, B2, B3, H3, MB1, MH1 (9); items citing
a label: B3, H1, H2, H3, H4, MB1, MH1, MH2 (8); items citing a caption word:
I1, MB1 (2); items citing a transcript word: A1, MS1 (2); items citing a
visual cue or a YAMNet tag name: 0 (both media assets are the committed benign
ones, manifest `description`).

`usefulness_1to5` is `null` for all 18 (lines 25, 36, ..., 227).

## 10. T7-human card (companion measure)

| field | value | source |
|---|---|---|
| Status | **NOT YET PRODUCED** — `ls outputs/evaluation/*/t7_human/results.json` -> no such file. `data/t7_ratings.json` IS present and tracked (last commit `d50b43c`): `source_run` `20260705-113456`, 18 `ratings` entries, 0 rated / 18 with `usefulness_1to5` null (i.e. `--init` has been run, rating has not started) | shell listing + `git log -1 -- data/t7_ratings.json` + json count, 2026-09-24 |
| Tool | `scripts/rate_t7.py` | file |
| Scale (verbatim, lines 10-12) | "1 = useless to a moderator, 3 = partly useful, 5 = directly actionable. Rate the RATIONALE's usefulness for a human review decision, not whether the verdict was right." | `rate_t7.py` lines 10-12 |
| Scale string stored in the ratings file | `"1 = useless to a moderator, 3 = partly useful, 5 = directly actionable"` | lines 60-61 |
| Input | newest `outputs/evaluation/*/t7/results.json` by sorted path (`_newest_t7`, lines 37-42) | |
| Validation | every item rated; integer 1-5 (lines 89-96); refuses to merge otherwise (lines 97-101) | |
| Aggregation (lines 104-115) | `distribution` = count per value 1..5 (line 104); `mean_usefulness` = `round(statistics.mean(scores), 4)` (113); `median_usefulness` = `statistics.median(scores)` (114); `n` = number of scores (111) | |
| Envelope `track` | `"T7-human"` | line 106 |
| Output path | `outputs/evaluation/<UTC timestamp>/t7_human/results.json` | lines 126-128 |
| Limitations written into the envelope (verbatim, lines 118-124) | "single rater (the author); no inter-rater agreement available"; "ratings assess rationale usefulness for a human reviewer, not verdict correctness"; "small sample (n={len(scores)}) from one judge run; indicative, not a benchmark claim" | `rate_t7.py` lines 119-123 |
| What the rater sees | `id` + the stored (possibly 200-char-truncated) `rationale` — `rate_t7.py` line 66 copies `it.get("rationale")` from the T7 envelope | |

### Runbook to produce it

1. `python scripts/rate_t7.py --init` (once). Writes `data/t7_ratings.json`
   with 18 entries from run `20260705-113456`. Refuses to run if the file
   already exists (lines 52-55) — never re-run `--init` after rating has
   started; delete the file only to restart from scratch. ALREADY DONE in
   this checkout: the file exists with all 18 `usefulness_1to5` null (see
   Status row above), so start at step 2.
2. Open `data/t7_ratings.json`; set every `usefulness_1to5` to an integer
   1-5 (the rater's own judgement; lines 20-21 of the script docstring).
3. `python scripts/rate_t7.py --merge`. Writes a NEW envelope; the original
   T7 file is never modified (docstring lines 17-18).
4. Rate before merge: `--merge` exits 1 listing unrated / non-integer items.
5. Commit the new `outputs/evaluation/<ts>/t7_human/results.json` envelope
   (script prints "commit this file as evidence", line 135). Committing is a
   user action; this session made no git changes.
6. The report may then cite `mean_usefulness`, `median_usefulness`,
   `distribution`, `n` and the three `limitations` strings from that file
   only.

Draft anchors that will need the number once it exists:
`docs/draft_as_submitted/ch5.md` `[p3b4fa517]` (section 5.7 heading),
`[p33129605]`, `[p4435fe4c]`, table row line 20 ("T7 | ... usefulness blank");
`ch5.md` `[pc4f2f13e]` (Objective 4 status).

## 11. [STUDENT] questions this section must answer

Questions only; the facts above are the material.

- What does `grounding_rate = 1.0` mean, given that one token suffices and
  `"toxicity"` is always in the vocabulary when text evidence exists?
- What does it NOT mean (completeness, correctness of the cited magnitude,
  usefulness to a moderator, native-llama3 provenance for all 18)?
- Why was a floor-style heuristic chosen as the implemented T7 measure
  rather than the two-rater protocol in `docs/evaluation_protocol.md`?
- Why is the metric reported for the llama3 judge and only asserted "by
  construction" for the rule judge?
- Which blind spots in Section 8 matter most for the moderation use case
  (number hallucination not scored; confidence values outside the
  vocabulary; substring modality test; 200-char truncation; MB1 provenance)?
- How should the missing T7-human measure be presented (planned, single
  rater, not a benchmark claim) if it is produced before submission — and
  how if it is not?
- Does a manifest labelled "AI-DRAFTED STARTER SET" change what the 18-item
  result can support, and how does the v2 replacement (6bfdfc3) affect any
  claim of comparability with T6?
