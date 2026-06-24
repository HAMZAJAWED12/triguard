"""
Text wrapper for TriGuard.

Three tiers (selected by force_mode, else env, else default):
    - "mock": deterministic keyword heuristic, no weights. For unit tests.
    - "sklearn": TF-IDF + logistic regression, trained on a small bundled
      corpus. Reproducible offline, no download. The offline default and a
      sanity-floor baseline.
    - "hf": real Hugging Face toxicity classifier (unitary/toxic-bert),
      multi-label sigmoid heads. Downloads ~440 MB weights on first use.

force_mode accepts "mock" | "sklearn" | "hf" | "real" | None.
    "real" is a backward-compat alias for "sklearn" (kept offline so the fast
    test suite never downloads). When force_mode is None, TRIGUARD_MOCK=1 forces
    mock; otherwise TRIGUARD_TEXT_BACKEND in {mock,sklearn,hf} selects the tier,
    defaulting to "sklearn".

Any tier that fails to import/load its backend falls back to the mock so the
pipeline never crashes.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional

# Heavy ML libs (sklearn, transformers, torch) are imported lazily inside the
# loader functions so the rest of the package imports cleanly when they are
# missing or broken. Each real tier auto-falls back to mock in that case.

from ..orchestrator.schemas import TextEvidence

_log = logging.getLogger("triguard.text_model")
_SKLEARN_BROKEN = False  # set True the first time the sklearn tier fails to load
_HF_BROKEN = False       # set True the first time the hf tier fails to load

# Pinned Hugging Face toxicity classifier (Sprint 1).
_HF_MODEL = "unitary/toxic-bert"
_HF_REVISION = "4d6c22e74ba2fdd26bc4f7238f50766b045a0d94"


# ---------------------------------------------------------------------------
# sklearn training data. Real deployment would use Civil Comments.
# Labels: 0 = non-toxic, 1 = toxic.
# ---------------------------------------------------------------------------

_TRAIN: list[tuple[str, int]] = [
    # non-toxic
    ("I really enjoyed the museum today, it was beautifully laid out", 0),
    ("Thanks for the help, the documentation made it easy to follow", 0),
    ("The new park looks great and is family friendly", 0),
    ("I appreciate your feedback on the draft, will revise tomorrow", 0),
    ("Looking forward to the team meeting on Monday", 0),
    ("The recipe came out perfectly, would make again", 0),
    ("Congratulations on the promotion, well deserved", 0),
    ("My commute was peaceful this morning, no traffic", 0),
    ("I respectfully disagree with that interpretation", 0),
    ("Hope you feel better soon, take care of yourself", 0),
    ("Reading the new book before bed is so relaxing", 0),
    ("Great explanation, I finally understand the concept", 0),
    ("The weather has been pleasant all week", 0),
    ("Volunteering at the food bank was rewarding", 0),
    ("I appreciate the patience while I learn this software", 0),
    # toxic / harmful
    ("You are utterly worthless and nobody should ever listen to you", 1),
    ("I hope something terrible happens to you and your family", 1),
    ("Anyone who believes that nonsense is a complete idiot", 1),
    ("Get lost you pathetic loser nobody likes you", 1),
    ("People like you are a stain on society and should disappear", 1),
    ("Shut up you absolute moron nobody cares what you think", 1),
    ("I would happily watch you suffer for being so stupid", 1),
    ("Disgusting people like you ruin everything around them", 1),
    ("You deserve to be humiliated in public for that opinion", 1),
    ("Threats and insults are the only thing your kind understands", 1),
    ("Your entire group of friends is worthless trash", 1),
    ("I hope the next disaster takes out your whole community", 1),
    ("You are a complete embarrassment to everyone who knows you", 1),
    ("Stop breathing my air you absolute waste of space", 1),
    ("Anyone with your views deserves to lose everything they care about", 1),
]


@lru_cache(maxsize=1)
def _trained_pipeline():
    """Lazy-import sklearn; train once per process and cache."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    texts = [t for t, _ in _TRAIN]
    labels = [y for _, y in _TRAIN]
    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, lowercase=True)),
            ("lr", LogisticRegression(max_iter=500, C=4.0)),
        ]
    )
    pipe.fit(texts, labels)
    return pipe


@lru_cache(maxsize=1)
def _hf_pipeline():
    """Lazy-import transformers/torch; load toxic-bert once per process.

    top_k=None returns every label; function_to_apply='sigmoid' gives
    independent per-label probabilities (toxic-bert is multi-label).
    """
    from transformers import pipeline  # transformers pulls torch lazily

    return pipeline(
        "text-classification",
        model=_HF_MODEL,
        revision=_HF_REVISION,
        top_k=None,
        function_to_apply="sigmoid",
        truncation=True,
    )


def _is_mock_mode() -> bool:
    return os.getenv("TRIGUARD_MOCK", "").strip() in {"1", "true", "yes"}


def _resolve_backend(force_mode: Optional[str]) -> str:
    """Map force_mode/env to one of: mock | sklearn | hf."""
    mode = force_mode
    if mode is None:
        if _is_mock_mode():
            return "mock"
        env = os.getenv("TRIGUARD_TEXT_BACKEND", "").strip().lower()
        return env if env in {"mock", "sklearn", "hf"} else "sklearn"
    if mode == "real":  # backward-compat alias (kept offline)
        return "sklearn"
    return mode


# Heuristic words for mock mode + high-precision override in the sklearn tier.
_HARD_TOXIC_TOKENS = {
    "kill", "hate", "die", "idiot", "worthless", "stupid", "moron",
    "loser", "trash", "scum", "disgusting",
}


def _mock_analyse(text: str) -> TextEvidence:
    lower = text.lower()
    hits = [tok for tok in _HARD_TOXIC_TOKENS if tok in lower]
    score = min(1.0, 0.25 + 0.2 * len(hits))
    labels: list[str] = []
    if hits:
        labels.append("insult")
    if "kill" in lower or "die" in lower:
        labels.append("threat")
    return TextEvidence(
        toxicity_score=score,
        top_labels=labels,
        confidence=0.5,
        raw={"mode": "mock", "hits": hits},
    )


def _sklearn_analyse(text: str) -> TextEvidence:
    global _SKLEARN_BROKEN
    if _SKLEARN_BROKEN:
        return _mock_analyse(text)
    try:
        pipe = _trained_pipeline()
    except Exception as e:  # broken sklearn install - fall back to mock
        _SKLEARN_BROKEN = True
        _log.warning("sklearn unavailable (%s); falling back to mock mode", e)
        return _mock_analyse(text)

    prob = float(pipe.predict_proba([text])[0, 1])

    # Heuristic boost if any hard token is present - closes obvious recall gaps
    # when the training set is small.
    lower = text.lower()
    hard_hits = [tok for tok in _HARD_TOXIC_TOKENS if tok in lower]
    if hard_hits:
        prob = max(prob, 0.6)

    labels: list[str] = []
    if hard_hits:
        labels.append("insult")
    if "kill" in lower or "die" in lower or "suffer" in lower:
        labels.append("threat")
    if not labels and prob >= 0.5:
        labels.append("toxic")

    return TextEvidence(
        toxicity_score=round(prob, 4),
        top_labels=labels,
        confidence=round(abs(prob - 0.5) * 2, 4),
        raw={"mode": "real", "classifier": "sklearn-tfidf-lr", "prob": prob},
    )


def _hf_analyse(text: str) -> TextEvidence:
    global _HF_BROKEN
    if _HF_BROKEN:
        return _mock_analyse(text)
    try:
        clf = _hf_pipeline()
    except Exception as e:  # transformers/torch missing or load failed
        _HF_BROKEN = True
        _log.warning("toxic-bert unavailable (%s); falling back to mock mode", e)
        return _mock_analyse(text)

    results = clf(text)
    # pipeline(top_k=None) returns list[dict] for one input, or list[list[dict]].
    if results and isinstance(results[0], list):
        results = results[0]
    scores = {d["label"].lower(): float(d["score"]) for d in results}  # pyright: ignore[reportArgumentType, reportIndexIssue]

    tox = scores.get("toxic", 0.0)
    top_labels = sorted(lbl for lbl, sc in scores.items() if sc >= 0.5)

    return TextEvidence(
        toxicity_score=round(tox, 4),
        top_labels=top_labels,
        confidence=round(abs(tox - 0.5) * 2, 4),
        raw={
            "mode": "real-hf",
            "model_name": _HF_MODEL,
            "model_revision": _HF_REVISION,
            "scores": {k: round(v, 4) for k, v in scores.items()},
        },
    )


def analyse(text: str, *, force_mode: Optional[str] = None) -> TextEvidence:
    """Score a piece of text for toxicity.

    force_mode: "mock" | "sklearn" | "hf" | "real" | None.
        "real" aliases "sklearn" (offline). None uses TRIGUARD_MOCK, then
        TRIGUARD_TEXT_BACKEND, defaulting to "sklearn".
    """
    if not text or not text.strip():
        return TextEvidence(
            toxicity_score=0.0,
            top_labels=[],
            confidence=0.0,
            raw={"reason": "empty_input"},
        )

    backend = _resolve_backend(force_mode)
    if backend == "mock":
        return _mock_analyse(text)
    if backend == "hf":
        return _hf_analyse(text)
    return _sklearn_analyse(text)
