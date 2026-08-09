"""Small data contract for pluggable soft-rule packs."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from app.schemas.layout_plan import LayoutPlan
from app.schemas.requirements import RequirementsSpec
from app.services.quality.soft_rules import SoftRuleResult

PackEvaluator = Callable[[LayoutPlan, RequirementsSpec], list[SoftRuleResult]]
PackPredicate = Callable[[LayoutPlan, RequirementsSpec], bool]


@dataclass(frozen=True)
class RulePack:
    key: str
    weights: Mapping[str, float]
    evaluate: PackEvaluator
    applies_to: PackPredicate
