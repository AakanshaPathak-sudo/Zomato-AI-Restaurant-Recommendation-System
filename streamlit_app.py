"""Phase 7 — Streamlit deployment entrypoint (Velocity-inspired UI)."""

from __future__ import annotations

import html
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

PRICE_TIERS: list[tuple[str, int]] = [
    ("Budget — Under ₹300", 300),
    ("Affordable — ₹300–₹600", 600),
    ("Mid-Range — ₹600–₹1200", 1200),
    ("Expensive — Above ₹1200", 5000),
]


def _inject_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --bg-deep: #030303;
  --bg-card: rgba(18, 16, 14, 0.65);
  --orange: #ff7a1a;
  --orange-bright: #ffb020;
  --orange-dim: rgba(255, 120, 40, 0.35);
  --text: #fafafa;
  --muted: #9ca3af;
  --glass-border: rgba(255, 140, 60, 0.22);
}

html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
  color: var(--text);
}

[data-testid="stAppViewContainer"] {
  background-color: var(--bg-deep) !important;
  background-image:
    radial-gradient(ellipse 100% 60% at 50% 0%, rgba(255, 100, 30, 0.14) 0%, transparent 55%),
    radial-gradient(ellipse 80% 50% at 80% 20%, rgba(255, 160, 60, 0.08) 0%, transparent 45%),
    radial-gradient(ellipse 90% 45% at 50% 100%, rgba(255, 120, 40, 0.18) 0%, transparent 50%) !important;
}

[data-testid="stHeader"] { background: transparent !important; }
.block-container {
  padding-top: 0.5rem !important;
  max-width: 1120px !important;
}

/* Nav pill */
.velocity-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 0.65rem 1.25rem;
  margin: 0 auto 2rem;
  max-width: 1000px;
  background: rgba(12, 12, 12, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
  border-radius: 999px;
  box-shadow: 0 0 40px rgba(255, 100, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.04);
}
.velocity-nav .logo {
  font-weight: 800;
  font-size: 1.05rem;
  background: linear-gradient(135deg, #fff 0%, #ffb86c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.velocity-nav .links { display: flex; gap: 1.25rem; flex-wrap: wrap; font-size: 0.8rem; color: var(--muted); }
.velocity-nav .links span { cursor: default; }
.velocity-nav .cta {
  padding: 0.4rem 1rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  background: linear-gradient(135deg, #ff6b00, #ffb020);
  color: #0a0a0a !important;
  box-shadow: 0 0 24px rgba(255, 140, 40, 0.45);
  border: none;
}

/* Hero */
.hero-wrap { text-align: center; margin-bottom: 2.5rem; position: relative; }
.hero-wrap::after {
  content: "";
  display: block;
  height: 120px;
  margin-top: 2rem;
  background: radial-gradient(ellipse 70% 80% at 50% 100%, rgba(255, 120, 40, 0.35) 0%, transparent 65%);
  pointer-events: none;
}
.hero-title {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: #fff;
  margin: 0 0 0.75rem 0;
}
.hero-sub {
  font-size: 1rem;
  color: var(--muted);
  max-width: 520px;
  margin: 0 auto 1.5rem;
  line-height: 1.55;
}
.hero-badges {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 0.5rem;
}
.hero-badge {
  font-size: 0.72rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--muted);
}

/* Section titles */
.sec-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: #fff;
  text-align: center;
  margin: 2.5rem 0 0.35rem 0;
}
.sec-sub {
  text-align: center;
  color: var(--muted);
  font-size: 0.88rem;
  margin: 0 0 1.5rem 0;
}

/* Glass grid cards */
.glass-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}
@media (max-width: 700px) { .glass-grid { grid-template-columns: 1fr; } }
.glass-card {
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  padding: 1.25rem 1.35rem;
  box-shadow: 0 0 32px rgba(255, 100, 0, 0.06);
}
.glass-card h4 { margin: 0 0 0.5rem 0; font-size: 0.95rem; color: #fff; font-weight: 700; }
.glass-card p { margin: 0; font-size: 0.82rem; color: var(--muted); line-height: 1.5; }
.glass-icon {
  width: 40px; height: 40px; border-radius: 12px;
  background: linear-gradient(135deg, rgba(255, 120, 40, 0.25), rgba(255, 180, 80, 0.1));
  border: 1px solid rgba(255, 140, 60, 0.3);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; margin-bottom: 0.75rem;
  box-shadow: 0 0 20px rgba(255, 120, 40, 0.15);
}

.process-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 2.5rem;
}
@media (max-width: 800px) { .process-row { grid-template-columns: 1fr; } }
.process-card {
  background: rgba(10, 10, 10, 0.6);
  border: 1px solid rgba(255, 140, 60, 0.18);
  border-radius: 20px;
  padding: 1.35rem 1.2rem;
  text-align: center;
  box-shadow: 0 0 40px rgba(255, 100, 0, 0.05);
}
.process-card .step {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--orange);
  margin-bottom: 0.5rem;
}
.process-card h4 { margin: 0 0 0.4rem 0; color: #fff; font-size: 0.95rem; }
.process-card p { margin: 0; font-size: 0.8rem; color: var(--muted); line-height: 1.45; }

/* Form glass shell */
[data-testid="stForm"] {
  background: rgba(12, 11, 10, 0.72) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border) !important;
  border-radius: 24px !important;
  padding: 1.5rem 1.35rem 1.75rem !important;
  box-shadow:
    0 0 60px rgba(255, 100, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
  margin-bottom: 2rem !important;
}

.try-title {
  text-align: center;
  font-size: 1.15rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 0.25rem 0;
}
.try-sub {
  text-align: center;
  font-size: 0.85rem;
  color: var(--muted);
  margin: 0 0 1rem 0;
}

label[data-testid="stWidgetLabel"] p {
  color: #fcd9a8 !important;
  font-weight: 600 !important;
  font-size: 0.78rem !important;
}
.stSelectbox > div > div,
.stTextInput > div > div > input {
  background-color: rgba(0, 0, 0, 0.45) !important;
  border-color: rgba(255, 140, 60, 0.28) !important;
  color: #f3f4f6 !important;
  border-radius: 12px !important;
}

.stSlider [data-baseweb="slider"] [role="slider"] {
  background: linear-gradient(135deg, #ff6b00, #ffb020) !important;
  border: 2px solid #1a1a1a !important;
  box-shadow: 0 0 16px rgba(255, 140, 40, 0.55) !important;
}
.stSlider [data-baseweb="slider"] [data-testid="stTickBarMin"],
.stSlider [data-baseweb="slider"] [data-testid="stTickBarMax"] {
  background: rgba(255, 120, 40, 0.2) !important;
}

.stForm [data-testid="stFormSubmitButton"] button {
  width: 100%;
  background: linear-gradient(135deg, #ff6b00 0%, #ffb020 100%) !important;
  color: #0a0a0a !important;
  border: none !important;
  border-radius: 14px !important;
  font-weight: 700 !important;
  padding: 0.7rem 1.25rem !important;
  box-shadow: 0 0 28px rgba(255, 140, 40, 0.4) !important;
}

.results-heading {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  margin: 1.5rem 0 1rem 0;
  text-align: center;
}

.rest-card {
  background: rgba(8, 8, 8, 0.75);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 140, 60, 0.28);
  border-radius: 20px;
  padding: 1rem 1.1rem 1.15rem;
  height: 100%;
  box-shadow:
    0 0 36px rgba(255, 100, 0, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}
.card-head { display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.5rem; }
.badge-num {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #ff6b00, #ffb020);
  color: #0a0a0a; font-size: 0.8rem; font-weight: 800;
  box-shadow: 0 0 14px rgba(255, 140, 40, 0.45);
}
.card-name { font-weight: 700; font-size: 1.02rem; color: #fff; }
.card-loc { color: #9ca3af; font-size: 0.82rem; margin-bottom: 0.65rem; }
.card-stats { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.35rem; }
.rating { color: #5eead4; font-weight: 600; font-size: 0.88rem; }
.price-tag { color: #fcd9a8; font-size: 0.88rem; font-weight: 600; }
.delivery-line { color: #86efac; font-size: 0.76rem; margin-bottom: 0.65rem; }
.desc-box {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 12px;
  padding: 0.65rem 0.75rem;
  font-size: 0.82rem;
  line-height: 1.45;
  color: #d1d5db;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

/* FAQ expanders */
.streamlit-expanderHeader { color: #fff !important; font-weight: 600 !important; }
[data-testid="stExpander"] {
  background: rgba(12, 12, 12, 0.6) !important;
  border: 1px solid rgba(255, 140, 60, 0.15) !important;
  border-radius: 14px !important;
  margin-bottom: 0.5rem !important;
}
[data-testid="stExpander"][aria-expanded="true"] {
  border-color: rgba(255, 140, 60, 0.45) !important;
  box-shadow: 0 0 20px rgba(255, 100, 0, 0.08) !important;
}

.footer-cta {
  text-align: center;
  margin: 3rem 0 1rem;
  padding: 2.5rem 1.5rem;
  border-radius: 24px;
  background: radial-gradient(ellipse 80% 100% at 50% 100%, rgba(255, 120, 40, 0.2) 0%, transparent 70%),
              rgba(8, 8, 8, 0.5);
  border: 1px solid rgba(255, 140, 60, 0.2);
}
.footer-cta h3 { margin: 0 0 0.5rem 0; color: #fff; font-size: 1.25rem; font-weight: 800; }
.footer-cta p { margin: 0; color: var(--muted); font-size: 0.88rem; }

.footer-note {
  text-align: center;
  color: #525252;
  font-size: 0.7rem;
  margin-top: 1.5rem;
  padding-bottom: 1rem;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _landing_sections() -> None:
    st.markdown(
        """
<nav class="velocity-nav">
  <span class="logo">Zomato AI</span>
  <div class="links">
    <span>Why AI picks</span>
    <span>How it works</span>
    <span>Bangalore data</span>
  </div>
  <span class="cta">Live recommendations</span>
</nav>
<div class="hero-wrap">
  <h1 class="hero-title">Discover faster.<br/>Dine smarter.</h1>
  <p class="hero-sub">Real Zomato-style listings, filtered by area and budget — ranked with Groq when your API key is configured.</p>
  <div class="hero-badges">
    <span class="hero-badge">Bangalore localities</span>
    <span class="hero-badge">Budget-aware</span>
    <span class="hero-badge">LLM + fallback ranking</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<h2 class="sec-title">Why this guide works</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sec-sub">Built for clarity, speed, and honest picks from your dataset.</p>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="glass-grid">
  <div class="glass-card">
    <div class="glass-icon">⚡</div>
    <h4>Instant shortlist</h4>
    <p>We filter thousands of rows to venues that match your area and max spend for two.</p>
  </div>
  <div class="glass-card">
    <div class="glass-icon">🧠</div>
    <h4>AI-ranked results</h4>
    <p>When Groq is enabled, the model explains why each spot fits your preferences.</p>
  </div>
  <div class="glass-card">
    <div class="glass-icon">🛡️</div>
    <h4>Safe fallback</h4>
    <p>No key or API hiccup? You still get a solid rating-based ordering.</p>
  </div>
  <div class="glass-card">
    <div class="glass-icon">📍</div>
    <h4>Locality-first</h4>
    <p>Search uses the same city field as the dataset — pick real Bangalore areas.</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<h2 class="sec-title">The process — fast, clear, done</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sec-sub">Three steps from idea to table.</p>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="process-row">
  <div class="process-card">
    <span class="step">01</span>
    <h4>Share your vibe</h4>
    <p>Choose locality, price tier, and optional preferences like cuisine or diet.</p>
  </div>
  <div class="process-card">
    <span class="step">02</span>
    <h4>We rank it</h4>
    <p>The pipeline loads candidates and runs LLM or deterministic ranking.</p>
  </div>
  <div class="process-card">
    <span class="step">03</span>
    <h4>Pick &amp; go</h4>
    <p>Scan glowing cards with ratings, cost, and “why this place” copy.</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _faq_section() -> None:
    st.markdown('<h2 class="sec-title">Questions</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sec-sub">Quick answers before you search.</p>', unsafe_allow_html=True)
    with st.expander("Which cities work?"):
        st.write(
            "The bundled dataset uses **Bangalore localities** (e.g. Banashankari, Koramangala). "
            "Pick names that exist in the data for best results."
        )
    with st.expander("Do I need a Groq API key?"):
        st.write(
            "No — the app falls back to **rating-based ranking**. "
            "Add `GROQ_API_KEY` in Streamlit Secrets (or `.env` locally) for LLM rationales."
        )
    with st.expander("Why is the first load slow?"):
        st.write(
            "On Streamlit Cloud the app may **download and build Parquet** on first run. "
            "You can set `BOOTSTRAP_MAX_ROWS` in secrets for a quicker cold start."
        )
    with st.expander("Is this the same as the Zomato app?"):
        st.write(
            "No — this is a **demo project** using public dataset-style fields. "
            "It is not affiliated with Zomato."
        )


def _footer_sections() -> None:
    st.markdown(
        """
<div class="footer-cta">
  <h3>Ready when you are</h3>
  <p>Scroll up, set your budget, and hit Get Recommendations.</p>
</div>
<p class="footer-note">Zomato AI · Streamlit · Groq-ready pipeline</p>
        """,
        unsafe_allow_html=True,
    )


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


def _esc(x: object) -> str:
    if x is None:
        return ""
    return html.escape(str(x), quote=True)


def _card_html(rank: int, item: dict) -> str:
    name = _esc(item.get("name") or "Unknown")
    loc = _esc(item.get("location") or item.get("city") or "—")
    rate = item.get("rate_numeric")
    rate_s = f"{float(rate):.1f}" if rate is not None and str(rate) != "nan" else "—"
    cost = item.get("approx_cost_for_two")
    if cost is not None and str(cost) != "nan":
        try:
            cost_int = int(float(cost))
            price_line = f"₹{cost_int} for two"
        except (TypeError, ValueError):
            price_line = "—"
    else:
        price_line = "—"
    rationale = item.get("rationale")
    desc = _esc(rationale) if rationale else _esc(item.get("cuisines") or "Great match for your search.")
    return f"""
<div class="rest-card">
  <div class="card-head">
    <span class="badge-num">{rank}</span>
    <span class="card-name">{name}</span>
  </div>
  <div class="card-loc">📍 {loc}</div>
  <div class="card-stats">
    <span class="rating">★ {rate_s} / 5</span>
    <span class="price-tag">{price_line}</span>
  </div>
  <div class="delivery-line">✓ Matched to your filters</div>
  <div class="desc-box">{desc}</div>
</div>
"""


def _render() -> None:
    st.set_page_config(page_title="Zomato AI", page_icon="🍽️", layout="wide", initial_sidebar_state="collapsed")
    _inject_styles()
    _landing_sections()

    pq = _parquet_path()
    with st.spinner("Loading restaurant dataset..."):
        try:
            ready_path = _ensure_parquet(str(pq))
            localities = _localities_from_parquet(ready_path)
        except Exception as e:  # pragma: no cover
            st.error(f"Could not prepare dataset: {e}")
            st.stop()

    st.markdown('<p class="try-title">Try it now</p>', unsafe_allow_html=True)
    st.markdown('<p class="try-sub">Pick a locality, budget tier, and optional preferences.</p>', unsafe_allow_html=True)

    with st.form("reco_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            city = st.selectbox("Select City", options=localities, index=0 if localities else None)
        with c2:
            tier_labels = [t[0] for t in PRICE_TIERS]
            tier_pick = st.selectbox("Price Range", options=tier_labels, index=1)
        with c3:
            top_k = st.slider("Recommendations", min_value=1, max_value=20, value=10)
        preferences = st.text_input(
            "Preferences (optional)",
            placeholder="e.g. vegetarian, outdoor seating",
        )
        submitted = st.form_submit_button("Get Recommendations")

    if not submitted:
        _faq_section()
        _footer_sections()
        return

    price = dict(PRICE_TIERS)[tier_pick]

    try:
        result = run_pipeline_structured(
            city=city or "",
            price=price,
            preferences=(preferences or "").strip() or None,
            parquet_path=ready_path,
            top_k=top_k,
        )
    except UserInputError as e:
        st.error(str(e))
        _faq_section()
        _footer_sections()
        return
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}")
        _faq_section()
        _footer_sections()
        return
    except OSError as e:
        st.error(f"Could not load data: {e}")
        _faq_section()
        _footer_sections()
        return
    except Exception as e:  # pragma: no cover
        st.error(f"Unexpected error: {e}")
        _faq_section()
        _footer_sections()
        return

    if result.used_fallback:
        st.caption("LLM ranking unavailable — showing top matches by rating.")
    if result.message:
        st.warning(result.message)
    if not result.items:
        _faq_section()
        _footer_sections()
        return

    n = len(result.items)
    st.markdown(f'<p class="results-heading">Found {n} top pick{"s" if n != 1 else ""}</p>', unsafe_allow_html=True)

    items = result.items
    chunk = 3
    for row_start in range(0, len(items), chunk):
        row = items[row_start : row_start + chunk]
        cols = st.columns(len(row))
        for col, item, global_idx in zip(cols, row, range(row_start + 1, row_start + 1 + len(row))):
            with col:
                st.markdown(_card_html(global_idx, item), unsafe_allow_html=True)

    _faq_section()
    _footer_sections()


def _hydrate_env_from_streamlit_secrets() -> None:
    for key in ("GROQ_API_KEY", "GROQ_MODEL", "RESTAURANTS_PARQUET", "BOOTSTRAP_MAX_ROWS"):
        if os.environ.get(key):
            continue
        if key in st.secrets:
            os.environ[key] = str(st.secrets[key])


if __name__ == "__main__":
    load_dotenv()
    _hydrate_env_from_streamlit_secrets()
    _render()
