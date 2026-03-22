from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserInput:
    """
    Validated request for recommendations.

    ``max_price_for_two`` is the user's maximum budget aligned with the dataset field
    ``approx_cost_for_two`` (approximate cost for two people, same currency as the data).
    """

    city: str
    max_price_for_two: float
    preferences: Optional[str] = None
