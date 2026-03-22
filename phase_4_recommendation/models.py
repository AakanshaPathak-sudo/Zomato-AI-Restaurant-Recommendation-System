from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RankedItem:
    """One recommended restaurant with optional LLM rationale."""

    name: str
    rate_numeric: float
    approx_cost_for_two: float
    location: Optional[str] = None
    cuisines: Optional[str] = None
    rationale: Optional[str] = None


@dataclass(frozen=True)
class RecommendationResult:
    items: list[RankedItem]
    used_fallback: bool
