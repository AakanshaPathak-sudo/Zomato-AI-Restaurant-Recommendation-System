"""Live Groq API tests — run with: pytest -m groq (needs: pip install groq python-dotenv, .env with GROQ_API_KEY)."""

import os

import pandas as pd
import pytest

pytest.importorskip("groq")

# Import first so recommender.load_dotenv() runs before GROQ_API_KEY is read.
from phase_4_recommendation.recommender import recommend

from phase_1_data_loading.schema import COL_APPROX_COST_FOR_TWO, COL_CITY, COL_RATE_NUMERIC
from phase_2_user_input.models import UserInput


def _sample_candidates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["Spice Kitchen", "Green Leaf", "Urban Grill"],
            COL_CITY: ["Bangalore"] * 3,
            "location": ["Indiranagar", "Koramangala", "MG Road"],
            "cuisines": ["North Indian", "South Indian", "Continental"],
            COL_RATE_NUMERIC: [4.2, 4.0, 3.9],
            COL_APPROX_COST_FOR_TWO: [600.0, 800.0, 1200.0],
        }
    )


@pytest.mark.groq
@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY", "").strip(),
    reason="Set GROQ_API_KEY in .env or environment to run live Groq tests",
)
def test_groq_llm_returns_ranked_items_without_fallback() -> None:
    """Groq returns valid JSON so we should not fall back to rating-only order."""
    df = _sample_candidates()
    user = UserInput(
        city="Bangalore",
        max_price_for_two=1000.0,
        preferences="vegetarian friendly",
    )
    result = recommend(df, user, top_k=3, max_candidates_for_llm=10)
    assert len(result.items) >= 1
    assert result.used_fallback is False, "LLM path should succeed; check API key and model"
    assert all(it.name for it in result.items)


@pytest.mark.groq
@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY", "").strip(),
    reason="Set GROQ_API_KEY in .env or environment to run live Groq tests",
)
def test_groq_respects_top_k() -> None:
    """Model is asked for at most top_k picks."""
    df = _sample_candidates()
    user = UserInput(city="Bangalore", max_price_for_two=2000.0, preferences=None)
    result = recommend(df, user, top_k=2, max_candidates_for_llm=10)
    assert len(result.items) <= 2
    assert len(result.items) >= 1


@pytest.mark.groq
@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY", "").strip(),
    reason="Set GROQ_API_KEY in .env or environment to run live Groq tests",
)
def test_groq_recommendations_only_from_candidates() -> None:
    """Every returned name must exist in the input dataframe (no hallucinated venues)."""
    df = _sample_candidates()
    allowed = set(df["name"].astype(str))
    user = UserInput(
        city="Bangalore",
        max_price_for_two=1500.0,
        preferences="good for dinner",
    )
    result = recommend(df, user, top_k=3, max_candidates_for_llm=10)
    assert len(result.items) >= 1
    for it in result.items:
        assert it.name in allowed, f"Unexpected name from model: {it.name!r}"
