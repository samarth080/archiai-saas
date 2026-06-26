"""
Sprint 17 Phase 2 (incremental) — interior doors on partition walls.

Every shared wall between two adjacent rooms long enough to fit a doorway
now gets a door marker centred on it, so a generated floor plan is actually
walkable room-to-room instead of just visually divided by solid walls.
"""
from app.services.layout_service import generate_layout
from app.services.prompt_service import detect_building_type, extract_rooms, extract_total_floors


def _generate(prompt: str) -> dict:
    return generate_layout(
        extract_rooms(prompt),
        prompt=prompt,
        building_type=detect_building_type(prompt),
        total_floors=extract_total_floors(prompt),
    )


def _interior_doors(layout: dict) -> list[dict]:
    return [
        room for room in layout["rooms"]
        if room["objectType"] == "door" and room["label"] == "Interior Door"
    ]


def _partition_walls(layout: dict) -> list[dict]:
    return [
        room for room in layout["rooms"]
        if room["objectType"] == "wall" and room["label"] == "Partition Wall"
    ]


def test_adjacent_rooms_get_an_interior_door():
    layout = _generate("apartment with living room, kitchen, dining room and bathroom")

    assert _partition_walls(layout)
    assert _interior_doors(layout)


def test_interior_door_sits_on_its_partition_wall():
    layout = _generate("apartment with living room, kitchen, dining room and bathroom")
    walls = _partition_walls(layout)
    doors = _interior_doors(layout)

    for door in doors:
        same_spot = [
            wall for wall in walls
            if wall["floorLevel"] == door["floorLevel"]
            and abs(wall["position"]["x"] - door["position"]["x"]) < 0.05
            and abs(wall["position"]["z"] - door["position"]["z"]) < 0.05
        ]
        assert same_spot, f"no partition wall under door at {door['position']}"


def test_interior_door_does_not_exceed_its_wall_span():
    layout = _generate("apartment with living room, kitchen, dining room and bathroom")
    walls = {(w["position"]["x"], w["position"]["z"], w["floorLevel"]): w for w in _partition_walls(layout)}

    for door in _interior_doors(layout):
        key = (door["position"]["x"], door["position"]["z"], door["floorLevel"])
        wall = walls[key]
        wall_span = max(wall["size"]["w"], wall["size"]["d"])
        door_span = max(door["size"]["w"], door["size"]["d"])
        assert door_span <= wall_span + 0.01


def test_very_short_partition_walls_get_no_doorway():
    from app.services.layout_service import _generate_partition_walls

    rooms = [
        {
            "id": "a", "objectType": "room", "floorLevel": 0,
            "position": {"x": 0.0, "y": 1.5, "z": 0.0},
            "size": {"w": 3.0, "h": 3.0, "d": 1.0},
        },
        {
            "id": "b", "objectType": "room", "floorLevel": 0,
            "position": {"x": 3.0, "y": 1.5, "z": 0.0},
            "size": {"w": 3.0, "h": 3.0, "d": 0.6},
        },
    ]
    markers = _generate_partition_walls(rooms, floor_id="floor_0", floor_level=0, elevation=0.0)

    assert any(m["label"] == "Partition Wall" for m in markers)
    assert not any(m["label"] == "Interior Door" for m in markers)


def test_multi_room_layout_has_more_doors_than_just_the_entry():
    layout = _generate("3 bedroom apartment with living room, kitchen, dining room and 2 bathrooms")
    all_doors = [room for room in layout["rooms"] if room["objectType"] == "door"]

    assert len(all_doors) > 1


def _room_by_type(layout: dict, room_type: str) -> dict:
    return next(r for r in layout["rooms"] if r.get("roomType") == room_type)


def _door_between(layout: dict, type_a: str, type_b: str) -> dict | None:
    a, b = _room_by_type(layout, type_a), _room_by_type(layout, type_b)
    for door in _interior_doors(layout):
        if abs(door["position"]["x"] - a["position"]["x"]) < 4 and abs(door["position"]["z"] - a["position"]["z"]) < 4:
            for room, other in ((a, b), (b, a)):
                ax1, ax2 = room["position"]["x"] - room["size"]["w"] / 2, room["position"]["x"] + room["size"]["w"] / 2
                az1, az2 = room["position"]["z"] - room["size"]["d"] / 2, room["position"]["z"] + room["size"]["d"] / 2
                if (ax1 - 0.2 <= door["position"]["x"] <= ax2 + 0.2) and (az1 - 0.2 <= door["position"]["z"] <= az2 + 0.2):
                    bx1 = other["position"]["x"] - other["size"]["w"] / 2 - 0.2
                    bx2 = other["position"]["x"] + other["size"]["w"] / 2 + 0.2
                    bz1 = other["position"]["z"] - other["size"]["d"] / 2 - 0.2
                    bz2 = other["position"]["z"] + other["size"]["d"] / 2 + 0.2
                    if bx1 <= door["position"]["x"] <= bx2 and bz1 <= door["position"]["z"] <= bz2:
                        return door
    return None


def test_private_service_cells_route_through_the_corridor_not_each_other():
    """
    Regression for the clinic layout where Office<->Bathroom and
    Bathroom<->Consultation Room each got a direct door (because they're
    adjacent in the same back row), instead of each opening onto the
    Hallway like an architecturally sane plan would.
    """
    layout = _generate(
        "clinic with entry, reception, waiting room, consultation room, office, bathroom and storage"
    )
    room_types = {r.get("roomType") for r in layout["rooms"]}
    assert "hallway" in room_types

    # Lateral doors between two private/service cells must not exist.
    assert _door_between(layout, "office", "bathroom") is None

    # Each private/service cell must still be reachable via the hallway.
    for private_type in ("office", "bathroom"):
        if private_type in room_types:
            assert _door_between(layout, "hallway", private_type) is not None, (
                f"{private_type} has no door onto the hallway"
            )


def test_open_plan_public_rooms_still_connect_directly():
    layout = _generate("apartment with entry, living room, kitchen, dining room and 2 bedrooms")

    assert _door_between(layout, "kitchen", "dining_room") is not None
