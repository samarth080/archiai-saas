"""Opt-in Phase 2 live gate against host LM Studio.

Run only after workflow Step 0.2 is complete:
    RUN_LLM_TESTS=1 pytest app/tests/test_mvp_llm_live.py -m llm -s
"""

import json
import os
from pathlib import Path

import pytest

from app.schemas.requirements import RequirementsSpec, RoomType
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


def _count(spec: RequirementsSpec, room_type: RoomType) -> int:
    return sum(room.count for room in spec.rooms if room.type == room_type)


def _has_adjacency(spec: RequirementsSpec, expected: dict) -> bool:
    wanted = {RoomType(expected["room_a"]), RoomType(expected["room_b"])}
    return any(
        {edge.room_a, edge.room_b} == wanted
        and edge.strength == expected["strength"]
        for edge in spec.adjacency
    )


def _matches(case: dict, spec: RequirementsSpec) -> bool:
    expected = case["expect"]
    checks: list[bool] = []
    if "building_type" in expected:
        checks.append(spec.building_type.value == expected["building_type"])
    if "floors" in expected:
        checks.append(spec.floors == expected["floors"])
    if "bedrooms_total" in expected:
        checks.append(
            _count(spec, RoomType.bedroom)
            + _count(spec, RoomType.master_bedroom)
            == expected["bedrooms_total"]
        )
    if "master_bedrooms" in expected:
        checks.append(
            _count(spec, RoomType.master_bedroom) == expected["master_bedrooms"]
        )
    if "bathrooms_total" in expected:
        checks.append(_count(spec, RoomType.bathroom) == expected["bathrooms_total"])
    for key, room_type in (
        ("has_pooja_room", RoomType.pooja_room),
        ("has_parking", RoomType.parking),
        ("has_study", RoomType.study),
    ):
        if expected.get(key):
            checks.append(_count(spec, room_type) > 0)
    if "adjacency_contains" in expected:
        checks.append(_has_adjacency(spec, expected["adjacency_contains"]))
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
        checks.append(sum(room.count for room in spec.rooms) <= expected["rooms_max"])
    elif expected["route"] == "vague":
        checks.append(sum(room.count for room in spec.rooms) == 0)
    if expected["route"] == "conflict":
        checks.append(any(item.startswith("conflict:") for item in spec.missing_info))
    return bool(checks) and all(checks)


async def test_live_golden_suite_scores_at_least_eight_of_ten_three_times():
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))["prompts"]

    for run in range(1, 4):
        rows = []
        for case in cases:
            spec = await extract_requirements(case["prompt"])
            rows.append((case["id"], _matches(case, spec)))
        passed = sum(ok for _, ok in rows)
        print(f"golden run {run}: {passed}/10 — {rows}")
        assert passed >= 8
