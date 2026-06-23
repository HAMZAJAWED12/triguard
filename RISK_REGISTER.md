# Risk Register — TriGuard

| ID | Risk | Likelihood | Impact | Mitigation | Status |
|---|---|---|---|---|---|
| R1 | Local LLM (Ollama) too slow on consumer hardware | High | Medium | Use quantised 3B model fallback; cache judge calls during eval | Open |
| R2 | Hateful Memes dataset access gated/refused | Medium | High | Apply for access in Week 6; fallback to MMHS150K + synthetic samples | Open |
| R3 | Model downloads fail mid-eval | Low | High | Pin model versions; mirror weights to Drive/HF Spaces by Week 11 | Open |
| R4 | LLM judge produces invalid JSON | High | Medium | Use Pydantic schema + `instructor` library; retry once with stricter prompt | Open |
| R5 | Audio component scope creep | Medium | Medium | Lock scope: YAMNet event tags + Whisper transcript only — no diarisation, no language ID | Open |
| R6 | Literature review lacks critical comparison | Medium | High | Each thematic section must end with a comparison paragraph (already enforced in template) | Open |
| R7 | Project design too vague | Medium | High | Every section must map to template + domain + users + gap + evaluation (CLAUDE.md §9) | Open |
| R8 | Report writing left too late | High | High | Start writing in Week 18 (formative draft); reuse all docs/ markdown | Open |
| R9 | Exam revision clashes with coding | High | High | Week 21 reserved exam-only; coding hard-stop end of Week 20 | Open |
| R10 | Final submission upload fails | Low | Critical | Submit 24 h early; keep zipped backup on Drive + USB | Open |
| R11 | Ethics issue from harmful sample content | Low | High | Use public datasets only; no scraping; store harmful examples in a separate gitignored folder; minimum-exposure principle | Open |
| R12 | Preliminary Report requires a feature prototype + MP4 video | Realised (high impact) | High | D-009: build Tier-A mock pipeline + at least one real wrapper before deadline; record MP4 demo | Closed by D-009 |
