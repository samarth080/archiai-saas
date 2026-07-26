"""MVP quality layer (workflow Phases 1 + 6).

Phase 1 ships the hard geometric validator (reject tier); Phase 6 adds the
soft rules, the data-driven Vastu module, and the weighted scorer on top.
Separate from the legacy `layout_quality_service`, which keeps scoring the
legacy engine path.
"""
from app.services.quality.hard_constraints import validate
from app.services.quality.scorer import score

__all__ = ["score", "validate"]
