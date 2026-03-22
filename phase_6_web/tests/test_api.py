"""HTTP API tests (TestClient; no live Groq when GROQ_API_KEY unset)."""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from phase_1_data_loading.schema import COL_APPROX_COST_FOR_TWO, COL_CITY, COL_RATE_NUMERIC


@pytest.fixture
def sample_parquet(tmp_path):
    pq = tmp_path / "restaurants.parquet"
    df = pd.DataFrame(
        {
            "name": ["Test Place"],
            COL_CITY: ["Testville"],
            "location": ["Main"],
            "cuisines": ["X"],
            COL_RATE_NUMERIC: [4.0],
            COL_APPROX_COST_FOR_TWO: [500.0],
        }
    )
    df.to_parquet(pq, index=False)
    return pq


@pytest.fixture
def api_client(sample_parquet, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("RESTAURANTS_PARQUET", str(sample_parquet))
    # Import app after env is set
    from phase_6_web.api import app

    return TestClient(app)


def test_health(api_client: TestClient) -> None:
    r = api_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root_serves_frontend(api_client: TestClient) -> None:
    r = api_client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert b"search-form" in r.content


def test_root_head_ok(api_client: TestClient) -> None:
    r = api_client.head("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert r.headers.get("content-length")


def test_ui_static_assets(api_client: TestClient) -> None:
    r = api_client.get("/ui/app.js")
    assert r.status_code == 200
    assert b"/api/recommend" in r.content


def test_post_recommend_success(api_client: TestClient) -> None:
    r = api_client.post(
        "/api/recommend",
        json={"city": "Testville", "price": 1000, "preferences": None, "top_k": 5},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["summary"]["city"] == "Testville"
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Test Place"


def test_post_recommend_validation_422(api_client: TestClient) -> None:
    r = api_client.post(
        "/api/recommend",
        json={"city": "", "price": 100},
    )
    assert r.status_code == 422
    body = r.json()
    assert body.get("ok") is False
    assert "error" in body
