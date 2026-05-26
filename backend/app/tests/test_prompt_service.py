import pytest
from app.services.prompt_service import RoomSpec, detect_building_type, extract_rooms


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
