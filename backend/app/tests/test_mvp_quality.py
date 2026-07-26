"""Workflow Phase 6 — canonical soft scoring and data-driven Vastu."""

from pathlib import Path

from app.schemas.layout_plan import Door, LayoutPlan, PlanPlot, PlanRoom, Wall
from app.schemas.requirements import RequirementsSpec, RoomType
from app.services.quality.scorer import score
from app.services.quality.vastu import evaluate_vastu, sector_for_room


FIXTURES = Path(__file__).parent / "fixtures" / "requirements"


def _spec(name: str = "3bhk_adjacencies") -> RequirementsSpec:
    return RequirementsSpec.model_validate_json(
        (FIXTURES / f"{name}.json").read_text(encoding="utf-8")
    )


def _room(
    room_id: str,
    room_type: RoomType,
    x: float,
    y: float,
    w: float,
    h: float,
) -> PlanRoom:
    return PlanRoom(
        id=room_id,
        type=room_type,
        label=room_type.value.replace("_", " ").title(),
        x=x,
        y=y,
        w=w,
        h=h,
    )


def _three_room_plan(*, kitchen_next_to_dining: bool) -> LayoutPlan:
    """Valid access graph in both variants; only kitchen/dining adjacency changes."""

    kitchen_x = 1.5 if kitchen_next_to_dining else 0.0
    entry_x = 0.0 if kitchen_next_to_dining else 3.0
    dining_x = 4.5
    rooms = [
        _room("entry", RoomType.entry, entry_x, 0, 1.5, 3),
        _room("kitchen", RoomType.kitchen, kitchen_x, 0, 3, 3),
        _room("dining", RoomType.dining, dining_x, 0, 3, 3),
    ]
    walls = [
        Wall(id="w-entry-kitchen", x1=1.5 if kitchen_next_to_dining else 3, y1=0, x2=1.5 if kitchen_next_to_dining else 3, y2=3),
        Wall(id="w-second", x1=4.5, y1=0, x2=4.5, y2=3),
    ]
    doors = [
        Door(id="d1", wall_ref="w-entry-kitchen", offset=1.0, width=0.9),
        Door(id="d2", wall_ref="w-second", offset=1.0, width=0.9),
    ]
    return LayoutPlan(
        plot=PlanPlot(width_m=7.5, depth_m=3, facing="east"),
        rooms=rooms,
        walls=walls,
        doors=doors,
    )


def test_weighted_scorer_returns_a_bounded_full_report():
    requirements = RequirementsSpec.model_validate(
        {
            "rooms": [
                {"type": "kitchen", "count": 1},
                {"type": "dining", "count": 1},
                {"type": "entry", "count": 1},
            ],
            "adjacency": [
                {"room_a": "kitchen", "room_b": "dining", "strength": "must"}
            ],
            "plot": {"width_m": 7.5, "depth_m": 3},
            "facing": "east",
        }
    )

    report = score(_three_room_plan(kitchen_next_to_dining=True), requirements)

    assert 0 <= report.score <= 100
    assert report.hard_violations == []
    assert all(warning.rule in {"generic", "vastu"} for warning in report.warnings)


def test_fixing_a_must_adjacency_never_lowers_the_score():
    requirements = RequirementsSpec.model_validate(
        {
            "rooms": [
                {"type": "kitchen", "count": 1},
                {"type": "dining", "count": 1},
                {"type": "entry", "count": 1},
            ],
            "adjacency": [
                {"room_a": "kitchen", "room_b": "dining", "strength": "must"}
            ],
            "plot": {"width_m": 7.5, "depth_m": 3},
            "facing": "east",
        }
    )

    separated = score(_three_room_plan(kitchen_next_to_dining=False), requirements)
    adjacent = score(_three_room_plan(kitchen_next_to_dining=True), requirements)

    assert adjacent.score > separated.score
    assert any("Kitchen" in warning.message and "Dining" in warning.message for warning in separated.warnings)


def test_bathroom_beside_kitchen_emits_a_human_warning():
    plan = LayoutPlan(
        plot=PlanPlot(width_m=5.4, depth_m=3, facing="east"),
        rooms=[
            _room("kitchen", RoomType.kitchen, 0, 0, 3, 3),
            _room("bathroom", RoomType.bathroom, 3, 0, 2.4, 3),
        ],
        walls=[Wall(id="shared", x1=3, y1=0, x2=3, y2=3)],
        doors=[Door(id="door", wall_ref="shared", offset=1.0, width=0.9)],
    )
    requirements = RequirementsSpec.model_validate(
        {
            "rooms": [
                {"type": "kitchen", "count": 1},
                {"type": "bathroom", "count": 1},
            ],
            "plot": {"width_m": 5.4, "depth_m": 3},
            "facing": "east",
        }
    )

    report = score(plan, requirements)

    assert any(
        warning.code == "generic.bath_kitchen_separation"
        and "Kitchen" in warning.message
        and "Bathroom" in warning.message
        for warning in report.warnings
    )


def test_hard_violations_cap_the_quality_score():
    valid = _three_room_plan(kitchen_next_to_dining=True)
    overlapping = valid.model_copy(
        update={
            "rooms": [
                valid.rooms[0],
                valid.rooms[1].model_copy(update={"x": valid.rooms[0].x}),
                valid.rooms[2],
            ]
        }
    )
    requirements = RequirementsSpec.model_validate(
        {
            "rooms": [
                {"type": "entry", "count": 1},
                {"type": "kitchen", "count": 1},
                {"type": "dining", "count": 1},
            ]
        }
    )

    report = score(overlapping, requirements)

    assert report.hard_violations
    assert report.score <= 49


def test_vastu_rules_are_external_data_and_southeast_kitchen_scores_higher():
    plot = PlanPlot(width_m=9, depth_m=12, facing="east")
    northeast = _room("kitchen-ne", RoomType.kitchen, 6, 0, 3, 3)
    southeast = northeast.model_copy(update={"id": "kitchen-se", "y": 9})

    ne_result = evaluate_vastu(
        LayoutPlan(plot=plot, rooms=[northeast], walls=[], doors=[])
    )
    se_result = evaluate_vastu(
        LayoutPlan(plot=plot, rooms=[southeast], walls=[], doors=[])
    )

    assert sector_for_room(northeast, plot) == "northeast"
    assert sector_for_room(southeast, plot) == "southeast"
    assert se_result.score > ne_result.score
    assert any(warning.code == "vastu.kitchen.northeast" for warning in ne_result.warnings)
    assert all(warning.rule == "vastu" for warning in ne_result.warnings)


def test_vastu_is_opt_in_at_the_weighted_scorer_boundary():
    plan = _three_room_plan(kitchen_next_to_dining=True)
    requirements = RequirementsSpec.model_validate(
        {
            "rooms": [
                {"type": "entry", "count": 1},
                {"type": "kitchen", "count": 1},
                {"type": "dining", "count": 1},
            ]
        }
    )

    default_report = score(plan, requirements)
    vastu_report = score(plan, requirements, include_vastu=True)

    assert all(warning.rule != "vastu" for warning in default_report.warnings)
    assert any(warning.rule == "vastu" for warning in vastu_report.warnings)
