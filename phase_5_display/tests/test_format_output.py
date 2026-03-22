from phase_2_user_input.models import UserInput
from phase_4_recommendation.models import RankedItem, RecommendationResult
from phase_5_display.format_output import format_no_matches, format_recommendations, format_summary


def test_format_summary_includes_budget_and_prefs() -> None:
    u = UserInput(city="Bangalore", max_price_for_two=1200.0, preferences="veg")
    s = format_summary(u)
    assert "Bangalore" in s
    assert "1200" in s
    assert "veg" in s


def test_format_no_matches_has_guidance() -> None:
    u = UserInput(city="Nowhere", max_price_for_two=100.0)
    s = format_no_matches(u)
    assert "No restaurants matched" in s
    assert "budget" in s.lower()


def test_format_recommendations_with_rationale() -> None:
    u = UserInput(city="X", max_price_for_two=500.0)
    r = RecommendationResult(
        items=[
            RankedItem(
                name="Test",
                rate_numeric=4.0,
                approx_cost_for_two=400.0,
                location="Area",
                cuisines="Italian",
                rationale="Good value",
            )
        ],
        used_fallback=False,
    )
    s = format_recommendations(u, r)
    assert "Test" in s
    assert "Good value" in s
    assert "LLM off" not in s


def test_format_recommendations_fallback_note() -> None:
    u = UserInput(city="X", max_price_for_two=500.0)
    r = RecommendationResult(items=[], used_fallback=True)
    s = format_recommendations(u, r)
    assert "rating" in s.lower() or "LLM" in s
