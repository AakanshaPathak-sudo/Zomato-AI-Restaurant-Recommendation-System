"""
Structured pipeline result for POST /api/recommend (ARCHITECTURE.md Phase 6).

Step 1: single JSON-serializable contract shared by future HTTP API and tests.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

from phase_2_user_input import parse_user_input
from phase_2_user_input.models import UserInput
from phase_3_integrate import get_candidates, load_processed_parquet
from phase_4_recommendation import recommend
from phase_4_recommendation.models import RankedItem, RecommendationResult


def item_to_api_dict(it: RankedItem) -> dict[str, Any]:
    """Map RankedItem to JSON-friendly dict (NaN → None)."""
    def num(x: float) -> Optional[float]:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return None
        return float(x)

    return {
        "name": it.name,
        "rate_numeric": num(it.rate_numeric),
        "approx_cost_for_two": num(it.approx_cost_for_two),
        "location": it.location,
        "cuisines": it.cuisines,
        "rationale": it.rationale,
    }


@dataclass
class StructuredPipelineResult:
    """
    Result of run_pipeline_structured.

    Use ``to_api_dict()`` for the wire format documented in ARCHITECTURE.md.
    ``user`` is included for CLI formatting only; omit from HTTP responses if desired
    by building the body from ``to_api_dict()`` alone.
    """

    ok: bool
    summary: dict[str, Any]
    used_fallback: bool
    items: list[dict[str, Any]]
    user: UserInput = field(repr=False)
    message: Optional[str] = None

    def to_api_dict(self) -> dict[str, Any]:
        """JSON body for successful recommend calls (excludes ``user``)."""
        out: dict[str, Any] = {
            "ok": self.ok,
            "summary": self.summary,
            "used_fallback": self.used_fallback,
            "items": self.items,
        }
        if self.message is not None:
            out["message"] = self.message
        return out


def _execute_core(
    *,
    city: str,
    price: Union[int, float, str],
    preferences: Optional[str],
    parquet_path: Union[str, Path],
    top_k: int,
    max_candidates_for_llm: int,
) -> tuple[UserInput, Optional[RecommendationResult], bool]:
    """
    Returns (user, recommendation_result_or_none, empty_candidates).
    """
    user = parse_user_input(city, price, preferences)
    path = Path(parquet_path)
    df = load_processed_parquet(path)
    candidates = get_candidates(df, user)
    if candidates.empty:
        return user, None, True
    result = recommend(
        candidates,
        user,
        top_k=top_k,
        max_candidates_for_llm=max_candidates_for_llm,
    )
    return user, result, False


def run_pipeline_structured(
    *,
    city: str,
    price: Union[int, float, str],
    preferences: Optional[str],
    parquet_path: Union[str, Path],
    top_k: int = 10,
    max_candidates_for_llm: int = 40,
) -> StructuredPipelineResult:
    """
    Same pipeline as CLI; returns structured data for POST /api/recommend.

    Raises:
        UserInputError: invalid input.
        FileNotFoundError, OSError: Parquet load failures.
    """
    user, rec_result, empty = _execute_core(
        city=city,
        price=price,
        preferences=preferences,
        parquet_path=parquet_path,
        top_k=top_k,
        max_candidates_for_llm=max_candidates_for_llm,
    )
    summary = {
        "city": user.city,
        "max_price_for_two": float(user.max_price_for_two),
        "preferences": user.preferences,
    }
    if empty:
        return StructuredPipelineResult(
            ok=True,
            summary=summary,
            used_fallback=True,
            items=[],
            user=user,
            message="No restaurants matched your city and budget.",
        )
    assert rec_result is not None
    items = [item_to_api_dict(it) for it in rec_result.items]
    return StructuredPipelineResult(
        ok=True,
        summary=summary,
        used_fallback=rec_result.used_fallback,
        items=items,
        user=user,
        message=None,
    )
