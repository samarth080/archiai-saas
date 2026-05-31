from copy import deepcopy

from app.services.layout_quality_service import score_layout_quality
from app.services.layout_service import generate_layout
from app.services.prompt_service import RoomSpec


def _residential_specs() -> list[RoomSpec]:
    return [
        RoomSpec(label="Living Room", room_type="living_room", w=5.0, h=3.0, d=5.0),
        RoomSpec(label="Kitchen", room_type="kitchen", w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Dining Room", room_type="dining_room", w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Bedroom", room_type="bedroom", w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Bathroom", room_type="bathroom", w=3.0, h=3.0, d=3.0),
    ]


def test_generated_layout_includes_readable_quality_insights():
    layout = generate_layout(_residential_specs())

    assert 0 <= layout["insights"]["score"] <= 100
    assert layout["insights"]["reasons"]
    assert "template:apartment" in layout["insights"]["appliedRules"]
    assert "pattern-data:fallback-defaults" in layout["insights"]["appliedRules"]


def test_quality_score_reports_missing_required_room():
    layout = generate_layout(_residential_specs())

    result = score_layout_quality(layout, required_room_types={"living_room", "garage"})

    assert result.score < 100
    assert any("Missing required rooms: garage" in warning for warning in result.warnings)


def test_quality_score_reports_avoid_adjacency_violation():
    layout = deepcopy(generate_layout(_residential_specs()))
    bedroom = next(room for room in layout["rooms"] if room["roomType"] == "bedroom")
    kitchen = next(room for room in layout["rooms"] if room["roomType"] == "kitchen")
    bedroom["position"] = kitchen["position"].copy()

    result = score_layout_quality(layout)

    assert result.score < 100
    assert any("Avoid-adjacency violations" in warning for warning in result.warnings)


def test_quality_score_reports_missing_multifloor_stairs():
    layout = generate_layout(_residential_specs(), total_floors=2)
    layout["rooms"] = [room for room in layout["rooms"] if room["roomType"] != "stairs"]

    result = score_layout_quality(layout)

    assert result.score < 100
    assert any("missing consistent stair" in warning.lower() for warning in result.warnings)
