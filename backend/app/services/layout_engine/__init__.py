"""MVP deterministic layout engine (workflow Phase 1).

RequirementsSpec -> LayoutPlan via recursive rectangular subdivision. Zero LLM
dependency — testable end-to-end from the hand-written fixtures. Kept fully
separate from the legacy `layout_service` engines (tiler/BSP/gtree), which
continue to serve the legacy /api/design path unchanged.
"""
from app.services.layout_engine.engine import DoesNotFitError, generate_plan

__all__ = ["generate_plan", "DoesNotFitError"]
