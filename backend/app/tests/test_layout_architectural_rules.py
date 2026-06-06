from app.services.layout_service import generate_layout
from app.services.prompt_service import RoomSpec, detect_building_type, extract_rooms, extract_total_floors


def _generate(prompt: str) -> dict:
    return generate_layout(
        extract_rooms(prompt),
        prompt=prompt,
        building_type=detect_building_type(prompt),
        total_floors=extract_total_floors(prompt),
    )


def _rooms_by_type(layout: dict, room_type: str) -> list[dict]:
    return [room for room in layout["rooms"] if room["roomType"] == room_type]


def _first(layout: dict, room_type: str) -> dict:
    return _rooms_by_type(layout, room_type)[0]


def _edge_gap(a: dict, b: dict) -> float:
    if a.get("floorLevel") != b.get("floorLevel"):
        return float("inf")
    x_gap = max(
        0.0,
        abs(a["position"]["x"] - b["position"]["x"]) - (a["size"]["w"] + b["size"]["w"]) / 2,
    )
    z_gap = max(
        0.0,
        abs(a["position"]["z"] - b["position"]["z"]) - (a["size"]["d"] + b["size"]["d"]) / 2,
    )
    return round(x_gap + z_gap, 2)


def _overlaps(a: dict, b: dict) -> bool:
    if a.get("floorLevel") != b.get("floorLevel"):
        return False
    ax1 = a["position"]["x"] - a["size"]["w"] / 2
    ax2 = a["position"]["x"] + a["size"]["w"] / 2
    az1 = a["position"]["z"] - a["size"]["d"] / 2
    az2 = a["position"]["z"] + a["size"]["d"] / 2
    bx1 = b["position"]["x"] - b["size"]["w"] / 2
    bx2 = b["position"]["x"] + b["size"]["w"] / 2
    bz1 = b["position"]["z"] - b["size"]["d"] / 2
    bz2 = b["position"]["z"] + b["size"]["d"] / 2
    return ax1 < bx2 and ax2 > bx1 and az1 < bz2 and az2 > bz1


def test_clinic_places_reception_near_entry():
    layout = _generate("clinic with reception, waiting room, two consultation rooms and bathroom")

    assert _edge_gap(_first(layout, "entry"), _first(layout, "reception")) <= 1.0


def test_clinic_places_waiting_near_reception():
    layout = _generate("clinic with reception, waiting room, two consultation rooms and bathroom")

    assert _edge_gap(_first(layout, "reception"), _first(layout, "waiting_room")) <= 1.0


def test_clinic_consultation_rooms_are_not_directly_at_entry():
    layout = _generate("clinic with reception, waiting room, two consultation rooms and bathroom")
    entry = _first(layout, "entry")

    assert all(_edge_gap(entry, room) > 1.0 for room in _rooms_by_type(layout, "consultation_room"))


def test_clinic_bathroom_is_accessible_from_waiting_or_circulation():
    layout = _generate("clinic with reception, waiting room, two consultation rooms and bathroom")
    bathroom = _first(layout, "bathroom")
    waiting = _first(layout, "waiting_room")
    hallways = _rooms_by_type(layout, "hallway")

    assert _edge_gap(waiting, bathroom) <= 2.0 or any(_edge_gap(hallway, bathroom) <= 2.0 for hallway in hallways)


def test_house_bedrooms_are_not_directly_at_entry():
    layout = _generate("house with entry, living room, dining room, kitchen, bathroom and three bedrooms")
    entry = _first(layout, "entry")

    assert all(_edge_gap(entry, room) > 1.0 for room in _rooms_by_type(layout, "bedroom"))


def test_office_reception_is_near_entry():
    layout = _generate("office with entry, reception, open workspace, meeting room, private office and storage")

    assert _edge_gap(_first(layout, "entry"), _first(layout, "reception")) <= 1.0


def test_restaurant_kitchen_is_not_at_public_entrance():
    layout = _generate("restaurant with entry, reception, dining room, kitchen, bathroom and storage")

    assert _edge_gap(_first(layout, "entry"), _first(layout, "kitchen")) > 1.0


def test_generated_rooms_do_not_overlap():
    layout = _generate("restaurant with entry, reception, dining room, kitchen, bathroom and storage")
    rooms = [room for room in layout["rooms"] if room["roomType"] != "stairs"]

    for index, room in enumerate(rooms):
        for other in rooms[index + 1:]:
            assert not _overlaps(room, other), f"{room['label']} overlaps {other['label']}"


def test_generated_rooms_stay_inside_computed_building_bounds():
    layout = _generate("clinic with reception, waiting room, two consultation rooms and bathroom")
    bounds = layout["building"]["bounds"]

    for room in layout["rooms"]:
        min_x = room["position"]["x"] - room["size"]["w"] / 2
        max_x = room["position"]["x"] + room["size"]["w"] / 2
        min_z = room["position"]["z"] - room["size"]["d"] / 2
        max_z = room["position"]["z"] + room["size"]["d"] / 2
        assert bounds["minX"] <= min_x <= max_x <= bounds["maxX"]
        assert bounds["minZ"] <= min_z <= max_z <= bounds["maxZ"]


def test_generator_still_works_without_pattern_data():
    layout = generate_layout(
        [RoomSpec(label="Bedroom", room_type="bedroom", w=4.0, h=3.0, d=4.0)],
        building_type="house",
    )

    assert layout["rooms"]
    assert layout["metadata"]["patternDataUsed"] is False


def test_multi_floor_generation_returns_valid_floor_metadata_and_floors_array():
    layout = _generate("two floor house with entry, living room, kitchen, bathroom and three bedrooms")

    assert layout["metadata"]["totalFloors"] == 2
    assert len(layout["floors"]) == 2
    assert [floor["level"] for floor in layout["floors"]] == [0, 1]
    assert all("id" in floor and "name" in floor and "rooms" in floor for floor in layout["floors"])
