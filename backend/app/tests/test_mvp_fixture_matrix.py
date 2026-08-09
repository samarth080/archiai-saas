"""Phase 9 golden fixture matrix across every parser building template."""

import json
from pathlib import Path

import pytest

from app.schemas.requirements import RequirementsSpec
from app.services.layout_engine.engine import generate_plan, rebuild_derived_geometry
from app.services.parser.data.building_templates import BUILDING_TEMPLATES
from app.services.quality.hard_constraints import validate
from app.services.quality.scorer import score


FIXTURES = Path(__file__).parent / "fixtures" / "requirements"
GOLDENS = Path(__file__).parent / "fixtures" / "golden" / "phase9_layouts.json"
TEMPLATE_NAMES = tuple(BUILDING_TEMPLATES)


def _load(name: str) -> RequirementsSpec:
    return RequirementsSpec.model_validate_json(
        (FIXTURES / f"template_{name}.json").read_text(encoding="utf-8")
    )


def _goldens() -> dict:
    return json.loads(GOLDENS.read_text(encoding="utf-8"))


def test_fixture_matrix_covers_every_building_template():
    assert len(TEMPLATE_NAMES) >= 12
    assert {
        path.stem.removeprefix("template_")
        for path in FIXTURES.glob("template_*.json")
    } == set(TEMPLATE_NAMES)

    for name, expected in BUILDING_TEMPLATES.items():
        spec = _load(name)
        assert [
            (space.space_type, space.count, space.size_hint)
            for space in spec.spaces
        ] == expected


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_template_fixture_matches_golden_layout_and_quality(name: str):
    spec = _load(name)
    plan = generate_plan(spec)
    expected = _goldens()[name]

    assert validate(plan, spec) == []
    assert plan.model_dump(mode="json") == expected["layout"]
    assert score(plan, spec).score == pytest.approx(
        expected["quality_score"],
        abs=2,
    )


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_editor_rebuild_preserves_new_space_types_and_floors(name: str):
    spec = _load(name)
    plan = generate_plan(spec)
    stale = plan.model_copy(update={"walls": [], "doors": []})

    rebuilt = rebuild_derived_geometry(stale, spec)

    assert rebuilt.rooms == plan.rooms
    assert rebuilt.walls
    assert rebuilt.doors
    assert validate(rebuilt, spec) == []
    assert {room.floor for room in rebuilt.rooms} == set(range(spec.floors))
    assert len({wall.id for wall in rebuilt.walls}) == len(rebuilt.walls)
    assert len({door.id for door in rebuilt.doors}) == len(rebuilt.doors)
