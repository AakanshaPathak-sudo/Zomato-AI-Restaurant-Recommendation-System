from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import pandas as pd

from phase_1_data_loading.schema import COL_APPROX_COST_FOR_TWO, COL_CITY, COL_RATE_NUMERIC
from phase_2_user_input.models import UserInput
from phase_4_recommendation.models import RankedItem, RecommendationResult

DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
ENV_GROQ_API_KEY = "GROQ_API_KEY"
ENV_GROQ_MODEL = "GROQ_MODEL"

_SYSTEM_PROMPT = """You are a restaurant recommendation assistant for India (Zomato-style data).
You MUST only recommend venues from the provided candidate list. Each candidate has a unique integer candidate_id.
Reply with ONLY valid JSON (no markdown fences) using exactly this shape:
{"recommendations":[{"candidate_id":<int>,"rationale":<string>},...]}
Order the array from best match to worst. Include at most the number of items requested.
Every candidate_id MUST appear in the input list. Do not invent names or ids."""


def _env_api_key() -> Optional[str]:
    key = os.environ.get(ENV_GROQ_API_KEY)
    if key is None or not str(key).strip():
        return None
    return str(key).strip()


def _resolve_model(model: Optional[str]) -> str:
    if model and str(model).strip():
        return str(model).strip()
    env_m = os.environ.get(ENV_GROQ_MODEL)
    if env_m and str(env_m).strip():
        return str(env_m).strip()
    return DEFAULT_GROQ_MODEL


def _ensure_rate_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if COL_RATE_NUMERIC not in out.columns:
        out[COL_RATE_NUMERIC] = float("nan")
    return out


def prefilter_candidates(candidates: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    """Cheap pre-sort by rating; cap rows for LLM context."""
    if candidates.empty:
        return candidates
    ranked = _ensure_rate_column(candidates)
    ranked = ranked.sort_values(COL_RATE_NUMERIC, ascending=False, na_position="last")
    return ranked.head(max_rows).reset_index(drop=True)


def _row_to_item(row: pd.Series, rationale: Optional[str]) -> RankedItem:
    return RankedItem(
        name=str(row.get("name", "")),
        location=None if pd.isna(row.get("location")) else str(row.get("location")),
        cuisines=None if pd.isna(row.get("cuisines")) else str(row.get("cuisines")),
        rate_numeric=float(row[COL_RATE_NUMERIC]) if pd.notna(row.get(COL_RATE_NUMERIC)) else float("nan"),
        approx_cost_for_two=float(row[COL_APPROX_COST_FOR_TWO])
        if pd.notna(row.get(COL_APPROX_COST_FOR_TWO))
        else float("nan"),
        rationale=rationale,
    )


def fallback_rank(trimmed: pd.DataFrame, top_k: int) -> list[RankedItem]:
    """Deterministic order: already sorted by rating in prefilter; take top_k."""
    n = min(top_k, len(trimmed))
    return [_row_to_item(trimmed.iloc[i], None) for i in range(n)]


def extract_json_object(text: str) -> str:
    """Strip optional markdown fences; return inner JSON string."""
    s = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", s)
    if m:
        return m.group(1).strip()
    return s


def _coerce_candidate_id(raw: Any, valid_ids: set[int]) -> Optional[int]:
    """Accept int, whole float, or numeric string (models sometimes emit floats)."""
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        cid = raw
    elif isinstance(raw, float) and raw.is_integer():
        cid = int(raw)
    elif isinstance(raw, str) and raw.strip().lstrip("-").isdigit():
        cid = int(raw.strip())
    else:
        return None
    return cid if cid in valid_ids else None


def parse_llm_recommendations(
    raw_text: str,
    valid_ids: set[int],
    top_k: int,
) -> Optional[list[tuple[int, str]]]:
    """
    Parse model output into (candidate_id, rationale) pairs.
    Returns None if parsing or validation fails.
    """
    try:
        blob = extract_json_object(raw_text)
        data = json.loads(blob)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    recs = data.get("recommendations")
    if recs is None:
        recs = data.get("Recommendations")
    if not isinstance(recs, list):
        return None
    out: list[tuple[int, str]] = []
    for item in recs:
        if not isinstance(item, dict):
            continue
        cid_raw = item.get("candidate_id", item.get("id"))
        cid = _coerce_candidate_id(cid_raw, valid_ids)
        if cid is None:
            continue
        rat = item.get("rationale", "")
        if not isinstance(rat, str):
            rat = str(rat) if rat is not None else ""
        out.append((cid, rat))
        if len(out) >= top_k:
            break
    if not out:
        return None
    return out


def _call_groq_chat(
    user_payload: dict[str, Any],
    *,
    api_key: str,
    model: str,
) -> str:
    from groq import Groq

    client = Groq(api_key=api_key)
    user_content = json.dumps(user_payload, ensure_ascii=False)
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
    }
    try:
        comp = client.chat.completions.create(
            **kwargs,
            response_format={"type": "json_object"},
        )
    except Exception:
        comp = client.chat.completions.create(**kwargs)
    choice = comp.choices[0].message
    content = choice.content if choice else None
    if not content:
        raise RuntimeError("empty completion from Groq")
    return content


def recommend(
    candidates: pd.DataFrame,
    user: UserInput,
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    top_k: int = 10,
    max_candidates_for_llm: int = 40,
) -> RecommendationResult:
    """
    Rank candidates with Groq when an API key is available; otherwise use rating-based fallback.
    Set ``GROQ_API_KEY`` or pass ``api_key``. Optional ``GROQ_MODEL`` / ``model``.
    """
    if candidates.empty:
        return RecommendationResult(items=[], used_fallback=True)

    trimmed = prefilter_candidates(candidates, max_candidates_for_llm)
    valid_ids = set(range(len(trimmed)))

    key = api_key if (api_key and str(api_key).strip()) else _env_api_key()
    resolved_model = _resolve_model(model)

    if key is None:
        return RecommendationResult(items=fallback_rank(trimmed, top_k), used_fallback=True)

    payload = {
        "city": user.city,
        "max_budget_for_two": float(user.max_price_for_two),
        "preferences": user.preferences,
        "top_k": top_k,
        "candidates": [],
    }
    for i, row in trimmed.iterrows():
        payload["candidates"].append(
            {
                "candidate_id": int(i),
                "name": str(row.get("name", "")),
                "location": None if pd.isna(row.get("location")) else str(row.get("location")),
                "cuisines": None if pd.isna(row.get("cuisines")) else str(row.get("cuisines")),
                COL_RATE_NUMERIC: float(row[COL_RATE_NUMERIC]) if pd.notna(row.get(COL_RATE_NUMERIC)) else None,
                COL_APPROX_COST_FOR_TWO: float(row[COL_APPROX_COST_FOR_TWO])
                if pd.notna(row.get(COL_APPROX_COST_FOR_TWO))
                else None,
                COL_CITY: None if pd.isna(row.get(COL_CITY)) else str(row.get(COL_CITY)),
            }
        )

    try:
        raw = _call_groq_chat(payload, api_key=key, model=resolved_model)
        parsed = parse_llm_recommendations(raw, valid_ids, top_k)
    except Exception:
        parsed = None

    if parsed is None:
        return RecommendationResult(items=fallback_rank(trimmed, top_k), used_fallback=True)

    items: list[RankedItem] = []
    seen: set[int] = set()
    for cid, rat in parsed:
        if cid in seen:
            continue
        seen.add(cid)
        row = trimmed.iloc[cid]
        items.append(_row_to_item(row, rat if rat else None))
        if len(items) >= top_k:
            break

    if not items:
        return RecommendationResult(items=fallback_rank(trimmed, top_k), used_fallback=True)

    return RecommendationResult(items=items, used_fallback=False)
