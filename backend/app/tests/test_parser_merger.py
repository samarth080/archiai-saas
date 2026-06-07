from app.services.parser.building_inference import TemplateRoom
from app.services.parser.merger import merge_rooms
from app.services.parser.room_extractor import ExtractedRoom


def _counts(rooms):
    return {room.room_type: room.count for room in rooms}


def test_explicit_room_replaces_template_count():
    result = merge_rooms(
        [
            TemplateRoom("bedroom", 2),
            TemplateRoom("bathroom", 1, size_key="small"),
        ],
        [ExtractedRoom("bedroom", 4)],
    )

    assert _counts(result)["bedroom"] == 4
    assert next(room for room in result if room.room_type == "bedroom").source == "explicit"


def test_explicit_room_adds_missing_template_room():
    result = merge_rooms(
        [TemplateRoom("living_room", 1)],
        [ExtractedRoom("garage", 1)],
    )

    assert _counts(result) == {"living_room": 1, "garage": 1}


def test_explicit_master_bedroom_reduces_generic_bedroom_count():
    result = merge_rooms(
        [TemplateRoom("bedroom", 3)],
        [ExtractedRoom("master_bedroom", 1)],
    )

    assert _counts(result)["master_bedroom"] == 1
    assert _counts(result)["bedroom"] == 2


def test_ensuite_is_distinct_from_bathroom():
    result = merge_rooms(
        [TemplateRoom("bathroom", 2, size_key="small")],
        [ExtractedRoom("ensuite", 1, source="compound", features={"attached": True})],
    )

    counts = _counts(result)
    assert counts["bathroom"] == 2
    assert counts["ensuite"] == 1


def test_open_plan_living_absorbs_standalone_public_rooms():
    result = merge_rooms(
        [
            TemplateRoom("living_room", 1),
            TemplateRoom("dining_room", 1),
            TemplateRoom("kitchen", 1),
        ],
        [ExtractedRoom("open_plan_living", 1, source="compound", features={"open_plan": True})],
    )

    counts = _counts(result)
    assert "living_room" not in counts
    assert "dining_room" not in counts
    assert counts["open_plan_living"] == 1
    assert counts["kitchen"] == 1


def test_open_plan_bias_merges_living_and_dining_defaults():
    result = merge_rooms(
        [
            TemplateRoom("living_room", 1),
            TemplateRoom("dining_room", 1),
            TemplateRoom("bedroom", 2),
        ],
        [],
        style_hints={"open_plan_bias": True},
    )

    counts = _counts(result)
    assert "living_room" not in counts
    assert "dining_room" not in counts
    assert counts["open_plan_living"] == 1
    assert counts["bedroom"] == 2


def test_exclusions_remove_template_rooms():
    result = merge_rooms(
        [TemplateRoom("garage", 1), TemplateRoom("living_room", 1)],
        [],
        exclusions=["garage"],
    )

    assert _counts(result) == {"living_room": 1}
