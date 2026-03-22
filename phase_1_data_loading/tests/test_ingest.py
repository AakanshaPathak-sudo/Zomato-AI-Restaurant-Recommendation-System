"""Tests for phase_1_data_loading: load, validate, and clean Zomato data."""

import math
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from phase_1_data_loading.ingest import (
    clean_dataframe,
    ingest_to_parquet,
    parse_approx_cost,
    parse_rate,
    validate_raw_columns,
)
from phase_1_data_loading.schema import COL_APPROX_COST_FOR_TWO, COL_CITY, COL_RATE_NUMERIC, RAW_COLUMNS
from phase_1_data_loading.tests.fixtures import minimal_zomato_dataframe


class TestParseRate:
    def test_parses_slash_form(self) -> None:
        assert parse_rate("4.1/5") == pytest.approx(4.1)

    def test_parses_plain_number(self) -> None:
        assert parse_rate("4") == pytest.approx(4.0)

    def test_invalid_returns_nan(self) -> None:
        assert math.isnan(parse_rate("NEW"))
        assert math.isnan(parse_rate("-"))
        assert math.isnan(parse_rate(None))


class TestParseApproxCost:
    def test_parses_digits(self) -> None:
        assert parse_approx_cost("800") == pytest.approx(800.0)

    def test_parses_with_commas(self) -> None:
        assert parse_approx_cost("1,200") == pytest.approx(1200.0)

    def test_int_passes_through(self) -> None:
        assert parse_approx_cost(500) == pytest.approx(500.0)

    def test_invalid_returns_nan(self) -> None:
        assert math.isnan(parse_approx_cost("-"))
        assert math.isnan(parse_approx_cost("nan"))


class TestValidateRawColumns:
    def test_accepts_full_schema(self) -> None:
        df = minimal_zomato_dataframe(1)
        validate_raw_columns(df.columns)

    def test_raises_on_missing_column(self) -> None:
        df = minimal_zomato_dataframe(1)
        bad = df.drop(columns=["url"])
        with pytest.raises(ValueError, match="Missing expected columns"):
            validate_raw_columns(bad.columns)


class TestCleanDataframe:
    def test_adds_canonical_columns(self) -> None:
        df = minimal_zomato_dataframe(2)
        out = clean_dataframe(df)
        assert COL_CITY in out.columns
        assert COL_RATE_NUMERIC in out.columns
        assert COL_APPROX_COST_FOR_TWO in out.columns

    def test_strips_city(self) -> None:
        df = minimal_zomato_dataframe(2)
        out = clean_dataframe(df)
        assert out[COL_CITY].iloc[1] == "Mumbai"

    def test_parsed_rate_and_cost(self) -> None:
        df = minimal_zomato_dataframe(2)
        out = clean_dataframe(df)
        assert out[COL_RATE_NUMERIC].iloc[0] == pytest.approx(4.1)
        assert out[COL_APPROX_COST_FOR_TWO].iloc[0] == pytest.approx(800.0)
        assert out[COL_APPROX_COST_FOR_TWO].iloc[1] == pytest.approx(1200.0)


class TestIngestToParquet:
    def test_writes_parquet_roundtrip(self, tmp_path) -> None:
        df = minimal_zomato_dataframe(2)
        mock_ds = MagicMock()
        mock_ds.__len__.return_value = len(df)
        mock_ds.select.return_value = mock_ds
        mock_ds.to_pandas.return_value = df

        out_file = tmp_path / "out.parquet"

        with patch("phase_1_data_loading.ingest.load_raw_dataset", return_value=mock_ds):
            path = ingest_to_parquet(out_file, max_rows=2)

        assert path == out_file
        assert out_file.is_file()
        read = pd.read_parquet(out_file)
        assert COL_CITY in read.columns
        assert len(read) == 2


@pytest.mark.integration
def test_load_raw_dataset_smoke() -> None:
    """Optional: hits Hugging Face — run with: pytest -m integration"""
    from datasets import Dataset

    from phase_1_data_loading.ingest import load_raw_dataset

    ds = load_raw_dataset(split="train")
    assert isinstance(ds, Dataset)
    assert len(ds) > 0
    row = ds[0]
    for col in RAW_COLUMNS:
        assert col in row
