"""Tests for Phase 6 Step 1: structured API contract (no HTTP yet)."""

import pandas as pd

from phase_1_data_loading.schema import COL_APPROX_COST_FOR_TWO, COL_CITY, COL_RATE_NUMERIC
from phase_4_recommendation.models import RankedItem
from phase_6_web.structured_pipeline import item_to_api_dict, run_pipeline_structured


def test_item_to_api_dict_serializes_nan_as_null() -> None:
    it = RankedItem(
        name="X",
        rate_numeric=float("nan"),
        approx_cost_for_two=100.0,
        location=None,
        cuisines="C",
        rationale=None,
    )
    d = item_to_api_dict(it)
    assert d["name"] == "X"
    assert d["rate_numeric"] is None
    assert d["approx_cost_for_two"] == 100.0


def test_to_api_dict_matches_architecture_shape(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    pq = tmp_path / "d.parquet"
    df = pd.DataFrame(
        {
            "name": ["Only One"],
            COL_CITY: ["Testville"],
            "location": ["Main St"],
            "cuisines": ["Veg"],
            COL_RATE_NUMERIC: [4.0],
            COL_APPROX_COST_FOR_TWO: [500.0],
        }
    )
    df.to_parquet(pq, index=False)
    r = run_pipeline_structured(
        city="Testville",
        price=1000,
        preferences="quiet",
        parquet_path=pq,
        top_k=5,
    )
    body = r.to_api_dict()
    assert body["ok"] is True
    assert body["summary"]["city"] == "Testville"
    assert body["summary"]["max_price_for_two"] == 1000.0
    assert body["summary"]["preferences"] == "quiet"
    assert "used_fallback" in body
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "Only One"
    assert body["items"][0]["location"] == "Main St"
    assert "message" not in body


def test_empty_candidates_returns_items_empty_and_message(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    pq = tmp_path / "d.parquet"
    df = pd.DataFrame(
        {
            "name": ["A"],
            COL_CITY: ["OtherCity"],
            COL_RATE_NUMERIC: [4.0],
            COL_APPROX_COST_FOR_TWO: [100.0],
        }
    )
    df.to_parquet(pq, index=False)
    r = run_pipeline_structured(
        city="Testville",
        price=500,
        preferences=None,
        parquet_path=pq,
    )
    body = r.to_api_dict()
    assert body["ok"] is True
    assert body["items"] == []
    assert "message" in body
    assert "matched" in body["message"].lower() or "budget" in body["message"].lower()
