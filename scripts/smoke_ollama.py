"""Manual smoke test for the real Ollama LLM judge (Prompt 4).

Runs one sample through BOTH judge paths on the SAME evidence and prints an
honest comparison:

    * the rule-based rationale,
    * the real llama3 rationale (via Ollama),
    * a grounding check — does the llama3 rationale cite real evidence from the
      JudgeInput (scores / caption / cues / tags), and does it invent numbers or
      modalities that are not present?
    * strict JudgeOutput re-validation of the Ollama verdict.

If the Ollama path falls back (server down, or invalid JSON twice), that is
reported plainly via the uncertainty tags — nothing is papered over.

Prerequisites (WSL):
    curl -fsSL https://ollama.com/install.sh | sh
    ollama serve &                       # keep this process alive
    ollama pull llama3:8b-instruct-q4_K_M

Run:
    PYTHONPATH=src python scripts/smoke_ollama.py data/sample_inputs/sample_harmful.json

Model override: TRIGUARD_OLLAMA_MODEL=<tag>. Endpoint override: OLLAMA_HOST=<url>.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from triguard.models import audio_model, image_model, llm_judge, text_model
from triguard.orchestrator.schemas import JudgeInput, JudgeOutput

_FALLBACK_TAGS = ("ollama_unavailable", "judge_output_invalid")


def _build_judge_input(sample: dict) -> JudgeInput:
    """Run the perception wrappers on the sample to produce one JudgeInput.

    Image/audio default to their offline mocks; text uses its default tier. The
    same JudgeInput is fed to both judge paths so the comparison is fair.
    """
    text_ev = text_model.analyse(sample["text"]) if sample.get("text") else None
    image_ev = image_model.analyse(sample["image"]) if sample.get("image") else None
    audio_ev = audio_model.analyse(sample["audio"]) if sample.get("audio") else None
    return JudgeInput(text=text_ev, image=image_ev, audio=audio_ev)


def _evidence_tokens(ji: JudgeInput) -> list[str]:
    """Concrete strings a grounded rationale could legitimately cite."""
    toks: list[str] = []
    if ji.text:
        toks.append(f"{ji.text.toxicity_score:.2f}")
        toks += [lbl.lower() for lbl in ji.text.top_labels]
        toks.append("toxicity")
    if ji.image:
        toks += [w for w in re.findall(r"[a-z]{4,}", ji.image.caption.lower())]
        toks += [c.lower() for c in ji.image.visual_risk_cues]
    if ji.audio:
        toks += [t.lower() for t, _ in ji.audio.yamnet_tags]
        toks += [w for w in re.findall(r"[a-z]{4,}", ji.audio.transcript.lower())]
    # dedupe, keep order
    seen: set[str] = set()
    out: list[str] = []
    for t in toks:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _allowed_numbers(ji: JudgeInput) -> set[str]:
    """Numeric values that legitimately appear in the evidence (2 dp)."""
    nums: set[str] = set()
    if ji.text:
        nums.add(f"{ji.text.toxicity_score:.2f}")
        nums.add(f"{ji.text.confidence:.2f}")
    if ji.image:
        nums.add(f"{ji.image.confidence:.2f}")
    if ji.audio:
        nums.add(f"{ji.audio.transcript_confidence:.2f}")
        nums |= {f"{s:.2f}" for _, s in ji.audio.yamnet_tags}
    return nums


def _grounding_report(ji: JudgeInput, rationale: str) -> dict:
    """Heuristic (not proof) grounding + hallucination check on a rationale."""
    low = rationale.lower()
    cited = [t for t in _evidence_tokens(ji) if t in low]

    present_modalities = {
        m for m, ev in (("text", ji.text), ("image", ji.image), ("audio", ji.audio))
        if ev is not None
    }
    claimed = {m for m in ("text", "image", "audio") if m in low}
    invented_modalities = sorted(claimed - present_modalities)

    allowed = _allowed_numbers(ji)
    found_numbers = re.findall(r"\d+\.\d+", rationale)
    # a decimal in the rationale that matches no evidence value is suspicious
    unmatched_numbers = sorted({n for n in found_numbers if n not in allowed})

    return {
        "grounded": bool(cited),
        "cited_evidence_tokens": cited,
        "invented_modalities": invented_modalities,
        "unmatched_numbers": unmatched_numbers,
    }


def _is_native_ollama(out: JudgeOutput) -> bool:
    """True if the verdict came from the LLM (no fallback uncertainty tag)."""
    return not any(u.startswith(_FALLBACK_TAGS) for u in out.uncertainties)


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else Path("data/sample_inputs/sample_harmful.json")
    sample = json.loads(path.read_text(encoding="utf-8"))

    ji = _build_judge_input(sample)

    print("=" * 72)
    print(f"SAMPLE: {path}")
    print("-" * 72)
    print("EVIDENCE (JudgeInput):")
    print(json.dumps(ji.model_dump(), indent=2, ensure_ascii=False))

    rule_out = llm_judge.judge(ji, force_mode="rule")
    ollama_out = llm_judge.judge(ji, force_mode="ollama")

    print("=" * 72)
    print("RULE rationale:")
    print(f"  {rule_out.rationale}")
    print(f"  -> label={rule_out.risk_label}  action={rule_out.recommended_action}")
    print("-" * 72)
    print(f"OLLAMA model: {llm_judge._ollama_model()}   host: {llm_judge._ollama_host()}")
    native = _is_native_ollama(ollama_out)
    if native:
        print("OLLAMA (llama3) rationale:")
    else:
        print("OLLAMA path FELL BACK to rule (see uncertainties) — rationale is rule-based:")
    print(f"  {ollama_out.rationale}")
    print(f"  -> label={ollama_out.risk_label}  action={ollama_out.recommended_action}")
    print(f"  uncertainties={ollama_out.uncertainties}")

    print("=" * 72)
    print("GROUNDING CHECK (llama3 rationale vs evidence):")
    if not native:
        print("  SKIPPED — no native llama3 verdict (Ollama unavailable or invalid JSON).")
    else:
        rep = _grounding_report(ji, ollama_out.rationale)
        print(f"  grounded (cites real evidence): {rep['grounded']}")
        print(f"  cited evidence tokens: {rep['cited_evidence_tokens']}")
        if rep["invented_modalities"]:
            print(f"  HALLUCINATION - modalities not in evidence: {rep['invented_modalities']}")
        if rep["unmatched_numbers"]:
            print(f"  POSSIBLE HALLUCINATION - numbers not in evidence: {rep['unmatched_numbers']}")
        if not rep["grounded"]:
            print("  WARNING - rationale cites no concrete evidence token (weakly grounded).")
        if not (rep["invented_modalities"] or rep["unmatched_numbers"]) and rep["grounded"]:
            print("  OK - grounded, no invented modalities/numbers detected (heuristic).")

    print("-" * 72)
    # Strict re-validation of the Ollama verdict against the schema.
    try:
        JudgeOutput.model_validate(ollama_out.model_dump())
        print("SCHEMA: JudgeOutput re-validation PASSED.")
    except Exception as e:  # pragma: no cover - defensive
        print(f"SCHEMA: JudgeOutput re-validation FAILED: {e}")

    print("=" * 72)
    print("OLLAMA verdict (full JSON):")
    print(ollama_out.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
