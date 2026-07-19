"""QualityReport — the locked contract of the quality/scoring layer (Phase 6).

Two tiers, per the workflow's Finch-derived architecture:
- ``hard_violations`` (reject tier): geometric invalidity. When non-empty the
  layout is INVALID — the UI shows "invalid layout", never a score pretending
  validity.
- ``warnings`` (soft tier): human sentences with room names in them; ``rule``
  distinguishes generic architectural rules from Vastu rules so the frontend can
  badge them.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Violation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str  # e.g. "overlap", "out_of_bounds", "below_min_size", "unreachable"
    room_ids: list[str] = Field(default_factory=list)
    message: str


class QualityWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    severity: Literal["info", "warn"] = "warn"
    rule: Literal["generic", "vastu"] = "generic"


class QualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100)
    hard_violations: list[Violation] = Field(default_factory=list)
    warnings: list[QualityWarning] = Field(default_factory=list)
