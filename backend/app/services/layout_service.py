import uuid

from app.services.prompt_service import RoomSpec

ROOM_COLORS: dict[str, str] = {
    "living_room":    "#818cf8",
    "kitchen":        "#34d399",
    "master_bedroom": "#fb923c",
    "bedroom":        "#f472b6",
    "bathroom":       "#60a5fa",
    "dining_room":    "#facc15",
    "office":         "#a78bfa",
    "hallway":        "#94a3b8",
    "balcony":        "#4ade80",
    "garage":         "#78716c",
    "utility":        "#cbd5e1",
}

_PUBLIC  = frozenset({"living_room", "kitchen", "dining_room", "hallway"})
_PRIVATE = frozenset({"master_bedroom", "bedroom", "bathroom"})
_GAP     = 1.0   # metres between rooms in same row
_ZONE_GAP = 2.0  # metres between zone rows


def _place_rooms(specs: list[RoomSpec]) -> list[dict]:
    public  = [r for r in specs if r.room_type in _PUBLIC]
    private = [r for r in specs if r.room_type in _PRIVATE]
    other   = [r for r in specs if r.room_type not in _PUBLIC and r.room_type not in _PRIVATE]

    result: list[dict] = []
    current_z = 0.0

    for zone in (public, private, other):
        if not zone:
            continue
        current_x = 0.0
        zone_max_d = 0.0
        for room in zone:
            pos_x = round(current_x + room.w / 2, 2)
            pos_y = round(room.h / 2, 2)
            pos_z = round(current_z + room.d / 2, 2)
            result.append({
                "id":       str(uuid.uuid4()),
                "label":    room.label,
                "position": {"x": pos_x, "y": pos_y, "z": pos_z},
                "size":     {"w": room.w, "h": room.h, "d": room.d},
                "color":    ROOM_COLORS.get(room.room_type, "#94a3b8"),
            })
            current_x += room.w + _GAP
            zone_max_d = max(zone_max_d, room.d)
        current_z += zone_max_d + _ZONE_GAP

    return result


def generate_layout(
    room_specs: list[RoomSpec],
    prompt: str = "",
    building_type: str = "apartment",
) -> dict:
    rooms = _place_rooms(room_specs)
    return {
        "version": "1.0",
        "metadata": {
            "prompt":        prompt,
            "building_type": building_type,
            "room_count":    len(rooms),
        },
        "rooms": rooms,
    }
