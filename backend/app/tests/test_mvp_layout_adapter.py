"""Canonical-to-canvas compatibility checks for the MVP layout adapter."""

from pathlib import Path

from app.schemas.requirements import RequirementsSpec
from app.services.layout_adapter import layout_plan_to_canvas
from app.services.layout_engine import generate_plan


def test_canvas_footprint_uses_min_corner_and_contains_converted_rooms():
    spec = RequirementsSpec.model_validate(
        {
            "rooms": [
                {"type": "bedroom", "count": 2},
                {"type": "living_room", "count": 1},
                {"type": "kitchen", "count": 1},
                {"type": "bathroom", "count": 1},
            ],
            "plot": {"width_m": 9.0, "depth_m": 12.0},
            "facing": "east",
        }
    )

    canvas = layout_plan_to_canvas(generate_plan(spec))
    floor = canvas["floors"][0]
    footprint = floor["footprint"]

    assert footprint == {"x": 0.0, "z": 0.0, "w": 9.0, "d": 12.0}
    assert canvas["building"]["footprint"] == footprint

    for room in floor["rooms"]:
        if room["objectType"] != "room":
            continue
        half_w = room["size"]["w"] / 2
        half_d = room["size"]["d"] / 2
        assert room["position"]["x"] - half_w >= footprint["x"]
        assert room["position"]["x"] + half_w <= footprint["x"] + footprint["w"]
        assert room["position"]["z"] - half_d >= footprint["z"]
        assert room["position"]["z"] + half_d <= footprint["z"] + footprint["d"]


def test_canvas_metadata_preserves_explicit_vastu_opt_in_only():
    spec = RequirementsSpec.model_validate(
        {
            "rooms": [{"type": "bedroom", "count": 1}],
            "plot": {"width_m": 9.0, "depth_m": 12.0},
            "facing": "east",
        }
    )
    plan = generate_plan(spec)

    default_canvas = layout_plan_to_canvas(plan, prompt="One bedroom house")
    vastu_canvas = layout_plan_to_canvas(plan, prompt="One bedroom Vastu house")

    assert default_canvas["metadata"]["mvpVastuEnabled"] is False
    assert vastu_canvas["metadata"]["mvpVastuEnabled"] is True


def test_multi_floor_plan_maps_objects_to_existing_canvas_levels():
    spec = RequirementsSpec.model_validate({
        "building_type": "duplex",
        "floors": 2,
        "rooms": [
            {"type": "living_room", "count": 1},
            {"type": "kitchen", "count": 1},
            {"type": "bedroom", "count": 3},
            {"type": "bathroom", "count": 2},
        ],
        "plot": {"width_m": 12, "depth_m": 14},
    })

    canvas = layout_plan_to_canvas(generate_plan(spec))

    assert canvas["metadata"]["totalFloors"] == 2
    assert [floor["level"] for floor in canvas["floors"]] == [0, 1]
    assert all(
        room["floorLevel"] == floor["level"]
        for floor in canvas["floors"]
        for room in floor["rooms"]
    )
    stairs = [room for room in canvas["rooms"] if room["objectType"] == "stair"]
    assert len(stairs) == 2
    assert {stair["floorLevel"] for stair in stairs} == {0, 1}
    assert {
        stair["position"]["y"] for stair in stairs
    } == {1.5, 4.5}


def test_hierarchical_zone_metadata_reaches_the_existing_canvas_contract():
    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "requirements"
        / "phase10_composed_school.json"
    )
    spec = RequirementsSpec.model_validate_json(fixture.read_text(encoding="utf-8"))

    canvas = layout_plan_to_canvas(generate_plan(spec))

    reasons = canvas["metadata"]["archetypeReasons"]
    assert {reason["archetype"] for reason in reasons} >= {
        "double_loaded_corridor",
        "open_core",
    }
    canonical_rooms = [
        room for room in canvas["rooms"]
        if room["objectType"] in {"room", "stair"}
    ]
    assert all(room["zoneId"] for room in canonical_rooms)
