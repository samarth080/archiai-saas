import pytest
from app.services.prompt_service import RoomSpec
from app.services.layout_service import generate_layout
from app.services.layout_pattern_service import LayoutPatternRules, RoomPatternRule


def _make_specs() -> list[RoomSpec]:
    return [
        RoomSpec(label="Living Room", room_type="living_room", w=5.0, h=3.0, d=5.0),
        RoomSpec(label="Kitchen",     room_type="kitchen",     w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Bedroom",     room_type="bedroom",     w=4.0, h=3.0, d=4.0),
    ]


def test_all_rooms_have_position_and_size():
    layout = generate_layout(_make_specs())
    for room in layout["rooms"]:
        assert "position" in room
        assert "size" in room
        assert all(k in room["position"] for k in ("x", "y", "z"))
        assert all(k in room["size"] for k in ("w", "h", "d"))


def test_room_count_matches_input():
    specs = _make_specs()
    layout = generate_layout(specs)
    assert len(layout["rooms"]) == len(specs)


def test_y_position_equals_half_height():
    layout = generate_layout(_make_specs())
    for room in layout["rooms"]:
        assert room["position"]["y"] == pytest.approx(room["size"]["h"] / 2)


def test_no_room_overlaps_in_xz_plane():
    layout = generate_layout(_make_specs())
    rooms = layout["rooms"]
    for i, a in enumerate(rooms):
        for j, b in enumerate(rooms):
            if i == j:
                continue
            ax1 = a["position"]["x"] - a["size"]["w"] / 2
            ax2 = a["position"]["x"] + a["size"]["w"] / 2
            az1 = a["position"]["z"] - a["size"]["d"] / 2
            az2 = a["position"]["z"] + a["size"]["d"] / 2
            bx1 = b["position"]["x"] - b["size"]["w"] / 2
            bx2 = b["position"]["x"] + b["size"]["w"] / 2
            bz1 = b["position"]["z"] - b["size"]["d"] / 2
            bz2 = b["position"]["z"] + b["size"]["d"] / 2
            x_overlap = ax1 < bx2 and ax2 > bx1
            z_overlap = az1 < bz2 and az2 > bz1
            assert not (x_overlap and z_overlap), (
                f"Rooms '{a['label']}' and '{b['label']}' overlap"
            )


def test_empty_specs_returns_empty_rooms():
    layout = generate_layout([])
    assert layout["rooms"] == []
    assert layout["metadata"]["room_count"] == 0


def test_metadata_fields_are_populated():
    layout = generate_layout(_make_specs(), prompt="test prompt", building_type="house")
    assert layout["version"] == "1.0"
    assert layout["metadata"]["prompt"] == "test prompt"
    assert layout["metadata"]["building_type"] == "house"
    assert layout["metadata"]["room_count"] == 3


def test_other_zone_rooms_are_placed():
    specs = [
        RoomSpec(label="Office", room_type="office", w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Garage", room_type="garage", w=5.0, h=3.0, d=6.0),
    ]
    layout = generate_layout(specs)
    assert len(layout["rooms"]) == 2
    for room in layout["rooms"]:
        assert "position" in room
        assert room["position"]["y"] == pytest.approx(room["size"]["h"] / 2)


def test_rooms_have_unique_ids():
    layout = generate_layout(_make_specs())
    ids = [r["id"] for r in layout["rooms"]]
    assert len(ids) == len(set(ids))


def test_multi_floor_layout_returns_requested_floor_count():
    layout = generate_layout(_make_specs(), total_floors=2)
    assert layout["metadata"]["totalFloors"] == 2
    assert len(layout["floors"]) == 2


def test_stairs_are_added_to_each_multi_floor_level():
    layout = generate_layout(_make_specs(), total_floors=3)
    stairs = [
        room
        for floor in layout["floors"]
        for room in floor["rooms"]
        if room["roomType"] == "stairs"
    ]
    assert len(stairs) == 3


def test_stairs_share_xz_position_across_floors():
    layout = generate_layout(_make_specs(), total_floors=3)
    stairs = [
        room
        for floor in layout["floors"]
        for room in floor["rooms"]
        if room["roomType"] == "stairs"
    ]
    positions = {(room["position"]["x"], room["position"]["z"]) for room in stairs}
    assert len(positions) == 1


def test_rooms_are_assigned_to_valid_floor_levels():
    layout = generate_layout(_make_specs(), total_floors=2)
    valid_levels = {floor["level"] for floor in layout["floors"]}
    for room in layout["rooms"]:
        assert room["floorLevel"] in valid_levels
        assert room["floorId"] == f"floor_{room['floorLevel']}"


def test_multi_floor_split_places_public_rooms_on_ground_and_bedrooms_upstairs():
    specs = [
        RoomSpec(label="Living Room", room_type="living_room", w=5.0, h=3.0, d=5.0),
        RoomSpec(label="Kitchen", room_type="kitchen", w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Bedroom 1", room_type="bedroom", w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Bedroom 2", room_type="bedroom", w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Bedroom 3", room_type="bedroom", w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Bathroom", room_type="bathroom", w=3.0, h=3.0, d=3.0),
    ]
    layout = generate_layout(specs, total_floors=2)

    ground_labels = {room["label"] for room in layout["floors"][0]["rooms"]}
    first_labels = {room["label"] for room in layout["floors"][1]["rooms"]}

    assert {"Living Room", "Kitchen", "Bathroom", "Stairs"}.issubset(ground_labels)
    assert {"Master Bedroom", "Bedroom 2", "Bedroom 3", "Stairs"}.issubset(first_labels)


def test_pattern_room_size_range_clamps_generated_dimensions():
    specs = [RoomSpec(label="Bedroom", room_type="bedroom", w=6.0, h=3.0, d=6.0)]
    rules = LayoutPatternRules(
        building_type="apartment",
        room_rules={
            "bedroom": RoomPatternRule(
                room_type="bedroom",
                typical_area_sqm_min=11.0,
                typical_area_sqm_max=15.0,
                zone="private",
                pattern_data_used=True,
            )
        },
        layout_patterns=("public_private_split",),
        pattern_data_used=True,
    )

    layout = generate_layout(specs, pattern_rules=rules)
    bedroom = layout["rooms"][0]

    assert bedroom["size"]["w"] * bedroom["size"]["d"] == pytest.approx(15.0, abs=0.1)
    assert layout["metadata"]["patternDataUsed"] is True


def test_total_area_ratio_guides_room_dimensions_when_pattern_provides_ratio():
    specs = [RoomSpec(label="Bedroom", room_type="bedroom", w=4.0, h=3.0, d=4.0)]
    rules = LayoutPatternRules(
        building_type="apartment",
        room_rules={
            "bedroom": RoomPatternRule(
                room_type="bedroom",
                typical_area_sqm_min=10.0,
                typical_area_sqm_max=20.0,
                zone="private",
                room_to_total_area_ratio_min=0.12,
                room_to_total_area_ratio_max=0.16,
                pattern_data_used=True,
            )
        },
        layout_patterns=("public_private_split",),
        pattern_data_used=True,
    )

    layout = generate_layout(specs, pattern_rules=rules, total_area_sqm=100.0)
    bedroom = layout["rooms"][0]

    assert bedroom["size"]["w"] * bedroom["size"]["d"] == pytest.approx(14.0, abs=0.1)


def test_fallback_sizing_metadata_does_not_claim_pattern_data():
    layout = generate_layout(_make_specs())

    assert layout["metadata"]["patternDataUsed"] is False
    assert layout["metadata"]["appliedPatternCount"] == 0
    assert layout["metadata"]["ignoredPatternCount"] == 0


def test_rooms_include_resolved_zone_metadata():
    layout = generate_layout(_make_specs())
    zones = {room["roomType"]: room["zone"] for room in layout["rooms"]}

    assert zones["living_room"] == "public"
    assert zones["kitchen"] == "service"
    assert zones["bedroom"] == "private"
    assert layout["metadata"]["zonesDetected"] == ["private", "public", "service"]


def test_living_kitchen_and_dining_cluster_are_ordered_together():
    specs = [
        RoomSpec(label="Dining Room", room_type="dining_room", w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Living Room", room_type="living_room", w=5.0, h=3.0, d=5.0),
        RoomSpec(label="Kitchen", room_type="kitchen", w=4.0, h=3.0, d=4.0),
    ]
    layout = generate_layout(specs)
    rooms = {room["roomType"]: room for room in layout["rooms"]}

    front_edges = {
        room["position"]["z"] - room["size"]["d"] / 2
        for room in rooms.values()
    }
    assert front_edges == {0.0}
    assert rooms["living_room"]["position"]["x"] < rooms["kitchen"]["position"]["x"]
    assert rooms["kitchen"]["position"]["x"] < rooms["dining_room"]["position"]["x"]


def test_private_bedroom_row_is_separated_from_kitchen_cluster():
    layout = generate_layout(_make_specs())
    rooms = {room["roomType"]: room for room in layout["rooms"]}
    kitchen = rooms["kitchen"]
    bedroom = rooms["bedroom"]
    kitchen_edge = kitchen["position"]["z"] + kitchen["size"]["d"] / 2
    bedroom_edge = bedroom["position"]["z"] - bedroom["size"]["d"] / 2

    assert bedroom_edge - kitchen_edge >= 2.0


def test_bathroom_row_aligns_near_bedroom_when_adjacency_rules_request_it():
    specs = [
        RoomSpec(label="Living Room", room_type="living_room", w=5.0, h=3.0, d=5.0),
        RoomSpec(label="Kitchen", room_type="kitchen", w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Bathroom", room_type="bathroom", w=3.0, h=3.0, d=3.0),
        RoomSpec(label="Bedroom", room_type="bedroom", w=4.0, h=3.0, d=4.0),
    ]
    layout = generate_layout(specs)
    rooms = {room["roomType"]: room for room in layout["rooms"]}
    bathroom = rooms["bathroom"]
    bedroom = rooms["bedroom"]
    x_gap = max(
        0.0,
        abs(bathroom["position"]["x"] - bedroom["position"]["x"])
        - (bathroom["size"]["w"] + bedroom["size"]["w"]) / 2,
    )
    z_gap = max(
        0.0,
        abs(bathroom["position"]["z"] - bedroom["position"]["z"])
        - (bathroom["size"]["d"] + bedroom["size"]["d"]) / 2,
    )

    assert round(x_gap + z_gap, 2) <= 1.0


def test_stairs_are_marked_as_circulation():
    layout = generate_layout(_make_specs(), total_floors=2)
    stairs = [room for room in layout["rooms"] if room["roomType"] == "stairs"]

    assert stairs
    assert {room["zone"] for room in stairs} == {"circulation"}
