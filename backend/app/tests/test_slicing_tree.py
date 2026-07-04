"""Phase 4 Stage 6 — guillotine slicing tree property tests."""
from app.services.planning.boundary import ALL_EDGES, Rect
from app.services.planning.slicing_tree import Item, SliceEdge, build_tree, leaves

_EPS = 0.05


def _share_wall(a: Rect, b: Rect) -> bool:
    x_touch = abs((a.x + a.w) - b.x) < _EPS or abs((b.x + b.w) - a.x) < _EPS
    z_touch = abs((a.z + a.d) - b.z) < _EPS or abs((b.z + b.d) - a.z) < _EPS
    z_overlap = min(a.z + a.d, b.z + b.d) - max(a.z, b.z) > _EPS
    x_overlap = min(a.x + a.w, b.x + b.w) - max(a.x, b.x) > _EPS
    return (x_touch and z_overlap) or (z_touch and x_overlap)


def _overlaps(a: Rect, b: Rect) -> bool:
    return (
        a.x + _EPS < b.x + b.w and b.x + _EPS < a.x + a.w
        and a.z + _EPS < b.z + b.d and b.z + _EPS < a.z + a.d
    )


def _leaf_rect(tree, item_id: str) -> Rect:
    return next(leaf.rect for leaf in leaves(tree) if leaf.item.id == item_id)


def _items(*specs):
    return [Item(id=i, area=area, min_w=mw, min_d=md, needs_external=ext)
            for (i, area, mw, md, ext) in specs]


# ── Guillotine invariants ─────────────────────────────────────────────────────


def test_leaves_tile_the_rect_exactly_with_no_overlap():
    rect = Rect(0, 0, 20, 12)
    items = _items(
        ("a", 40, 2, 2, False), ("b", 30, 2, 2, False),
        ("c", 50, 2, 2, False), ("d", 20, 2, 2, False), ("e", 25, 2, 2, False),
    )
    tree = build_tree(items, rect, ALL_EDGES, [])
    rects = [leaf.rect for leaf in leaves(tree)]

    assert len(rects) == 5
    # tiles exactly
    assert abs(sum(r.area for r in rects) - rect.area) < 0.1
    # no overlap
    for i, ra in enumerate(rects):
        for rb in rects[i + 1:]:
            assert not _overlaps(ra, rb)
        # inside footprint
        assert ra.x >= -_EPS and ra.z >= -_EPS
        assert ra.x + ra.w <= rect.w + _EPS and ra.z + ra.d <= rect.d + _EPS


# ── MUST adjacency is structural ──────────────────────────────────────────────


def test_two_must_items_are_siblings_sharing_a_wall():
    rect = Rect(0, 0, 10, 8)
    items = _items(("a", 40, 2, 2, False), ("b", 40, 2, 2, False))
    tree = build_tree(items, rect, ALL_EDGES, [SliceEdge("a", "b", "must")])
    assert _share_wall(_leaf_rect(tree, "a"), _leaf_rect(tree, "b"))


def test_must_pair_stays_adjacent_among_many():
    rect = Rect(0, 0, 24, 12)
    items = _items(
        ("a", 30, 2, 2, False), ("b", 30, 2, 2, False),
        ("c", 30, 2, 2, False), ("d", 30, 2, 2, False),
    )
    # a MUST b — they must end up sharing a wall despite c, d competing.
    tree = build_tree(items, rect, ALL_EDGES, [SliceEdge("a", "b", "must")])
    assert _share_wall(_leaf_rect(tree, "a"), _leaf_rect(tree, "b"))


def test_avoid_pair_is_pushed_apart():
    rect = Rect(0, 0, 24, 12)
    items = _items(
        ("a", 30, 2, 2, False), ("b", 30, 2, 2, False),
        ("c", 30, 2, 2, False), ("d", 30, 2, 2, False),
    )
    tree = build_tree(items, rect, ALL_EDGES, [SliceEdge("a", "b", "avoid")])
    # avoid pair should not share a wall
    assert not _share_wall(_leaf_rect(tree, "a"), _leaf_rect(tree, "b"))


# ── External-wall routing ─────────────────────────────────────────────────────


def test_external_room_reaches_a_boundary_edge():
    rect = Rect(0, 0, 20, 12)
    items = _items(
        ("ext", 40, 2, 2, True),   # needs an exterior wall
        ("s1", 30, 2, 2, False), ("s2", 30, 2, 2, False), ("s3", 30, 2, 2, False),
    )
    tree = build_tree(items, rect, ALL_EDGES, [])
    r = _leaf_rect(tree, "ext")
    touches = (
        abs(r.x - 0) < _EPS or abs((r.x + r.w) - rect.w) < _EPS
        or abs(r.z - 0) < _EPS or abs((r.z + r.d) - rect.d) < _EPS
    )
    assert touches


# ── Min dims + determinism + large k ─────────────────────────────────────────


def test_leaves_respect_min_dims_in_a_generous_rect():
    rect = Rect(0, 0, 24, 16)
    items = _items(*[(chr(97 + i), 30, 3, 3, False) for i in range(5)])
    tree = build_tree(items, rect, ALL_EDGES, [])
    for leaf in leaves(tree):
        assert leaf.rect.w >= 3 - _EPS
        assert leaf.rect.d >= 3 - _EPS


def test_build_is_deterministic():
    rect = Rect(0, 0, 20, 12)
    items = _items(
        ("a", 40, 2, 2, True), ("b", 30, 2, 2, False),
        ("c", 50, 2, 2, False), ("d", 20, 2, 2, True),
    )
    edges = [SliceEdge("a", "b", "should"), SliceEdge("c", "d", "must")]
    first = [(l.item.id, l.rect) for l in leaves(build_tree(items, rect, ALL_EDGES, edges))]
    second = [(l.item.id, l.rect) for l in leaves(build_tree(items, rect, ALL_EDGES, edges))]
    assert first == second


def test_large_k_greedy_path_still_tiles_exactly():
    rect = Rect(0, 0, 30, 20)
    items = _items(*[(chr(97 + i), 20 + i, 2, 2, False) for i in range(9)])
    tree = build_tree(items, rect, ALL_EDGES, [])
    rects = [leaf.rect for leaf in leaves(tree)]
    assert len(rects) == 9
    assert abs(sum(r.area for r in rects) - rect.area) < 0.2
    for i, ra in enumerate(rects):
        for rb in rects[i + 1:]:
            assert not _overlaps(ra, rb)
