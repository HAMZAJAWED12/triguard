from triguard.models import image_model


def test_image_mock_no_cues() -> None:
    e = image_model.analyse("/tmp/holiday_beach.jpg")
    assert e.visual_risk_cues == []
    assert e.caption


def test_image_mock_with_weapon_cue() -> None:
    e = image_model.analyse("/tmp/photo_with_gun.jpg")
    assert "weapon" in e.visual_risk_cues
