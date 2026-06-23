from triguard.models import audio_model


def test_audio_mock_calm_speech() -> None:
    e = audio_model.analyse("/tmp/calm_speech_sample.wav")
    assert e.transcript
    assert any(tag == "speech" for tag, _ in e.yamnet_tags)


def test_audio_mock_shouting() -> None:
    e = audio_model.analyse("/tmp/loud_shout.wav")
    assert any(tag == "shouting" for tag, _ in e.yamnet_tags)
