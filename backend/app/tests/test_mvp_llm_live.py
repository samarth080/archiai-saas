"""Opt-in Phase 2 live gate against host LM Studio.

Run only after workflow Step 0.2 is complete:
    RUN_LLM_TESTS=1 pytest app/tests/test_mvp_llm_live.py -m llm -s
"""

import json
import os
from pathlib import Path

import pytest

from app.schemas.requirements import RequirementsSpec
from app.services.catalog import resolve_alias
from app.services.clarification import assess
from app.services.extraction import extract_requirements
from app.services.llm_client import chat_structured

pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(
        os.getenv("RUN_LLM_TESTS") != "1",
        reason="set RUN_LLM_TESTS=1 after starting LM Studio",
    ),
]

GOLDEN = Path(__file__).parent / "golden_prompts.json"


async def test_live_structured_output_smoke():
    result = await chat_structured(
        "Extract only the requested room count.",
        "Two bedrooms",
        {
            "type": "object",
            "properties": {
                "rooms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "count": {"type": "integer"},
                        },
                        "required": ["type", "count"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["rooms"],
            "additionalProperties": False,
        },
    )
    assert isinstance(result.get("rooms"), list)


def _program_counts(spec: RequirementsSpec) -> dict[str, int]:
    counts: dict[str, int] = {}
    if spec.spaces:
        entries = (
            (space.space_type, space.count)
            for space in spec.spaces
        )
    else:
        entries = (
            (room.type.value, room.count)
            for room in spec.rooms
        )
    for raw_type, count in entries:
        room_type = resolve_alias(raw_type) or raw_type
        counts[room_type] = counts.get(room_type, 0) + count
    return counts


def _has_adjacency(spec: RequirementsSpec, expected: dict) -> bool:
    wanted = {
        resolve_alias(expected["room_a"]) or expected["room_a"],
        resolve_alias(expected["room_b"]) or expected["room_b"],
    }
    return any(
        {
            resolve_alias(edge.room_a) or edge.room_a,
            resolve_alias(edge.room_b) or edge.room_b,
        } == wanted
        and edge.strength == expected["strength"]
        for edge in spec.adjacency
    )


def _has_avoid(spec: RequirementsSpec, expected: dict) -> bool:
    wanted = {
        resolve_alias(expected["room_a"]) or expected["room_a"],
        resolve_alias(expected["room_b"]) or expected["room_b"],
    }
    return any(
        {
            resolve_alias(edge.room_a) or edge.room_a,
            resolve_alias(edge.room_b) or edge.room_b,
        } == wanted
        for edge in spec.avoid_adjacency
    )


def _checks(case: dict, spec: RequirementsSpec) -> list[bool]:
    expected = case["expect"]
    counts = _program_counts(spec)
    decision = assess(spec)
    checks: list[bool] = [decision.route == expected["route"]]
    if "building_type" in expected:
        checks.append(spec.building_type.value == expected["building_type"])
    if "floors" in expected:
        checks.append(spec.floors == expected["floors"])
    if "bedrooms_total" in expected:
        checks.append(
            counts.get("bedroom", 0)
            + counts.get("master_bedroom", 0)
            == expected["bedrooms_total"]
        )
    if "master_bedrooms" in expected:
        checks.append(counts.get("master_bedroom", 0) == expected["master_bedrooms"])
    if "bathrooms_total" in expected:
        checks.append(counts.get("bathroom", 0) == expected["bathrooms_total"])
    for key, room_type in (
        ("has_pooja_room", "pooja_room"),
        ("has_parking", "garage"),
        ("has_study", "study"),
    ):
        if expected.get(key):
            checks.append(counts.get(room_type, 0) > 0)
    for room_type, count in expected.get("space_counts", {}).items():
        canonical = resolve_alias(room_type) or room_type
        checks.append(counts.get(canonical, 0) == count)
    if "adjacency_contains" in expected:
        checks.append(_has_adjacency(spec, expected["adjacency_contains"]))
    if "avoid_contains" in expected:
        checks.append(_has_avoid(spec, expected["avoid_contains"]))
    if "plot_width_m_approx" in expected:
        checks.append(
            spec.plot.width_m is not None
            and abs(spec.plot.width_m - expected["plot_width_m_approx"]) < 0.03
        )
    if "plot_depth_m_approx" in expected:
        checks.append(
            spec.plot.depth_m is not None
            and abs(spec.plot.depth_m - expected["plot_depth_m_approx"]) < 0.03
        )
    if "facing" in expected:
        checks.append(spec.facing is not None and spec.facing.value == expected["facing"])
    if "rooms_max" in expected:
        checks.append(sum(counts.values()) <= expected["rooms_max"])
    elif expected["route"] == "vague":
        checks.append(sum(counts.values()) == 0)
    if expected["route"] == "conflict":
        checks.append(any(item.startswith("conflict:") for item in spec.missing_info))
    if "question_count" in expected:
        checks.append(len(decision.questions) == expected["question_count"])
    return checks


async def test_live_golden_suite_field_accuracy_is_at_least_eighty_percent_three_times():
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))["prompts"]

    for run in range(1, 4):
        rows = []
        field_checks: list[bool] = []
        for case in cases:
            spec = await extract_requirements(case["prompt"])
            checks = _checks(case, spec)
            field_checks.extend(checks)
            rows.append((case["id"], sum(checks), len(checks)))
        passed = sum(field_checks)
        accuracy = passed / len(field_checks)
        print(
            f"golden run {run}: {passed}/{len(field_checks)} "
            f"fields ({accuracy:.1%}) - {rows}"
        )
        assert accuracy >= 0.8


async def test_live_golden_suite_routes_all_prompts_correctly():
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))["prompts"]
    rows = []
    for case in cases:
        spec = await extract_requirements(case["prompt"])
        actual = assess(spec).route
        rows.append((case["id"], actual, case["expect"]["route"]))

    print(f"clarification routes — {rows}")
    assert all(actual == expected for _, actual, expected in rows)
