"""Phase 7 — Streamlit deployment entrypoint."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

from phase_1_data_loading.ingest import ingest_to_parquet
from phase_2_user_input import UserInputError
from phase_3_integrate import load_processed_parquet
from phase_6_web.structured_pipeline import run_pipeline_structured

DEFAULT_PARQUET = "data/processed/restaurants.parquet"
DEFAULT_BOOTSTRAP_ROWS = 60000


def _parquet_path() -> Path:
    raw = os.environ.get("RESTAURANTS_PARQUET", DEFAULT_PARQUET)
    return Path(raw).expanduser().resolve()


@st.cache_data(show_spinner=False)
def _ensure_parquet(path: str) -> str:
    out = Path(path)
    if out.exists():
        return str(out)
    max_rows_raw = os.environ.get("BOOTSTRAP_MAX_ROWS", str(DEFAULT_BOOTSTRAP_ROWS)).strip()
    max_rows: Optional[int]
    try:
        max_rows = int(max_rows_raw) if max_rows_raw else None
    except ValueError:
        max_rows = DEFAULT_BOOTSTRAP_ROWS
    ingest_to_parquet(out, max_rows=max_rows)
    return str(out)


@st.cache_data(show_spinner=False)
def _localities_from_parquet(path: str) -> list[str]:
    df = load_processed_parquet(path)
    vals = [str(x).strip() for x in df["city"].dropna().tolist()]
    seen: set[str] = set()
    out: list[str] = []
    for city in vals:
        key = city.lower()
        if not city or key in seen:
            continue
        seen.add(key)
        out.append(city)
    out.sort(key=lambda x: x.lower())
    return out


def _render() -> None:
    st.set_page_config(page_title="Zomato AI Recs", page_icon="🍽️", layout="centered")
    st.title("Zomato AI Restaurant Recommendations")
    st.caption("Choose a Bangalore locality, budget, and optional preferences.")

    pq = _parquet_path()
    with st.spinner("Loading restaurant dataset..."):
        try:
            ready_path = _ensure_parquet(str(pq))
            localities = _localities_from_parquet(ready_path)
        except Exception as e:  # pragma: no cover
            st.error(f"Could not prepare dataset: {e}")
            st.stop()

    with st.form("reco_form"):
        city = st.selectbox("Locality", options=localities, index=0 if localities else None)
        price = st.slider("Max budget for two (INR)", min_value=100, max_value=5000, value=600, step=50)
        top_k = st.slider("Number of recommendations", min_value=1, max_value=20, value=10)
        preferences = st.text_input("Preferences (optional)", placeholder="e.g. vegetarian, outdoor seating")
        submitted = st.form_submit_button("Get AI Recommendations")

    if not submitted:
        return

    try:
        result = run_pipeline_structured(
            city=city or "",
            price=price,
            preferences=preferences or None,
            parquet_path=ready_path,
            top_k=top_k,
        )
    except UserInputError as e:
        st.error(str(e))
        return
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}")
        return
    except OSError as e:
        st.error(f"Could not load data: {e}")
        return
    except Exception as e:  # pragma: no cover
        st.error(f"Unexpected error: {e}")
        return

    summary = result.summary
    st.success(
        f"Area: {summary.get('city', '-')}, Budget: {int(summary.get('max_price_for_two', 0))}, "
        f"Preferences: {summary.get('preferences') or '(none)'}"
    )
    if result.used_fallback:
        st.info("LLM ranking unavailable. Showing top matches by rating.")
    if result.message:
        st.warning(result.message)
    if not result.items:
        return

    for idx, item in enumerate(result.items, start=1):
        title = f"{idx}. {item.get('name') or 'Unknown'}"
        subtitle = (
            f"Rating: {item.get('rate_numeric') or '-'} | "
            f"Cost for two: {item.get('approx_cost_for_two') or '-'} | "
            f"Location: {item.get('location') or '-'}"
        )
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(subtitle)
            st.caption(f"Cuisines: {item.get('cuisines') or '-'}")
            rationale = item.get("rationale")
            if rationale:
                st.write(rationale)


def _hydrate_env_from_streamlit_secrets() -> None:
    # Streamlit Cloud stores keys in st.secrets; map known keys to env for existing pipeline code.
    for key in ("GROQ_API_KEY", "GROQ_MODEL", "RESTAURANTS_PARQUET", "BOOTSTRAP_MAX_ROWS"):
        if os.environ.get(key):
            continue
        if key in st.secrets:
            os.environ[key] = str(st.secrets[key])


if __name__ == "__main__":
    load_dotenv()
    _hydrate_env_from_streamlit_secrets()
    _render()
