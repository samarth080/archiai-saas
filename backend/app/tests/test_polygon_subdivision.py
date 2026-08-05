"""polygon_subdivision.py — straight-edge polygon subdivider (workflow Phase 8)."""
import pytest
from shapely.geometry import Polygon, box

from app.schemas.requirements import Facing
from app.services.layout_engine.polygon_subdivision import subdivide_polygon
from app.services.layout_engine.subdivision import RoomNeed, SubdivisionError


def _need(key: str, area: float, min_w: float = 1.5, min_d: float = 1.5) -> RoomNeed:
    return RoomNeed(key=key, type="bedroom", label=key, preferred_area=area, min_w=min_w, min_d=min_d)


def _assert_zero_gap_zero_overlap(placed, boundary: Polygon):
    polys = [poly for _, poly in placed]
    for i, a in enumerate(polys):
        for b in polys[i + 1:]:
            assert a.intersection(b).area <= 1e-6, "leaves must not overlap"
    total = sum(p.area for p in polys)
    assert total == pytest.approx(boundary.area, rel=1e-3), "leaves must tile the boundary exactly"


def test_single_need_returns_the_whole_polygon_unchanged():
    boundary = box(0, 0, 5, 5)
    need = _need("r1", 25.0)
    result = subdivide_polygon([need], boundary, Facing.east)
    assert result == [(need, boundary)]


def test_rectangular_boundary_tiles_with_zero_gaps_and_overlaps():
    boundary = box(0, 0, 10, 10)
    needs = [_need(f"r{i}", 20.0) for i in range(5)]
    placed = subdivide_polygon(needs, boundary, Facing.east)
    assert {n.key for n, _ in placed} == {n.key for n in needs}
    _assert_zero_gap_zero_overlap(placed, boundary)


def test_trapezoidal_boundary_tiles_with_zero_gaps_and_overlaps():
    # Rectangle with the top-right corner sliced off — a "slanted side" plot.
    boundary = Polygon([(0, 0), (12, 0), (12, 6), (8, 10), (0, 10)])
    needs = [_need(f"r{i}", 20.0) for i in range(6)]
    placed = subdivide_polygon(needs, boundary, Facing.south)
    assert {n.key for n, _ in placed} == {n.key for n in needs}
    _assert_zero_gap_zero_overlap(placed, boundary)
    # At least one leaf should have actually been clipped by the slant (not
    # every leaf can land as a plain rectangle on this boundary).
    from app.services.layout_engine import polygon as polygon_mod

    assert any(not polygon_mod.is_axis_aligned_rect(p) for _, p in placed)


def test_l_shaped_non_convex_boundary_tiles_with_zero_gaps_and_overlaps():
    boundary = Polygon([(0, 0), (10, 0), (10, 6), (6, 6), (6, 10), (0, 10)])
    needs = [_need(f"r{i}", 12.0) for i in range(6)]
    placed = subdivide_polygon(needs, boundary, Facing.east)
    assert {n.key for n, _ in placed} == {n.key for n in needs}
    _assert_zero_gap_zero_overlap(placed, boundary)


def test_impossibly_small_boundary_raises_subdivision_error():
    boundary = box(0, 0, 2, 2)
    needs = [_need(f"r{i}", 20.0, min_w=3.0, min_d=3.0) for i in range(3)]
    with pytest.raises(SubdivisionError):
        subdivide_polygon(needs, boundary, Facing.east)


def test_facing_side_gets_the_first_group():
    boundary = box(0, 0, 10, 10)
    first = _need("r1", 50.0)
    second = _need("r2", 50.0)
    placed = subdivide_polygon([first, second], boundary, Facing.east)
    by_key = {n.key: poly for n, poly in placed}
    # East-facing: the first group should land on the higher-x (east) side.
    assert by_key["r1"].bounds[0] >= by_key["r2"].bounds[0]
