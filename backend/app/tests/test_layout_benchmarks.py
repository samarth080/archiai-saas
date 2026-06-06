import pytest

from app.services.layout_service import generate_layout
from app.services.prompt_service import detect_building_type, extract_rooms, extract_total_floors


REALISTIC_AREA_RANGES = {
    "bedroom": (8.0, 22.0),
    "master_bedroom": (12.0, 30.0),
    "bathroom": (3.0, 12.0),
    "kitchen": (6.0, 24.0),
    "living_room": (12.0, 40.0),
    "dining_room": (8.0, 24.0),
    "study": (6.0, 18.0),
    "office": (6.0, 18.0),
    "workspace": (12.0, 80.0),
    "meeting_room": (8.0, 30.0),
    "reception": (6.0, 24.0),
    "waiting_room": (8.0, 30.0),
    "storage": (3.0, 20.0),
    "classroom": (24.0, 80.0),
    "consultation_room": (8.0, 20.0),
    "retail_display": (16.0, 100.0),
    "checkout": (4.0, 16.0),
    "hallway": (4.0, 20.0),
}


def _generate(prompt: str) -> dict:
    return generate_layout(
        extract_rooms(prompt),
        prompt=prompt,
        building_type=detect_building_type(prompt),
        total_floors=extract_total_floors(prompt),
    )


def _room_types(layout: dict, *, floor_level: int | None = None) -> list[str]:
    rooms = layout["rooms"]
    if floor_level is not None:
        rooms = [room for room in rooms if room["floorLevel"] == floor_level]
    return [room["roomType"] for room in rooms]


def _architectural_rooms(layout: dict) -> list[dict]:
    return [room for room in layout["rooms"] if room["objectType"] in {"room", "stair"}]


def _find_room(layout: dict, room_type: str) -> dict:
    return next(room for room in layout["rooms"] if room["roomType"] == room_type)


def _edge_gap(a: dict, b: dict) -> float:
    x_gap = max(
        0.0,
        abs(a["position"]["x"] - b["position"]["x"]) - (a["size"]["w"] + b["size"]["w"]) / 2,
    )
    z_gap = max(
        0.0,
        abs(a["position"]["z"] - b["position"]["z"]) - (a["size"]["d"] + b["size"]["d"]) / 2,
    )
    return round(x_gap + z_gap, 2)


def _overlap_in_xz(a: dict, b: dict) -> bool:
    if a["floorLevel"] != b["floorLevel"]:
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


BENCHMARK_PROMPTS = [
    "1 bedroom studio apartment with open plan kitchen living and bathroom",
    "2 bedroom apartment with living room, kitchen, dining and bathroom",
    "2 floor house with living room, kitchen, bathroom and 3 bedrooms upstairs",
    "small office with reception, meeting room, open workspace and storage",
    "small clinic with waiting room, reception, 2 consultation rooms and bathroom",
    "classroom layout with 2 classrooms, corridor and bathroom",
    "retail store layout with display area, storage and checkout",
]


@pytest.mark.parametrize(
    ("prompt", "building_type", "required_rooms"),
    [
        (
            "1 bedroom studio apartment with open plan kitchen living and bathroom",
            "studio",
            {"bedroom", "living_room", "kitchen", "bathroom"},
        ),
        (
            "2 bedroom apartment with living room, kitchen, dining and bathroom",
            "apartment",
            {"bedroom", "living_room", "kitchen", "dining_room", "bathroom"},
        ),
        (
            "3 bedroom apartment with living room, kitchen, dining and 2 bathrooms",
            "apartment",
            {"bedroom", "living_room", "kitchen", "dining_room", "bathroom"},
        ),
        (
            "small house with 2 bedrooms, living room, kitchen, bathroom and storage",
            "house",
            {"bedroom", "living_room", "kitchen", "bathroom", "storage"},
        ),
        (
            "2 floor house with living room, kitchen, bathroom and 3 bedrooms upstairs",
            "house",
            {"bedroom", "living_room", "kitchen", "bathroom", "stairs"},
        ),
        (
            "small office with reception, meeting room, open workspace and storage",
            "office",
            {"reception", "meeting_room", "workspace", "storage"},
        ),
        (
            "small clinic with waiting room, reception, 2 consultation rooms and bathroom",
            "clinic",
            {"waiting_room", "reception", "consultation_room", "bathroom"},
        ),
        (
            "classroom layout with 2 classrooms, corridor and bathroom",
            "classroom",
            {"classroom", "hallway", "bathroom"},
        ),
        (
            "retail store layout with display area, storage and checkout",
            "retail",
            {"retail_display", "storage", "checkout"},
        ),
    ],
)
def test_benchmark_prompt_generates_required_room_groups(
    prompt: str,
    building_type: str,
    required_rooms: set[str],
):
    layout = _generate(prompt)

    assert layout["metadata"]["buildingType"] == building_type
    assert required_rooms.issubset(set(_room_types(layout)))


def test_benchmark_room_sizes_stay_within_realistic_ranges():
    layout = _generate(
        "3 bedroom apartment with living room, kitchen, dining room, 2 bathrooms, home office and hallway"
    )

    for room in layout["rooms"]:
        if room["objectType"] != "room":
            continue
        area = room["size"]["w"] * room["size"]["d"]
        minimum, maximum = REALISTIC_AREA_RANGES[room["roomType"]]
        assert minimum <= area <= maximum, f"{room['roomType']} area {area} is outside {minimum}-{maximum} sqm"


def test_benchmark_rooms_include_explicit_zones():
    layout = _generate("2 bedroom apartment with entry, living room, kitchen, dining room, bathroom and hallway")
    zones = {room["roomType"]: room["zone"] for room in layout["rooms"]}

    assert zones["living_room"] == "public"
    assert zones["bedroom"] == "private"
    assert zones["kitchen"] == "service"
    assert zones["bathroom"] == "service"
    assert zones["hallway"] == "circulation"


def test_benchmark_public_cluster_places_kitchen_near_living_and_dining():
    layout = _generate("apartment with living room, kitchen, dining room and bathroom")
    living_room = _find_room(layout, "living_room")
    kitchen = _find_room(layout, "kitchen")
    dining_room = _find_room(layout, "dining_room")

    assert _edge_gap(living_room, kitchen) <= 1.0
    assert _edge_gap(kitchen, dining_room) <= 1.0


def test_benchmark_avoids_direct_bedroom_to_kitchen_placement():
    layout = _generate("2 bedroom apartment with entry, living room, kitchen, dining room, bathroom and hallway")
    kitchen = _find_room(layout, "kitchen")
    bedrooms = [room for room in layout["rooms"] if room["roomType"] == "bedroom"]

    assert all(_edge_gap(kitchen, bedroom) > 1.0 for bedroom in bedrooms)


def test_benchmark_multi_floor_house_keeps_public_ground_private_upper_and_stairs():
    layout = _generate("2 floor house with living room, kitchen, bathroom and 3 bedrooms upstairs")

    assert len(layout["floors"]) == 2
    assert {"living_room", "kitchen", "bathroom", "stairs"}.issubset(set(_room_types(layout, floor_level=0)))
    assert {"master_bedroom", "bedroom", "stairs"}.issubset(set(_room_types(layout, floor_level=1)))


def test_benchmark_layout_schema_remains_backward_compatible():
    layout = _generate("2 bedroom apartment with living room, kitchen and bathroom")

    assert layout["version"] == "1.0"
    assert isinstance(layout["rooms"], list)
    assert isinstance(layout["floors"], list)
    assert layout["metadata"]["totalFloors"] == 1
    assert layout["building"]["floorHeight"] > 0
    for room in layout["rooms"]:
        assert {"id", "label", "roomType", "objectType", "floorId", "floorLevel", "position", "size", "color"}.issubset(room)


def test_benchmark_generator_works_without_stored_pattern_data():
    layout = _generate("1 bedroom apartment with living room, kitchen and bathroom")

    assert layout["rooms"]
    assert layout["metadata"]["totalRooms"] == 4
    assert layout["metadata"]["patternDataUsed"] is False


@pytest.mark.parametrize(
    ("prompt", "expected_template"),
    [
        ("1 bedroom studio apartment", "studio"),
        ("2 bedroom apartment", "apartment"),
        ("small house with 2 bedrooms", "house"),
        ("small office", "office"),
        ("small clinic", "clinic"),
        ("classroom layout", "classroom"),
        ("retail store layout", "retail"),
    ],
)
def test_benchmark_records_applied_building_template(prompt: str, expected_template: str):
    layout = _generate(prompt)

    assert layout["metadata"]["template"] == expected_template


@pytest.mark.parametrize("prompt", BENCHMARK_PROMPTS)
def test_benchmark_layouts_have_no_room_overlaps(prompt: str):
    layout = _generate(prompt)
    rooms = _architectural_rooms(layout)

    for index, room in enumerate(rooms):
        for other in rooms[index + 1:]:
            assert not _overlap_in_xz(room, other), f"{room['label']} overlaps {other['label']}"


@pytest.mark.parametrize("prompt", BENCHMARK_PROMPTS)
def test_benchmark_layouts_meet_quality_floor_and_report_pattern_source(prompt: str):
    layout = _generate(prompt)

    assert layout["insights"]["score"] >= 70
    assert layout["metadata"]["patternDataSource"] == "fallback-defaults"
    assert layout["metadata"]["appliedPatternCount"] == 0
    assert "suggestions" in layout["insights"]


@pytest.mark.parametrize(
    ("prompt", "room_type", "target_type"),
    [
        ("small office with reception, meeting room, open workspace and storage", "reception", "workspace"),
        ("small clinic with waiting room, reception, consultation room and bathroom", "waiting_room", "consultation_room"),
        ("retail store layout with display area, storage and checkout", "retail_display", "checkout"),
        ("classroom layout with classroom, corridor and bathroom", "hallway", "classroom"),
    ],
)
def test_benchmark_key_non_residential_adjacencies_are_close(
    prompt: str,
    room_type: str,
    target_type: str,
):
    layout = _generate(prompt)

    assert _edge_gap(_find_room(layout, room_type), _find_room(layout, target_type)) <= 1.0
