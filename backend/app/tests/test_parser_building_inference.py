from app.services.parser.building_inference import (
    detect_style_hints,
    extract_bhk,
    infer_building,
    infer_building_type,
    infer_template_rooms,
)


def test_infer_building_type_detects_bhk_as_apartment():
    assert infer_building_type("3bhk apartment") == "apartment"


def test_infer_building_type_detects_family_home():
    assert infer_building_type("modern family home") == "family_home"


def test_infer_building_type_detects_restaurant_from_coffee_shop():
    assert infer_building_type("coffee shop with seating for 20") == "restaurant"


def test_extract_bhk_returns_core_rooms():
    assert extract_bhk("3bhk flat") == {
        "bedroom": 3,
        "living_room": 1,
        "kitchen": 1,
        "bathroom": 2,
    }


def test_infer_template_rooms_uses_bhk_counts():
    rooms = infer_template_rooms("2bhk flat")
    counts = {room.room_type: room.count for room in rooms}

    assert counts["bedroom"] == 2
    assert counts["living_room"] == 1
    assert counts["kitchen"] == 1
    assert counts["bathroom"] == 1


def test_detect_style_hints_combines_known_styles():
    hints = detect_style_hints("modern minimalist open plan apartment")

    assert hints["open_plan_bias"] is True
    assert hints["ceiling_height"] == "standard"


def test_infer_building_returns_default_floors_and_rooms():
    inference = infer_building("two storey family house")

    assert inference.building_type == "two_storey_home"
    assert inference.total_floors == 2
    assert any(room.room_type == "master_bedroom" for room in inference.inferred_rooms)
