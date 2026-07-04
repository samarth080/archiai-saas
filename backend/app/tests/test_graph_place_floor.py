"""Phase 4 Stages 4-8 — place_floor end-to-end (graph -> legacy room dicts)."""
from itertools import count

from app.services.planning.boundary import compute_footprint
from app.services.planning.clustering import contract
from app.services.planning.graph_layout import place_floor, prepare
from app.services.planning import from_parser_output
from app.services.prompt_service import parse_prompt, parsed_to_room_specs

_EPS = 0.1


def _run(prompt: str):
    parsed = parse_prompt(prompt)
    specs = parsed_to_room_specs(parsed)
    prepared = prepare(from_parser_output(parsed, specs), None)
    cg = contract(prepared)
    total_area = sum(c.item().area for c in cg.clusters)
    target_width = compute_footprint(total_area).w
    ids = count()
    rooms, footprint = place_floor(
        cg.clusters,
        list(cg.edges),
        floor_id="floor_0",
        floor_level=0,
        elevation=0.0,
        target_width=target_width,
        new_id=lambda: f"r{next(ids)}",
    )
    return rooms, footprint


def _bounds(room):
    x, z = room["position"]["x"], room["position"]["z"]
    w, d = room["size"]["w"], room["size"]["d"]
    return x - w / 2, x + w / 2, z - d / 2, z + d / 2


def _overlap(a, b) -> bool:
    ax0, ax1, az0, az1 = _bounds(a)
    bx0, bx1, bz0, bz1 = _bounds(b)
    return ax0 + _EPS < bx1 and bx0 + _EPS < ax1 and az0 + _EPS < bz1 and bz0 + _EPS < az1


def _share_wall(a, b) -> bool:
    ax0, ax1, az0, az1 = _bounds(a)
    bx0, bx1, bz0, bz1 = _bounds(b)
    x_touch = abs(ax1 - bx0) < _EPS or abs(bx1 - ax0) < _EPS
    z_touch = abs(az1 - bz0) < _EPS or abs(bz1 - az0) < _EPS
    z_overlap = min(az1, bz1) - max(az0, bz0) > _EPS
    x_overlap = min(ax1, bx1) - max(ax0, bx0) > _EPS
    return (x_touch and z_overlap) or (z_touch and x_overlap)


def _room(rooms, room_type):
    return next(r for r in rooms if r["roomType"] == room_type)


def test_place_floor_emits_legacy_room_schema():
    rooms, footprint = _run("clinic with reception, waiting room and 2 consultation rooms")
    assert rooms
    for r in rooms:
        assert set(r) >= {"id", "label", "roomType", "objectType", "floorId", "floorLevel",
                          "position", "size", "rotation", "color"}
        assert r["objectType"] == "room"
        assert set(r["position"]) == {"x", "y", "z"} and set(r["size"]) == {"w", "h", "d"}
    assert set(footprint) == {"x", "z", "w", "d"}


def test_place_floor_tiles_without_overlap_inside_footprint():
    rooms, footprint = _run("3 bedroom house with living room, kitchen, 2 bathrooms and a study")
    # rooms fill the plate exactly (Σ area ≈ footprint area, no stair reserve here)
    total = sum(r["size"]["w"] * r["size"]["d"] for r in rooms)
    assert abs(total - footprint["w"] * footprint["d"]) < 1.0
    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            assert not _overlap(a, b)
        x0, x1, z0, z1 = _bounds(a)
        assert x0 >= -_EPS and z0 >= -_EPS
        assert x1 <= footprint["w"] + _EPS and z1 <= footprint["d"] + _EPS


def test_cross_zone_must_becomes_a_shared_wall():
    # reception (public) MUST consultation (private) — different zones, so the
    # zone tiler can't; the graph clusters them and the guillotine shares a wall.
    rooms, _ = _run("clinic where the reception is next to the consultation room")
    assert _share_wall(_room(rooms, "reception"), _room(rooms, "consultation_room"))


def test_place_floor_is_deterministic():
    assert _run("clinic with reception, waiting room and 2 consultation rooms") == \
        _run("clinic with reception, waiting room and 2 consultation rooms")
