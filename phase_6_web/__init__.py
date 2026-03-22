"""Phase 6 — web: API contract and structured pipeline output (HTTP server in a later step)."""

from phase_6_web.structured_pipeline import (
    StructuredPipelineResult,
    item_to_api_dict,
    run_pipeline_structured,
)

__all__ = [
    "StructuredPipelineResult",
    "item_to_api_dict",
    "run_pipeline_structured",
]
