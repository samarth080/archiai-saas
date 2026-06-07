from dataclasses import dataclass, field

from app.services.parser.building_inference import TemplateRoom
from app.services.parser.room_extractor import ExtractedRoom


COMPOUND_ROOM_ABSORBS: dict[str, set[str]] = {
    "open_plan_living": {"living_room", "dining_room"},
    "kitchen_dining": {"kitchen", "dining_room"},
    "studio_unit": {"bedroom", "living_room"},
}


@dataclass(frozen=True)
class MergedRoom:
    room_type: str
    count: int = 1
    size_key: str = "medium"
    source: str = "inferred"
    is_compound: bool = False
    features: dict = field(default_factory=dict)


def _from_template(room: TemplateRoom) -> MergedRoom:
    return MergedRoom(
        room_type=room.room_type,
        count=room.count,
        size_key=room.size_key,
        source=room.source,
    )


def _from_explicit(room: ExtractedRoom) -> MergedRoom:
    return MergedRoom(
        room_type=room.room_type,
        count=room.count,
        source=room.source,
        is_compound=room.room_type in COMPOUND_ROOM_ABSORBS,
        features=dict(room.features),
    )


def _apply_compound_absorption(rooms: dict[str, MergedRoom], compound_type: str) -> None:
    absorbed_types = COMPOUND_ROOM_ABSORBS.get(compound_type, set())
    for room_type in absorbed_types:
        rooms.pop(room_type, None)


def _apply_open_plan_bias(rooms: dict[str, MergedRoom], style_hints: dict | None) -> None:
    if not style_hints or not style_hints.get("open_plan_bias"):
        return
    if "open_plan_living" in rooms:
        _apply_compound_absorption(rooms, "open_plan_living")
        return
    if "living_room" not in rooms or "dining_room" not in rooms:
        return

    rooms.pop("living_room")
    rooms.pop("dining_room")
    rooms["open_plan_living"] = MergedRoom(
        room_type="open_plan_living",
        count=1,
        size_key="large",
        source="style",
        is_compound=True,
        features={"open_plan": True},
    )


def _subtract_master_from_bedrooms(rooms: dict[str, MergedRoom], explicit_master_count: int) -> None:
    bedroom = rooms.get("bedroom")
    if bedroom is None or explicit_master_count <= 0:
        return
    remaining_count = bedroom.count - explicit_master_count
    if remaining_count <= 0:
        rooms.pop("bedroom")
        return
    rooms["bedroom"] = MergedRoom(
        room_type=bedroom.room_type,
        count=remaining_count,
        size_key=bedroom.size_key,
        source=bedroom.source,
        is_compound=bedroom.is_compound,
        features=dict(bedroom.features),
    )


def merge_rooms(
    template_rooms: list[TemplateRoom],
    explicit_rooms: list[ExtractedRoom],
    style_hints: dict | None = None,
    exclusions: list[str] | None = None,
) -> list[MergedRoom]:
    rooms: dict[str, MergedRoom] = {
        room.room_type: _from_template(room)
        for room in template_rooms
        if room.count > 0
    }

    explicit_master_count = 0
    for room in explicit_rooms:
        if room.count <= 0:
            continue
        merged = _from_explicit(room)
        if merged.room_type == "master_bedroom":
            explicit_master_count += merged.count
        rooms[merged.room_type] = merged
        if merged.is_compound:
            _apply_compound_absorption(rooms, merged.room_type)

    _subtract_master_from_bedrooms(rooms, explicit_master_count)
    _apply_open_plan_bias(rooms, style_hints)

    for excluded_room_type in exclusions or []:
        rooms.pop(excluded_room_type, None)

    return list(rooms.values())
