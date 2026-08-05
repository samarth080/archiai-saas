"""polygon.py — straight-edge polygon geometry primitives (workflow Phase 8)."""
from shapely.geometry import box

from app.services.layout_engine import polygon
from app.services.layout_engine.geometry import Rect


def test_polygon_from_vertices_matches_rect_to_polygon():
    rect = Rect(1.0, 2.0, 3.0, 4.0)
    from app.schemas.requirements import Vertex

    verts = [Vertex(x=1.0, y=2.0), Vertex(x=4.0, y=2.0), Vertex(x=4.0, y=6.0), Vertex(x=1.0, y=6.0)]
    assert polygon.polygon_from_vertices(verts).equals(polygon.rect_to_polygon(rect))


def test_is_axis_aligned_rect_true_for_a_plain_box():
    assert polygon.is_axis_aligned_rect(box(0, 0, 5, 3))


def test_is_axis_aligned_rect_false_for_a_triangle():
    from shapely.geometry import Polygon

    triangle = Polygon([(0, 0), (5, 0), (0, 3)])
    assert not polygon.is_axis_aligned_rect(triangle)


def test_shared_edges_of_two_touching_boxes():
    a = box(0, 0, 5, 5)
    b = box(5, 0, 10, 5)
    segs = polygon.shared_edges(a, b)
    assert len(segs) == 1
    assert segs[0].length == 5  # the full 5m vertical seam


def test_shared_edges_empty_for_corner_only_contact():
    a = box(0, 0, 5, 5)
    b = box(5, 5, 10, 10)  # touches only at the (5,5) corner
    assert polygon.shared_edges(a, b) == []


def test_shared_edges_handles_two_disjoint_runs_on_a_non_convex_pair():
    # A U-shaped room (a notch cut from its top edge) sitting under a strip
    # that spans the full width — the two "prongs" of the U each touch the
    # strip, but the notch between them doesn't: two disjoint shared runs.
    from shapely.geometry import Polygon

    u_shape = Polygon([(0, 0), (10, 0), (10, 10), (7, 10), (7, 3), (3, 3), (3, 10), (0, 10)])
    strip = box(0, 10, 10, 12)
    segs = polygon.shared_edges(u_shape, strip)
    assert len(segs) == 2
    assert sorted(seg.length for seg in segs) == [3, 3]  # (0-3) and (7-10)


def test_is_on_boundary_true_for_a_plot_edge_midpoint():
    plot = box(0, 0, 10, 10)
    assert polygon.is_on_boundary((5.0, 0.0), plot)
    assert not polygon.is_on_boundary((5.0, 5.0), plot)
