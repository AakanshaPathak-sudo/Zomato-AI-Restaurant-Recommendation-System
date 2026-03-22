from __future__ import annotations

import re
from typing import Optional, Union

from phase_2_user_input.models import UserInput

# Tunable limits shared by CLI and future web UI.
MAX_CITY_LEN = 200
MAX_PREFERENCES_LEN = 4000


class UserInputError(ValueError):
    """Raised when city, price, or preferences fail validation."""


def _normalize_city(city: str) -> str:
    s = city.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _normalize_preferences(preferences: Optional[str]) -> Optional[str]:
    if preferences is None:
        return None
    s = preferences.strip()
    if not s:
        return None
    return s


def _parse_price(price: Union[int, float, str]) -> float:
    if isinstance(price, bool):
        raise UserInputError("price must be a number")
    if isinstance(price, (int, float)):
        return float(price)
    s = str(price).strip().replace(",", "")
    if not s:
        raise UserInputError("price is required")
    try:
        return float(s)
    except ValueError as e:
        raise UserInputError("price must be a valid number") from e


def parse_user_input(
    city: str,
    price: Union[int, float, str],
    preferences: Optional[str] = None,
) -> UserInput:
    """
    Validate and return a UserInput. ``city`` must be non-empty after trim;
    ``price`` must be strictly greater than zero.
    """
    normalized_city = _normalize_city(city)
    if not normalized_city:
        raise UserInputError("city is required")
    if len(normalized_city) > MAX_CITY_LEN:
        raise UserInputError(f"city must be at most {MAX_CITY_LEN} characters")

    amount = _parse_price(price)
    if amount <= 0:
        raise UserInputError("price must be greater than zero")

    prefs = _normalize_preferences(preferences)
    if prefs is not None and len(prefs) > MAX_PREFERENCES_LEN:
        raise UserInputError(f"preferences must be at most {MAX_PREFERENCES_LEN} characters")

    return UserInput(
        city=normalized_city,
        max_price_for_two=amount,
        preferences=prefs,
    )
