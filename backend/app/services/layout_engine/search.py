"""layout_engine/search.py — workflow Phase 5.1: generate-and-score
candidate search.

The production MVP API uses :func:`best_candidate` for rectangular plots.
Every candidate flows through the exact same proven ``engine.plan_from_program``
pipeline ``generate_plan()`` itself uses, parameterized by a room-order-
shuffled copy of the same ``EngineProgram`` — so a candidate carries the
identical zero-overlap/zero-gap/reachability guarantees a single-shot plan
already has; search only varies WHICH valid layout comes out, never how
validity itself is checked.

Variation axis implemented: placement-order permutation of the program's
room list (a seeded shuffle). ``subdivide()``'s cumulative-area halving and
the archetype band-grouping helpers are order-sensitive, so different
orderings genuinely produce different geometries through the exact same
deterministic code — no new placement logic needed. The doc's other three
axes (per-archetype parameter jitter, a subdivision cut-axis bias, splitting
the candidate budget across the top-2 viable archetypes) are deferred — a
bounded first slice, same practice as every other phase in this workflow.
"""
import dataclasses
import random

from app.config.mvp_defaults import DEFAULT_FACING, DEFAULT_PLOT_DEPTH_M, DEFAULT_PLOT_WIDTH_M
from app.schemas.layout_plan import LayoutPlan
from app.schemas.requirements import RequirementsSpec
from app.services.layout_adapter import layout_plan_to_canvas
from app.services.layout_engine.engine import (
    DoesNotFitError,
    _build_program,
    generate_plan,
    plan_from_program,
)
from app.services.planning import EngineProgram, ProgramGraph, from_requirements
from app.services.planning.graph_scoring import score_graph_satisfaction
from app.services.planning.program_completion import ensure_corridor, ensure_entry
from app.services.quality.scorer import score

# Hard violations always rank worse than any valid candidate (a large fixed
# floor), but +10 per violation still ranks "less broken" above "more
# broken" for diagnostics — matches the doc's own energy() pseudocode.
_HARD_VIOLATION_FLOOR = 1000.0
_HARD_VIOLATION_STEP = 10.0
_GRAPH_WEIGHT = 2.0


@dataclasses.dataclass(frozen=True)
class Candidate:
    plan: LayoutPlan
    energy: float
    seed: int


def energy(plan: LayoutPlan, spec: RequirementsSpec, graph: ProgramGraph) -> float:
    """Lower is better. ``include_vastu`` stays False here deliberately —
    Vastu is an explicit product opt-in the caller decides, not something
    the search process should weight candidates by on its own."""
    report = score(plan, spec, include_vastu=False)
    if report.hard_violations:
        return _HARD_VIOLATION_FLOOR + _HARD_VIOLATION_STEP * len(report.hard_violations)
    satisfaction = score_graph_satisfaction(graph, layout_plan_to_canvas(plan))
    return (1 - report.score / 100) + _GRAPH_WEIGHT * (1 - satisfaction.score)


def _shuffled(program: EngineProgram, rng: random.Random) -> EngineProgram:
    needs = list(program.needs)
    rng.shuffle(needs)
    return dataclasses.replace(program, needs=needs)


def generate_candidates(spec: RequirementsSpec, *, n: int = 64, seed: int = 0) -> list[Candidate]:
    """Deterministic: the same ``spec`` + ``seed`` always produces the same
    ranked candidate list, ranked lowest-energy (best) first. The first
    candidate is always the plain single-shot ordering (identical to what
    ``generate_plan(spec)`` itself would produce); the rest are seeded
    shuffles of it, deduplicated by room order so a program too small to
    have distinct permutations doesn't pad the list with repeats. Raises
    the last ``DoesNotFitError`` seen only if literally every attempt
    failed — a program that fits under most orderings but not all still
    returns its valid candidates."""
    plot_w = spec.plot.width_m or DEFAULT_PLOT_WIDTH_M
    plot_d = spec.plot.depth_m or DEFAULT_PLOT_DEPTH_M
    facing = spec.facing or DEFAULT_FACING

    graph = ensure_corridor(ensure_entry(from_requirements(spec)))
    base_program = _build_program(spec)

    rng = random.Random(seed)
    candidates: list[Candidate] = []
    last_error: DoesNotFitError | None = None
    seen_orders: set[tuple[str, ...]] = set()
    for i in range(max(0, n)):
        program = base_program if i == 0 else _shuffled(base_program, rng)
        order = tuple(need.key for need in program.needs)
        if order in seen_orders:
            continue
        seen_orders.add(order)
        try:
            plan = plan_from_program(spec, program, plot_w, plot_d, facing)
        except DoesNotFitError as exc:
            last_error = exc
            continue
        candidates.append(Candidate(plan=plan, energy=energy(plan, spec, graph), seed=seed + i))

    if not candidates and last_error is not None:
        raise last_error
    candidates.sort(key=lambda c: c.energy)
    return candidates


def best_candidate(spec: RequirementsSpec, *, n: int = 64, seed: int = 0) -> LayoutPlan:
    # Polygon subdivision has its own proven geometry path and no band/order
    # search surface yet. Never discard the supplied boundary by treating its
    # bounding box as a rectangular search plot.
    if spec.plot.boundary is not None or spec.floors > 1:
        return generate_plan(spec)
    candidates = generate_candidates(spec, n=n, seed=seed)
    if not candidates:
        raise DoesNotFitError("no candidate could be generated")
    return candidates[0].plan
