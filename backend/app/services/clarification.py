"""Deterministic clarification and default handling for the MVP workflow.

The extraction model reports facts through :class:`RequirementsSpec`; this
module decides whether those validated facts are sufficient to generate.  It
does not ask the model for confidence and it never mutates the input spec.

Only an empty room program blocks a vague request.  Plot size, facing, and
bathroom count are optional because each has an explicit product default.
Conflicting requirements and a layout-engine ``DoesNotFitError`` require a
human choice before generation continues.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.config.mvp_defaults import (
    DEFAULT_FACING,
    DEFAULT_PLOT_DEPTH_M,
    DEFAULT_PLOT_WIDTH_M,
)
from app.schemas.requirements import PlotSpec, RequirementsSpec, RoomRequest, RoomType
from app.services.layout_engine.engine import DoesNotFitError


ROOM_PROGRAM_QUESTION = "What spaces do you need, and how many of each?"
PLOT_SIZE_QUESTION = (
    "What plot size should I use (width × depth, in metres or feet)?"
)
FACING_QUESTION = (
    "Which direction should the main entrance face (north, south, east, or west)?"
)
BATHROOM_QUESTION = "How many bathrooms should the layout include?"

class ClarificationResult(BaseModel):
    """A deterministic decision for the API/UI orchestration layer."""

    model_config = ConfigDict(frozen=True)

    route: Literal["vague", "generate", "conflict"]
    questions: list[str] = Field(default_factory=list)
    optional_missing: list[str] = Field(default_factory=list)


class DefaultsApplication(BaseModel):
    """A defaulted requirements snapshot plus plain-language assumptions."""

    model_config = ConfigDict(frozen=True)

    requirements: RequirementsSpec
    defaults_applied: list[str] = Field(default_factory=list)


class ClarificationRequiredError(ValueError):
    """Defaults cannot replace a missing program or resolve a contradiction."""


def _room_count(spec: RequirementsSpec, room_type: RoomType) -> int:
    return sum(room.count for room in spec.rooms if room.type == room_type)


def _has_room_program(spec: RequirementsSpec) -> bool:
    return sum(room.count for room in spec.rooms) > 0


def _optional_questions(spec: RequirementsSpec) -> list[str]:
    questions: list[str] = []
    if spec.plot.width_m is None or spec.plot.depth_m is None:
        questions.append(PLOT_SIZE_QUESTION)
    if spec.facing is None:
        questions.append(FACING_QUESTION)
    if _room_count(spec, RoomType.bathroom) == 0:
        questions.append(BATHROOM_QUESTION)
    return questions


def _conflict_details(spec: RequirementsSpec) -> list[str]:
    details: list[str] = []
    for item in spec.missing_info:
        prefix, separator, detail = item.partition(":")
        if separator and prefix.strip().casefold() == "conflict" and detail.strip():
            details.append(detail.strip())
    return details


def _fit_question(error: DoesNotFitError) -> str:
    if error.required_area is not None and error.plot_area is not None:
        required = _format_number(error.required_area)
        available = _format_number(error.plot_area)
        return (
            "The plot is too small for the requested program "
            f"(about {required} m² required and {available} m² available). "
            "Would you like to increase the plot or reduce the room program?"
        )
    detail = str(error).strip()
    return (
        f"The requested program cannot be generated: {detail}. "
        "Would you like to adjust the plot or room program?"
    )


def assess(
    spec: RequirementsSpec,
    *,
    fit_error: DoesNotFitError | None = None,
) -> ClarificationResult:
    """Route a validated requirement set to vague, generate, or conflict.

    An empty program wins over stale/confused conflict text so junk and prompt
    injection attempts receive useful guided questions rather than a dead-end
    conflict screen.
    """

    optional_questions = _optional_questions(spec)
    if not _has_room_program(spec):
        return ClarificationResult(
            route="vague",
            questions=[ROOM_PROGRAM_QUESTION, *optional_questions],
        )

    conflict_questions = [
        f"I found conflicting requirements: {detail}. Which requirement should I use?"
        for detail in _conflict_details(spec)
    ]
    if fit_error is not None:
        conflict_questions.append(_fit_question(fit_error))

    if conflict_questions:
        return ClarificationResult(route="conflict", questions=conflict_questions)

    return ClarificationResult(
        route="generate",
        optional_missing=optional_questions,
    )


def _format_number(value: float) -> str:
    return f"{value:g}"


def _resolved_missing_info(
    missing_info: list[str],
    *,
    plot_complete: bool,
    facing_complete: bool,
    bathroom_complete: bool,
) -> list[str]:
    resolved: set[str] = set()
    if plot_complete:
        resolved.add("plot_size")
    if facing_complete:
        resolved.add("facing")
    if bathroom_complete:
        resolved.add("bathroom_count")

    return [
        item
        for item in missing_info
        if item.strip().casefold() not in resolved
    ]


def apply_defaults_with_report(spec: RequirementsSpec) -> DefaultsApplication:
    """Return a defaulted copy and user-readable assumptions.

    Field values, rather than ``missing_info``, decide what needs a default.
    This makes the function robust to stale model metadata while preserving all
    explicit user values.
    """

    decision = assess(spec)
    if decision.route != "generate":
        raise ClarificationRequiredError(
            "Defaults can only fill optional information after the room program "
            "is present and conflicts are resolved."
        )

    defaults_applied: list[str] = []

    width = spec.plot.width_m
    depth = spec.plot.depth_m
    if width is None or depth is None:
        width = width if width is not None else DEFAULT_PLOT_WIDTH_M
        depth = depth if depth is not None else DEFAULT_PLOT_DEPTH_M
        defaults_applied.append(
            f"{_format_number(width)}\u00d7{_format_number(depth)} m plot"
        )

    facing = spec.facing
    if facing is None:
        facing = DEFAULT_FACING
        defaults_applied.append(f"{facing.value} facing")

    rooms = [room.model_copy(deep=True) for room in spec.rooms]
    bathroom_count = _room_count(spec, RoomType.bathroom)
    if bathroom_count == 0:
        bedroom_count = (
            _room_count(spec, RoomType.bedroom)
            + _room_count(spec, RoomType.master_bedroom)
        )
        bathroom_count = max(1, bedroom_count - 1)
        rooms.append(RoomRequest(type=RoomType.bathroom, count=bathroom_count))
        noun = "bathroom" if bathroom_count == 1 else "bathrooms"
        defaults_applied.append(f"{bathroom_count} {noun}")

    missing_info = _resolved_missing_info(
        spec.missing_info,
        plot_complete=width is not None and depth is not None,
        facing_complete=facing is not None,
        bathroom_complete=bathroom_count > 0,
    )

    requirements = spec.model_copy(
        update={
            "plot": PlotSpec(width_m=width, depth_m=depth),
            "facing": facing,
            "rooms": rooms,
            "missing_info": missing_info,
        },
        deep=True,
    )
    return DefaultsApplication(
        requirements=requirements,
        defaults_applied=defaults_applied,
    )


def apply_defaults(spec: RequirementsSpec) -> RequirementsSpec:
    """Compatibility helper returning only the defaulted requirements object."""

    return apply_defaults_with_report(spec).requirements
