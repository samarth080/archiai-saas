"""Workflow Phase 6: weighted soft quality and data-driven Vastu."""

from pathlib import Path

import pytest

from app.schemas.layout_plan import Door, LayoutPlan, PlanPlot, PlanRoom, Wall
from app.schemas.requirements import RequirementsSpec, RoomRequest, RoomType
from app.services.quality.hard_constraints import validate
from app.services.quality.scorer import score
from app.services.quality.soft_rules import adjacency_rule, bath_kitchen_rule
from app.services.quality.vastu import evaluate_vastu, sector_for_room


RULES_PATH = Path(__file__).parents[1] / "services" / "quality" / "vastu_rules.json"


def _room(
    room_id: str,
    room_type: RoomType,
    label: str,
    x: float,
    y: float,
    w: float,
    h: float,
) -> PlanRoom:
    return PlanRoom(
        id=room_id,
        type=room_type,
        label=label,
        x=x,
        y=y,
        w=w,
        h=h,
    )


def _adjacency_plan(*, kitchen_next_to_dining: bool) -> LayoutPlan:
    kitchen = _room("k", RoomType.kitchen, "Kitchen", 0, 0, 3, 3)
    if kitchen_next_to_dining:
        entry = _room("e", RoomType.entry, "Entry", 6, 0, 1.5, 3)
        dining = _room("d", RoomType.dining, "Dining", 3, 0, 3, 3)
        walls = [
            Wall(id="w-kd", x1=3, y1=0, x2=3, y2=3),
            Wall(id="w-de", x1=6, y1=0, x2=6, y2=3),
        ]
        doors = [
            Door(id="door-kd", wall_ref="w-kd", offset=1.0),
            Door(id="door-de", wall_ref="w-de", offset=1.0),
        ]
    else:
        entry = _room("e", RoomType.entry, "Entry", 3, 0, 1.5, 3)
        dining = _room("d", RoomType.dining, "Dining", 4.5, 0, 3, 3)
        walls = [
            Wall(id="w-ke", x1=3, y1=0, x2=3, y2=3),
            Wall(id="w-ed", x1=4.5, y1=0, x2=4.5, y2=3),
        ]
        doors = [
            Door(id="door-ke", wall_ref="w-ke", offset=1.0),
            Door(id="door-ed", wall_ref="w-ed", offset=1.0),
        ]
    return LayoutPlan(
        plot=PlanPlot(width_m=7.5, depth_m=3, facing="east"),
        rooms=[kitchen, dining, entry],
        walls=walls,
        doors=doors,
    )


def _adjacency_spec() -> RequirementsSpec:
    return RequirementsSpec.model_validate(
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


def test_vastu_rules_are_committed_data_not_hardcoded_python():
    assert RULES_PATH.exists()
    assert '"room_type": "kitchen"' in RULES_PATH.read_text(encoding="utf-8")


def test_fixing_must_adjacency_improves_the_rule_and_total_score():
    spec = _adjacency_spec()
    separated = _adjacency_plan(kitchen_next_to_dining=False)
    adjacent = _adjacency_plan(kitchen_next_to_dining=True)

    separated_rule = adjacency_rule(separated, spec)
    adjacent_rule = adjacency_rule(adjacent, spec)

    assert separated_rule.score == 0
    assert adjacent_rule.score == 1
    assert score(adjacent, spec).score > score(separated, spec).score


def test_bathroom_beside_kitchen_emits_a_human_warning_with_room_names():
    plan = LayoutPlan(
        plot=PlanPlot(width_m=6, depth_m=3),
        rooms=[
            _room("k", RoomType.kitchen, "Family Kitchen", 0, 0, 3, 3),
            _room("b", RoomType.bathroom, "Guest Bathroom", 3, 0, 3, 3),
        ],
    )

    result = bath_kitchen_rule(plan, RequirementsSpec())

    assert result.score == 0
    assert len(result.warnings) == 1
    assert "Family Kitchen" in result.warnings[0].message
    assert "Guest Bathroom" in result.warnings[0].message


def test_hard_violations_cap_the_report_below_a_valid_quality_score():
    spec = _adjacency_spec()
    valid = _adjacency_plan(kitchen_next_to_dining=True)
    overlap = valid.rooms[1].model_copy(update={"x": valid.rooms[0].x})
    broken = valid.model_copy(
        update={
            "rooms": [valid.rooms[0], overlap, valid.rooms[2]],
        }
    )

    report = score(broken, spec)

    assert report.hard_violations
    assert report.score <= 49


def test_missing_requested_bedroom_is_a_hard_violation_not_a_soft_warning():
    """Packet 7.1 — prompt-to-program truth gate: the engine always places every
    requested room (test_mvp_engine.py pins that), so a shortfall here only
    happens if requirements were wrong going in, or an edit dropped a room. Either
    way quality must not call the layout satisfactory."""
    spec = RequirementsSpec(
        rooms=[RoomRequest(type=RoomType.bedroom, count=2)]
    )
    plan = LayoutPlan(
        plot=PlanPlot(width_m=6, depth_m=6),
        rooms=[_room("b1", RoomType.bedroom, "Bedroom 1", 0, 0, 3, 3)],
    )

    violations = validate(plan, spec)
    assert [v.code for v in violations] == ["missing_requested_room"]

    report = score(plan, spec)
    assert report.hard_violations
    assert report.score <= 49


def test_validate_without_requirements_stays_geometry_only():
    plan = LayoutPlan(
        plot=PlanPlot(width_m=6, depth_m=6),
        rooms=[_room("b1", RoomType.bedroom, "Bedroom 1", 0, 0, 3, 3)],
    )

    assert validate(plan) == []
    assert validate(plan, None) == []


def test_kitchen_scores_better_in_southeast_than_northeast():
    plot = PlanPlot(width_m=9, depth_m=12, facing="east")
    northeast = _room("k", RoomType.kitchen, "Kitchen", 6, 0, 3, 3)
    southeast = northeast.model_copy(update={"y": 9})

    bad = evaluate_vastu(LayoutPlan(plot=plot, rooms=[northeast]))
    good = evaluate_vastu(LayoutPlan(plot=plot, rooms=[southeast]))

    assert sector_for_room(northeast, plot) == "northeast"
    assert sector_for_room(southeast, plot) == "southeast"
    assert good.score > bad.score
    assert any(warning.code == "vastu.kitchen_northeast" for warning in bad.warnings)


def test_vastu_stays_opt_in_at_the_weighted_scorer_boundary():
    spec = _adjacency_spec()
    plan = _adjacency_plan(kitchen_next_to_dining=True)

    default_report = score(plan, spec)
    vastu_report = score(plan, spec, include_vastu=True)

    assert all(warning.rule != "vastu" for warning in default_report.warnings)
    assert any(warning.rule == "vastu" for warning in vastu_report.warnings)


@pytest.mark.parametrize(
    ("x", "y", "expected"),
    [
        (0, 0, "northwest"),
        (3, 0, "north"),
        (6, 0, "northeast"),
        (0, 4, "west"),
        (3, 4, "center"),
        (6, 4, "east"),
        (0, 8, "southwest"),
        (3, 8, "south"),
        (6, 8, "southeast"),
    ],
)
def test_sector_grid_is_north_up_for_every_plot_cell(x: float, y: float, expected: str):
    plot = PlanPlot(width_m=9, depth_m=12, facing="west")
    room = _room("r", RoomType.study, "Study", x, y, 3, 4)
    assert sector_for_room(room, plot) == expected
