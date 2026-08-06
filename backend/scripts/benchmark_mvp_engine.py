"""Print the Phase 9 canonical-engine benchmark matrix as Markdown."""

from __future__ import annotations

import time
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.schemas.requirements import RequirementsSpec
from app.services.layout_engine.engine import generate_plan
from app.services.layout_engine.search import best_candidate
from app.services.parser.data.building_templates import BUILDING_TEMPLATES
from app.services.quality.hard_constraints import validate
from app.services.quality.scorer import score


FIXTURES = Path(__file__).parents[1] / "app" / "tests" / "fixtures" / "requirements"
MAX_BEST_OF_64_SECONDS = 3.0


@dataclass(frozen=True)
class BenchmarkRow:
    fixture: str
    single_score: int
    best_score: int
    single_ms: float
    best_ms: float


def _timed(call):
    started = time.perf_counter()
    result = call()
    return result, (time.perf_counter() - started) * 1000


def benchmark_fixture(name: str) -> BenchmarkRow:
    spec = RequirementsSpec.model_validate_json(
        (FIXTURES / f"template_{name}.json").read_text(encoding="utf-8")
    )
    single, single_ms = _timed(lambda: generate_plan(spec))
    best, best_ms = _timed(lambda: best_candidate(spec, n=64, seed=0))
    assert validate(single, spec) == []
    assert validate(best, spec) == []
    return BenchmarkRow(
        fixture=name,
        single_score=score(single, spec).score,
        best_score=score(best, spec).score,
        single_ms=single_ms,
        best_ms=best_ms,
    )


def run_benchmarks() -> list[BenchmarkRow]:
    return [benchmark_fixture(name) for name in BUILDING_TEMPLATES]


def render_markdown(rows: list[BenchmarkRow]) -> str:
    lines = [
        "| Fixture | Single score | Best-of-64 score | SA score | Single ms | Best-of-64 ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    lines.extend(
        (
            f"| {row.fixture} | {row.single_score} | {row.best_score} | deferred | "
            f"{row.single_ms:.1f} | {row.best_ms:.1f} |"
        )
        for row in rows
    )
    lines.extend([
        "",
        "SA is deferred until the Phase 5.2 benchmark gate demonstrates value.",
    ])
    return "\n".join(lines)


def main() -> int:
    rows = run_benchmarks()
    print(render_markdown(rows))
    regressions = [
        row.fixture
        for row in rows
        if row.best_score < row.single_score
        or row.best_ms > MAX_BEST_OF_64_SECONDS * 1000
    ]
    if regressions:
        print(f"Benchmark gate failed: {', '.join(regressions)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
