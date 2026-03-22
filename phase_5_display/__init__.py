"""Phase 5 — display: CLI formatting and full pipeline orchestration."""

from phase_5_display.format_output import (
    format_file_error,
    format_no_matches,
    format_recommendations,
    format_summary,
)
from phase_5_display.pipeline import run_pipeline

__all__ = [
    "format_file_error",
    "format_no_matches",
    "format_recommendations",
    "format_summary",
    "run_pipeline",
]
