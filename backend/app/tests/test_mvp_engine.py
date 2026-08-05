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


# ── Connectivity: every genuinely adjacent pair gets a door, not just the
# minimum spanning tree (user-reported: rooms visibly touching with no door
# between them, forcing a detour through another room even though nothing
# was technically "unreachable"). ────────────────────────────────────────


def _shared_wall_pairs(plan: LayoutPlan) -> dict[frozenset, str]:
    """room-id-pair -> the wall id of their shared edge, for every pair of
    rooms in the plan whose rectangles actually touch."""
    pairs: dict[frozenset, str] = {}
    for i, a in enumerate(plan.rooms):
        for b in plan.rooms[i + 1:]:
            seg = _room_rect(a).shared_edge(_room_rect(b))
            if seg is None:
                continue
            endpoints = {(round(seg.x1, 3), round(seg.y1, 3)), (round(seg.x2, 3), round(seg.y2, 3))}
            for wall in plan.walls:
                if {(wall.x1, wall.y1), (wall.x2, wall.y2)} == endpoints:
                    pairs[frozenset((a.id, b.id))] = wall.id
                    break
    return pairs


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_every_adjacent_public_or_circulation_room_pair_gets_a_door(name):
    spec = _load(name)
    plan = generate_plan(spec)
    doored_walls = {d.wall_ref for d in plan.doors}
    labels_by_id = {r.id: r.label for r in plan.rooms}
    circulation_or_public_labels = {
        RoomType.entry.value, RoomType.living_room.value, RoomType.dining.value,
    }

    for pair, wall_id in _shared_wall_pairs(plan).items():
        a, b = pair
        if labels_by_id[a] in circulation_or_public_labels or labels_by_id[b] in circulation_or_public_labels:
            assert wall_id in doored_walls, (
                f"{labels_by_id[a]} and {labels_by_id[b]} share a wall but have no door "
                f"between them in {name}"
            )


def test_two_adjacent_private_rooms_do_not_get_a_redundant_direct_door():
    # 4bhk's real generated layout has multiple bedroom-bedroom /
    # bedroom-bathroom adjacencies that are already reachable via the
    # spanning tree — privacy says don't also punch a direct door there.
    plan = generate_plan(_load("4bhk"))
    private_types = {RoomType.bedroom.value, RoomType.master_bedroom.value, RoomType.bathroom.value}
    doored_walls = {d.wall_ref for d in plan.doors}
    types_by_id = {r.id: r.type for r in plan.rooms}

    private_adjacent_pairs = [
        pair for pair in _shared_wall_pairs(plan)
        if all(types_by_id[k] in private_types for k in pair)
    ]
    assert private_adjacent_pairs, "fixture must actually exercise this case"
    assert validate(plan) == []  # still fully valid/reachable without the extra doors


def test_explicitly_avoided_adjacent_pair_gets_no_direct_door():
    spec = RequirementsSpec.model_validate({
        "rooms": [
            {"type": "kitchen", "count": 1},
            {"type": "bathroom", "count": 1},
            {"type": "living_room", "count": 1},
            {"type": "entry", "count": 1},
        ],
        "avoid_adjacency": [{"room_a": "kitchen", "room_b": "bathroom"}],
        "plot": {"width_m": 8.0, "depth_m": 8.0},
    })
    plan = generate_plan(spec)
    types_by_id = {r.id: r.type for r in plan.rooms}
    doored_walls = {d.wall_ref for d in plan.doors}

    for pair, wall_id in _shared_wall_pairs(plan).items():
        types = {types_by_id[k] for k in pair}
        if types == {RoomType.kitchen.value, RoomType.bathroom.value}:
            assert wall_id not in doored_walls


# ── Door policy rewrite (workflow Phase 4.4) ──────────────────────────────


def test_circulation_key_prefers_a_real_corridor_over_living_room_or_entry():
    from app.services.layout_engine.engine import _circulation_key
    from app.services.layout_engine.subdivision import RoomNeed

    def need(key: str, kind: str) -> RoomNeed:
        return RoomNeed(key=key, type=kind, label=kind, preferred_area=10.0, min_w=2.0, min_d=2.0)

    placed = [
        (need("r1", "entry"), Rect(0, 0, 1, 1)),
        (need("r2", "living_room"), Rect(1, 0, 1, 1)),
        (need("r3", "corridor"), Rect(2, 0, 1, 1)),
    ]
    assert _circulation_key(placed) == "r3"


def test_avoid_pair_vetoes_a_door_even_when_it_is_the_only_bridge():
    """The doc's exact Phase 4.4 requirement: an AVOID edge must veto a door
    even if that pair is the ONLY way to keep the floor connected — routing
    should fail structurally (DoesNotFitError) rather than silently break
    the avoidance to preserve connectivity."""
    from app.services.layout_engine.engine import DoesNotFitError, _build_walls, _place_doors
    from app.services.layout_engine.subdivision import RoomNeed

    def need(key: str, kind: str) -> RoomNeed:
        return RoomNeed(key=key, type=kind, label=kind, preferred_area=9.0, min_w=3.0, min_d=3.0)

    # kitchen - bathroom - entry in a row; kitchen only touches bathroom.
    placed = [
        (need("a", "kitchen"), Rect(0, 0, 3, 3)),
        (need("b", "bathroom"), Rect(3, 0, 3, 3)),
        (need("c", "entry"), Rect(6, 0, 3, 3)),
    ]
    walls, wall_rooms = _build_walls(placed, 9.0, 3.0)
    spec = RequirementsSpec.model_validate({
        "rooms": [
            {"type": "kitchen", "count": 1},
            {"type": "bathroom", "count": 1},
            {"type": "entry", "count": 1},
        ],
        "avoid_adjacency": [{"room_a": "kitchen", "room_b": "bathroom"}],
    })
    zone_of = {"a": "public", "b": "service", "c": "circulation"}

    with pytest.raises(DoesNotFitError):
        _place_doors(placed, walls, wall_rooms, spec, Facing.east, zone_of)

    # The lenient editor-sync path must not raise, and must still honour the
    # veto rather than silently connecting kitchen through it.
    doors = _place_doors(
        placed, walls, wall_rooms, spec, Facing.east, zone_of, allow_disconnected=True,
    )
    doored_walls = {d.wall_ref for d in doors}
    kitchen_bathroom_wall = next(w for w in walls if set(wall_rooms[w.id]) == {"a", "b"})
    assert kitchen_bathroom_wall.id not in doored_walls


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


# ── PlanRoom.type migration (engine generalization workflow, migration-order
# item 4) — spec.spaces free-string programs now run end to end, not just
# through archetypes.py unit tests. ───────────────────────────────────────


def test_generate_plan_supports_a_non_residential_free_string_program():
    spec = RequirementsSpec.model_validate({
        "spaces": [
            {"space_type": "reception", "count": 1},
            {"space_type": "waiting_room", "count": 1},
            {"space_type": "consultation_room", "count": 3},
            {"space_type": "bathroom", "count": 1},
        ],
        "plot": {"width_m": 12.0, "depth_m": 14.0},
        "facing": "east",
    })

    plan = generate_plan(spec)

    types = sorted(r.type for r in plan.rooms)
    assert types.count("consultation_room") == 3
    assert "reception" in types
    assert "waiting_room" in types
    assert validate(plan) == []  # zero hard violations, same bar as every residential fixture


def test_generate_plan_rejects_an_unknown_space_type_as_a_structured_does_not_fit():
    spec = RequirementsSpec.model_validate({
        "spaces": [{"space_type": "zzz_totally_unknown", "count": 1}],
        "plot": {"width_m": 9.0, "depth_m": 9.0},
    })

    with pytest.raises(DoesNotFitError) as exc:
        generate_plan(spec)
    assert "zzz_totally_unknown" in str(exc.value)


def test_rebuild_derived_geometry_handles_a_hand_edited_non_residential_room_type():
    spec = RequirementsSpec.model_validate({"rooms": [{"type": "living_room", "count": 1}]})
    plan = generate_plan(spec)
    edited = plan.model_copy(update={
        "rooms": [r.model_copy(update={"type": "consultation_room"}) for r in plan.rooms],
    })

    rebuilt = rebuild_derived_geometry(edited, spec)  # must not raise (e.g. KeyError)

    assert rebuilt.rooms[0].type == "consultation_room"


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
