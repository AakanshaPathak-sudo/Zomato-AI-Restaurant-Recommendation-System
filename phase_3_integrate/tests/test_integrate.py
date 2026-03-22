"""Tests for phase_3_integrate: city + budget filtering."""

import pandas as pd
import pytest

from phase_1_data_loading.schema import COL_APPROX_COST_FOR_TWO, COL_CITY
from phase_2_user_input.models import UserInput
from phase_3_integrate.integrate import get_candidates, load_processed_parquet, normalize_city_for_match


def _minimal_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_CITY: ["Bangalore", "Bangalore", "Mumbai", "Bangalore"],
            COL_APPROX_COST_FOR_TWO: [500.0, 1500.0, 800.0, float("nan")],
            "name": ["A", "B", "C", "D"],
        }
    )


class TestNormalizeCityForMatch:
    def test_casefold(self) -> None:
        assert normalize_city_for_match("Bangalore") == normalize_city_for_match("bangalore")

    def test_whitespace(self) -> None:
        assert normalize_city_for_match("  New  Delhi  ") == "new delhi"


class TestGetCandidates:
    def test_filters_city_and_budget(self) -> None:
        df = _minimal_df()
        user = UserInput(city="Bangalore", max_price_for_two=1000.0)
        out = get_candidates(df, user)
        assert len(out) == 1
        assert out["name"].iloc[0] == "A"
        assert out[COL_APPROX_COST_FOR_TWO].iloc[0] == 500.0

    def test_city_match_is_case_insensitive(self) -> None:
        df = _minimal_df()
        user = UserInput(city="bangalore", max_price_for_two=2000.0)
        out = get_candidates(df, user)
        assert len(out) == 2
        assert set(out["name"]) == {"A", "B"}

    def test_excludes_nan_cost(self) -> None:
        df = _minimal_df()
        user = UserInput(city="Bangalore", max_price_for_two=5000.0)
        out = get_candidates(df, user)
        assert "D" not in set(out["name"])

    def test_empty_when_no_city(self) -> None:
        df = _minimal_df()
        user = UserInput(city="Chennai", max_price_for_two=5000.0)
        out = get_candidates(df, user)
        assert len(out) == 0

    def test_missing_columns_raises(self) -> None:
        df = pd.DataFrame({COL_CITY: ["X"]})
        user = UserInput(city="X", max_price_for_two=100.0)
        with pytest.raises(ValueError, match="missing columns"):
            get_candidates(df, user)


class TestLoadProcessedParquet:
    def test_roundtrip(self, tmp_path) -> None:
        df = _minimal_df()
        path = tmp_path / "t.parquet"
        df.to_parquet(path, index=False)
        loaded = load_processed_parquet(path)
        assert len(loaded) == len(df)
        assert list(loaded.columns) == list(df.columns)
