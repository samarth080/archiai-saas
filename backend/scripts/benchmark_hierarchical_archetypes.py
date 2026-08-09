"""Print the Phase 10.1 composed-school benchmark against Phase 9 geometry."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.schemas.requirements import RequirementsSpec
from app.services.layout_engine.engine import generate_plan
from app.services.layout_engine.search import best_candidate
from app.services.quality.hard_constraints import validate
from app.services.quality.scorer import score


FIXTURE = (
    Path(__file__).parents[1]
    / "app"
    / "tests"
    / "fixtures"
    / "requirements"
    / "phase10_composed_school.json"
)
MAX_BEST_OF_64_SECONDS = 3.0


@dataclass(frozen=True)
class CompositionBenchmark:
    baseline_score: int
    composed_score: int
    baseline_doors: int
    composed_doors: int
    best_ms: float
    archetypes: tuple[str, ...]


def run_benchmark() -> CompositionBenchmark:
    spec = RequirementsSpec.model_validate_json(FIXTURE.read_text(encoding="utf-8"))
    baseline_spec = spec.model_copy(update={"layout_style": "zoned_bands"})
    baseline = generate_plan(baseline_spec)
    started = time.perf_counter()
    composed = best_candidate(spec, n=64, seed=0)
    best_ms = (time.perf_counter() - started) * 1000

    assert validate(baseline, baseline_spec) == []
    assert validate(composed, spec) == []
    return CompositionBenchmark(
        baseline_score=score(baseline, baseline_spec).score,
        composed_score=score(composed, spec).score,
        baseline_doors=len(baseline.doors),
        composed_doors=len(composed.doors),
        best_ms=best_ms,
        archetypes=tuple(
            reason.archetype
            for reason in composed.archetype_reasons or []
        ),
    )


def render_markdown(row: CompositionBenchmark) -> str:
    return "\n".join([
        "| Fixture | Phase 9 global score | Phase 10.1 score | Global doors | Composed doors | Best-of-64 ms | Regions |",
        "|---|---:|---:|---:|---:|---:|---|",
        (
            f"| composed_school | {row.baseline_score} | {row.composed_score} | "
            f"{row.baseline_doors} | {row.composed_doors} | {row.best_ms:.1f} | "
            f"{', '.join(row.archetypes)} |"
        ),
    ])


def main() -> int:
    row = run_benchmark()
    print(render_markdown(row))
    passed = (
        row.composed_score >= row.baseline_score
        and row.composed_doors < row.baseline_doors
        and len(set(row.archetypes)) >= 2
        and row.best_ms <= MAX_BEST_OF_64_SECONDS * 1000
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
