"""Workflow Steps 1.2 + 1.3 — engine invariants, hand-broken plans, and the
project's main go/no-go gate: the Hypothesis property suite (zero hard
violations over the random spec space; DoesNotFitError is the only permitted
alternative outcome, per the workflow's structured "plot too small" contract).
"""
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.schemas.layout_plan import LayoutPlan
from app.schemas.requirements import Facing, RequirementsSpec, RoomType
from app.services.layout_engine import (
    DoesNotFitError,
    generate_plan,
    rebuild_derived_geometry,
)
from app.services.layout_engine.geometry import Rect
from app.services.quality import validate

FIXTURES = Path(__file__).parent / "fixtures" / "requirements"
FIXTURE_NAMES = ["1bhk", "2bhk", "3bhk_adjacencies", "4bhk", "clinic"]


def _load(name: str) -> RequirementsSpec:
    return RequirementsSpec.model_validate_json((FIXTURES / f"{name}.json").read_text())


def _room_rect(room) -> Rect:
    return Rect(room.x, room.y, room.w, room.h)


# ── Step 1.2 — fixture invariants (never exact coordinates) ──────────────────


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_produces_valid_plan(name):
    spec = _load(name)
    plan = generate_plan(spec)

    requested = sum(r.count for r in spec.rooms)
    has_entry = any(r.type == RoomType.entry for r in spec.rooms)
    assert len(plan.rooms) == requested + (0 if has_entry else 1)  # auto-entry

    for spec_room in spec.rooms:  # every requested room type present, right count
        placed = [r for r in plan.rooms if r.type == spec_room.type]
        assert len(placed) == spec_room.count, spec_room.type

    assert validate(plan) == []  # zero hard violations: overlap/bounds/min/reachability


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_plan_fills_plot_exactly(name):
    plan = generate_plan(_load(name))
    total = sum(r.w * r.h for r in plan.rooms)
    assert total == pytest.approx(plan.plot.width_m * plan.plot.depth_m, rel=0.01)


def test_entry_lands_on_the_facing_side():
    plan = generate_plan(_load("3bhk_adjacencies"))  # east-facing
    entry = next(r for r in plan.rooms if r.type == RoomType.entry)
    assert entry.x + entry.w / 2 > plan.plot.width_m / 2  # east half


def test_attached_bathroom_touches_master_bedroom():
    plan = generate_plan(_load("3bhk_adjacencies"))  # master-bathroom `must`
    master = next(r for r in plan.rooms if r.type == RoomType.master_bedroom)
    baths = [r for r in plan.rooms if r.type == RoomType.bathroom]
    assert any(_room_rect(master).shared_edge(_room_rect(b)) for b in baths)


def test_walls_are_deduplicated():
    plan = generate_plan(_load("2bhk"))
    seen = set()
    for w in plan.walls:
        key = (round(w.x1, 2), round(w.y1, 2), round(w.x2, 2), round(w.y2, 2))
        assert key not in seen, f"duplicate wall segment {key}"
        seen.add(key)


def test_doors_reference_existing_walls():
    plan = generate_plan(_load("4bhk"))
    wall_ids = {w.id for w in plan.walls}
    assert plan.doors, "a plan must have doors"
    for door in plan.doors:
        assert door.wall_ref in wall_ids


def test_engine_is_deterministic():
    a = generate_plan(_load("3bhk_adjacencies"))
    b = generate_plan(_load("3bhk_adjacencies"))
    assert a == b


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_room_ids_follow_the_legacy_r_n_scheme(name):
    # Phase 2.2b: _expand() now builds needs via the ProgramGraph bridge
    # instead of a flat dict-counting loop, and remaps the graph's own
    # node ids ("node-3") back to this "r1".."rN" scheme. Not cosmetic —
    # _place_doors's BFS spanning tree tie-breaks on the lexicographic sort
    # of room keys, so a different id scheme can silently change *which*
    # doors get placed for a fixture with real adjacency ambiguity (caught
    # by diffing 4bhk/3bhk_adjacencies against a pre-refactor snapshot: the
    # node-id scheme produced a different door set, not just different ids).
    plan = generate_plan(_load(name))
    assert {r.id for r in plan.rooms} == {f"r{i}" for i in range(1, len(plan.rooms) + 1)}


def test_rebuild_derived_geometry_restores_generated_plan_artifacts():
    spec = _load("2bhk")
    plan = generate_plan(spec)
    stale = plan.model_copy(update={"walls": [], "doors": []})

    rebuilt = rebuild_derived_geometry(stale, spec)

    assert rebuilt == plan
    assert validate(rebuilt) == []


def test_rebuild_derived_geometry_reports_disconnected_edits_without_raising():
    spec = _load("2bhk")
    plan = generate_plan(spec)
    bedroom = next(room for room in plan.rooms if room.type == RoomType.bedroom)
    moved = bedroom.model_copy(
        update={
            "x": bedroom.x + 0.2,
            "y": bedroom.y + 0.2,
            "w": bedroom.w - 0.4,
            "h": bedroom.h - 0.4,
        }
    )
    edited = plan.model_copy(
        update={
            "rooms": [
                moved if room.id == bedroom.id else room for room in plan.rooms
            ],
        }
    )

    rebuilt = rebuild_derived_geometry(edited, spec)

    assert "unreachable" in _codes(rebuilt)


def test_too_many_rooms_for_plot_raises_structured_does_not_fit():
    spec = RequirementsSpec.model_validate({
        "rooms": [
            {"type": "bedroom", "count": 4},
            {"type": "bathroom", "count": 2},
            {"type": "kitchen", "count": 1},
            {"type": "living_room", "count": 1},
        ],
        "plot": {"width_m": 6.0, "depth_m": 7.0},
    })
    with pytest.raises(DoesNotFitError) as exc:
        generate_plan(spec)
    assert "increase plot size" in str(exc.value)


def test_single_room_spec_works():
    spec = RequirementsSpec.model_validate({"rooms": [{"type": "living_room", "count": 1}]})
    plan = generate_plan(spec)
    assert validate(plan) == []


def test_demo_three_bhk_fits_a_thirty_by_forty_foot_plot():
    """Regression from the Phase 4 live gate: area-only cut clamping made the
    attached bathroom a 1.2 m sliver despite sufficient total plot area."""

    spec = RequirementsSpec.model_validate(
        {
            "building_type": "house",
            "rooms": [
                {"type": "master_bedroom", "count": 1},
                {"type": "bedroom", "count": 2},
                {"type": "bathroom", "count": 1},
                {"type": "living_room", "count": 1},
                {"type": "kitchen", "count": 1},
                {"type": "pooja_room", "count": 1},
            ],
            "adjacency": [
                {
                    "room_a": "master_bedroom",
                    "room_b": "bathroom",
                    "strength": "must",
                }
            ],
            "plot": {"width_m": 9.144, "depth_m": 12.192},
            "facing": "east",
        }
    )

    plan = generate_plan(spec)

    assert validate(plan) == []
    assert len(plan.rooms) == 8  # seven requested rooms + auto-entry


# ── Step 1.3 — hand-broken plans trigger exactly their violation codes ────────


def _codes(plan: LayoutPlan) -> set[str]:
    return {v.code for v in validate(plan)}


def test_manually_overlapped_rooms_flagged():
    plan = generate_plan(_load("2bhk"))
    victim = plan.rooms[1].model_copy(update={"x": plan.rooms[0].x, "y": plan.rooms[0].y})
    broken = plan.model_copy(update={"rooms": [plan.rooms[0], victim, *plan.rooms[2:]]})
    assert "overlap" in _codes(broken)


def test_out_of_bounds_room_flagged():
    plan = generate_plan(_load("2bhk"))
    victim = plan.rooms[0].model_copy(update={"x": plan.plot.width_m - 0.5})
    broken = plan.model_copy(update={"rooms": [victim, *plan.rooms[1:]]})
    assert "out_of_bounds" in _codes(broken)


def test_below_min_size_flagged():
    plan = generate_plan(_load("2bhk"))
    bedroom = next(r for r in plan.rooms if r.type == RoomType.bedroom)
    shrunk = bedroom.model_copy(update={"w": 2.0, "h": 2.0})
    broken = plan.model_copy(update={"rooms": [shrunk if r.id == bedroom.id else r for r in plan.rooms]})
    assert "below_min_size" in _codes(broken)


def test_doorless_plan_flags_unreachable_rooms():
    plan = generate_plan(_load("2bhk"))
    broken = plan.model_copy(update={"doors": []})
    assert "unreachable" in _codes(broken)


# ── The go/no-go gate: property test over random specs ───────────────────────


@st.composite
def random_specs(draw):
    rooms = [
        {"type": "bedroom", "count": draw(st.integers(1, 6))},
        {"type": "bathroom", "count": draw(st.integers(1, 3))},
        {"type": "kitchen", "count": 1},
        {"type": "living_room", "count": 1},
    ]
    for extra in ("dining", "study", "pooja_room", "balcony", "utility"):
        if draw(st.booleans()):
            rooms.append({"type": extra, "count": 1})
    return RequirementsSpec.model_validate({
        "rooms": rooms,
        "plot": {
            "width_m": draw(st.floats(8.0, 20.0).map(lambda v: round(v, 1))),
            "depth_m": draw(st.floats(8.0, 20.0).map(lambda v: round(v, 1))),
        },
        "facing": draw(st.sampled_from([f.value for f in Facing])),
    })


@settings(max_examples=200, deadline=None, derandomize=True)
@given(random_specs())
def test_property_engine_output_never_violates_hard_constraints(spec):
    """THE gate: for every random spec the engine either returns a plan with
    ZERO hard violations, or refuses with the structured does-not-fit error.
    It never returns broken geometry."""
    try:
        plan = generate_plan(spec)
    except DoesNotFitError:
        return  # honest refusal is a valid outcome for undersized plots

    violations = validate(plan)
    assert violations == [], [v.message for v in violations]

    requested = sum(r.count for r in spec.rooms) + 1  # + auto-entry
    assert len(plan.rooms) == requested
