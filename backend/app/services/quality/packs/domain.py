"""Geometry-only rules for non-residential quality packs."""

from statistics import fmean

from app.schemas.layout_plan import LayoutPlan, PlanRoom
from app.schemas.quality_report import QualityWarning
from app.schemas.requirements import RequirementsSpec
from app.services.quality.soft_rules import SoftRuleResult, rooms_share_wall
from app.services.layout_engine.polygon import room_area

_CONSULTATION_TYPES = {"consultation_room", "exam_room", "treatment_room"}
_WAITING_TYPES = {"waiting_room", "waiting_area"}
_MEETING_TYPES = {"meeting_room", "conference_room"}
_WORKSPACE_TYPES = {"open_workspace", "workspace", "coworking_area", "office"}
_REPEAT_TYPES = {"classroom", "hotel_room", "guest_room"}


def _of_type(plan: LayoutPlan, types: set[str]) -> list[PlanRoom]:
    return [room for room in plan.rooms if room.type in types]


def consultation_privacy_rule(
    plan: LayoutPlan,
    _requirements: RequirementsSpec,
) -> SoftRuleResult:
    consultations = _of_type(plan, _CONSULTATION_TYPES)
    waiting = _of_type(plan, _WAITING_TYPES)
    if not consultations or not waiting:
        return SoftRuleResult(name="consultation_privacy", score=1.0)

    exposed = [
        room
        for room in consultations
        if any(rooms_share_wall(room, public_room) for public_room in waiting)
    ]
    return SoftRuleResult(
        name="consultation_privacy",
        score=(len(consultations) - len(exposed)) / len(consultations),
        warnings=[
            QualityWarning(
                code="healthcare.consultation_privacy",
                message=(
                    f"{room.label} directly adjoins the waiting area; add a "
                    "privacy buffer or guarded corridor."
                ),
            )
            for room in exposed
        ],
    )


def meeting_access_rule(
    plan: LayoutPlan,
    _requirements: RequirementsSpec,
) -> SoftRuleResult:
    meetings = _of_type(plan, _MEETING_TYPES)
    workspaces = _of_type(plan, _WORKSPACE_TYPES)
    if not meetings or not workspaces:
        return SoftRuleResult(name="meeting_access", score=1.0)

    disconnected = [
        room
        for room in meetings
        if not any(rooms_share_wall(room, workspace) for workspace in workspaces)
    ]
    return SoftRuleResult(
        name="meeting_access",
        score=(len(meetings) - len(disconnected)) / len(meetings),
        warnings=[
            QualityWarning(
                code="workplace.meeting_access",
                message=f"{room.label} should open from the main workspace or its circulation edge.",
            )
            for room in disconnected
        ],
    )


def repeat_unit_uniformity_rule(
    plan: LayoutPlan,
    _requirements: RequirementsSpec,
) -> SoftRuleResult:
    groups = [
        rooms
        for room_type in _REPEAT_TYPES
        if len(rooms := _of_type(plan, {room_type})) >= 3
    ]
    if not groups:
        return SoftRuleResult(name="repeat_unit_uniformity", score=1.0)

    scores: list[float] = []
    warnings: list[QualityWarning] = []
    for rooms in groups:
        areas = [room_area(room) for room in rooms]
        spread = (max(areas) - min(areas)) / fmean(areas)
        scores.append(max(0.0, 1.0 - spread))
        if spread > 0.2:
            label = rooms[0].type.replace("_", " ")
            warnings.append(
                QualityWarning(
                    code="hospitality_edu.repeat_unit_uniformity",
                    message=f"{label.title()} areas vary by more than 20%; rebalance the repeat units.",
                )
            )
    return SoftRuleResult(
        name="repeat_unit_uniformity",
        score=fmean(scores),
        warnings=warnings,
    )
