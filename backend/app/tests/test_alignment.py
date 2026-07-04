"""Phase 4 Stage 7 — box alignment (snap + merge collinear cuts)."""
from app.services.planning.alignment import align
from app.services.planning.boundary import Rect
from app.services.planning.slicing_tree import Item


def _pairs(*specs):
    return [(Item(id=i, area=w * d), Rect(x, z, w, d)) for (i, x, z, w, d) in specs]


def _overlap(a: Rect, b: Rect, eps=0.01) -> bool:
    return (
        a.x + eps < b.x + b.w and b.x + eps < a.x + a.w
        and a.z + eps < b.z + b.d and b.z + eps < a.z + a.d
    )


def test_near_collinear_cuts_merge_to_one_line():
    placed = _pairs(
        ("a", 0.0, 0.0, 5.03, 3.0),
        ("b", 5.03, 0.0, 5.0, 3.0),
        ("c", 0.0, 3.0, 5.08, 3.0),   # right edge 0.05 off from row above
        ("d", 5.08, 3.0, 4.95, 3.0),
    )
    aligned, _ = align(placed)
    rects = {item.id: r for item, r in aligned}
    # the two internal cuts (5.03, 5.08) collapse to a single collinear x
    assert abs((rects["a"].x + rects["a"].w) - (rects["c"].x + rects["c"].w)) < 1e-6


def test_alignment_preserves_shared_edges_no_overlap():
    placed = _pairs(
        ("a", 0.0, 0.0, 5.031, 4.0),
        ("b", 5.031, 0.0, 4.969, 4.0),
        ("c", 0.0, 4.0, 10.0, 4.0),
    )
    aligned, _ = align(placed)
    rects = [r for _, r in aligned]
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            assert not _overlap(a, b)
    # a and b still share the (snapped) vertical wall
    a = next(r for it, r in aligned if it.id == "a")
    b = next(r for it, r in aligned if it.id == "b")
    assert abs((a.x + a.w) - b.x) < 1e-6


def test_alignment_snaps_to_grid():
    placed = _pairs(("a", 0.0, 0.0, 4.237, 3.0))
    aligned, _ = align(placed)
    _, r = aligned[0]
    # edges land on the 0.05 grid
    assert abs((r.x + r.w) / 0.05 - round((r.x + r.w) / 0.05)) < 1e-6


def test_alignment_is_deterministic():
    placed = _pairs(("a", 0.0, 0.0, 5.03, 3.0), ("b", 5.03, 0.0, 4.97, 3.0))
    assert align(placed) == align(placed)


def test_alignment_empty():
    assert align([]) == ([], [])
