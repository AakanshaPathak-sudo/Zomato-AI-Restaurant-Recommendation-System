"""Unit tests for phase_4_recommendation (no Groq network by default)."""

import pandas as pd
import pytest

from phase_1_data_loading.schema import COL_APPROX_COST_FOR_TWO, COL_CITY, COL_RATE_NUMERIC
from phase_2_user_input.models import UserInput
from phase_4_recommendation.recommender import (
    extract_json_object,
    fallback_rank,
    parse_llm_recommendations,
    prefilter_candidates,
    recommend,
)


def _sample_candidates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["Low", "High", "Mid"],
            COL_CITY: ["Bangalore"] * 3,
            "location": ["A", "B", "C"],
            "cuisines": ["X", "Y", "Z"],
            COL_RATE_NUMERIC: [3.0, 4.5, 4.0],
            COL_APPROX_COST_FOR_TWO: [500.0, 900.0, 700.0],
        }
    )


class TestPrefilterCandidates:
    def test_orders_by_rating_desc(self) -> None:
        df = _sample_candidates()
        out = prefilter_candidates(df, max_rows=10)
        assert list(out["name"]) == ["High", "Mid", "Low"]

    def test_respects_max_rows(self) -> None:
        df = _sample_candidates()
        out = prefilter_candidates(df, max_rows=2)
        assert len(out) == 2
        assert list(out["name"]) == ["High", "Mid"]


class TestExtractJsonObject:
    def test_plain_json(self) -> None:
        s = '{"a": 1}'
        assert extract_json_object(s) == '{"a": 1}'

    def test_fenced_json(self) -> None:
        s = 'Here:\n```json\n{"recommendations":[]}\n```'
        assert '{"recommendations"' in extract_json_object(s)


class TestParseLlmRecommendations:
    def test_success(self) -> None:
        raw = '{"recommendations":[{"candidate_id":1,"rationale":"nice"}]}'
        out = parse_llm_recommendations(raw, {0, 1, 2}, top_k=5)
        assert out == [(1, "nice")]

    def test_accepts_float_candidate_id(self) -> None:
        raw = '{"recommendations":[{"candidate_id":1.0,"rationale":"ok"}]}'
        out = parse_llm_recommendations(raw, {0, 1, 2}, top_k=5)
        assert out == [(1, "ok")]

    def test_accepts_id_alias(self) -> None:
        raw = '{"recommendations":[{"id":2,"rationale":"x"}]}'
        out = parse_llm_recommendations(raw, {0, 1, 2}, top_k=5)
        assert out == [(2, "x")]

    def test_invalid_id_ignored(self) -> None:
        raw = '{"recommendations":[{"candidate_id":99,"rationale":"x"}]}'
        assert parse_llm_recommendations(raw, {0, 1}, top_k=5) is None

    def test_malformed_returns_none(self) -> None:
        assert parse_llm_recommendations("not json", {0}, top_k=5) is None


class TestFallbackRank:
    def test_top_k(self) -> None:
        df = prefilter_candidates(_sample_candidates(), max_rows=10)
        items = fallback_rank(df, top_k=2)
        assert len(items) == 2
        assert items[0].name == "High"
        assert items[0].rationale is None


class TestRecommendWithoutApiKey:
    def test_uses_fallback_when_no_key(self, monkeypatch) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        user = UserInput(city="Bangalore", max_price_for_two=1000.0)
        df = _sample_candidates()
        result = recommend(df, user, api_key=None, top_k=2)
        assert result.used_fallback is True
        assert len(result.items) == 2
        assert result.items[0].name == "High"


class TestRecommendEmpty:
    def test_empty_candidates(self) -> None:
        user = UserInput(city="X", max_price_for_two=100.0)
        result = recommend(pd.DataFrame(), user)
        assert result.items == []
        assert result.used_fallback is True


class TestRecommendGroqMocked:
    def test_success_without_network(self, monkeypatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "test-key")

        def fake_call(user_payload: dict, *, api_key: str, model: str) -> str:
            return '{"recommendations":[{"candidate_id":0,"rationale":"Great vibe"}]}'

        monkeypatch.setattr(
            "phase_4_recommendation.recommender._call_groq_chat",
            fake_call,
        )
        df = _sample_candidates()
        trimmed = prefilter_candidates(df, max_rows=10)
        user = UserInput(city="Bangalore", max_price_for_two=2000.0)
        result = recommend(df, user, top_k=2)
        assert result.used_fallback is False
        assert len(result.items) >= 1
        assert result.items[0].rationale == "Great vibe"
        assert result.items[0].name == trimmed.iloc[0]["name"]

    def test_falls_back_when_groq_raises(self, monkeypatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "test-key")

        def boom(*args, **kwargs):
            raise RuntimeError("api error")

        monkeypatch.setattr("phase_4_recommendation.recommender._call_groq_chat", boom)
        df = _sample_candidates()
        user = UserInput(city="Bangalore", max_price_for_two=2000.0)
        result = recommend(df, user, top_k=2)
        assert result.used_fallback is True
        assert result.items[0].name == "High"
