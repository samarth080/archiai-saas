"""Canonical-to-canvas compatibility checks for the MVP layout adapter."""

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
