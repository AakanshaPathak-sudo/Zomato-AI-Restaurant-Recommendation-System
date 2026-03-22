from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from phase_1_data_loading.schema import COL_APPROX_COST_FOR_TWO, COL_CITY

if TYPE_CHECKING:
    from phase_2_user_input.models import UserInput


def normalize_city_for_match(city: str) -> str:
    """Normalize city for case-insensitive equality (matches Phase 2 whitespace rules intent)."""
    return " ".join(str(city).split()).casefold()


def load_processed_parquet(path: str | Path) -> pd.DataFrame:
    """Load Parquet written by ``phase_1_data_loading.ingest_to_parquet``."""
    return pd.read_parquet(path)


def get_candidates(df: pd.DataFrame, user: UserInput) -> pd.DataFrame:
    """
    Return rows in ``df`` where ``city`` matches the user (case-insensitive) and
    ``approx_cost_for_two`` is present and at most ``user.max_price_for_two``.
    """
    required = {COL_CITY, COL_APPROX_COST_FOR_TWO}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing columns: {sorted(missing)}")

    target = normalize_city_for_match(user.city)
    city_match = df[COL_CITY].astype(str).map(normalize_city_for_match) == target

    cost = df[COL_APPROX_COST_FOR_TWO]
    has_cost = cost.notna()
    within_budget = cost <= float(user.max_price_for_two)

    return df[city_match & has_cost & within_budget].copy()
