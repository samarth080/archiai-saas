from app.services.refinement_service import AddOp, RemoveOp, ResizeOp, parse_refinement


def test_parse_add_single_bedroom():
    assert parse_refinement("add a bedroom") == [AddOp(room_type="bedroom", count=1)]


def test_parse_add_numeric_count():
    assert parse_refinement("add 3 bathrooms") == [AddOp(room_type="bathroom", count=3)]


def test_parse_add_word_count():
    assert parse_refinement("add three bedrooms") == [AddOp(room_type="bedroom", count=3)]


def test_parse_add_another():
    assert parse_refinement("another bedroom please") == [AddOp(room_type="bedroom", count=1)]


def test_parse_remove_single():
    assert parse_refinement("remove the office") == [RemoveOp(room_type="office", count=1)]


def test_parse_remove_all():
    assert parse_refinement("remove all bathrooms") == [RemoveOp(room_type="bathroom", count=None)]


def test_parse_remove_no_more():
    assert parse_refinement("no more bathrooms") == [RemoveOp(room_type="bathroom", count=None)]


def test_parse_resize_bigger():
    assert parse_refinement("make the kitchen bigger") == [ResizeOp(room_type="kitchen", factor=1.4)]


def test_parse_resize_smaller():
    assert parse_refinement("shrink the living room") == [
        ResizeOp(room_type="living_room", factor=0.7)
    ]


def test_parse_combined_add_remove():
    assert parse_refinement("add a bedroom and remove the office") == [
        AddOp(room_type="bedroom", count=1),
        RemoveOp(room_type="office", count=1),
    ]


def test_parse_returns_empty_for_unrecognised():
    assert parse_refinement("just chilling here") == []


import copy
from math import sqrt

from app.services.refinement_service import apply_refinement

SAMPLE_LAYOUT = {
    "version": "1.0",
    "metadata": {"prompt": "starter", "building_type": "apartment", "room_count": 3},
    "building": {"floorHeight": 3.2},
    "floors": [
        {
            "id": "floor_0",
            "name": "Ground Floor",
            "level": 0,
            "elevation": 0.0,
            "rooms": [
                {
                    "id": "r-1", "label": "Living Room", "roomType": "living_room",
                    "objectType": "room", "floorId": "floor_0", "floorLevel": 0,
                    "position": {"x": 2.5, "y": 1.5, "z": 2.5},
                    "size": {"w": 5.0, "h": 3.0, "d": 5.0},
                    "rotation": {"x": 0, "y": 0, "z": 0}, "color": "#818cf8",
                },
                {
                    "id": "r-2", "label": "Kitchen", "roomType": "kitchen",
                    "objectType": "room", "floorId": "floor_0", "floorLevel": 0,
                    "position": {"x": 8.0, "y": 1.5, "z": 2.0},
                    "size": {"w": 4.0, "h": 3.0, "d": 4.0},
                    "rotation": {"x": 0, "y": 0, "z": 0}, "color": "#34d399",
                },
                {
                    "id": "r-3", "label": "Office", "roomType": "office",
                    "objectType": "room", "floorId": "floor_0", "floorLevel": 0,
                    "position": {"x": 2.0, "y": 1.5, "z": 9.0},
                    "size": {"w": 4.0, "h": 3.0, "d": 4.0},
                    "rotation": {"x": 0, "y": 0, "z": 0}, "color": "#a78bfa",
                },
            ],
        }
    ],
    "rooms": [],
}
# Mirror floor rooms into top-level for sanity
SAMPLE_LAYOUT["rooms"] = [
    copy.deepcopy(r) for r in SAMPLE_LAYOUT["floors"][0]["rooms"]
]


def test_apply_resize_scales_w_and_d_by_sqrt_factor_and_keeps_xz():
    layout = copy.deepcopy(SAMPLE_LAYOUT)
    new_layout, summary = apply_refinement(layout, [ResizeOp(room_type="kitchen", factor=1.4)])

    kitchen = next(r for r in new_layout["rooms"] if r["id"] == "r-2")
    expected_w = round(4.0 * sqrt(1.4), 1)
    assert kitchen["size"]["w"] == expected_w
    assert kitchen["size"]["d"] == expected_w
    assert kitchen["position"]["x"] == 8.0
    assert kitchen["position"]["z"] == 2.0
    assert kitchen["position"]["y"] == 0.0 + kitchen["size"]["h"] / 2
    assert "Resized" in summary and "kitchen" in summary.lower()


def test_apply_remove_existing_room_returns_summary():
    layout = copy.deepcopy(SAMPLE_LAYOUT)
    new_layout, summary = apply_refinement(layout, [RemoveOp(room_type="office", count=1)])

    assert all(r["id"] != "r-3" for r in new_layout["rooms"])
    assert len(new_layout["rooms"]) == 2
    assert "Removed" in summary and "office" in summary.lower()


def test_apply_remove_missing_room_returns_empty_summary():
    layout = copy.deepcopy(SAMPLE_LAYOUT)
    new_layout, summary = apply_refinement(layout, [RemoveOp(room_type="balcony", count=1)])

    assert len(new_layout["rooms"]) == 3
    assert summary == ""


def test_apply_add_appends_room_without_moving_existing():
    layout = copy.deepcopy(SAMPLE_LAYOUT)
    before_by_id = {r["id"]: copy.deepcopy(r) for r in layout["rooms"]}

    new_layout, summary = apply_refinement(layout, [AddOp(room_type="bedroom", count=1)])

    # Append-only invariant: existing rooms identical
    existing = [r for r in new_layout["rooms"] if r["id"] in before_by_id]
    for room in existing:
        assert room == before_by_id[room["id"]]

    # New bedroom present
    new_rooms = [r for r in new_layout["rooms"] if r["id"] not in before_by_id]
    assert len(new_rooms) == 1
    bedroom = new_rooms[0]
    assert bedroom["roomType"] == "bedroom"
    assert bedroom["objectType"] == "room"
    assert bedroom["floorLevel"] == 0
    assert bedroom["size"] == {"w": 4.0, "h": 3.0, "d": 4.0}
    assert bedroom["color"] == "#f472b6"
    # Y bottom on the floor
    assert bedroom["position"]["y"] == bedroom["size"]["h"] / 2

    assert "Added" in summary and "bedroom" in summary.lower()
