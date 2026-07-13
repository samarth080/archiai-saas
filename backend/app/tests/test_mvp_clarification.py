"""MVP workflow Phase 3 — deterministic clarification and defaults."""

import json
from pathlib import Path

from app.schemas.requirements import RequirementsSpec, RoomType
from app.services.clarification import (
    BATHROOM_QUESTION,
    FACING_QUESTION,
    PLOT_SIZE_QUESTION,
    ROOM_PROGRAM_QUESTION,
    apply_defaults,
    apply_defaults_with_report,
    assess,
)
from app.services.extraction import normalize_extraction
from app.services.layout_engine.engine import DoesNotFitError, generate_plan
from app.services.quality.hard_constraints import validate

GOLDEN = Path(__file__).parent / "golden_prompts.json"


def _count(spec: RequirementsSpec, room_type: RoomType) -> int:
    return sum(room.count for room in spec.rooms if room.type == room_type)


def test_vague_program_routes_to_four_guided_questions():
    spec = RequirementsSpec(
        rooms=[],
        missing_info=["rooms", "plot_size", "facing", "bathroom_count"],
    )

    result = assess(spec)

    assert result.route == "vague"
    assert result.questions == [
        ROOM_PROGRAM_QUESTION,
        PLOT_SIZE_QUESTION,
        FACING_QUESTION,
        BATHROOM_QUESTION,
    ]
    assert result.optional_missing == []


def test_detailed_program_generates_and_surfaces_only_optional_questions():
    spec = RequirementsSpec.model_validate(
        {
            "rooms": [
                {"type": "bedroom", "count": 3},
                {"type": "living_room", "count": 1},
                {"type": "kitchen", "count": 1},
            ],
            "plot": {"width_m": None, "depth_m": None},
            "facing": None,
            "missing_info": ["plot_size", "facing", "bathroom_count"],
        }
    )

    result = assess(spec)

    assert result.route == "generate"
    assert result.questions == []
    assert result.optional_missing == [
        PLOT_SIZE_QUESTION,
        FACING_QUESTION,
        BATHROOM_QUESTION,
    ]


def test_extraction_conflict_marker_blocks_generation_with_human_question():
    spec = RequirementsSpec.model_validate(
        {
            "rooms": [{"type": "bedroom", "count": 3}],
            "missing_info": ["conflict: 2BHK conflicts with 3 explicit bedrooms"],
        }
    )

    result = assess(spec)

    assert result.route == "conflict"
    assert result.optional_missing == []
    assert len(result.questions) == 1
    assert "2BHK conflicts with 3 explicit bedrooms" in result.questions[0]
    assert "which" in result.questions[0].lower()


def test_entirely_missing_junk_is_vague_even_if_model_left_conflict_text():
    spec = RequirementsSpec(
        rooms=[],
        missing_info=["rooms", "conflict: no usable spatial request"],
    )

    assert assess(spec).route == "vague"


def test_does_not_fit_error_becomes_plot_resolution_question():
    spec = RequirementsSpec.model_validate(
        {"rooms": [{"type": "bedroom", "count": 2}]}
    )
    error = DoesNotFitError(
        "plot too small to satisfy room minima",
        required_area=80.0,
        plot_area=54.0,
    )

    result = assess(spec, fit_error=error)

    assert result.route == "conflict"
    assert "plot" in result.questions[0].lower()
    assert "80" in result.questions[0]
    assert "54" in result.questions[0]


def test_apply_defaults_is_non_mutating_transparent_and_fit_able():
    spec = RequirementsSpec.model_validate(
        {
            "building_type": "house",
            "rooms": [
                {"type": "bedroom", "count": 3},
                {"type": "living_room", "count": 1},
                {"type": "kitchen", "count": 1},
            ],
            "missing_info": ["plot_size", "facing", "bathroom_count"],
        }
    )
    original = spec.model_copy(deep=True)

    report = apply_defaults_with_report(spec)
    defaulted = apply_defaults(spec)

    assert spec == original
    assert report.requirements == defaulted
    assert defaulted.plot.width_m == 9.0
    assert defaulted.plot.depth_m == 12.0
    assert defaulted.facing.value == "east"
    assert defaulted.floors == 1
    assert _count(defaulted, RoomType.bathroom) == 2
    assert report.defaults_applied == [
        "9×12 m plot",
        "east facing",
        "2 bathrooms",
    ]
    assert assess(defaulted).route == "generate"

    plan = generate_plan(defaulted)
    assert validate(plan) == []


def test_apply_defaults_preserves_explicit_values():
    spec = RequirementsSpec.model_validate(
        {
            "rooms": [
                {"type": "bedroom", "count": 2},
                {"type": "bathroom", "count": 1},
            ],
            "plot": {"width_m": 10.0, "depth_m": 14.0},
            "facing": "north",
            "missing_info": [],
        }
    )

    report = apply_defaults_with_report(spec)

    assert report.requirements == spec
    assert report.defaults_applied == []


def test_all_ten_golden_prompts_route_correctly_without_model_dependency():
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))["prompts"]

    routes = {}
    for case in cases:
        normalized = normalize_extraction({"rooms": []}, prompt=case["prompt"])
        spec = RequirementsSpec.model_validate(normalized)
        routes[case["id"]] = assess(spec).route

    assert routes == {
        case["id"]: case["expect"]["route"] for case in cases
    }
