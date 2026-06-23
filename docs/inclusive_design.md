# Inclusive Design — TriGuard

CLAUDE.md §19. Ten commitments, treated as first-class design requirements.

## Commitments

| # | Commitment | How TriGuard satisfies it |
|---|---|---|
| 1 | Output is understandable to non-technical reviewers | The `rationale` field is a plain-English paragraph; the demo UI shows it prominently above the raw evidence |
| 2 | Decisions include explanation, not only a score | `JudgeOutput.rationale` is required; a result with no rationale is treated as an error |
| 3 | Interface does not overwhelm with raw output | Demo UI shows three tiers: top-line label/score; one-paragraph rationale; "show raw evidence" toggle |
| 4 | Uncertainty is shown clearly | `JudgeOutput.uncertainties` list + a visible confidence band; orchestrator escalates low-confidence cases to `review` |
| 5 | Labels are readable | Single-syllable colour-coded labels (`safe` / `borderline` / `harmful`); no jargon in user-facing copy |
| 6 | Future UI uses clear contrast and font size | Demo CSS pinned to ≥ 16 px body, WCAG-AA contrast, system fonts; no decorative-only icons |
| 7 | Uncertain outputs are not presented as truth | A `borderline` label is always paired with the recommended action `review`, never `block` |
| 8 | System supports auditability + human review | Every decision logged with input hash, model versions, evidence, rationale; logs are reviewable offline |
| 9 | Digitally disadvantaged languages flagged as a limitation | Prototype is English-only; multilingual support documented as future work; Whisper's multilingual capability noted as a hook |
| 10 | System does not exclude non-AI experts | The demo UI requires no model knowledge — a moderator can use it on day one with a one-page guide |

## Connection to user needs

The CLAUDE.md §10 user list (human moderators, T&S teams, researchers, NGOs, small platforms) is dominated by non-technical users. Commitments 1–5 are aimed primarily at them. Commitments 6–10 protect against the "researcher's prototype" pitfall — a demo that only the author can interpret.

## Connection to literature

Gorwa, Binns and Katzenbach (2020) argue that opaque moderation pipelines fail their users and their regulators. The ten commitments above are a direct translation of that argument into product requirements.

## Things explicitly out of scope

- Multilingual UI translation (prototype is English).
- Screen-reader testing beyond label aria-attributes (planned for future work, documented as a limitation).
- Accessibility user studies with people with disabilities (out of scope per CLAUDE.md ethics rules — no real participant data in the prototype).
