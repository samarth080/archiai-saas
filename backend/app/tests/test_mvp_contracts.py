"""MVP workflow Phase 0 — contract lock tests (Steps 0.3 + 0.4) and the
extended /api/health (Step 0.1).

Fixture note: the clinic fixture expresses consultation rooms as `study`
(closed RoomType enum has no clinical types by design — the MVP is
residential-first; `building_type: clinic` is what the extraction gate checks).
"""
import json
from pathlib import Path

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.schemas.layout_plan import Door, LayoutPlan, PlanPlot, PlanRoom, Wall
from app.schemas.quality_report import QualityReport, QualityWarning, Violation
from app.schemas.requirements import RequirementsSpec, RoomType

FIXTURES = Path(__file__).parent / "fixtures" / "requirements"
GOLDEN = Path(__file__).parent / "golden_prompts.json"


# ── Step 0.4 — fixtures and golden prompts load ──────────────────────────────


@pytest.mark.parametrize("name", ["1bhk", "2bhk", "3bhk_adjacencies", "4bhk", "clinic"])
def test_fixture_validates_and_round_trips(name):
    raw = (FIXTURES / f"{name}.json").read_text()
    spec = RequirementsSpec.model_validate_json(raw)
    again = RequirementsSpec.model_validate_json(spec.model_dump_json())
    assert again == spec


def test_golden_prompt_suite_loads_with_ten_prompts():
    data = json.loads(GOLDEN.read_text())
    assert len(data["prompts"]) == 10
    ids = [p["id"] for p in data["prompts"]]
    assert len(set(ids)) == 10
    assert all(p["prompt"].strip() for p in data["prompts"])
    assert all(p["expect"]["route"] in ("generate", "vague", "conflict") for p in data["prompts"])


# ── Step 0.3 — the wrong-type failure modes are caught at the boundary ───────


def test_string_count_rejected():
    with pytest.raises(ValidationError):
        RequirementsSpec.model_validate(
            {"rooms": [{"type": "bedroom", "count": "three"}]}
        )


def test_float_count_rejected():
    with pytest.raises(ValidationError):
        RequirementsSpec.model_validate({"rooms": [{"type": "bedroom", "count": 3.0}]})


def test_unknown_room_type_rejected():
    with pytest.raises(ValidationError):
        RequirementsSpec.model_validate({"rooms": [{"type": "dungeon", "count": 1}]})


def test_string_dimension_rejected():
    with pytest.raises(ValidationError):
        RequirementsSpec.model_validate({"plot": {"width_m": "3.5", "depth_m": 12.0}})


def test_extra_keys_rejected():
    with pytest.raises(ValidationError):
        RequirementsSpec.model_validate({"rooms": [], "hallucinated_field": True})


def test_plot_bounds_enforced():
    with pytest.raises(ValidationError):
        RequirementsSpec.model_validate({"plot": {"width_m": 150.0, "depth_m": 12.0}})
    with pytest.raises(ValidationError):
        RequirementsSpec.model_validate({"plot": {"width_m": -3.0, "depth_m": 12.0}})


def test_int_dimension_coerces_to_float():
    spec = RequirementsSpec.model_validate({"plot": {"width_m": 9, "depth_m": 12}})
    assert spec.plot.width_m == 9.0


# ── Step 0.3 — LayoutPlan contract ───────────────────────────────────────────


def _plan() -> LayoutPlan:
    return LayoutPlan(
        plot=PlanPlot(width_m=9.0, depth_m=12.0),
        rooms=[PlanRoom(id="r1", type=RoomType.bedroom, label="Bedroom", x=0, y=0, w=3.5, h=3.5)],
        walls=[Wall(id="w1", x1=0, y1=0, x2=3.5, y2=0)],
        doors=[Door(id="d1", wall_ref="w1", offset=1.0)],
    )


def test_layout_plan_round_trips():
    plan = _plan()
    assert LayoutPlan.model_validate_json(plan.model_dump_json()) == plan


def test_rotation_limited_to_quarter_turns():
    for ok in (0, 90, 180, 270):
        PlanRoom(id="r", type=RoomType.study, label="S", x=0, y=0, w=3, h=3, rotation=ok)
    with pytest.raises(ValidationError):
        PlanRoom(id="r", type=RoomType.study, label="S", x=0, y=0, w=3, h=3, rotation=45)


def test_door_requires_wall_ref():
    with pytest.raises(ValidationError):
        Door.model_validate({"id": "d1", "offset": 1.0})


# ── Step 0.3 — QualityReport contract ────────────────────────────────────────


def test_quality_report_bounds_and_shapes():
    report = QualityReport(
        score=72,
        hard_violations=[Violation(code="overlap", room_ids=["r1", "r2"], message="Bedroom overlaps Kitchen")],
        warnings=[QualityWarning(code="vastu.kitchen_ne", message="Kitchen sits in the north-east zone", rule="vastu")],
    )
    assert report.hard_violations[0].code == "overlap"
    with pytest.raises(ValidationError):
        QualityReport(score=101)
    with pytest.raises(ValidationError):
        QualityReport(score=-1)


# ── Step 0.1 — extended health endpoint ──────────────────────────────────────


async def test_health_reports_db_and_llm(client: AsyncClient, monkeypatch):
    async def up(timeout_s: float = 2.0) -> bool:
        return True

    monkeypatch.setattr("app.main.llm_reachable", up)
    response = await client.get("/api/health")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["llm"] == "ok"


async def test_health_degrades_gracefully_when_llm_down(client: AsyncClient, monkeypatch):
    async def down(timeout_s: float = 2.0) -> bool:
        return False

    monkeypatch.setattr("app.main.llm_reachable", down)
    response = await client.get("/api/health")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"  # LLM down degrades a feature, not the app
    assert body["llm"] == "unreachable"
