from triguard.models import text_model


def test_text_model_mock_mode_returns_evidence() -> None:
    e = text_model.analyse("you are a stupid idiot", force_mode="mock")
    assert e.toxicity_score > 0.5
    assert "insult" in e.top_labels


def test_text_model_real_mode_classifies_benign() -> None:
    e = text_model.analyse("Thanks for the wonderful help today", force_mode="real")
    assert e.toxicity_score < 0.5
    assert e.confidence >= 0.0


def test_text_model_real_mode_classifies_toxic() -> None:
    # Real mode preferred; if sklearn is broken on the host, the wrapper
    # transparently falls back to mock - which is still expected to flag
    # this clearly toxic input.
    e = text_model.analyse("You are utterly worthless and pathetic", force_mode="real")
    assert e.toxicity_score >= 0.5
    assert "insult" in e.top_labels or "toxic" in e.top_labels


def test_text_model_empty_input() -> None:
    e = text_model.analyse("", force_mode="real")
    assert e.toxicity_score == 0.0
    assert e.confidence == 0.0
