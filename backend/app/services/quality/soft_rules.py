"""Deterministic generic soft rules for canonical ``LayoutPlan`` geometry.

Each rule returns a normalized 0..1 score plus plain-language warnings.  The
weighted combination lives in ``scorer.py``; this module does not know about UI
or persistence.
"""

from dataclasses import dataclass, field

from app.schemas.layout_plan import LayoutPlan, PlanRoom
from app.schemas.quality_report import QualityWarning
from app.schemas.requirements import RequirementsSpec, RoomType
from app.services.layout_engine.geometry import EPS, Rect


@dataclass(frozen=True)
class SoftRuleResult:
    name: str
    score: float
    warnings: list[QualityWarning] = field(default_factory=list)


def _rect(room: PlanRoom) -> Rect:
    return Rect(room.x, room.y, room.w, room.h)


def _share_wall(a: PlanRoom, b: PlanRoom) -> bool:
    return _rect(a).shared_edge(_rect(b)) is not None


def _rooms_by_type(plan: LayoutPlan) -> dict[RoomType, list[PlanRoom]]:
    grouped: dict[RoomType, list[PlanRoom]] = {}
    for room in plan.rooms:
        grouped.setdefault(room.type, []).append(room)
    return grouped


def _pair_is_adjacent(a_rooms: list[PlanRoom], b_rooms: list[PlanRoom]) -> bool:
    for a in a_rooms:
        for b in b_rooms:
            if a.id != b.id and _share_wall(a, b):
                return True
    return False


def adjacency_rule(plan: LayoutPlan, requirements: RequirementsSpec) -> SoftRuleResult:
    grouped = _rooms_by_type(plan)
    earned = 0.0
    possible = 0.0
    warnings: list[QualityWarning] = []

    for preference in requirements.adjacency:
        weight = 2.0 if preference.strength == "must" else 1.0
        possible += weight
        a_rooms = grouped.get(preference.room_a, [])
        b_rooms = grouped.get(preference.room_b, [])
        satisfied = bool(a_rooms and b_rooms) and _pair_is_adjacent(a_rooms, b_rooms)
        if satisfied:
            earned += weight
            continue
        a_label = preference.room_a.value.replace("_", " ").title()
        b_label = preference.room_b.value.replace("_", " ").title()
        qualifier = "must share a wall" if preference.strength == "must" else "would work better beside"
        warnings.append(
            QualityWarning(
                code=f"generic.adjacency.{preference.strength}",
                message=f"{a_label} {qualifier} {b_label}.",
                severity="warn" if preference.strength == "must" else "info",
            )
        )

    for pair in requirements.avoid_adjacency:
        possible += 2.0
        a_rooms = grouped.get(pair.room_a, [])
        b_rooms = grouped.get(pair.room_b, [])
        violates = bool(a_rooms and b_rooms) and _pair_is_adjacent(a_rooms, b_rooms)
        if not violates:
            earned += 2.0
            continue
        a_label = pair.room_a.value.replace("_", " ").title()
        b_label = pair.room_b.value.replace("_", " ").title()
        warnings.append(
            QualityWarning(
                code="generic.adjacency.avoid",
                message=f"{a_label} should be separated from {b_label}.",
            )
        )

    return SoftRuleResult(
        name="adjacency",
        score=earned / possible if possible else 1.0,
        warnings=warnings,
    )


def privacy_rule(plan: LayoutPlan, _requirements: RequirementsSpec) -> SoftRuleResult:
    entries = [room for room in plan.rooms if room.type == RoomType.entry]
    private_rooms = [
        room
        for room in plan.rooms
        if room.type in {RoomType.bedroom, RoomType.master_bedroom}
    ]
    if not entries or not private_rooms:
        return SoftRuleResult(name="privacy", score=1.0)

    warnings: list[QualityWarning] = []
    protected = 0
    for room in private_rooms:
        if any(_share_wall(entry, room) for entry in entries):
            warnings.append(
                QualityWarning(
                    code="generic.privacy_entry",
                    message=f"{room.label} opens too directly onto the Entry; add a buffer space.",
                )
            )
        else:
            protected += 1
    return SoftRuleResult(
        name="privacy",
        score=protected / len(private_rooms),
        warnings=warnings,
    )


def _touches_plot_edge(room: PlanRoom, plan: LayoutPlan) -> bool:
    return (
        room.x <= EPS
        or room.y <= EPS
        or room.x + room.w >= plan.plot.width_m - EPS
        or room.y + room.h >= plan.plot.depth_m - EPS
    )


def natural_light_rule(plan: LayoutPlan, _requirements: RequirementsSpec) -> SoftRuleResult:
    daylight_rooms = [
        room
        for room in plan.rooms
        if room.type
        in {
            RoomType.bedroom,
            RoomType.master_bedroom,
            RoomType.living_room,
            RoomType.kitchen,
        }
    ]
    if not daylight_rooms:
        return SoftRuleResult(name="natural_light", score=1.0)

    lit = [room for room in daylight_rooms if _touches_plot_edge(room, plan)]
    warnings = [
        QualityWarning(
            code="generic.natural_light",
            message=f"{room.label} has no exterior edge for a daylight opening.",
            severity="info",
        )
        for room in daylight_rooms
        if room not in lit
    ]
    return SoftRuleResult(
        name="natural_light",
        score=len(lit) / len(daylight_rooms),
        warnings=warnings,
    )


def bath_kitchen_rule(plan: LayoutPlan, _requirements: RequirementsSpec) -> SoftRuleResult:
    kitchens = [room for room in plan.rooms if room.type == RoomType.kitchen]
    bathrooms = [room for room in plan.rooms if room.type == RoomType.bathroom]
    if not kitchens or not bathrooms:
        return SoftRuleResult(name="bath_kitchen", score=1.0)

    touching = [
        (kitchen, bathroom)
        for kitchen in kitchens
        for bathroom in bathrooms
        if _share_wall(kitchen, bathroom)
    ]
    warnings = [
        QualityWarning(
            code="generic.bath_kitchen_separation",
            message=f"{bathroom.label} shares a wall with {kitchen.label}; add a service buffer where practical.",
        )
        for kitchen, bathroom in touching
    ]
    possible = len(kitchens) * len(bathrooms)
    return SoftRuleResult(
        name="bath_kitchen",
        score=(possible - len(touching)) / possible,
        warnings=warnings,
    )


def evaluate_generic_rules(
    plan: LayoutPlan,
    requirements: RequirementsSpec,
) -> list[SoftRuleResult]:
    """Stable rule order keeps identical input byte-for-byte deterministic."""

    return [
        adjacency_rule(plan, requirements),
        privacy_rule(plan, requirements),
        natural_light_rule(plan, requirements),
        bath_kitchen_rule(plan, requirements),
    ]
