"""Data-driven Vastu advisory evaluator for canonical north-up plans.

This module never decides whether Vastu applies.  ``scorer.score`` includes it
only when the caller explicitly sets ``include_vastu=True``.  Rules live in
``vastu_rules.json`` so domain review does not require code changes.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.schemas.layout_plan import LayoutPlan, PlanPlot, PlanRoom
from app.schemas.quality_report import QualityWarning


@dataclass(frozen=True)
class VastuRule:
    room_type: str
    preferred_zones: tuple[str, ...]
    avoid_zones: tuple[str, ...]
    weight: float
    message_preferred: str
    message_violation: str


@dataclass(frozen=True)
class VastuEvaluation:
    score: float
    warnings: list[QualityWarning]


@lru_cache(maxsize=1)
def load_rules() -> tuple[VastuRule, ...]:
    path = Path(__file__).with_name("vastu_rules.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        VastuRule(
            room_type=item["room_type"],
            preferred_zones=tuple(item["preferred_zones"]),
            avoid_zones=tuple(item["avoid_zones"]),
            weight=float(item["weight"]),
            message_preferred=item["message_preferred"],
            message_violation=item["message_violation"],
        )
        for item in payload["rules"]
    )


def sector_for_room(room: PlanRoom, plot: PlanPlot) -> str:
    """Return one of the north-up 3x3 compass sectors from room centroid."""

    centre_x = room.x + room.w / 2
    centre_y = room.y + room.h / 2
    horizontal = (
        "west"
        if centre_x < plot.width_m / 3
        else "east"
        if centre_x > plot.width_m * 2 / 3
        else "center"
    )
    vertical = (
        "north"
        if centre_y < plot.depth_m / 3
        else "south"
        if centre_y > plot.depth_m * 2 / 3
        else "center"
    )
    if horizontal == "center" and vertical == "center":
        return "center"
    if horizontal == "center":
        return vertical
    if vertical == "center":
        return horizontal
    return f"{vertical}{horizontal}"


def evaluate_vastu(plan: LayoutPlan) -> VastuEvaluation:
    rules = {rule.room_type: rule for rule in load_rules()}
    earned = 0.0
    possible = 0.0
    warnings: list[QualityWarning] = []

    for room in plan.rooms:
        rule = rules.get(room.type)
        if rule is None:
            continue
        sector = sector_for_room(room, plan.plot)
        possible += rule.weight
        preferred = ", ".join(rule.preferred_zones)
        if sector in rule.preferred_zones:
            earned += rule.weight
            continue
        if sector in rule.avoid_zones:
            severity = "warn"
            credit = 0.0
        else:
            severity = "info"
            credit = 0.6
        earned += rule.weight * credit
        warnings.append(
            QualityWarning(
                code=f"vastu.{room.type}_{sector}",
                message=rule.message_violation.format(
                    label=room.label,
                    sector=sector.replace("_", " "),
                    preferred=preferred.replace("_", " "),
                ),
                severity=severity,
                rule="vastu",
            )
        )

    return VastuEvaluation(
        score=earned / possible if possible else 1.0,
        warnings=warnings,
    )
