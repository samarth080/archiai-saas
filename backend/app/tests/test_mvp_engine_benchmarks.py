"""Phase 9 score/runtime benchmark gate for every template fixture."""

import pytest

from app.services.parser.data.building_templates import BUILDING_TEMPLATES
from scripts.benchmark_mvp_engine import (
    MAX_BEST_OF_64_SECONDS,
    render_markdown,
    run_benchmarks,
)


@pytest.fixture(scope="module")
def benchmark_rows():
    return run_benchmarks()


def test_every_fixture_stays_within_score_and_runtime_budgets(benchmark_rows):
    assert {row.fixture for row in benchmark_rows} == set(BUILDING_TEMPLATES)
    for row in benchmark_rows:
        assert row.best_score >= row.single_score
        assert row.best_ms / 1000 <= MAX_BEST_OF_64_SECONDS


def test_benchmark_report_is_a_complete_markdown_table(benchmark_rows):
    report = render_markdown(benchmark_rows)

    assert report.startswith("| Fixture | Single score |")
    assert report.count("\n| ") == len(BUILDING_TEMPLATES)
    assert "SA is deferred until the Phase 5.2 benchmark gate" in report
