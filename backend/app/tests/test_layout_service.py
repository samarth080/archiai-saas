import pytest
from app.services.prompt_service import RoomSpec
from app.services.layout_service import generate_layout


def _make_specs() -> list[RoomSpec]:
    return [
        RoomSpec(label="Living Room", room_type="living_room", w=5.0, h=3.0, d=5.0),
        RoomSpec(label="Kitchen",     room_type="kitchen",     w=4.0, h=3.0, d=4.0),
        RoomSpec(label="Bedroom",     room_type="bedroom",     w=4.0, h=3.0, d=4.0),
    ]


def test_all_rooms_have_position_and_size():
    layout = generate_layout(_make_specs())
    for room in layout["rooms"]:
        assert "position" in room
        assert "size" in room
        assert all(k in room["position"] for k in ("x", "y", "z"))
        assert all(k in room["size"] for k in ("w", "h", "d"))


def test_room_count_matches_input():
    specs = _make_specs()
    layout = generate_layout(specs)
    assert len(layout["rooms"]) == len(specs)


def test_y_position_equals_half_height():
    layout = generate_layout(_make_specs())
    for room in layout["rooms"]:
        assert room["position"]["y"] == pytest.approx(room["size"]["h"] / 2)


def test_no_room_overlaps_in_xz_plane():
    layout = generate_layout(_make_specs())
    rooms = layout["rooms"]
    for i, a in enumerate(rooms):
        for j, b in enumerate(rooms):
            if i == j:
                continue
            ax1 = a["position"]["x"] - a["size"]["w"] / 2
            ax2 = a["position"]["x"] + a["size"]["w"] / 2
            az1 = a["position"]["z"] - a["size"]["d"] / 2
            az2 = a["position"]["z"] + a["size"]["d"] / 2
            bx1 = b["position"]["x"] - b["size"]["w"] / 2
            bx2 = b["position"]["x"] + b["size"]["w"] / 2
            bz1 = b["position"]["z"] - b["size"]["d"] / 2
            bz2 = b["position"]["z"] + b["size"]["d"] / 2
            x_overlap = ax1 < bx2 and ax2 > bx1
            z_overlap = az1 < bz2 and az2 > bz1
            assert not (x_overlap and z_overlap), (
                f"Rooms '{a['label']}' and '{b['label']}' overlap"
            )
