import pytest
from app.services.prompt_service import (
    RoomSpec,
    detect_building_type,
    extract_rooms,
    extract_total_area_sqm,
    extract_total_floors,
)


def test_extracts_bedroom_count():
    specs = extract_rooms("3 bedroom apartment")
    bedroom_specs = [s for s in specs if s.room_type == "bedroom"]
    assert len(bedroom_specs) == 3


def test_extracts_word_number():
    specs = extract_rooms("three bedrooms")
    bedroom_specs = [s for s in specs if s.room_type == "bedroom"]
    assert len(bedroom_specs) == 3


def test_extracts_master_bedroom_and_bathroom():
    specs = extract_rooms("master bedroom with en suite")
    types = [s.room_type for s in specs]
    assert "master_bedroom" in types
    assert "bathroom" in types


def test_large_kitchen_is_bigger_than_default():
    specs = extract_rooms("large kitchen")
    kitchen_specs = [s for s in specs if s.room_type == "kitchen"]
    assert len(kitchen_specs) == 1
    assert kitchen_specs[0].w > 4.0  # default kitchen w is 4.0


def test_small_bathroom_is_smaller_than_default():
    specs = extract_rooms("small bathroom")
    bath_specs = [s for s in specs if s.room_type == "bathroom"]
    assert len(bath_specs) == 1
    assert bath_specs[0].w < 3.0  # default bathroom w is 3.0


def test_extracts_living_room_and_kitchen():
    specs = extract_rooms("open plan living room and kitchen")
    types = [s.room_type for s in specs]
    assert "living_room" in types
    assert "kitchen" in types


from app.services.prompt_service import detect_building_type


def test_detect_building_type_apartment():
    assert detect_building_type("2 bedroom apartment") == "apartment"


def test_detect_building_type_house():
    assert detect_building_type("3 bedroom house with garden") == "house"


def test_extract_rooms_returns_empty_for_unrecognised_prompt():
    specs = extract_rooms("a place to live")
    assert specs == []


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("2 floors apartment", 2),
        ("2 floor apartment", 2),
        ("two floors apartment", 2),
        ("two floor apartment", 2),
        ("2 storey house", 2),
        ("two storey house", 2),
        ("2 story house", 2),
        ("two story house", 2),
        ("3 floors villa", 3),
        ("three floors villa", 3),
    ],
)
def test_extract_total_floors_from_common_phrases(prompt: str, expected: int):
    assert extract_total_floors(prompt) == expected


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("G+1 house with 4 bedrooms", 2),
        ("G+2 house with 4 bedrooms", 3),
        ("ground plus first apartment", 2),
        ("ground plus two apartment", 3),
    ],
)
def test_extract_total_floors_from_ground_plus(prompt: str, expected: int):
    assert extract_total_floors(prompt) == expected


def test_extract_total_floors_defaults_to_one():
    assert extract_total_floors("3 bedroom apartment with kitchen") == 1


def test_floor_count_does_not_break_room_extraction():
    specs = extract_rooms("2 floor, 3 bedroom layout with kitchen, living room, bathroom")
    types = [s.room_type for s in specs]
    assert types.count("bedroom") == 3
    assert "kitchen" in types
    assert "living_room" in types
    assert "bathroom" in types


@pytest.mark.parametrize(
    ("prompt", "expected_types"),
    [
        ("open plan kitchen living", {"kitchen", "living_room"}),
        ("ensuite master bedroom", {"bathroom", "master_bedroom"}),
        ("home office", {"study"}),
        ("small clinic with waiting and consultation rooms", {"consultation_room"}),
        ("office with reception, meeting room and open workspace", {"reception", "meeting_room", "workspace"}),
        ("studio apartment with balcony", {"balcony"}),
        ("retail shop with storage and checkout", {"storage", "checkout"}),
    ],
)
def test_extract_rooms_handles_sprint11_phrases(prompt: str, expected_types: set[str]):
    types = {room.room_type for room in extract_rooms(prompt)}
    assert expected_types.issubset(types)


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("apartment around 120 sqm", 120.0),
        ("house with 120 square meters", 120.0),
        ("shop with 1000 sq ft", 92.9),
    ],
)
def test_extract_total_area_sqm(prompt: str, expected: float):
    assert extract_total_area_sqm(prompt) == expected


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("studio apartment", "studio"),
        ("small clinic", "clinic"),
        ("classroom layout", "classroom"),
        ("retail shop", "retail"),
        ("small office", "office"),
    ],
)
def test_detect_building_type_for_sprint11_templates(prompt: str, expected: str):
    assert detect_building_type(prompt) == expected
