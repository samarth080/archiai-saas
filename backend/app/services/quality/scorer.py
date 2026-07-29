"""Canonical hard-filter plus weighted soft-quality scorer (Phase 6)."""

from app.config.mvp_defaults import INVALID_QUALITY_SCORE_CAP, QUALITY_RULE_WEIGHTS
from app.schemas.layout_plan import LayoutPlan
from app.schemas.quality_report import QualityReport, QualityWarning
from app.schemas.requirements import RequirementsSpec
from app.services.quality.hard_constraints import validate
from app.services.quality.soft_rules import SoftRuleResult, evaluate_generic_rules
from app.services.quality.vastu import evaluate_vastu


def _deduplicate_warnings(warnings: list[QualityWarning]) -> list[QualityWarning]:
    seen: set[tuple[str, str]] = set()
    result: list[QualityWarning] = []
    for warning in warnings:
        key = (warning.code, warning.message)
        if key in seen:
            continue
        seen.add(key)
        result.append(warning)
    return result


def score(
    plan: LayoutPlan,
    requirements: RequirementsSpec,
    *,
    include_vastu: bool = False,
) -> QualityReport:
    """Return a deterministic 0..100 report; invalid plans stay visibly invalid."""

    violations = validate(plan, requirements)
    results = evaluate_generic_rules(plan, requirements)
    if include_vastu:
        vastu = evaluate_vastu(plan)
        results.append(
            SoftRuleResult(name="vastu", score=vastu.score, warnings=vastu.warnings)
        )

    weighted_total = sum(QUALITY_RULE_WEIGHTS[result.name] for result in results)
    weighted_score = sum(
        QUALITY_RULE_WEIGHTS[result.name] * result.score for result in results
    )
    raw_score = round(100 * weighted_score / weighted_total) if weighted_total else 100
    final_score = min(raw_score, INVALID_QUALITY_SCORE_CAP) if violations else raw_score
    warnings = _deduplicate_warnings(
        [warning for result in results for warning in result.warnings]
    )
    return QualityReport(
        score=max(0, min(100, final_score)),
        hard_violations=violations,
        warnings=warnings,
    )
