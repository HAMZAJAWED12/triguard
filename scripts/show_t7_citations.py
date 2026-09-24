"""Per-item citation viewer for a committed T7 (rationale-grounding) run.

    python scripts/show_t7_citations.py outputs/evaluation/<run>/t7/results.json
    python scripts/show_t7_citations.py <results.json> --manifest-rev c8f22a8

Read-only: prints what the committed file contains plus a mechanical
classification of every cited token. Computes no new metric.

Per item it prints: id, modalities supplied (from the manifest at the given
git revision -- default c8f22a8, the v1 18-item set), the tokens the run
recorded as cited, a class for each token derived from the vocabulary rules
in ``src/triguard/evaluation/grounding.py`` (evidence_tokens), the stored
rationale length with a ``truncated@200`` flag (run_t7 stores
``rationale[:200]``), and a ``rule-template`` flag when the rationale matches
the exact rule-judge template strings in ``src/triguard/models/llm_judge.py``
(_rule_based_judge).

Token classes (in the order grounding.evidence_tokens builds them):
  score            -- ``f"{toxicity_score:.2f}"``            (text)
  label            -- a lower-cased text top_label            (text)
  generic-toxicity -- the literal word "toxicity"             (text, always appended)
  caption-word     -- ``[a-z]{4,}`` word from the caption      (image)
  cue              -- a visual_risk_cue category               (image)
  tag              -- a YAMNet tag name                        (audio)
  transcript-word  -- ``[a-z]{4,}`` word from the transcript   (audio)
  stopword         -- a caption/transcript word that carries no evidence
                      (function words; list below)

Caption and transcript words are told apart by the item's modalities. For an
item that has BOTH image and audio the caption vocabulary is recovered
mechanically from any rule-template rationale in the same file
(``the image caption '<caption>'``); if none is present the class is
reported as ``caption-or-transcript-word``. ``--caption`` / ``--transcript``
override that recovery.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_MANIFEST_PATH = "data/sample_inputs/triguard_eval_v1/manifest.json"
_DEFAULT_REV = "c8f22a8"

# toxic-bert label names (text_model._hf_analyse lower-cases them) plus the
# sklearn / mock wrapper labels ("insult", "threat", "toxic").
_TEXT_LABELS = {
    "toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate",
}
# image_model._RISK_KEYWORDS values.
_CUES = {"weapon", "violence", "hate_symbol", "drug", "nudity_warning"}
# llm_judge risky tags + mock audio tags; real YAMNet names are matched by
# the manifest modality fallback below.
_TAGS = {"shouting", "screaming", "gunshot", "speech", "music", "silence"}
# Function words of length >= 4 that grounding.evidence_tokens admits from a
# caption / transcript but which name no piece of evidence.
_STOPWORDS = {
    "that", "this", "they", "them", "their", "there", "then", "than", "with",
    "have", "from", "what", "when", "which", "were", "will", "would", "been",
    "being", "about", "into", "does", "some", "such", "also", "just", "only",
    "very", "here", "your", "these", "those", "where", "while", "shall",
    "could", "should", "might", "because",
}
_SCORE_RE = re.compile(r"^\d\.\d{2}$")
_WORD_RE = re.compile(r"[a-z]{4,}")

# Exact rule-judge template fragments (llm_judge._rule_based_judge).
_RULE_TEMPLATES = (
    "the text classifier flagged toxicity at",
    "the text appeared benign",
    "showed no obvious risk cues",
    "audio analysis detected",
    "audio events:",
)
_RULE_MENTIONED_RE = re.compile(r"the image caption '.*' mentioned ")
_CAPTION_RE = re.compile(r"the image caption '([^']*)'")


def _load_manifest(rev: str) -> dict[str, dict]:
    out = subprocess.run(
        ["git", "show", f"{rev}:{_MANIFEST_PATH}"],
        cwd=_REPO, capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0:
        raise SystemExit(f"git show {rev}:{_MANIFEST_PATH} failed: {out.stderr.strip()}")
    data = json.loads(out.stdout)
    return {it["id"]: it for it in data["items"]}


def _is_rule_template(rationale: str) -> bool:
    low = rationale.lower()
    return any(t in low for t in _RULE_TEMPLATES) or bool(_RULE_MENTIONED_RE.search(low))


def _classify(tok: str, mods: set[str], caption_words: set[str] | None,
              transcript_words: set[str] | None) -> str:
    if _SCORE_RE.match(tok):
        return "score"
    if tok == "toxicity":
        return "generic-toxicity"
    if tok in _TEXT_LABELS and "text" in mods:
        return "label"
    if tok in _CUES and "image" in mods:
        return "cue"
    if tok in _TAGS and "audio" in mods:
        return "tag"
    if tok in _STOPWORDS:
        return "stopword"
    if not _WORD_RE.fullmatch(tok):
        return "unclassified"
    has_img, has_aud = "image" in mods, "audio" in mods
    if caption_words is not None and tok in caption_words and has_img:
        return "caption-word"
    if transcript_words is not None and tok in transcript_words and has_aud:
        return "transcript-word"
    if has_img and not has_aud:
        return "caption-word"
    if has_aud and not has_img:
        return "transcript-word"
    if has_img and has_aud:
        return "caption-or-transcript-word"
    return "unclassified"


_SPECIFIC = {"score", "label", "caption-word", "cue", "tag", "transcript-word",
             "caption-or-transcript-word"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("results", help="path to a T7 results.json")
    p.add_argument("--manifest-rev", default=_DEFAULT_REV,
                   help=f"git revision whose manifest lists the items (default {_DEFAULT_REV})")
    p.add_argument("--caption", default=None,
                   help="caption text for the shared image asset (overrides recovery)")
    p.add_argument("--transcript", default=None,
                   help="transcript text for the shared audio asset")
    args = p.parse_args(argv)

    path = Path(args.results)
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("per_item") or []
    manifest = _load_manifest(args.manifest_rev)

    # Recover the caption vocabulary mechanically from any rule-template rationale.
    caption_words: set[str] | None = None
    if args.caption:
        caption_words = set(_WORD_RE.findall(args.caption.lower()))
    else:
        for it in items:
            m = _CAPTION_RE.search(it.get("rationale", "").lower())
            if m:
                caption_words = set(_WORD_RE.findall(m.group(1)))
                break
    transcript_words: set[str] | None = (
        set(_WORD_RE.findall(args.transcript.lower())) if args.transcript else None
    )

    print("=" * 78)
    print(f"file:          {path.as_posix()}")
    print(f"judge:         {data.get('judge')}   n={data.get('n')}   "
          f"grounding_rate={data.get('grounding_rate')}   "
          f"invented_modality_count={data.get('invented_modality_count')}")
    print(f"config:        {json.dumps(data.get('config'))}")
    print(f"manifest:      git show {args.manifest_rev}:{_MANIFEST_PATH}  "
          f"({len(manifest)} items)")
    print(f"caption vocab: {sorted(caption_words) if caption_words else 'not recovered'}")
    print("=" * 78)

    n_specific = n_generic_only = n_rule = n_trunc = 0
    for it in items:
        iid = it["id"]
        man = manifest.get(iid)
        if man is None:
            mods_str, mods = "NOT IN MANIFEST", set()
        else:
            mods = {m for m in ("text", "image", "audio") if man.get(m)}
            mods_str = "+".join(m for m in ("text", "image", "audio") if m in mods)
        rationale = it.get("rationale", "")
        classes = {t: _classify(t, mods, caption_words, transcript_words)
                   for t in it.get("cited", [])}
        specific = any(c in _SPECIFIC for c in classes.values())
        rule = _is_rule_template(rationale)
        trunc = len(rationale) >= 200
        n_specific += specific
        n_generic_only += (not specific) and bool(classes)
        n_rule += rule
        n_trunc += trunc
        print(f"{iid:<4} modalities={mods_str:<16} grounded={it.get('grounded')} "
              f"invented={it.get('invented_modalities')}")
        print(f"     cited: " + (", ".join(f"{t} [{c}]" for t, c in classes.items()) or "(none)"))
        flags = []
        if trunc:
            flags.append("truncated@200")
        if rule:
            flags.append("rule-template")
        print(f"     rationale_len={len(rationale)}  flags={flags or '-'}")

    print("-" * 78)
    print(f"{n_specific} cite a specific token (score/label/caption/cue/tag/transcript non-stopword)")
    print(f"{n_generic_only} cite only generic 'toxicity' and/or stopwords")
    print(f"{n_rule} rule-template")
    print(f"{n_trunc} truncated at 200")
    return 0


if __name__ == "__main__":
    sys.exit(main())
