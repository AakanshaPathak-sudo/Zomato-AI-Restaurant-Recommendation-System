from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from phase_4_recommendation.models import RankedItem, RecommendationResult
from phase_5_display.format_output import format_no_matches, format_recommendations
from phase_6_web.structured_pipeline import run_pipeline_structured


def _recommendation_result_from_api_items(
    items: list[dict],
    used_fallback: bool,
) -> RecommendationResult:
    ranked: list[RankedItem] = []
    for d in items:
        rn = d.get("rate_numeric")
        ac = d.get("approx_cost_for_two")
        ranked.append(
            RankedItem(
                name=str(d["name"]),
                rate_numeric=float(rn) if rn is not None else float("nan"),
                approx_cost_for_two=float(ac) if ac is not None else float("nan"),
                location=d.get("location"),
                cuisines=d.get("cuisines"),
                rationale=d.get("rationale"),
            )
        )
    return RecommendationResult(items=ranked, used_fallback=used_fallback)


def run_pipeline(
    *,
    city: str,
    price: Union[int, float, str],
    preferences: Optional[str],
    parquet_path: Union[str, Path],
    top_k: int = 10,
    max_candidates_for_llm: int = 40,
) -> str:
    """
    End-to-end: validate input → load Parquet → candidates → recommend → formatted CLI text.

    Delegates to ``run_pipeline_structured`` (Phase 6 API contract).

    Raises:
        UserInputError: invalid city/price/preferences.
        FileNotFoundError: parquet missing.
    """
    structured = run_pipeline_structured(
        city=city,
        price=price,
        preferences=preferences,
        parquet_path=parquet_path,
        top_k=top_k,
        max_candidates_for_llm=max_candidates_for_llm,
    )
    if not structured.items and structured.message:
        return format_no_matches(structured.user)
    rec = _recommendation_result_from_api_items(structured.items, structured.used_fallback)
    return format_recommendations(structured.user, rec)
