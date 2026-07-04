"""API tests for the FastAPI demo surface.

Skip cleanly where `fastapi`/`httpx` are absent (e.g. the Windows offline venv),
so they never break collection there. Where present, they run fully offline in
mock mode (`TRIGUARD_MOCK=1`): no real models, no network.
"""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRIGUARD_MOCK", "1")  # force mock everywhere, offline
    from triguard.api.main import app
    return TestClient(app)


def test_health(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"]


def test_analyse_text_harmful(client: TestClient) -> None:
    resp = client.post("/analyse/text",
                       json={"text": "you are a worthless idiot and should die"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_label"] in {"safe", "borderline", "harmful"}
    assert body["recommended_action"] in {"allow", "review", "block"}
    assert body["rationale"]
    assert "text_model" in body["model_versions"]


def test_analyse_text_benign(client: TestClient) -> None:
    resp = client.post("/analyse/text",
                       json={"text": "thank you so much for the lovely afternoon"})
    assert resp.status_code == 200
    assert resp.json()["risk_label"] == "safe"
