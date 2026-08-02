"""Workflow Phase 3.1a — per-archetype unit tests with synthetic programs
(the doc's own acceptance style: prove ``zoned_bands`` bands correctly
without going through the full ``generate_plan``/closed-``RoomType``
pipeline, since ``PlanRoom.type`` is still a closed enum — see the module
docstring's "not done in this slice" note).
"""
import pytest

from app.schemas.requirements import Facing
from app.services.layout_engine.archetypes import BandPlan, select_archetype, zoned_bands
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


def test_select_archetype_returns_zoned_bands_with_a_reason():
    key, fn, reason = select_archetype(_program([], {}))
    assert key == "zoned_bands"
    assert fn is zoned_bands
    assert reason
