import uuid
from math import sqrt

from app.services.building_template_service import apply_template_defaults, get_building_template
from app.services.layout_pattern_service import LayoutPatternRules, fallback_layout_rules
from app.services.prompt_service import RoomSpec

ROOM_COLORS: dict[str, str] = {
    "living_room":    "#818cf8",
    "kitchen":        "#34d399",
    "master_bedroom": "#fb923c",
    "bedroom":        "#f472b6",
    "bathroom":       "#60a5fa",
    "dining_room":    "#facc15",
    "office":         "#a78bfa",
    "study":          "#c084fc",
    "workspace":      "#8b5cf6",
    "meeting_room":   "#7c3aed",
    "reception":      "#14b8a6",
    "waiting_room":   "#2dd4bf",
    "consultation_room": "#38bdf8",
    "classroom":      "#f59e0b",
    "retail_display": "#22c55e",
    "checkout":       "#eab308",
    "storage":        "#a8a29e",
    "entry":          "#64748b",
    "hallway":        "#94a3b8",
    "balcony":        "#4ade80",
    "garage":         "#78716c",
    "utility":        "#cbd5e1",
    "stairs":         "#9ca3af",
}

_GAP     = 1.0   # metres between rooms in same row
_ZONE_GAP = 2.0  # metres between zone rows
_FLOOR_HEIGHT = 3.2
_STAIRS_SIZE = {"w": 2.0, "h": _FLOOR_HEIGHT, "d": 3.0}
_STAIRS_POSITION = {"x": 1.0, "z": 1.5}


def _floor_name(level: int) -> str:
    names = {
        0: "Ground Floor",
        1: "First Floor",
        2: "Second Floor",
        3: "Third Floor",
    }
    return names.get(level, f"Floor {level}")


def _room_area(specs: list[RoomSpec]) -> float:
    return round(sum(room.w * room.d for room in specs), 2)


def _size_room_specs(
    specs: list[RoomSpec],
    rules: LayoutPatternRules,
    total_area_sqm: float | None = None,
) -> list[RoomSpec]:
    targets: list[tuple[RoomSpec, float]] = []
    for room in specs:
        rule = rules.rule_for(room.room_type)
        current_area = room.w * room.d
        target_area = min(max(current_area, rule.typical_area_sqm_min), rule.typical_area_sqm_max)
        if (
            total_area_sqm is not None
            and rule.room_to_total_area_ratio_min is not None
            and rule.room_to_total_area_ratio_max is not None
        ):
            ratio = (rule.room_to_total_area_ratio_min + rule.room_to_total_area_ratio_max) / 2
            target_area = min(
                max(total_area_sqm * ratio, rule.typical_area_sqm_min),
                rule.typical_area_sqm_max,
            )

        targets.append((room, target_area))

    has_ratio_guidance = any(
        rules.rule_for(room.room_type).room_to_total_area_ratio_min is not None
        and rules.rule_for(room.room_type).room_to_total_area_ratio_max is not None
        for room, _ in targets
    )
    if total_area_sqm is not None and targets and not has_ratio_guidance:
        allocated_area = sum(target for _, target in targets)
        scale = total_area_sqm / allocated_area if allocated_area else 1.0
        targets = [
            (
                room,
                min(
                    max(target * scale, rules.rule_for(room.room_type).typical_area_sqm_min),
                    rules.rule_for(room.room_type).typical_area_sqm_max,
                ),
            )
            for room, target in targets
        ]

    sized: list[RoomSpec] = []
    for room, target_area in targets:
        aspect_ratio = room.w / room.d if room.d else 1.0
        sized.append(
            RoomSpec(
                label=room.label,
                room_type=room.room_type,
                w=round(sqrt(target_area * aspect_ratio), 2),
                h=room.h,
                d=round(sqrt(target_area / aspect_ratio), 2),
            )
        )
    return sized


def _place_rooms(
    specs: list[RoomSpec],
    rules: LayoutPatternRules,
    floor_id: str = "floor_0",
    floor_level: int = 0,
    elevation: float = 0.0,
    x_offset: float = 0.0,
) -> list[dict]:
    public_cluster = {"entry", "living_room", "kitchen", "dining_room"}
    placement_priority = {
        "entry": 0,
        "living_room": 1,
        "kitchen": 2,
        "dining_room": 3,
        "hallway": 4,
    }

    def placement_group(room: RoomSpec) -> str:
        zone = rules.zone_for(room.room_type)
        if room.room_type in public_cluster:
            return "public_cluster"
        return zone

    groups: dict[str, list[RoomSpec]] = {
        "public_cluster": [],
        "circulation": [],
        "private": [],
        "service": [],
        "public": [],
        "other": [],
    }
    for room in specs:
        groups.get(placement_group(room), groups["other"]).append(room)

    for rooms in groups.values():
        rooms.sort(key=lambda room: (placement_priority.get(room.room_type, 50), room.label))

    result: list[dict] = []
    current_z = 0.0

    for zone_rooms in groups.values():
        if not zone_rooms:
            continue
        current_x = x_offset
        zone_max_d = 0.0
        for room in zone_rooms:
            pos_x = round(current_x + room.w / 2, 2)
            pos_y = round(elevation + room.h / 2, 2)
            pos_z = round(current_z + room.d / 2, 2)
            result.append({
                "id":       str(uuid.uuid4()),
                "label":    room.label,
                "roomType": room.room_type,
                "objectType": "room",
                "floorId": floor_id,
                "floorLevel": floor_level,
                "zone": rules.zone_for(room.room_type),
                "position": {"x": pos_x, "y": pos_y, "z": pos_z},
                "size":     {"w": room.w, "h": room.h, "d": room.d},
                "color":    ROOM_COLORS.get(room.room_type, "#94a3b8"),
            })
            current_x += room.w + _GAP
            zone_max_d = max(zone_max_d, room.d)
        current_z += zone_max_d + _ZONE_GAP

    return result


def _add_stairs(floor_id: str, floor_level: int, elevation: float) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "label": "Stairs",
        "roomType": "stairs",
        "objectType": "stair",
        "floorId": floor_id,
        "floorLevel": floor_level,
        "zone": "circulation",
        "position": {
            "x": _STAIRS_POSITION["x"],
            "y": round(elevation + _STAIRS_SIZE["h"] / 2, 2),
            "z": _STAIRS_POSITION["z"],
        },
        "size": _STAIRS_SIZE.copy(),
        "color": ROOM_COLORS["stairs"],
    }


def _assign_rooms_to_floors(specs: list[RoomSpec], total_floors: int) -> list[list[RoomSpec]]:
    floors: list[list[RoomSpec]] = [[] for _ in range(total_floors)]
    if total_floors <= 1:
        floors[0].extend(specs)
        return floors

    upper_levels = list(range(1, total_floors))
    next_upper = 0
    ground_bathroom_added = False
    has_master = any(room.room_type == "master_bedroom" for room in specs)
    promoted_master = False

    def add_to_next_upper(room: RoomSpec) -> None:
        nonlocal next_upper
        level = upper_levels[next_upper % len(upper_levels)]
        floors[level].append(room)
        next_upper += 1

    for room in specs:
        if room.room_type in {"living_room", "kitchen", "dining_room", "hallway", "garage"}:
            floors[0].append(room)
            continue

        if room.room_type == "bathroom":
            if not ground_bathroom_added:
                floors[0].append(room)
                ground_bathroom_added = True
            else:
                add_to_next_upper(room)
            continue

        if room.room_type in {"master_bedroom", "bedroom"}:
            if room.room_type == "bedroom" and not has_master and not promoted_master:
                room = RoomSpec(
                    label="Master Bedroom",
                    room_type="master_bedroom",
                    w=room.w,
                    h=room.h,
                    d=room.d,
                )
                promoted_master = True
            add_to_next_upper(room)
            continue

        if room.room_type in {"balcony", "utility"}:
            floors[-1].append(room)
            continue

        add_to_next_upper(room)

    return floors


def generate_layout(
    room_specs: list[RoomSpec],
    prompt: str = "",
    building_type: str = "apartment",
    total_floors: int = 1,
    pattern_rules: LayoutPatternRules | None = None,
    total_area_sqm: float | None = None,
) -> dict:
    total_floors = max(1, total_floors)
    template = get_building_template(building_type)
    room_specs = apply_template_defaults(room_specs, building_type)
    pattern_rules = pattern_rules or fallback_layout_rules(
        building_type,
        {room.room_type for room in room_specs},
    )
    room_specs = _size_room_specs(room_specs, pattern_rules, total_area_sqm)
    floor_specs = _assign_rooms_to_floors(room_specs, total_floors)
    floors: list[dict] = []
    flat_rooms: list[dict] = []

    for level, specs in enumerate(floor_specs):
        floor_id = f"floor_{level}"
        elevation = round(level * _FLOOR_HEIGHT, 2)
        rooms = _place_rooms(
            specs,
            pattern_rules,
            floor_id=floor_id,
            floor_level=level,
            elevation=elevation,
            x_offset=(_STAIRS_SIZE["w"] + _GAP if total_floors > 1 else 0.0),
        )
        if total_floors > 1:
            rooms.insert(0, _add_stairs(floor_id, level, elevation))

        floor = {
            "id": floor_id,
            "name": _floor_name(level),
            "level": level,
            "elevation": elevation,
            "rooms": rooms,
        }
        floors.append(floor)
        flat_rooms.extend(rooms)

    return {
        "version": "1.0",
        "metadata": {
            "prompt":        prompt,
            "building_type": building_type,
            "buildingType":  building_type,
            "style":         "modern",
            "room_count":    len(flat_rooms),
            "totalFloors":   total_floors,
            "totalRooms":    len(room_specs),
            "totalAreaSqm":  _room_area(room_specs),
            "requestedAreaSqm": total_area_sqm,
            "patternDataUsed": pattern_rules.pattern_data_used,
            "zonesDetected": sorted({pattern_rules.zone_for(room.room_type) for room in room_specs}),
            "template": template.name,
            "templateStrategy": template.layout_pattern_strategy,
        },
        "building": {
            "floorHeight": _FLOOR_HEIGHT,
        },
        "floors": floors,
        "rooms": flat_rooms,
    }
