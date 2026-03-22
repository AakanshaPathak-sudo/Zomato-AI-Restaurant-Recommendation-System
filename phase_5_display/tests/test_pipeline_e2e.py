"""
End-to-end integration: phases 2→3→4→5 on a local Parquet file.
Clears GROQ_API_KEY so Groq is not called (saves quota).
"""

import pandas as pd
import pytest

from phase_1_data_loading.schema import COL_APPROX_COST_FOR_TWO, COL_CITY, COL_RATE_NUMERIC
from phase_2_user_input import UserInputError
from phase_5_display.pipeline import run_pipeline


def _write_sample_parquet(path, *, city: str = "Bangalore") -> None:
    df = pd.DataFrame(
        {
            "name": ["Alpha Diner", "Beta Cafe"],
            COL_CITY: [city, city],
            "location": ["Indiranagar", "Koramangala"],
            "cuisines": ["North Indian", "Cafe"],
            COL_RATE_NUMERIC: [4.2, 3.8],
            COL_APPROX_COST_FOR_TWO: [600.0, 450.0],
        }
    )
    df.to_parquet(path, index=False)


@pytest.mark.e2e
def test_pipeline_happy_path_no_groq(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    pq = tmp_path / "r.parquet"
    _write_sample_parquet(pq)
    out = run_pipeline(
        city="bangalore",
        price="800",
        preferences="coffee",
        parquet_path=pq,
        top_k=5,
    )
    assert "Alpha Diner" in out or "Beta Cafe" in out
    assert "bangalore" in out.lower()
    assert "800" in out or "coffee" in out.lower()
    assert "rating" in out.lower() or "LLM" in out


@pytest.mark.e2e
def test_pipeline_empty_candidates(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    pq = tmp_path / "r.parquet"
    _write_sample_parquet(pq, city="Mumbai")
    out = run_pipeline(
        city="Bangalore",
        price=2000,
        preferences=None,
        parquet_path=pq,
    )
    assert "No restaurants matched" in out
    assert "Bangalore" in out


@pytest.mark.e2e
def test_pipeline_invalid_input_raises(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    pq = tmp_path / "r.parquet"
    _write_sample_parquet(pq)
    with pytest.raises(UserInputError):
        run_pipeline(city="", price=100, preferences=None, parquet_path=pq)
