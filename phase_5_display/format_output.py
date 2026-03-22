from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phase_2_user_input.models import UserInput
    from phase_4_recommendation.models import RecommendationResult


def _fmt_rating(x: float) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    return f"{x:.1f}"


def _fmt_cost(x: float) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    if float(x).is_integer():
        return str(int(x))
    return f"{x:.0f}"


def format_summary(user: UserInput) -> str:
    prefs = user.preferences or "(none)"
    return (
        f"City: {user.city}\n"
        f"Max budget (for two): {_fmt_cost(user.max_price_for_two)}\n"
        f"Preferences: {prefs}"
    )


def format_recommendations(user: UserInput, result: RecommendationResult) -> str:
    lines = [format_summary(user), ""]
    if result.used_fallback:
        lines.append("Note: ranked by rating (LLM off or unavailable).")
        lines.append("")
    if not result.items:
        lines.append("No recommendations to show.")
        return "\n".join(lines)
    lines.append("Recommendations:")
    lines.append("-" * 72)
    for i, it in enumerate(result.items, 1):
        loc = it.location or "-"
        cuis = it.cuisines or "-"
        lines.append(
            f"{i}. {it.name}\n"
            f"   Rating: {_fmt_rating(it.rate_numeric)} | Cost for two: {_fmt_cost(it.approx_cost_for_two)} | {loc}\n"
            f"   Cuisines: {cuis}"
        )
        if it.rationale:
            lines.append(f"   Why: {it.rationale}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_no_matches(user: UserInput) -> str:
    return (
        format_summary(user)
        + "\n\n"
        + "No restaurants matched your city and budget.\n"
        + "Try a different spelling for the city, or increase your budget.\n"
    )


def format_file_error(path: str, detail: str) -> str:
    return f"Could not load restaurant data from {path!r}.\n{detail}\n"
