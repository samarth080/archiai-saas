"""Phase 8 arbitrary-program extraction to geometry acceptance matrix."""

import json
from pathlib import Path

from app.schemas.requirements import PlotSpec, RequirementsSpec
from app.services.clarification import apply_defaults
from app.services.extraction import normalize_extraction
from app.services.layout_engine.engine import generate_plan
from app.services.quality.hard_constraints import validate

GOLDEN = Path(__file__).parent / "golden_prompts.json"
NON_RESIDENTIAL_TYPES = {"clinic", "office", "other"}


def test_fifteen_non_residential_briefs_generate_valid_layouts_on_a_fit_plot():
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))["prompts"]
    cases = [
        case
        for case in cases
        if case["expect"].get("building_type") in NON_RESIDENTIAL_TYPES
    ]

    assert len(cases) >= 15
    for case in cases:
        spec = RequirementsSpec.model_validate(
            normalize_extraction({"rooms": [], "spaces": []}, prompt=case["prompt"])
        )
        spec = spec.model_copy(
            update={"plot": PlotSpec(width_m=20, depth_m=30)},
            deep=True,
        )
        defaulted = apply_defaults(spec)
        plan = generate_plan(defaulted)

        assert validate(plan, defaulted) == [], case["id"]
