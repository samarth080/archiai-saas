"""Graph-aware guillotine slicing tree (Phase 4 Stage 6) — the heart.

Pure algorithm over lightweight Items / SliceEdges / Rects (no ArchiAI domain
types), so it is exhaustively unit-testable in isolation. It builds a binary
guillotine partition of a rectangle by recursive balanced min-cut bipartition.

Three invariants hold *by construction* (Phase 4 §4.0):
  * every cut tiles its rectangle exactly → no overlaps, no gaps, inside footprint;
  * siblings across a cut share the full cut segment → MUST-adjacency is a
    tree-shape rule, not a scoring hope;
  * boundary contact propagates down each cut (see boundary.split_contact) →
    `requires_external_wall` is routed deterministically.

Fully deterministic: all enumeration is over sorted ids, all ties break to the
lexicographically smallest id set. Identical input → identical tree.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

from app.services.planning.boundary import Rect, split_contact

# Edge weight = cost of a cut *separating* the pair (higher = worse to split).
# AVOID is negative: separating an avoid-pair is desirable.
_WEIGHT = {"should": 3.0, "near": 2.0, "visual": 1.0, "avoid": -3.0, "must": 0.0}
_MUST_SPLIT_PENALTY = 1000.0     # splitting a MUST pair into different subtrees (len > 2)
_POSITION_PENALTY = 4.0          # a preferred_relative_position hint violated by the cut
_EXTERNAL_PENALTY = 10.0         # a needs_external item stranded with no boundary contact
_MIN_DIM_FLOOR = 1.5


@dataclass(frozen=True)
class Item:
    id: str
    area: float
    min_w: float = _MIN_DIM_FLOOR
    min_d: float = _MIN_DIM_FLOOR
    needs_external: bool = False


@dataclass(frozen=True)
class SliceEdge:
    a: str
    b: str
    relation: str = "should"   # must | should | near | visual | avoid
    rel_pos: str = "any"       # a relative to b: left_of|right_of|front|back|any


@dataclass(frozen=True)
class Leaf:
    item: Item
    rect: Rect


@dataclass(frozen=True)
class Branch:
    a: "Leaf | Branch"        # left (vertical) / front (horizontal)
    b: "Leaf | Branch"        # right / back
    direction: str            # "vertical" | "horizontal"
    ratio: float


TreeNode = "Leaf | Branch"


def leaves(node) -> list[Leaf]:
    if isinstance(node, Leaf):
        return [node]
    return leaves(node.a) + leaves(node.b)


# ── Bipartition enumeration ──────────────────────────────────────────────────


def _enumerate_bipartitions(ids: list[str], items_by_id: dict[str, Item], edges: list[SliceEdge]):
    """Deterministic set of (A, B) id-splits. Balanced sizes for small k;
    edge-weighted greedy agglomeration for large k. A always contains ids[0] so
    (A,B) and (B,A) aren't both produced."""
    k = len(ids)
    ids = sorted(ids)
    seen: set[frozenset[str]] = set()
    result: list[tuple[frozenset[str], frozenset[str]]] = []

    def add(a_ids: set[str]):
        if not a_ids or len(a_ids) == k:
            return
        key = frozenset(a_ids)
        if ids[0] not in a_ids:  # canonicalise so A holds the smallest id
            a_ids = set(ids) - a_ids
            key = frozenset(a_ids)
        if key in seen:
            return
        seen.add(key)
        result.append((frozenset(a_ids), frozenset(set(ids) - a_ids)))

    if k <= 6:
        for size in {k // 2, (k + 1) // 2}:
            for combo in combinations(ids, size):
                add(set(combo))
    else:
        # Greedy: seed A with the largest-area item, pull in the highest-weight
        # neighbour until A holds ~45% of the area. A couple of alternate seeds
        # give the candidate competition some diversity, still deterministically.
        total = sum(items_by_id[i].area for i in ids)
        by_area = sorted(ids, key=lambda i: (-items_by_id[i].area, i))
        for seed in by_area[:3]:
            a_ids = {seed}
            while sum(items_by_id[i].area for i in a_ids) < 0.45 * total and len(a_ids) < k - 1:
                best = min(
                    (i for i in ids if i not in a_ids),
                    key=lambda i: (-_weight_to_set(i, a_ids, edges), i),
                )
                a_ids.add(best)
            add(a_ids)
    return result


def _weight_to_set(item_id: str, group: set[str], edges: list[SliceEdge]) -> float:
    total = 0.0
    for e in edges:
        if (e.a == item_id and e.b in group) or (e.b == item_id and e.a in group):
            total += abs(_WEIGHT.get(e.relation, 1.0))
    return total


# ── Cost terms ───────────────────────────────────────────────────────────────


def _crossing_edges(a_ids: frozenset[str], b_ids: frozenset[str], edges: list[SliceEdge]):
    for e in edges:
        if (e.a in a_ids and e.b in b_ids) or (e.a in b_ids and e.b in a_ids):
            yield e


def _pick_direction(rect: Rect, crossing: list[SliceEdge]) -> str:
    vertical_votes = sum(1 for e in crossing if e.rel_pos in ("left_of", "right_of"))
    horizontal_votes = sum(1 for e in crossing if e.rel_pos in ("front", "back", "above", "below"))
    if vertical_votes > horizontal_votes:
        return "vertical"
    if horizontal_votes > vertical_votes:
        return "horizontal"
    # No hint (or tie): cut the longer side so children get plumper aspect ratios.
    return "vertical" if rect.w >= rect.d else "horizontal"


def _position_penalty(a_ids, b_ids, crossing, direction) -> float:
    penalty = 0.0
    for e in crossing:
        if e.rel_pos == "any":
            continue
        a_in_A = e.a in a_ids  # A = left/front child
        if e.rel_pos in ("left_of", "right_of"):
            if direction != "vertical":
                penalty += _POSITION_PENALTY
            else:
                want_a_left = e.rel_pos == "left_of"
                if want_a_left != a_in_A:
                    penalty += _POSITION_PENALTY
        elif e.rel_pos in ("front", "back", "above", "below"):
            if direction != "horizontal":
                penalty += _POSITION_PENALTY
            else:
                want_a_front = e.rel_pos in ("front", "below")
                if want_a_front != a_in_A:
                    penalty += _POSITION_PENALTY
    return penalty


def _external_penalty(a_items, b_items, contact, direction) -> float:
    contact_a, contact_b = split_contact(contact, direction)
    penalty = 0.0
    if not contact_a:
        penalty += _EXTERNAL_PENALTY * sum(1 for it in a_items if it.needs_external)
    if not contact_b:
        penalty += _EXTERNAL_PENALTY * sum(1 for it in b_items if it.needs_external)
    return penalty


def _area(items) -> float:
    return sum(it.area for it in items)


def _imbalance(a_items, b_items) -> float:
    total = _area(a_items) + _area(b_items)
    if total <= 0:
        return 0.0
    return abs(_area(a_items) / total - 0.5) * 2.0


# ── Recursion ────────────────────────────────────────────────────────────────


def _ratio_for(a_items, b_items, rect: Rect, direction: str) -> float:
    total = _area(a_items) + _area(b_items)
    base = _area(a_items) / total if total > 0 else 0.5
    span = rect.w if direction == "vertical" else rect.d
    if span <= 0:
        return 0.5
    min_a = max((it.min_w if direction == "vertical" else it.min_d) for it in a_items)
    min_b = max((it.min_w if direction == "vertical" else it.min_d) for it in b_items)
    lo = min_a / span
    hi = 1.0 - min_b / span
    if lo > hi:  # rect too small to honour both mins — centre it, scorer flags size
        return 0.5
    return max(lo, min(base, hi))


def _guillotine(rect: Rect, direction: str, ratio: float) -> tuple[Rect, Rect]:
    if direction == "vertical":
        wa = round(rect.w * ratio, 4)
        a = Rect(rect.x, rect.z, wa, rect.d)
        b = Rect(round(rect.x + wa, 4), rect.z, round(rect.w - wa, 4), rect.d)
    else:
        da = round(rect.d * ratio, 4)
        a = Rect(rect.x, rect.z, rect.w, da)
        b = Rect(rect.x, round(rect.z + da, 4), rect.w, round(rect.d - da, 4))
    return a, b


def build_tree(items: list[Item], rect: Rect, contact: frozenset[str], edges: list[SliceEdge]):
    """Build a guillotine slicing tree placing every item inside `rect`."""
    if len(items) == 1:
        return Leaf(items[0], rect)

    items_by_id = {it.id: it for it in items}
    ids = [it.id for it in items]
    penalise_must = len(items) > 2  # at len 2 the split *creates* the shared wall

    best = None  # (cost_key, a_items, b_items, direction, ratio)
    for a_ids, b_ids in _enumerate_bipartitions(ids, items_by_id, edges):
        a_items = [items_by_id[i] for i in sorted(a_ids)]
        b_items = [items_by_id[i] for i in sorted(b_ids)]
        crossing = list(_crossing_edges(a_ids, b_ids, edges))
        direction = _pick_direction(rect, crossing)

        must_split = sum(1 for e in crossing if e.relation == "must")
        cost = (
            (must_split * _MUST_SPLIT_PENALTY if penalise_must else 0.0)
            + sum(_WEIGHT.get(e.relation, 1.0) for e in crossing)
            + _position_penalty(a_ids, b_ids, crossing, direction)
            + _external_penalty(a_items, b_items, contact, direction)
            + _imbalance(a_items, b_items)
        )
        key = (round(cost, 4), tuple(sorted(a_ids)))
        if best is None or key < best[0]:
            best = (key, a_items, b_items, direction)

    _, a_items, b_items, direction = best
    ratio = _ratio_for(a_items, b_items, rect, direction)
    rect_a, rect_b = _guillotine(rect, direction, ratio)
    contact_a, contact_b = split_contact(contact, direction)
    return Branch(
        a=build_tree(a_items, rect_a, contact_a, edges),
        b=build_tree(b_items, rect_b, contact_b, edges),
        direction=direction,
        ratio=ratio,
    )
