"""Box alignment pass (Phase 4 Stage 7).

Graph2Plan's box-alignment made rule-based and deterministic. Operates on the
realized leaf rectangles: snaps every cut coordinate to a grid and merges cut
lines that are within a tolerance of each other, so walls from sibling subtrees
become collinear (cleaner plans, fewer partition-wall segments downstream). This
is done by canonicalising the *shared* x/z coordinates, so adjacent rectangles
keep sharing the same (snapped) edge — the exact tiling is preserved by
construction, no overlaps or gaps introduced.

Sliver rooms below the minimum dimension are reported as warnings (absorb/merge
and aspect-rotation repair are noted as future refinements). Pure, deterministic.
"""
from __future__ import annotations

from app.services.planning.boundary import Rect
from app.services.planning.slicing_tree import Item

_GRID = 0.05
_MERGE_TOL = 0.10
_MIN_DIM = 1.5


def _canonical_coords(coords: list[float], grid: float, merge_tol: float) -> dict[float, float]:
    """Snap each coordinate to `grid`, then collapse runs within `merge_tol` to a
    single canonical value. Returns original -> canonical."""
    snapped = {c: round(round(c / grid) * grid, 4) for c in coords}
    ordered = sorted(set(snapped.values()))
    canonical: dict[float, float] = {}
    anchor = None
    for value in ordered:
        if anchor is None or value - anchor > merge_tol:
            anchor = value
        canonical[value] = anchor
    return {original: canonical[snap] for original, snap in snapped.items()}


def align(
    placed: list[tuple[Item, Rect]],
    *,
    grid: float = _GRID,
    merge_tol: float = _MERGE_TOL,
) -> tuple[list[tuple[Item, Rect]], list[str]]:
    if not placed:
        return placed, []

    xs = [r.x for _, r in placed] + [r.x + r.w for _, r in placed]
    zs = [r.z for _, r in placed] + [r.z + r.d for _, r in placed]
    xmap = _canonical_coords(xs, grid, merge_tol)
    zmap = _canonical_coords(zs, grid, merge_tol)

    result: list[tuple[Item, Rect]] = []
    warnings: list[str] = []
    for item, r in placed:
        x0, x1 = xmap[r.x], xmap[r.x + r.w]
        z0, z1 = zmap[r.z], zmap[r.z + r.d]
        w, d = round(x1 - x0, 4), round(z1 - z0, 4)
        if w < _MIN_DIM - 0.01 or d < _MIN_DIM - 0.01:
            warnings.append(f"Room '{item.id}' is a sliver ({w:g}x{d:g} m) after alignment")
        result.append((item, Rect(x0, z0, w, d)))
    return result, warnings
