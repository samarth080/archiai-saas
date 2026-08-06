"""Workflow Phase 3.1a — per-archetype unit tests with synthetic programs
(the doc's own acceptance style: prove ``zoned_bands`` bands correctly
without going through the full ``generate_plan``/closed-``RoomType``
pipeline, since ``PlanRoom.type`` is still a closed enum — see the module
docstring's "not done in this slice" note).
"""
import pytest

from app.schemas.requirements import Facing
from app.services.layout_engine.archetypes import (
    BandPlan,
    double_loaded_corridor,
    hub_and_spoke,
    open_core,
    select_archetype,
    vertical_core_bands,
    zoned_bands,
)
from app.services.layout_engine.geometry import Rect
from app.services.layout_engine.subdivision import RoomNeed, SubdivisionError
from app.services.planning import EngineProgram


def _need(key: str, kind: str, area: float, min_w: float, min_d: float) -> RoomNeed:
    return RoomNeed(key=key, type=kind, label=kind, preferred_area=area, min_w=min_w, min_d=min_d)


def _program(needs, zone_of, must_adjacent=(), **overrides) -> EngineProgram:
    defaults = dict(
        needs=needs,
        zone_of=zone_of,
        must_adjacent=list(must_adjacent),
        should_adjacent=[],
        avoid=[],
        circulation_nodes=[],
        floor_of={n.key: 0 for n in needs},
        entry_node=None,
    )
    defaults.update(overrides)
    return EngineProgram(**defaults)


def _band_containing(plan: BandPlan, key: str):
    return next(rect for rect, rooms in plan.bands if any(n.key == key for n in rooms))


def test_single_zone_program_returns_one_band_covering_the_whole_plot():
    needs = [_need("r1", "office", 20.0, 3.0, 3.0), _need("r2", "office", 20.0, 3.0, 3.0)]
    program = _program(needs, {"r1": "private", "r2": "private"})

    plan = zoned_bands(program, 10.0, 10.0, Facing.east)

    assert len(plan.bands) == 1
    rect, rooms = plan.bands[0]
    assert (rect.w, rect.d) == (10.0, 10.0)
    assert {n.key for n in rooms} == {"r1", "r2"}


def test_three_macro_bands_tile_the_plot_with_zero_gaps_and_zero_overlap():
    needs = [
        _need("entry", "entry", 3.0, 1.2, 1.5),
        _need("living", "living_room", 16.0, 3.3, 3.6),
        _need("balcony", "balcony", 4.5, 1.2, 2.4),
        _need("bath", "bathroom", 4.0, 1.5, 2.1),
        _need("bed", "bedroom", 12.0, 3.0, 3.0),
    ]
    zone_of = {
        "entry": "circulation", "living": "public", "balcony": "semi_private",
        "bath": "service", "bed": "private",
    }
    program = _program(needs, zone_of)

    plan = zoned_bands(program, 9.0, 12.0, Facing.east)

    assert [n.key for _, rooms in plan.bands for n in rooms].count("entry") == 1
    total_band_area = sum(rect.area for rect, _ in plan.bands)
    assert total_band_area == pytest.approx(9.0 * 12.0)
    # bands tile the width with zero gaps: sorted by x, each one's x2 meets
    # the next one's x with no overlap.
    rects = sorted((rect for rect, _ in plan.bands), key=lambda r: r.x)
    for a, b in zip(rects, rects[1:]):
        assert a.x2 == pytest.approx(b.x)
        assert not a.overlaps(b)
    assert all(rect.d == pytest.approx(12.0) for rect in rects)  # full depth


def test_facing_side_band_is_the_public_one():
    needs = [_need("entry", "entry", 3.0, 1.2, 1.5), _need("bed", "bedroom", 12.0, 3.0, 3.0)]
    program = _program(needs, {"entry": "circulation", "bed": "private"})

    plan = zoned_bands(program, 9.0, 12.0, Facing.east)

    public_rect = _band_containing(plan, "entry")
    private_rect = _band_containing(plan, "bed")
    assert public_rect.x2 == pytest.approx(9.0)  # touches the east (facing) edge
    assert private_rect.x == pytest.approx(0.0)


def test_service_room_redistributes_into_its_must_adjacent_partners_band():
    needs = [
        _need("living", "living_room", 16.0, 3.3, 3.6),
        _need("wc", "bathroom", 4.0, 1.5, 2.1),
    ]
    zone_of = {"living": "public", "wc": "service"}
    program_no_pref = _program(needs, zone_of)
    program_with_pref = _program(needs, zone_of, must_adjacent=[("living", "wc")])

    # Without a must-adjacency, the bathroom defaults into the private band.
    default_plan = zoned_bands(program_no_pref, 9.0, 12.0, Facing.east)
    assert _band_containing(default_plan, "wc") is not _band_containing(default_plan, "living")

    # With one, it moves into living's (public) band instead.
    redistributed_plan = zoned_bands(program_with_pref, 9.0, 12.0, Facing.east)
    assert _band_containing(redistributed_plan, "wc") == _band_containing(redistributed_plan, "living")


def test_must_adjacent_partner_is_ordered_directly_after_its_anchor():
    needs = [
        _need("bed", "bedroom", 12.0, 3.0, 3.0),
        _need("study", "study", 8.0, 2.4, 2.7),
        _need("wc", "bathroom", 4.0, 1.5, 2.1),
    ]
    zone_of = {"bed": "private", "study": "private", "wc": "private"}
    program = _program(needs, zone_of, must_adjacent=[("bed", "wc")])

    plan = zoned_bands(program, 9.0, 12.0, Facing.east)

    _, rooms = plan.bands[0]
    keys = [n.key for n in rooms]
    assert keys.index("wc") == keys.index("bed") + 1


def test_non_residential_free_string_types_work_without_crashing():
    """The whole point of catalog/graph-driven zone_of instead of
    RoomType(n.type) in PUBLIC_ROOM_TYPES: free-string, non-enum space types
    (a clinic's reception/consultation rooms) band without raising."""
    needs = [
        _need("reception", "reception", 12.0, 3.0, 3.0),
        _need("consult1", "consultation_room", 10.0, 3.0, 3.0),
        _need("consult2", "consultation_room", 10.0, 3.0, 3.0),
    ]
    zone_of = {"reception": "public", "consult1": "private", "consult2": "private"}
    program = _program(needs, zone_of)

    plan = zoned_bands(program, 10.0, 10.0, Facing.south)

    assert sum(rect.area for rect, _ in plan.bands) == pytest.approx(100.0)
    assert {n.key for _, rooms in plan.bands for n in rooms} == {"reception", "consult1", "consult2"}


def test_bands_that_cannot_fit_raise_subdivision_error():
    needs = [_need("living", "living_room", 16.0, 3.3, 3.6), _need("bed", "bedroom", 12.0, 3.0, 3.0)]
    program = _program(needs, {"living": "public", "bed": "private"})

    with pytest.raises(SubdivisionError):
        zoned_bands(program, 3.0, 3.0, Facing.east)  # nowhere near enough span


def test_empty_program_returns_no_bands():
    assert zoned_bands(_program([], {}), 9.0, 12.0, Facing.east) == BandPlan(bands=[])


# ── corridor carving (workflow 4.3) ───────────────────────────────────────


def _corridor_program():
    needs = [
        _need("entry", "entry", 3.0, 1.2, 1.5),
        _need("corr", "corridor", 8.0, 1.0, 1.5),
        _need("living", "living_room", 16.0, 3.3, 3.6),
        _need("b1", "bedroom", 12.0, 3.0, 3.0),
        _need("b2", "bedroom", 12.0, 3.0, 3.0),
        _need("b3", "bedroom", 12.0, 3.0, 3.0),
    ]
    zone_of = {
        "entry": "circulation", "corr": "circulation", "living": "public",
        "b1": "private", "b2": "private", "b3": "private",
    }
    return _program(needs, zone_of)


def test_corridor_becomes_its_own_band_not_folded_into_public():
    plan = zoned_bands(_corridor_program(), 12.0, 14.0, Facing.east)

    corridor_bands = [(r, g) for r, g in plan.bands if any(n.key == "corr" for n in g)]
    assert len(corridor_bands) == 1
    rect, group = corridor_bands[0]
    assert [n.key for n in group] == ["corr"]  # alone, not grouped with entry/living


def test_corridor_band_sits_between_public_and_private():
    plan = zoned_bands(_corridor_program(), 12.0, 14.0, Facing.east)

    def band_x(key: str) -> float:
        return next(rect.x for rect, group in plan.bands if any(n.key == key for n in group))

    public_x, corridor_x, private_x = band_x("living"), band_x("corr"), band_x("b1")
    # facing east: public is highest-x (touches the facing edge), private is
    # lowest-x — the corridor's band must sit strictly between them.
    assert private_x < corridor_x < public_x


def test_corridor_rects_is_populated_with_real_geometry():
    plan = zoned_bands(_corridor_program(), 12.0, 14.0, Facing.east)

    assert len(plan.corridor_rects) == 1
    key, rect = plan.corridor_rects[0]
    assert key == "corr"
    assert rect.d == pytest.approx(14.0)  # spans the full plot depth
    assert rect.w >= 1.0  # at least its catalog minimum width


def test_corridor_carving_tiles_the_whole_plot_with_zero_gaps():
    # The 3 bedrooms served by the corridor are now comb-arranged (workflow
    # 4.5) — stacked side by side along the corridor's edge rather than one
    # combined band left to the general recursive tree — so bands no longer
    # form a single 1-D strip sorted by x. Verify real 2-D tiling instead:
    # total area matches exactly, and no two bands genuinely overlap.
    plan = zoned_bands(_corridor_program(), 12.0, 14.0, Facing.east)
    assert sum(rect.area for rect, _ in plan.bands) == pytest.approx(12.0 * 14.0)
    rects = [rect for rect, _ in plan.bands]
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            assert not a.overlaps(b)


def test_corridor_served_rooms_are_all_directly_adjacent_to_the_corridor():
    """Workflow 4.5's actual guarantee: every semi_private/private room the
    corridor serves shares a real wall with it — not just some of them,
    which is what a plain recursive-tree subdivision of the whole served
    group could produce (a room nested behind another, only reachable
    through it — the exact shape of a real Hypothesis counterexample this
    fix closes)."""
    plan = zoned_bands(_corridor_program(), 12.0, 14.0, Facing.east)
    corridor_rect = next(rect for rect, group in plan.bands if any(n.key == "corr" for n in group))
    served_keys = {"b1", "b2", "b3"}
    for rect, group in plan.bands:
        if not any(n.key in served_keys for n in group):
            continue
        assert corridor_rect.shared_edge(rect) is not None, group[0].key


def test_no_corridor_node_means_unchanged_behavior():
    # Regression pin: a program with no corridor node must produce the exact
    # same bands as before this feature existed (the whole carving block is
    # a documented no-op in that case).
    needs = [_need("entry", "entry", 3.0, 1.2, 1.5), _need("bed", "bedroom", 12.0, 3.0, 3.0)]
    program = _program(needs, {"entry": "circulation", "bed": "private"})
    plan = zoned_bands(program, 9.0, 12.0, Facing.east)
    assert plan.corridor_rects == []


def test_select_archetype_returns_zoned_bands_with_a_reason():
    key, fn, reason = select_archetype(_program([], {}))
    assert key == "zoned_bands"
    assert fn is zoned_bands
    assert reason


# ── double_loaded_corridor (workflow 3.1.b) ───────────────────────────────


def _repeat_unit_program(**overrides) -> EngineProgram:
    needs = [
        _need("entry", "entry", 3.0, 1.2, 1.5),
        _need("b1", "bedroom", 12.0, 3.0, 3.0),
        _need("b2", "bedroom", 12.0, 3.0, 3.0),
        _need("b3", "bedroom", 12.0, 3.0, 3.0),
        _need("b4", "bedroom", 12.0, 3.0, 3.0),
    ]
    zone_of = {"entry": "circulation", "b1": "private", "b2": "private", "b3": "private", "b4": "private"}
    return _program(needs, zone_of, **overrides)


def test_double_loaded_corridor_splits_repeat_units_into_two_parallel_wings():
    plan = double_loaded_corridor(_repeat_unit_program(), 12.0, 16.0, Facing.east)

    assert len(plan.bands) == 3  # public band + 2 wings
    entry_rect = _band_containing(plan, "entry")
    assert entry_rect.x2 == pytest.approx(12.0)  # touches the facing (east) edge

    wing_bands = [(rect, rooms) for rect, rooms in plan.bands if not any(n.key == "entry" for n in rooms)]
    assert len(wing_bands) == 2
    (rect_a, _), (rect_b, _) = wing_bands
    assert not rect_a.overlaps(rect_b)
    assert rect_a.y2 == pytest.approx(rect_b.y) or rect_b.y2 == pytest.approx(rect_a.y)  # stacked
    assert sum(rect.area for rect, _ in plan.bands) == pytest.approx(12.0 * 16.0)


def test_double_loaded_corridor_alternates_repeat_units_between_wings():
    plan = double_loaded_corridor(_repeat_unit_program(), 12.0, 16.0, Facing.east)

    wing_keysets = [
        {n.key for n in rooms} for _, rooms in plan.bands if not any(n.key == "entry" for n in rooms)
    ]
    assert {"b1", "b3"} in wing_keysets
    assert {"b2", "b4"} in wing_keysets


def test_double_loaded_corridor_falls_back_to_one_band_without_two_wings_worth_of_rooms():
    needs = [_need("entry", "entry", 3.0, 1.2, 1.5), _need("b1", "bedroom", 12.0, 3.0, 3.0)]
    program = _program(needs, {"entry": "circulation", "b1": "private"})

    plan = double_loaded_corridor(program, 9.0, 12.0, Facing.east)

    assert len(plan.bands) == 2  # public band + one private band, no wing split possible
    assert sum(rect.area for rect, _ in plan.bands) == pytest.approx(9.0 * 12.0)


# ── hub_and_spoke (workflow 3.1.c) ────────────────────────────────────────


def test_hub_and_spoke_gives_the_highest_circulation_weight_public_node_its_own_band():
    needs = [
        _need("waiting", "waiting_room", 15.0, 3.5, 4.0),
        _need("consult1", "consultation_room", 10.0, 3.0, 3.0),
        _need("consult2", "consultation_room", 10.0, 3.0, 3.0),
    ]
    zone_of = {"waiting": "public", "consult1": "private", "consult2": "private"}
    program = _program(needs, zone_of)

    plan = hub_and_spoke(program, 10.0, 10.0, Facing.south)

    assert len(plan.bands) == 2
    hub_rect = _band_containing(plan, "waiting")
    assert hub_rect.y2 == pytest.approx(10.0)  # touches the facing (south) edge


def test_hub_and_spoke_orders_must_adjacent_spokes_first():
    needs = [
        _need("reception", "reception", 12.0, 3.0, 3.0),
        _need("consult1", "consultation_room", 10.0, 3.0, 3.0),
        _need("consult2", "consultation_room", 10.0, 3.0, 3.0),
        _need("bath", "bathroom", 4.0, 1.5, 2.1),
    ]
    zone_of = {"reception": "public", "consult1": "private", "consult2": "private", "bath": "service"}
    program = _program(needs, zone_of, must_adjacent=[("reception", "consult2")])

    plan = hub_and_spoke(program, 12.0, 12.0, Facing.east)

    _, spokes = next((r, g) for r, g in plan.bands if not any(n.key == "reception" for n in g))
    assert spokes[0].key == "consult2"


def test_hub_and_spoke_falls_back_to_any_node_when_theres_no_public_room():
    needs = [_need("a", "storage", 6.0, 2.0, 2.0), _need("b", "storage", 6.0, 2.0, 2.0)]
    program = _program(needs, {"a": "service", "b": "service"})

    plan = hub_and_spoke(program, 6.0, 8.0, Facing.east)

    assert len(plan.bands) == 2
    assert sum(rect.area for rect, _ in plan.bands) == pytest.approx(6.0 * 8.0)


# ── open_core (workflow 3.1.d) ────────────────────────────────────────────


def test_open_core_gives_the_largest_area_node_the_facing_band():
    needs = [
        _need("floor", "sales_floor", 80.0, 6.0, 6.0),
        _need("office", "office", 9.0, 3.0, 3.0),
        _need("storage", "storage", 6.0, 2.0, 3.0),
    ]
    zone_of = {"floor": "public", "office": "private", "storage": "service"}
    program = _program(needs, zone_of)

    plan = open_core(program, 12.0, 10.0, Facing.west)

    dominant_rect = _band_containing(plan, "floor")
    assert dominant_rect.x == pytest.approx(0.0)  # touches the facing (west) edge
    _, rest = next((r, g) for r, g in plan.bands if not any(n.key == "floor" for n in g))
    assert {n.key for n in rest} == {"office", "storage"}


# -- fixed vertical core (workflow Phase 7) -----------------------------------


def _vertical_program(with_lift: bool = False) -> EngineProgram:
    needs = [
        _need("stair", "staircase", 2.88, 2.4, 1.2),
        _need("corr", "corridor", 8.0, 1.2, 1.5),
        _need("entry", "entry", 3.0, 1.2, 1.5),
        _need("living", "living_room", 16.0, 3.3, 3.6),
        _need("bed1", "bedroom", 12.0, 3.0, 3.0),
        _need("bath", "bathroom", 4.0, 1.5, 2.1),
        _need("bed2", "bedroom", 12.0, 3.0, 3.0),
    ]
    if with_lift:
        needs.insert(1, _need("lift", "lift", 3.24, 1.8, 1.8))
    return _program(
        needs,
        {
            need.key: (
                "circulation"
                if need.type in {"staircase", "corridor", "lift"}
                else "private"
                if need.type == "bedroom"
                else "service"
                if need.type == "bathroom"
                else "public"
            )
            for need in needs
        },
        must_adjacent=[("bed1", "bath")],
    )


def test_vertical_core_has_an_exact_stair_rect_and_tiles_the_plot():
    plan = vertical_core_bands(_vertical_program(), 12.0, 14.0, Facing.east)

    stair_rect = _band_containing(plan, "stair")
    assert (stair_rect.x, stair_rect.y, stair_rect.w, stair_rect.d) == (0.0, 0.0, 1.2, 2.4)
    assert sum(rect.area for rect, _ in plan.bands) == pytest.approx(12.0 * 14.0)
    rects = [rect for rect, _ in plan.bands]
    for index, rect in enumerate(rects):
        for other in rects[index + 1:]:
            assert not rect.overlaps(other)


def test_vertical_core_private_components_touch_core_directly():
    plan = vertical_core_bands(_vertical_program(), 12.0, 14.0, Facing.east)
    core_rects = [
        _band_containing(plan, "stair"),
        _band_containing(plan, "corr"),
    ]

    for key in ("bed1", "bed2"):
        room_rect = _band_containing(plan, key)
        assert any(core.shared_edge(room_rect) is not None for core in core_rects)


def test_vertical_core_precarves_an_aligned_lift_rect():
    first = vertical_core_bands(_vertical_program(with_lift=True), 12.0, 14.0, Facing.east)
    second = vertical_core_bands(_vertical_program(with_lift=True), 12.0, 14.0, Facing.west)

    lift_a = _band_containing(first, "lift")
    lift_b = _band_containing(second, "lift")
    assert lift_a == lift_b == Rect(0.0, 2.4, 1.8, 1.8)
    assert _band_containing(first, "stair") == Rect(0.0, 0.0, 1.8, 2.4)


def test_vertical_core_rejects_a_plot_too_shallow_for_stair_and_lift():
    with pytest.raises(SubdivisionError, match="vertical core needs"):
        vertical_core_bands(_vertical_program(with_lift=True), 12.0, 5.0, Facing.east)


# ── select_archetype graph-shape rules (workflow 3.2) ─────────────────────


def test_select_archetype_explicit_layout_style_always_wins():
    key, fn, reason = select_archetype(_repeat_unit_program(), "open_core")
    assert key == "open_core"
    assert fn is open_core
    assert "open_core" in reason


def _repeat_unit_program_with_corridor(**overrides) -> EngineProgram:
    needs = [
        _need("entry", "entry", 3.0, 1.2, 1.5),
        _need("hall", "hallway", 6.0, 1.5, 3.0),
        _need("b1", "bedroom", 12.0, 3.0, 3.0),
        _need("b2", "bedroom", 12.0, 3.0, 3.0),
        _need("b3", "bedroom", 12.0, 3.0, 3.0),
    ]
    zone_of = {
        "entry": "circulation", "hall": "circulation",
        "b1": "private", "b2": "private", "b3": "private",
    }
    return _program(needs, zone_of, **overrides)


def test_select_archetype_chooses_double_loaded_corridor_for_repeat_units_with_a_corridor_spine():
    key, fn, reason = select_archetype(_repeat_unit_program_with_corridor())

    assert key == "double_loaded_corridor"
    assert fn is double_loaded_corridor
    assert reason


def test_select_archetype_ignores_repeat_units_without_a_real_corridor_spine():
    # An auto-injected `entry` is a circulation node too, but "the program
    # has an entry" alone must not select double_loaded_corridor — every
    # generated program has one, residential included (see the selector's
    # own `_CORRIDOR_SPINE_TYPES` comment for the fixture that caught this).
    program = _repeat_unit_program()

    key, fn, reason = select_archetype(program)

    assert key == "zoned_bands"
    assert reason


def test_select_archetype_does_not_flip_existing_residential_fixtures_with_three_plus_bedrooms():
    """Regression pin for the exact false-positive the corridor-spine gate
    above fixes: 4bhk.json has 3 `bedroom` + an auto-injected `entry` (no
    hallway) and must keep resolving to `zoned_bands`, not silently switch
    archetypes the moment this file gained a second/third archetype."""
    needs = [
        _need("master", "master_bedroom", 16.0, 3.3, 3.6),
        _need("b1", "bedroom", 12.0, 3.0, 3.0),
        _need("b2", "bedroom", 12.0, 3.0, 3.0),
        _need("b3", "bedroom", 12.0, 3.0, 3.0),
        _need("entry", "entry", 3.0, 1.2, 1.5),
    ]
    zone_of = {"master": "private", "b1": "private", "b2": "private", "b3": "private", "entry": "circulation"}
    program = _program(needs, zone_of, circulation_nodes=["entry"])

    key, _, _ = select_archetype(program)

    assert key == "zoned_bands"


def test_select_archetype_chooses_hub_and_spoke_for_a_public_hub_with_three_must_spokes():
    needs = [
        _need("waiting", "waiting_room", 15.0, 3.5, 4.0),
        _need("c1", "consultation_room", 10.0, 3.0, 3.0),
        _need("c2", "consultation_room", 10.0, 3.0, 3.0),
        _need("c3", "consultation_room", 10.0, 3.0, 3.0),
    ]
    zone_of = {"waiting": "public", "c1": "private", "c2": "private", "c3": "private"}
    program = _program(
        needs, zone_of,
        must_adjacent=[("waiting", "c1"), ("waiting", "c2"), ("waiting", "c3")],
    )

    key, fn, reason = select_archetype(program)

    assert key == "hub_and_spoke"
    assert fn is hub_and_spoke
    assert reason


def test_select_archetype_chooses_open_core_for_one_dominant_node():
    needs = [_need("floor", "sales_floor", 80.0, 6.0, 6.0), _need("office", "office", 9.0, 3.0, 3.0)]
    program = _program(needs, {"floor": "public", "office": "private"})

    key, fn, reason = select_archetype(program)

    assert key == "open_core"
    assert fn is open_core
    assert reason


def test_select_archetype_reasons_are_always_non_empty():
    programs = [
        _program([], {}),
        _repeat_unit_program(),
        _repeat_unit_program_with_corridor(),
        _program(
            [_need("floor", "sales_floor", 80.0, 6.0, 6.0), _need("office", "office", 9.0, 3.0, 3.0)],
            {"floor": "public", "office": "private"},
        ),
    ]
    for program in programs:
        _, _, reason = select_archetype(program)
        assert reason
