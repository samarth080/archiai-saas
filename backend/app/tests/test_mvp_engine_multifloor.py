"""Workflow Phase 7 canonical multi-floor generation."""

from app.schemas.requirements import RequirementsSpec
from app.services.layout_engine import generate_plan
from app.services.layout_engine.search import best_candidate
from app.services.quality.hard_constraints import validate


def _two_storey() -> RequirementsSpec:
    return RequirementsSpec.model_validate({
        "building_type": "duplex",
        "floors": 2,
        "rooms": [
            {"type": "living_room", "count": 1},
            {"type": "kitchen", "count": 1},
            {"type": "bedroom", "count": 3},
            {"type": "bathroom", "count": 2},
        ],
        "plot": {"width_m": 12, "depth_m": 14},
        "facing": "east",
    })


def _hotel() -> RequirementsSpec:
    return RequirementsSpec.model_validate({
        "building_type": "other",
        "floors": 3,
        "spaces": [
            {"space_type": "reception", "count": 1},
            {"space_type": "waiting_room", "count": 1},
            {"space_type": "dining_room", "count": 1},
            {"space_type": "kitchen", "count": 1},
            {"space_type": "bedroom", "count": 6},
            {"space_type": "bathroom", "count": 3},
        ],
        "plot": {"width_m": 16, "depth_m": 20},
        "facing": "south",
    })


def _footprints(plan, room_type: str):
    return {
        (room.x, room.y, room.w, room.h)
        for room in plan.rooms
        if room.type == room_type
    }


def test_two_storey_home_splits_day_and_night_zones_and_stays_valid():
    spec = _two_storey()

    plan = generate_plan(spec)

    assert validate(plan, spec) == []
    assert {room.floor for room in plan.rooms} == {0, 1}
    assert {
        room.type for room in plan.rooms if room.floor == 0
    } >= {"entry", "living_room", "kitchen"}
    assert {
        room.type for room in plan.rooms if room.floor == 1
    } >= {"bedroom"}
    assert all(
        room.floor == 1
        for room in plan.rooms
        if room.type == "bedroom"
    )


def test_staircases_are_exactly_aligned_and_geometry_ids_are_unique():
    plan = generate_plan(_two_storey())

    stairs = [room for room in plan.rooms if room.type == "staircase"]
    assert len(stairs) == 2
    assert _footprints(plan, "staircase") == {(0.0, 0.0, 1.2, 2.4)}
    assert len({room.id for room in plan.rooms}) == len(plan.rooms)
    assert len({wall.id for wall in plan.walls}) == len(plan.walls)
    assert len({door.id for door in plan.doors}) == len(plan.doors)

    walls = {wall.id: wall for wall in plan.walls}
    assert all(
        door.floor == walls[door.wall_ref].floor
        for door in plan.doors
    )


def test_three_floor_hotel_program_gets_aligned_stairs_and_lifts():
    spec = _hotel()

    plan = generate_plan(spec)

    assert validate(plan, spec) == []
    assert _footprints(plan, "staircase") == {(0.0, 0.0, 1.8, 2.4)}
    assert _footprints(plan, "lift") == {(0.0, 2.4, 1.8, 1.8)}
    assert len([room for room in plan.rooms if room.type == "staircase"]) == 3
    assert len([room for room in plan.rooms if room.type == "lift"]) == 3
    assert all(
        room.floor == 0
        for room in plan.rooms
        if room.type in {"reception", "waiting_room", "dining_room", "kitchen", "entry"}
    )


def test_candidate_entrypoint_dispatches_multi_floor_to_the_proven_path():
    spec = _two_storey()

    assert best_candidate(spec) == generate_plan(spec)


def test_hard_validator_rejects_a_misaligned_staircase():
    spec = _two_storey()
    plan = generate_plan(spec)
    shifted = [
        room.model_copy(update={"x": room.x + 0.5})
        if room.type == "staircase" and room.floor == 1
        else room
        for room in plan.rooms
    ]

    violations = validate(plan.model_copy(update={"rooms": shifted}), spec)

    assert any(violation.code == "staircase_alignment" for violation in violations)


def test_hard_validator_rejects_a_missing_intermediate_floor():
    spec = _hotel()
    plan = generate_plan(spec)
    without_first_floor = plan.model_copy(update={
        "rooms": [room for room in plan.rooms if room.floor != 1],
    })

    violations = validate(without_first_floor, spec)

    assert any(violation.code == "staircase_alignment" for violation in violations)
