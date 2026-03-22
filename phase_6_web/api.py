"""
Phase 6: HTTP API + static web UI.

Set RESTAURANTS_PARQUET to the processed Parquet path (default: data/processed/restaurants.parquet).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from phase_2_user_input import UserInputError
from phase_6_web.structured_pipeline import run_pipeline_structured

ENV_PARQUET = "RESTAURANTS_PARQUET"
ENV_CORS = "CORS_ORIGINS"
DEFAULT_PARQUET = "data/processed/restaurants.parquet"
UI_DIR = Path(__file__).resolve().parent / "ui"


def _parquet_path() -> Path:
    return Path(os.environ.get(ENV_PARQUET, DEFAULT_PARQUET)).expanduser().resolve()


def _cors_origins() -> list[str]:
    raw = os.environ.get(
        ENV_CORS,
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,"
        "http://localhost:8000,http://127.0.0.1:8000,null",
    )
    if raw.strip() == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


class RecommendRequest(BaseModel):
    city: str
    price: Union[int, float, str]
    preferences: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=50)
    max_candidates_for_llm: int = Field(default=40, ge=1, le=200)


app = FastAPI(title="Zomato AI Recommendations", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


_INDEX_PATH = UI_DIR / "index.html"


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(_INDEX_PATH, media_type="text/html")


@app.head("/")
def head_index() -> Response:
    size = _INDEX_PATH.stat().st_size
    return Response(
        status_code=200,
        media_type="text/html",
        headers={"content-length": str(size)},
    )


@app.post("/api/recommend")
def api_recommend(body: RecommendRequest) -> dict:
    pq = _parquet_path()
    try:
        result = run_pipeline_structured(
            city=body.city,
            price=body.price,
            preferences=body.preferences,
            parquet_path=pq,
            top_k=body.top_k,
            max_candidates_for_llm=body.max_candidates_for_llm,
        )
        return result.to_api_dict()
    except UserInputError as e:
        return JSONResponse(
            status_code=422,
            content={"ok": False, "error": str(e)},
        )
    except FileNotFoundError:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"Restaurant data file not found: {pq}"},
        )
    except OSError as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"Could not load restaurant data: {e}"},
        )


app.mount("/ui", StaticFiles(directory=str(UI_DIR)), name="ui")
