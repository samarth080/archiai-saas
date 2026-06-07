from app.services.parser.room_extractor import extract_explicit_rooms


def _counts(prompt: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for room in extract_explicit_rooms(prompt):
        counts[room.room_type] = counts.get(room.room_type, 0) + room.count
    return counts


def test_extracts_counted_rooms_from_common_prompt():
    counts = _counts("4 bedroom and 3 bathroom apartment with kitchen")

    assert counts["bedroom"] == 4
    assert counts["bathroom"] == 3
    assert counts["kitchen"] == 1


def test_extracts_compound_master_bedroom_with_ensuite():
    rooms = extract_explicit_rooms("master bedroom with attached bathroom")
    room_types = [room.room_type for room in rooms]
    ensuite = next(room for room in rooms if room.room_type == "ensuite")

    assert "master_bedroom" in room_types
    assert ensuite.features["attached"] is True
    assert ensuite.source == "compound"


def test_extracts_kitchen_dining_compound_terms():
    counts = _counts("open plan kitchen dining and lounge")

    assert counts["open_plan_living"] == 1
    assert counts["kitchen"] == 1
    assert counts["dining_room"] == 1
    assert counts["living_room"] == 1


def test_extracts_suffix_count_syntax():
    counts = _counts("bedroom: 3, bathroom x 2, kitchen")

    assert counts["bedroom"] == 3
    assert counts["bathroom"] == 2
    assert counts["kitchen"] == 1


def test_guest_bedroom_keeps_guest_feature():
    rooms = extract_explicit_rooms("guest bedroom with bathroom")
    guest_bedroom = next(room for room in rooms if room.room_type == "bedroom")

    assert guest_bedroom.features["guest"] is True
