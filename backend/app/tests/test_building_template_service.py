import pytest

from app.services.building_template_service import BUILDING_TEMPLATES, apply_template_defaults, get_building_template
from app.services.prompt_service import RoomSpec


@pytest.mark.parametrize(
    "building_type",
    ["apartment", "studio", "house", "office", "clinic", "classroom", "retail"],
)
def test_supported_building_templates_define_generation_strategy(building_type: str):
    template = get_building_template(building_type)

    assert template.name == building_type
    assert template.default_rooms
    assert template.zone_priorities
    assert template.adjacency_priorities
    assert template.layout_pattern_strategy
    assert template.multi_floor_behavior


def test_unknown_building_type_falls_back_to_apartment_template():
    assert get_building_template("unknown").name == "apartment"


def test_office_template_adds_missing_default_room_group():
    specs = [RoomSpec(label="Open Workspace", room_type="workspace", w=6.0, h=3.0, d=5.0)]

    enriched = apply_template_defaults(specs, "office")
    types = {room.room_type for room in enriched}

    assert {"entry", "reception", "workspace", "meeting_room", "storage"}.issubset(types)


def test_residential_template_keeps_prompt_driven_room_list_small():
    specs = [RoomSpec(label="Bedroom", room_type="bedroom", w=4.0, h=3.0, d=4.0)]

    assert apply_template_defaults(specs, "apartment") == specs


def test_registry_contains_only_supported_mvp_templates():
    assert set(BUILDING_TEMPLATES) == {"apartment", "studio", "house", "office", "clinic", "classroom", "retail"}
