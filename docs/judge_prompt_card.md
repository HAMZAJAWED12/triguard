# Judge prompt card — `src/triguard/models/llm_judge.py` (facts and pointers only)

Every line number is at commit `908b1e5` (HEAD at time of writing) unless a
`git show <commit>:` form is given. Verbatim blocks are copied from the
source. No design justification is written here; where a "why" belongs in the
report it is marked [STUDENT].

---

## 1. The prompt, verbatim

### 1a. `JUDGE_PROMPT_TEMPLATE`, `llm_judge.py` lines 55-76

```python
JUDGE_PROMPT_TEMPLATE = """You are a content-moderation judge. Read the evidence below
and return ONE JSON object that conforms exactly to this schema:

{{
  "risk_score": float in [0,1],
  "risk_label": "safe" | "borderline" | "harmful",
  "flagged_modalities": list of "text" | "image" | "audio",
  "rationale": short paragraph grounded in the evidence,
  "uncertainties": list of short strings,
  "recommended_action": "allow" | "review" | "block"
}}

Rules:
- A "safe" label must NOT recommend block.
- A "harmful" label must NOT recommend allow.
- Reference at least one piece of evidence in the rationale.
- If evidence is conflicting, prefer "borderline" + "review".

Evidence:
{evidence_block}

Return ONLY the JSON object, nothing else."""
```

Brace escaping: the template is rendered with `str.format` (line 226,
`JUDGE_PROMPT_TEMPLATE.format(evidence_block=evidence_block)`). In
`str.format`, `{{` and `}}` are escapes for literal `{` and `}`, so the model
receives a single `{` on the schema's opening line and a single `}` on its
closing line; `{evidence_block}` is the only substitution field. Verified in
this session: `JUDGE_PROMPT_TEMPLATE.format(evidence_block='X').splitlines()`
gives `{` at index 3 and `}` at index 10.

### 1b. Stricter retry suffix, lines 232-233

Appended to the already-rendered prompt on the second attempt only
(`stricter = prompt + ...`):

```python
        stricter = prompt + "\n\nIMPORTANT: respond with ONLY the JSON object. " \
                            "Do not add commentary, markdown or code fences."
```

### 1c. One rendered evidence block

Produced in this session by importing `triguard.models.llm_judge` read-only
and calling `_build_evidence_block` (lines 346-365) on the `_harmful()`
fixture from `tests/test_llm_judge.py` lines 19-32 (text toxicity 0.85,
labels `["threat"]`, confidence 0.8; image caption "an image apparently
depicting weapon", cues `["weapon"]`, confidence 0.55; audio transcript
"(loud distressed vocalisation)", transcript_confidence 0.4, tags
`[("shouting", 0.7)]`). Output, verbatim (the dash is U+2014):

```
TEXT — toxicity=0.85, labels=['threat'], confidence=0.80
IMAGE — caption='an image apparently depicting weapon', visual_risk_cues=['weapon'], confidence=0.55
AUDIO — transcript='(loud distressed vocalisation)', tags=[('shouting', 0.7)], transcript_confidence=0.40
```

Format facts: one line per supplied modality, in the fixed order text, image,
audio (lines 348, 353, 359); absent modalities produce no line; numbers are
rendered at 2 dp (`:.2f`); lists are Python `repr` (single quotes, tuples for
YAMNet tags); lines joined with `"\n"` (line 365).

## 2. Structure table

| segment | lines | what the segment instructs (mechanical) | enforcement beyond the prompt | where enforced | student note |
|---|---|---|---|---|---|
| Role + task sentence | 55-56 | act as a content-moderation judge; return ONE JSON object matching the schema | none for "ONE"; parser takes the span from the first `{` to the last `}` in the response | `_parse_judge_output` 335-343 | |
| Schema block, `risk_score` | 59 | float in [0,1] | `Field(ge=0.0, le=1.0)` | `orchestrator/schemas.py` line 64 | |
| Schema block, `risk_label` | 60 | one of safe / borderline / harmful | `RiskLabel` Literal | `schemas.py` line 65 | |
| Schema block, `flagged_modalities` | 61 | list of text / image / audio | `list[Modality]`, `Modality = Literal["text","image","audio"]` | `schemas.py` lines 59, 66 | |
| Schema block, `rationale` | 62 | "short paragraph grounded in the evidence" | length only: `min_length=1, max_length=600`; no length is stated in the prompt; groundedness not checked at judge time | `schemas.py` line 67; post-hoc only via `evaluation/grounding.py` 37-48 (T7) | |
| Schema block, `uncertainties` | 63 | list of short strings | `list[str]` (any length, any content) | `schemas.py` line 68 | |
| Schema block, `recommended_action` | 64 | one of allow / review / block | `Action` Literal | `schemas.py` lines 60, 69 | |
| Rule 1 | 68 | safe must NOT recommend block | `model_validator` raises `ValueError("safe label cannot recommend block")` | `schemas.py` lines 71-75 | |
| Rule 2 | 69 | harmful must NOT recommend allow | `model_validator` raises `ValueError("harmful label cannot recommend allow")` | `schemas.py` lines 71-73, 76-77 | |
| Rule 3 | 70 | reference >= 1 piece of evidence in the rationale | not enforced at judge time (no regex in `llm_judge.py`); measured post hoc in T7 | `evaluation/grounding.py` 37-48 via `run_t7.py` 52 | |
| Rule 4 | 71 | conflicting evidence -> prefer borderline + review | none (no code defines "conflicting") | — | |
| Evidence block | 73-74 | the rendered `_build_evidence_block` text | n/a (input) | `_build_evidence_block` 346-365 | |
| Output instruction | 76 | return ONLY the JSON object | tolerant parse (see row 1); on failure the stricter suffix is appended once (non-stream path only) | 232-233; stream path has no retry, 302-304 (docstring), 327-328 | |
| Not in the prompt | — | no `model_versions`, thresholds, examples, or the 600-char limit; no system message | — | — | |

Parser behaviour (`_parse_judge_output`, 335-343): `text.find("{")`,
`text.rfind("}")`; if either is -1 or `end <= start`, raises
`ValidationError.from_exception_data("JudgeOutput", [])` (line 340); else
`json.loads(blob)` (342) then `JudgeOutput.model_validate(obj)` (343).
`json.JSONDecodeError` and `ValidationError` are both caught by the caller
(lines 231, 237, 327).

## 3. Request parameters (non-stream `_ollama_generate`, lines 241-255)

| parameter | value | line(s) |
|---|---|---|
| endpoint | `f"{_ollama_host()}/api/generate"`; host = env `OLLAMA_HOST`, default `http://localhost:11434` | 248; 30, 34-36 |
| method / headers | POST (`data=body`), `Content-Type: application/json` | 247-251 |
| `model` | `_ollama_model()`: env `TRIGUARD_OLLAMA_MODEL`, else `OLLAMA_MODEL`, else `llama3:8b-instruct-q4_K_M` | 243; 31, 39-45 |
| `prompt` | the rendered template (single string; no chat `messages`) | 243 |
| `stream` | `False` | 243 |
| `keep_alive` | `_ollama_keep_alive()`: env `TRIGUARD_OLLAMA_KEEP_ALIVE`, default `"30m"` | 244; 48-52 |
| `options.temperature` | `0.0` (literal; not env-configurable) | 245 |
| client timeout | `float(os.getenv("OLLAMA_TIMEOUT", "60"))` seconds, passed to `urlopen` | 252-253 |
| response field read | `data.get("response", "")` | 255 |
| **not set** | `format` (no `"format": "json"`), `system`, `seed`, `num_ctx`, `top_p`, `num_predict`, `stop` — the body dict at 242-246 contains exactly `model, prompt, stream, keep_alive, options{temperature}` | 242-246 |

Streaming variant `_ollama_generate_stream` (258-287): same body except
`"stream": True` (268); NDJSON chunks read line by line; stops at
`done: true` (286-287); the same `OLLAMA_TIMEOUT` is applied per read
(docstring 264-265).

## 4. Fallback tags

### 4a. Non-stream ladder (`judge`, lines 88-114; `_judge_via_ollama`, 223-238)

| condition | attempts | exception caught | uncertainty tag appended | judge that answers | lines |
|---|---|---|---|---|---|
| valid JSON on first attempt | 1 | — | none | ollama | 228-230 |
| invalid on first, valid on retry (prompt + suffix) | 2 | — | none | ollama | 231-236 |
| invalid twice | 2 | `JudgeFailure` (raised 238) | `judge_output_invalid` | rule | 99-103 |
| server unreachable / connection refused | 1 (raises before response) | `urllib.error.URLError` | `ollama_unavailable:{e.reason}` | rule | 104-108 |
| any other error (incl. socket timeout) | 1 | `Exception` | `ollama_unavailable:{type(e).__name__}` | rule | 109-113 |
| `force_mode`/`TRIGUARD_JUDGE` not `"ollama"` | 0 | — | none | rule | 94, 114 |

Recorded example tags (DECISIONS.md lines 256-258): `ollama_unavailable:TimeoutError`;
`ollama_unavailable:[Errno 111] Connection refused`.

### 4b. Stream ladder (`judge_stream`, lines 290-332) — "invalid once"

| condition | attempts | tag | terminal event `source` | lines |
|---|---|---|---|---|
| all chunks received, joined text parses | 1 | none | `"ollama"` | 321-326 |
| joined text invalid | 1 (no stricter retry: docstring 302-304) | `judge_output_invalid` | `"rule_fallback"` | 327-328, 330-332 |
| `URLError` before/while streaming | 1 | `ollama_unavailable:{e.reason}` | `"rule_fallback"` | 316-317 |
| other exception mid-stream | 1 | `ollama_unavailable:{type(e).__name__}` | `"rule_fallback"` | 318-319 |

### 4c. Label mapping

| layer | rule | lines |
|---|---|---|
| `pipeline._JUDGE_FALLBACK_TAGS` | `("ollama_unavailable", "judge_output_invalid")` | `orchestrator/pipeline.py` 35 |
| `pipeline.judge_label(judge_mode, judge_out)` | effective mode = arg, else env `TRIGUARD_JUDGE`, else `"rule"`; if effective is `"ollama"` and any uncertainty `startswith` a fallback tag -> `"ollama->rule"`, else `"ollama"`; otherwise `"rule"` | 43-56 |
| written to | `TriGuardResult.model_versions["llm_judge"]` | 141 |
| API `/analyse/compare` | `"ollama": {"judge_label": judge_label("ollama", ollama_out), ...}` after `llm_judge.judge(judge_input, force_mode="ollama")` | `api/main.py` 298, 321 |
| API `/analyse/stream` | terminal event gets `judge_label = "ollama" if source == "ollama" else "ollama->rule"` | `api/main.py` 387-392 |
| `scripts/smoke_ollama.py --save` (working tree) | `judge_label` key = `pipeline.judge_label("ollama", out)` | `smoke_ollama.py` `_save_envelope` |

## 5. E13a — prompt revision log (git facts)

Method: `git log --date=short -- src/triguard/models/llm_judge.py` lists
exactly four commits. For each, `git show <c>:src/triguard/models/llm_judge.py`
was read, the text between `JUDGE_PROMPT_TEMPLATE = """` and the closing
`"""` was extracted, and SHA-256 computed; for the retry suffix the two
source lines starting at `stricter = prompt +` were compared verbatim across
the same five points and the resulting Python string value was hashed.

| commit | date | subject | what changed in `llm_judge.py` (from `git diff`) | template lines | template SHA-256 (first 16) | prompt text changed? |
|---|---|---|---|---|---|---|
| `1373e06` | 2026-06-23 | fix(repo): track src/triguard/models + feat(image): real BLIP tier (Sprint 2) | file first enters git history (256 lines). Commit body: the `.gitignore` rule `models/` had shadowed `src/triguard/models/`, so the initial commit omitted all four wrappers | 34-55 | `1df9a321a8f1c535` | n/a (first tracked version) |
| `4f10803` | 2026-07-02 | feat(judge): exercise + harden real Ollama LLM judge path (Prompt 4) | +34/-10: module-level `OLLAMA_HOST`/`OLLAMA_MODEL` replaced by call-time `_ollama_host()`/`_ollama_model()` (+`TRIGUARD_OLLAMA_MODEL`); single `except (URLError, JudgeFailure)` split into three handlers with distinct tags; `json.JSONDecodeError` added to both parse `except`s; `OLLAMA_TIMEOUT` env (was literal 60); tag spelling `ollama_unavailable: X` -> `ollama_unavailable:X` | 48-69 | `1df9a321a8f1c535` | no |
| `e866541` | 2026-07-05 | feat(demo): Phase D - presets, rule-vs-llama3 compare, streaming judge, eval dashboard (D-025) | +77/-1: `Iterator` import; new `_ollama_generate_stream` and `judge_stream` (additive; non-stream path untouched) | 48-69 | `1df9a321a8f1c535` | no |
| `daae032` | 2026-07-25 | fix(demo): demo-readiness hardening (D-027) | +9: new `_ollama_keep_alive()` (env `TRIGUARD_OLLAMA_KEEP_ALIVE`, default `"30m"`); `keep_alive` added to both request bodies | 55-76 | `1df9a321a8f1c535` | no |
| `908b1e5` (HEAD) | — | — | no diff vs `daae032` for this file | 55-76 | `1df9a321a8f1c535` | no |

Full template hash (identical at all five points):
`1df9a321a8f1c535d3a3c5c0685e8314364b4d3e2233404a04387c56f2a824a0`.
Retry suffix: the two source lines (`1373e06` 202-203, `4f10803` 225-226,
`e866541` 225-226, `daae032` 232-233, `908b1e5` 232-233) are byte-identical
at all five points; SHA-256 of the suffix's Python string value
(`"\n\nIMPORTANT: respond with ONLY the JSON object. Do not add commentary,
markdown or code fences."`) is
`7439584c7114e054e87ceb7e7313af341e034b6a1f2d6da7a925540393c73c58`
(recomputed 2026-09-24).

History note: `1373e06` is the first commit containing the file; its body
states the wrappers were absent from the initial commit because of the
`.gitignore` rule. Any prompt drafting before 2026-06-23 is therefore not
recoverable from git (no earlier blob exists).

## 6. E13b — prompt validation log (pointers only, no metric values)

| date | evidence | n | what was checked | outcome word | pointer |
|---|---|---|---|---|---|
| 2026-06-25 | D-015 real-run result, `data/sample_inputs/sample_harmful.json`, WSL, `llama3:8b-instruct-q4_K_M` | 1 sample | schema re-validation; rationale grounding (tokens cited, no invented modalities/numbers) via `scripts/smoke_ollama.py`; fallback on cold-load timeout and on server stopped | passed / degraded-honestly | `DECISIONS.md` lines 204-258 (result block 240-258) |
| 2026-07-05 | T7 grounding run, llama3 judge, v1 set | 18 items | per-item `grounded` + `invented_modalities` under `grounding.py` 37-48 | grounded (floor) | `outputs/evaluation/20260705-113456/t7/results.json`; `docs/report_evidence_tables.md` Table E7 (line 194), E7b (line 245); `docs/t7_measurement_card.md` |
| 2026-07-05 | Phase D live smoke (streaming judge, compare endpoint), WSL, mock perception, warm llama3 | 1 sample (stream) + slow tests | terminal event `source:"ollama"` schema-valid; offline endpoints degrade to `ollama->rule` / `rule_fallback`; `--run-slow` on the two Phase D test files | passed | `DECISIONS.md` lines 626-633 (D-025, header line 552) |
| 2026-07-25 | T6 v2 two-judge comparison (rule vs llama3), same v2 set | 24 items | label agreement per condition, confusion matrices, latency | compared | `DECISIONS.md` line 754 (D-029); `docs/report_evidence_tables.md` Table E6c (line 140) |
| any | opt-in slow test | 1 fixture | `JudgeOutput` schema validity of the live path; skips when Ollama unreachable | skip-or-pass | `tests/test_llm_judge_ollama.py` |
| any | offline tests | fixtures | stream token/final protocol and fallback tags with `_ollama_generate_stream` monkeypatched; unreachable-host fallback | pass | `tests/test_llm_judge_stream.py`; `tests/test_llm_judge.py` |

## 7. Design-vs-shipped map

| design statement | source line | shipped behaviour | source line | difference (factual) |
|---|---|---|---|---|
| Orchestrator validates `JudgeOutput`; if invalid, retries once with a stricter prompt; if still invalid, returns a `borderline` result with `uncertainties=["judge_output_invalid"]` | `docs/system_architecture.md` 107 | retry lives inside `llm_judge._judge_via_ollama`, not the orchestrator; after two invalid attempts `judge()` returns the rule judge's output (label from rule scoring, 185-193) with `judge_output_invalid` appended | `llm_judge.py` 223-238, 99-103; `pipeline.py` 137 (single call) | location of retry (judge module vs orchestrator); fallback result is rule-scored, not a fixed `borderline` |
| Same statement | `docs/project_design_draft.md` 75 | as above | as above | as above |
| Fixture test: all three modalities + invalid JSON -> orchestrator retries once -> if still invalid -> `borderline` result with `uncertainties=["judge_output_invalid"]` | `docs/evaluation_protocol.md` 58 | stream path (single attempt, no retry): `tests/test_llm_judge_stream.py` line 104 asserts `judge_output_invalid`; non-stream invalid-twice: `tests/test_smoke_ollama_save.py` (working tree) asserts two `_ollama_generate` calls, `judge_output_invalid`, `judge_label` `ollama->rule` on a text-only sample; the label is whatever the rule judge computes | `tests/test_llm_judge_stream.py` 91-104; `tests/test_smoke_ollama_save.py`; `llm_judge.py` 99-103 | no test asserts a fixed `borderline` on fallback (label is data-dependent); no committed test uses a three-modality invalid-JSON fixture on the non-stream path |
| Ollama JSON that does not parse -> retry once -> fall back to rule judge recording `"ollama_unavailable: ..."` | `docs/chapter4_prototype.md` 13 | invalid-twice records `judge_output_invalid`; `ollama_unavailable:<reason>` is recorded for unreachable/timeout/other errors, without a space after the colon | `llm_judge.py` 99-113 | tag name for the invalid-JSON case; spacing |
| Prompt template: system message defining role + JSON schema; user message containing the evidence summary | `docs/system_architecture.md` 113 | single `prompt` string sent to `/api/generate`; no `system` key, no chat `messages` | `llm_judge.py` 242-246 | one field vs two-message structure |
| Guardrail: judge must reference >= 1 piece of evidence in its rationale (regex check); else flag uncertainty | `docs/system_architecture.md` 115 | no regex or grounding check in `llm_judge.py`; rule 3 is a prompt instruction only (line 70); grounding measured post hoc in T7 | `llm_judge.py` 70; `evaluation/grounding.py` 37-48 | runtime guardrail not shipped; offline measurement exists instead |
| Default model `llama3:8b-instruct-q4` | `docs/system_architecture.md` 112 | `_DEFAULT_OLLAMA_MODEL = "llama3:8b-instruct-q4_K_M"` | `llm_judge.py` 31 | quantisation suffix `_K_M` |
| Connect to local Ollama, default `http://localhost:11434` | `docs/system_architecture.md` 111 | `_DEFAULT_OLLAMA_HOST = "http://localhost:11434"`, env `OLLAMA_HOST` | `llm_judge.py` 30, 34-36 | none |

Draft-report pointers (anchors only, no quotation): `docs/draft_as_submitted/ch4.md`
`[p3245e8cd]` (the prompt paragraph); `ch5.md` `[p3b4fa517]` (5.7 heading),
`[p4435fe4c]` (grounding result paragraph), `[p64998ef6]` (live comparison
paragraph), `[pc4f2f13e]` (Objective 4).

## 8. For integration

Owned by the Integrate stage; copy from here.

### E13a — prompt revision log (Ch4.3)

Source: `git log -- src/triguard/models/llm_judge.py`; per-commit
`git show <c>:src/triguard/models/llm_judge.py`; SHA-256 of the text inside
`JUDGE_PROMPT_TEMPLATE = """..."""`.

| commit | date | change to `llm_judge.py` | prompt text changed? | template SHA-256 (16) |
|---|---|---|---|---|
| `1373e06` | 2026-06-23 | first tracked version of the file (earlier drafting not in git) | n/a | `1df9a321a8f1c535` |
| `4f10803` | 2026-07-02 | call-time host/model/timeout; split fallback tags; `JSONDecodeError` handled | no | `1df9a321a8f1c535` |
| `e866541` | 2026-07-05 | streaming variant added (`_ollama_generate_stream`, `judge_stream`) | no | `1df9a321a8f1c535` |
| `daae032` | 2026-07-25 | `keep_alive` request parameter added | no | `1df9a321a8f1c535` |

Retry suffix (lines 232-233) likewise unchanged across all four commits.

### E13b — prompt validation log (Ch4.3, pointers only)

| date | evidence | n | what was checked | outcome word | pointer |
|---|---|---|---|---|---|
| 2026-06-25 | D-015 real run on `sample_harmful.json` | 1 | schema re-validation; grounding; two fallback modes | passed | `DECISIONS.md` 240-258 |
| 2026-07-05 | T7 grounding run (llama3, v1 set) | 18 | `grounded`, `invented_modalities` | grounded (floor) | Table E7 / E7b; `docs/t7_measurement_card.md` |
| 2026-07-05 | Phase D live smoke (stream + compare) | 1 | schema-valid `source:"ollama"` terminal event; honest degradation offline | passed | `DECISIONS.md` 626-633 |
| 2026-07-25 | T6 v2 two-judge comparison | 24 | rule vs llama3 per condition | compared | Table E6c; `DECISIONS.md` 754 |

### DECISIONS draft entry

```
## Decision 0XX: Judge prompt — designed once, validated, not revised
Date: [STUDENT — date of integration]
Status: [STUDENT]

Context: `JUDGE_PROMPT_TEMPLATE` (`src/triguard/models/llm_judge.py` 55-76)
and the stricter retry suffix (232-233) have identical content at every commit
that touched the file (1373e06, 4f10803, e866541, daae032; SHA-256
1df9a321a8f1c535...). The four commits changed request handling (call-time
env, fallback-tag split, JSON hardening, streaming variant, keep_alive) but
not the prompt text. Validation evidence: D-015 single-sample real run
(DECISIONS.md 240-258); T7 grounding run n=18
(outputs/evaluation/20260705-113456/t7/results.json); Phase D live smoke
(DECISIONS.md 626-633); T6 v2 two-judge comparison n=24 (D-029). Design
documents differ from the shipped prompt in: system/user two-message
structure vs single prompt field (system_architecture.md 113); runtime regex
guardrail vs post-hoc T7 measurement (system_architecture.md 115); model tag
suffix (112); fallback result rule-scored rather than fixed borderline
(107; project_design_draft.md 75; evaluation_protocol.md 58); tag name for
invalid JSON (chapter4_prototype.md 13). Request omits `format`, `system`,
`seed`, `num_ctx` (llm_judge.py 242-246); `temperature` is a literal 0.0
(245).
Options considered: [STUDENT]
Decision: [STUDENT]
Reason: [STUDENT — the repo records NO reason for single-prompt design,
temperature 0.0, or the absence of format=json; see Section 9]
Impact: prompt text is identical (same SHA-256) at every commit spanning
the T7, E6c and D-015 runs listed above; the design-vs-shipped differences
above are not yet stated in Ch4/Ch5 (E9 lists protocol deviations only) —
[STUDENT] to decide where and whether they are stated; no code change.
```


## 9. [STUDENT] questions

The repository contains NO recorded reason for any of the following
(searched: `llm_judge.py` comments/docstrings, `DECISIONS.md` D-015/D-025/
D-027, design docs). Answers must be the student's own.

- Why a single prompt field rather than the system + user message structure
  in `docs/system_architecture.md` 113?
- Why is `format: "json"` (an Ollama request option) not set, given that the
  parser tolerates surrounding text and a stricter retry exists instead?
- Why `temperature: 0.0`, and why is it a literal rather than configurable
  (unlike host, model, timeout, keep_alive)?
- Why was the prompt never revised after the D-015 observations (audio
  modality omitted from flags; risk_score high relative to a borderline
  label — DECISIONS.md 252-256)?
- Why is the streaming path "invalid once" while the non-stream path is
  "invalid twice"?
- Why does the prompt state no rationale length, while the schema enforces
  600 characters?
- Why was the runtime grounding guardrail (`system_architecture.md` 115)
  replaced by an offline measurement?
