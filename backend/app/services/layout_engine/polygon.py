"""Straight-edge polygon geometry (workflow Phase 8, polygon boundary engine).

Thin shapely wrappers — kept deliberately small, only the primitives the
guillotine polygon-clipping subdivider (``polygon_subdivision.py``) and the
polygon wall builder (``engine.py``) actually need. Coordinates follow the
same LayoutPlan convention as ``geometry.py``: meters, origin NW, +x east,
+y south. Reuses ``geometry.EPS`` (1 mm) for consistency.

Deliberately NOT reused/extended by the existing rect (``Rect``) path: GEOS's
floating-point arithmetic is not guaranteed bit-identical to the hand-rolled
exact ``Rect`` arithmetic the rest of the engine leans on, so the rect and
polygon code paths stay parallel rather than unified (see ``engine.py``'s
module docstring for the full rationale).
"""
from __future__ import annotations

from shapely.geometry import Point, Polygon, box
from shapely.ops import snap

from app.services.layout_engine.geometry import EPS, Rect, Segment

_AREA_EPS = EPS * EPS  # ~1 mm^2 floor for "non-trivial area"


def polygon_from_vertices(vertices) -> Polygon:
    """``vertices``: objects with ``.x``/``.y`` (e.g. schema ``Vertex``)."""
    return Polygon([(v.x, v.y) for v in vertices])


def rect_to_polygon(rect: Rect) -> Polygon:
    return box(rect.x, rect.y, rect.x2, rect.y2)


def room_to_polygon(room) -> Polygon:
    """Return a room's real outline, falling back to its rectangular bbox."""
    if room.vertices is not None:
        return polygon_from_vertices(room.vertices)
    return box(room.x, room.y, room.x + room.w, room.y + room.h)


def plot_to_polygon(plot) -> Polygon:
    """Return a plot's real boundary without changing the rectangular path."""
    if plot.boundary is not None:
        return polygon_from_vertices(plot.boundary)
    return box(0.0, 0.0, plot.width_m, plot.depth_m)


def room_area(room) -> float:
    """Floor area from the outline; byte-identical multiplication for rects."""
    if room.vertices is None:
        return room.w * room.h
    return room_to_polygon(room).area


def is_axis_aligned_rect(polygon: Polygon) -> bool:
    """True if ``polygon`` fully occupies its own bounding box — i.e. it *is*
    an axis-aligned rectangle, whatever its vertex count (collinear extra
    vertices along a straight edge don't change this test).

    Tolerance is a fixed, size-independent area floor (`_AREA_EPS`), not a
    fraction of the room's own area: a real clipped corner (e.g. a boundary
    chamfer nibbling a leaf) can be a small fraction of a large room's area
    while still being a geometrically real, non-negligible notch — scaling
    the tolerance by the room's own size let exactly that case slip through
    as a false "plain rect" and silently drop its true clipped shape."""
    minx, miny, maxx, maxy = polygon.bounds
    bbox_area = (maxx - minx) * (maxy - miny)
    return abs(polygon.area - bbox_area) <= _AREA_EPS


def shared_edges(a: Polygon, b: Polygon, eps: float = EPS) -> list[Segment]:
    """Straight-line segments where two polygons' boundaries touch along a
    run (not a single point — corner-only contact is not adjacency, mirroring
    ``Rect.shared_edge``'s documented rule). A non-convex pair can share more
    than one disjoint run, hence a list."""
    # Canonical plans round coordinates to millimetres before editor sync.
    # Snap that harmless drift back together so rebuilding derived walls does
    # not drop an edge whose two serialized endpoints differ by < EPS.
    inter = snap(a, b, eps).boundary.intersection(b.boundary)
    geoms = list(getattr(inter, "geoms", [inter]))
    segments: list[Segment] = []
    for geom in geoms:
        if geom.geom_type != "LineString" or geom.length <= eps:
            continue
        coords = list(geom.coords)
        for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
            if abs(x1 - x2) <= eps and abs(y1 - y2) <= eps:
                continue  # degenerate zero-length hop between coincident points
            segments.append(Segment(x1, y1, x2, y2))
    return segments


def is_on_boundary(point: tuple[float, float], plot_polygon: Polygon, eps: float = EPS) -> bool:
    return plot_polygon.exterior.distance(Point(point)) <= eps
