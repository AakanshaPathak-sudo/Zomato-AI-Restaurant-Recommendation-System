from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset

from phase_1_data_loading.schema import (
    COL_APPROX_COST_FOR_TWO,
    COL_CITY,
    COL_RATE_NUMERIC,
    DATASET_ID,
    DEFAULT_SPLIT,
    RAW_COLUMNS,
)

_COST_DIGITS = re.compile(r"(\d+)")


def parse_rate(value: Any) -> float:
    """Parse Zomato `rate` strings like '4.1/5' into a float; invalid -> NaN."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return float("nan")
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none", "-", "new"}:
        return float("nan")
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*/\s*5", s)
    if m:
        return float(m.group(1))
    m2 = re.match(r"^\s*(\d+(?:\.\d+)?)\s*$", s)
    if m2:
        return float(m2.group(1))
    return float("nan")


def parse_approx_cost(value: Any) -> float:
    """Parse `approx_cost(for two people)` like '800' or '1,200' into a float; invalid -> NaN."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return float("nan")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none", "-"}:
        return float("nan")
    digits = _COST_DIGITS.search(s.replace(",", ""))
    if not digits:
        return float("nan")
    return float(digits.group(1))


def validate_raw_columns(columns: Any) -> None:
    """Raise ValueError if required raw columns are missing."""
    missing = [c for c in RAW_COLUMNS if c not in columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")


def load_raw_dataset(
    *,
    revision: Optional[str] = None,
    split: str = DEFAULT_SPLIT,
    streaming: bool = False,
) -> Dataset | DatasetDict:
    """Load the Hugging Face Zomato dataset (full split or streaming)."""
    if revision is not None:
        return load_dataset(DATASET_ID, split=split, revision=revision, streaming=streaming)
    return load_dataset(DATASET_ID, split=split, streaming=streaming)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize strings, parse rate and cost, and expose canonical column names.
    Drops rows with no city or no parsed cost (optional filter for usable rows).
    """
    validate_raw_columns(df.columns)
    out = df.copy()
    city_col = "listed_in(city)"
    cost_col = "approx_cost(for two people)"

    out[COL_CITY] = out[city_col].astype(str).str.strip()
    out[COL_RATE_NUMERIC] = out["rate"].map(parse_rate)
    out[COL_APPROX_COST_FOR_TWO] = out[cost_col].map(parse_approx_cost)

    return out


def ingest_to_parquet(
    output_path: str | Path,
    *,
    revision: Optional[str] = None,
    split: str = DEFAULT_SPLIT,
    max_rows: Optional[int] = None,
) -> Path:
    """
    Load dataset from Hugging Face, clean, and write Parquet.
    If max_rows is set, only the first N rows are processed (for dev/smoke runs).
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    ds = load_raw_dataset(revision=revision, split=split, streaming=False)
    if max_rows is not None:
        n = min(max_rows, len(ds))
        ds = ds.select(range(n))
    df = ds.to_pandas()
    cleaned = clean_dataframe(df)
    cleaned.to_parquet(path, index=False)
    return path
