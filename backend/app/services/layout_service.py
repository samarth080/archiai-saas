import uuid
from math import sqrt

from app.services.building_template_service import BuildingTemplate, apply_template_defaults, get_building_template
from app.services.layout_pattern_service import LayoutPatternRules, fallback_layout_rules
from app.services.layout_quality_service import score_layout_quality
from app.services.prompt_service import RoomSpec
from app.services.parser.constraint_extractor import AdjacencyConstraint

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
    "wall":           "#475569",
    "door":           "#a16207",
    "window":         "#38bdf8",
}

_GAP = 0.6  # metres between rooms in same row
_ADJACENCY_ROW_GAP = 0.35
_ZONE_GAP = 1.0  # metres between zone rows
_FLOOR_HEIGHT = 3.2
_STAIRS_SIZE = {"w": 2.0, "h": _FLOOR_HEIGHT, "d": 3.0}

BUILDING_FLOW_PRIORITY: dict[str, dict[str, int]] = {
    "clinic": {
        "entry": 0,
        "reception": 1,
        "waiting_room": 2,
        "consultation_room": 3,
        "bathroom": 4,
        "storage": 5,
        "utility": 6,
    },
    "house": {
        "entry": 0,
        "living_room": 1,
        "dining_room": 2,
        "kitchen": 3,
        "hallway": 4,
        "bathroom": 5,
        "bedroom": 6,
        "master_bedroom": 7,
        "storage": 8,
    },
    "apartment": {
        "entry": 0,
        "living_room": 1,
        "kitchen": 2,
        "dining_room": 3,
        "hallway": 4,
        "bathroom": 5,
        "bedroom": 6,
        "master_bedroom": 7,
    },
    "studio": {
        "entry": 0,
        "living_room": 1,
        "kitchen": 2,
        "bathroom": 3,
    },
    "office": {
        "entry": 0,
        "reception": 1,
        "waiting_room": 2,
        "workspace": 3,
        "meeting_room": 4,
        "office": 5,
        "storage": 6,
        "bathroom": 7,
    },
    "restaurant": {
        "entry": 0,
        "reception": 1,
        "waiting_room": 2,
        "dining_room": 3,
        "kitchen": 4,
        "storage": 5,
        "bathroom": 6,
    },
    "retail": {
        "entry": 0,
        "retail_display": 1,
        "checkout": 2,
        "storage": 3,
        "bathroom": 4,
    },
}

ENTRY_PRIVATE_AVOID_TYPES = {
    "bedroom",
    "master_bedroom",
    "consultation_room",
    "office",
    "storage",
    "utility",
}


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


def _edge_gap(a: dict, b: dict) -> float:
    if a.get("floorLevel") != b.get("floorLevel"):
        return float("inf")
    x_gap = max(
        0.0,
        abs(a["position"]["x"] - b["position"]["x"]) - (a["size"]["w"] + b["size"]["w"]) / 2,
    )
    z_gap = max(
        0.0,
        abs(a["position"]["z"] - b["position"]["z"]) - (a["size"]["d"] + b["size"]["d"]) / 2,
    )
    return round(x_gap + z_gap, 2)


def _room_bounds(room: dict) -> tuple[float, float, float, float]:
    return (
        room["position"]["x"] - room["size"]["w"] / 2,
        room["position"]["x"] + room["size"]["w"] / 2,
        room["position"]["z"] - room["size"]["d"] / 2,
        room["position"]["z"] + room["size"]["d"] / 2,
    )


def _rooms_overlap(a: dict, b: dict) -> bool:
    if a.get("floorLevel") != b.get("floorLevel"):
        return False
    ax1, ax2, az1, az2 = _room_bounds(a)
    bx1, bx2, bz1, bz2 = _room_bounds(b)
    return ax1 < bx2 and ax2 > bx1 and az1 < bz2 and az2 > bz1


def _flow_priority(building_type: str, room: RoomSpec) -> tuple[int, str]:
    priority = BUILDING_FLOW_PRIORITY.get(building_type, BUILDING_FLOW_PRIORITY["apartment"])
    return priority.get(room.room_type, 80), room.label


def _placement_group(
    room: RoomSpec,
    *,
    building_type: str,
    rules: LayoutPatternRules,
) -> str:
    room_type = room.room_type
    if building_type in {"apartment", "studio", "house"} and room_type in {
        "entry",
        "living_room",
        "kitchen",
        "dining_room",
        "hallway",
    }:
        return "front_public_flow"
    if building_type == "clinic" and room_type in {
        "entry",
        "reception",
        "waiting_room",
        "consultation_room",
        "bathroom",
    }:
        return "front_public_flow"
    if building_type == "office" and room_type in {
        "entry",
        "reception",
        "waiting_room",
        "workspace",
        "meeting_room",
    }:
        return "front_public_flow"
    if building_type == "restaurant" and room_type in {
        "entry",
        "reception",
        "waiting_room",
        "dining_room",
        "kitchen",
    }:
        return "front_public_flow"
    if building_type == "retail" and room_type in {"entry", "retail_display", "checkout"}:
        return "front_public_flow"
    return rules.zone_for(room_type)


def _ordered_group_names(template: BuildingTemplate) -> list[str]:
    names = ["front_public_flow"]
    for zone in template.zone_priorities:
        if zone not in names:
            names.append(zone)
    for zone in ("circulation", "public", "semi_private", "private", "service", "other"):
        if zone not in names:
            names.append(zone)
    return names


def _place_rooms(
    specs: list[RoomSpec],
    rules: LayoutPatternRules,
    template: BuildingTemplate,
    building_type: str,
    floor_id: str = "floor_0",
    floor_level: int = 0,
    elevation: float = 0.0,
    x_offset: float = 0.0,
    max_row_width: float | None = None,
    must_adjacency_pairs: set[frozenset] | None = None,
) -> list[dict]:
    ordered_groups = _ordered_group_names(template)
    groups: dict[str, list[RoomSpec]] = {group: [] for group in ordered_groups}
    for room in specs:
        group = _placement_group(room, building_type=building_type, rules=rules)
        groups.setdefault(group, []).append(room)

    for rooms in groups.values():
        rooms.sort(key=lambda room: _flow_priority(building_type, room))

    if must_adjacency_pairs:
        for key in list(groups):
            groups[key] = _sort_by_adjacency(groups[key], must_adjacency_pairs)

    result: list[dict] = []
    placed_by_type: dict[str, list[dict]] = {}
    current_z = 0.0
    previous_zone_max_d = 0.0

    for group_name in ordered_groups:
        zone_rooms = groups.get(group_name, [])
        if not zone_rooms:
            continue
        has_adjacent_anchor = any(
            target_type in placed_by_type
            for room in zone_rooms
            for target_type in rules.adjacency_for(room.room_type)
        )
        if result:
            current_z += previous_zone_max_d + (_ADJACENCY_ROW_GAP if has_adjacent_anchor else _ZONE_GAP)

        current_x = x_offset
        zone_max_d = 0.0
        for room in zone_rooms:
            anchor = next(
                (
                    candidate
                    for target_type in rules.adjacency_for(room.room_type)
                    for candidate in placed_by_type.get(target_type, [])
                    if candidate["position"]["z"] + candidate["size"]["d"] / 2 <= current_z + 0.001
                ),
                None,
            )
            if anchor is not None:
                current_x = max(current_x, x_offset, round(anchor["position"]["x"] - room.w / 2, 2))

            if (
                max_row_width is not None
                and current_x > x_offset
                and current_x + room.w > x_offset + max_row_width
            ):
                current_z += zone_max_d + _ADJACENCY_ROW_GAP
                current_x = x_offset
                zone_max_d = 0.0

            pos_x = round(current_x + room.w / 2, 2)
            pos_y = round(elevation + room.h / 2, 2)
            pos_z = round(current_z + room.d / 2, 2)
            placed_room = {
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
            }
            result.append(placed_room)
            placed_by_type.setdefault(room.room_type, []).append(placed_room)
            current_x += room.w + _GAP
            zone_max_d = max(zone_max_d, room.d)
        previous_zone_max_d = zone_max_d

    return result


def _repair_rooms(rooms: list[dict], *, building_type: str) -> list[dict]:
    repaired = [dict(room) for room in rooms]
    for room in repaired:
        room["position"] = dict(room["position"])
        room["size"] = dict(room["size"])
        room["position"]["x"] = max(room["size"]["w"] / 2, room["position"]["x"])
        room["position"]["z"] = max(room["size"]["d"] / 2, room["position"]["z"])

    by_floor: dict[int, list[dict]] = {}
    for room in repaired:
        by_floor.setdefault(room.get("floorLevel", 0), []).append(room)

    for floor_rooms in by_floor.values():
        # Iterative overlap resolution — run until stable (max 10 passes)
        for _ in range(10):
            changed = False
            floor_rooms.sort(key=lambda room: (room["position"]["z"], room["position"]["x"], room["label"]))
            for i, room in enumerate(floor_rooms):
                for previous in floor_rooms[:i]:
                    if not _rooms_overlap(previous, room):
                        continue
                    # Determine cheapest push direction
                    prev_x1, prev_x2, prev_z1, prev_z2 = _room_bounds(previous)
                    cur_x1, cur_x2, cur_z1, cur_z2 = _room_bounds(room)
                    overlap_z = min(prev_z2, cur_z2) - max(prev_z1, cur_z1)
                    overlap_x = min(prev_x2, cur_x2) - max(prev_x1, cur_x1)
                    if overlap_z <= overlap_x:
                        # push in Z (cheaper)
                        room["position"]["z"] = round(
                            prev_z2 + _GAP + room["size"]["d"] / 2, 2
                        )
                    else:
                        # push in X
                        room["position"]["x"] = round(
                            prev_x2 + _GAP + room["size"]["w"] / 2, 2
                        )
                    changed = True
                    break  # re-sort and retry after each move
            if not changed:
                break

        entry = next((room for room in floor_rooms if room.get("roomType") == "entry"), None)
        if entry is None:
            continue
        for room in floor_rooms:
            if room.get("roomType") not in ENTRY_PRIVATE_AVOID_TYPES:
                continue
            if _edge_gap(entry, room) <= 1.0:
                room["position"]["z"] = round(
                    entry["position"]["z"] + entry["size"]["d"] / 2 + _ZONE_GAP + room["size"]["d"] / 2,
                    2,
                )

    if building_type == "clinic":
        waiting = next((room for room in repaired if room.get("roomType") == "waiting_room"), None)
        bathroom = next((room for room in repaired if room.get("roomType") == "bathroom"), None)
        if waiting is not None and bathroom is not None and _edge_gap(waiting, bathroom) > 1.0:
            bathroom["position"]["x"] = waiting["position"]["x"]
            bathroom["position"]["z"] = round(
                waiting["position"]["z"] + waiting["size"]["d"] / 2 + _GAP + bathroom["size"]["d"] / 2,
                2,
            )

    return repaired


def _add_stairs(floor_id: str, floor_level: int, elevation: float, x_offset: float = 0.0) -> dict:
    stair_w = _STAIRS_SIZE["w"]
    stair_d = _STAIRS_SIZE["d"]
    # Place stairs in the reserved left strip (before x_offset), centred in it
    x_pos = max(stair_w / 2, (x_offset - _GAP) / 2) if x_offset > stair_w else stair_w / 2
    return {
        "id": str(uuid.uuid4()),
        "label": "Stairs",
        "roomType": "stairs",
        "objectType": "stair",
        "floorId": floor_id,
        "floorLevel": floor_level,
        "zone": "circulation",
        "position": {
            "x": round(x_pos, 2),
            "y": round(elevation + _STAIRS_SIZE["h"] / 2, 2),
            "z": round(stair_d / 2 + 0.3, 2),
        },
        "size": _STAIRS_SIZE.copy(),
        "color": ROOM_COLORS["stairs"],
    }


def _footprint_for_rooms(rooms: list[dict], margin: float = 0.5) -> dict:
    if not rooms:
        return {"x": 0.0, "z": 0.0, "w": 0.0, "d": 0.0}

    min_x = min(room["position"]["x"] - room["size"]["w"] / 2 for room in rooms) - margin
    max_x = max(room["position"]["x"] + room["size"]["w"] / 2 for room in rooms) + margin
    min_z = min(room["position"]["z"] - room["size"]["d"] / 2 for room in rooms) - margin
    max_z = max(room["position"]["z"] + room["size"]["d"] / 2 for room in rooms) + margin
    return {
        "x": round(min_x, 2),
        "z": round(min_z, 2),
        "w": round(max_x - min_x, 2),
        "d": round(max_z - min_z, 2),
    }


def _shared_footprint(footprints: list[dict]) -> dict:
    usable = [footprint for footprint in footprints if footprint.get("w") and footprint.get("d")]
    if not usable:
        return {"x": 0.0, "z": 0.0, "w": 0.0, "d": 0.0}

    min_x = min(footprint["x"] for footprint in usable)
    min_z = min(footprint["z"] for footprint in usable)
    max_x = max(footprint["x"] + footprint["w"] for footprint in usable)
    max_z = max(footprint["z"] + footprint["d"] for footprint in usable)
    return {
        "x": round(min_x, 2),
        "z": round(min_z, 2),
        "w": round(max_x - min_x, 2),
        "d": round(max_z - min_z, 2),
    }


def _max_row_width_for_layout(room_specs: list[RoomSpec], total_floors: int, building_type: str) -> float | None:
    if total_floors <= 1:
        return None

    total_area = sum(room.w * room.d for room in room_specs)
    base_width = sqrt(total_area) * 1.7 if total_area else 14.0
    if building_type in {"apartment", "house", "studio"}:
        return round(min(max(base_width, 12.0), 15.5), 2)
    return round(min(max(base_width, 16.0), 22.0), 2)


def _make_marker(
    *,
    label: str,
    room_type: str,
    object_type: str,
    floor_id: str,
    floor_level: int,
    elevation: float,
    position: dict[str, float],
    size: dict[str, float],
    rotation_y: float = 0.0,
) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "label": label,
        "roomType": room_type,
        "objectType": object_type,
        "floorId": floor_id,
        "floorLevel": floor_level,
        "zone": "boundary",
        "position": {
            "x": round(position["x"], 2),
            "y": round(elevation + position["y"], 2),
            "z": round(position["z"], 2),
        },
        "size": size,
        "rotation": {"x": 0, "y": rotation_y, "z": 0},
        "color": ROOM_COLORS.get(room_type, "#64748b"),
    }


def _architectural_markers(
    rooms: list[dict],
    *,
    floor_id: str,
    floor_level: int,
    elevation: float,
    footprint: dict,
) -> list[dict]:
    if not rooms or not footprint["w"] or not footprint["d"]:
        return []

    x = footprint["x"]
    z = footprint["z"]
    w = footprint["w"]
    d = footprint["d"]
    wall_h = 2.8
    wall_t = 0.18
    horizontal_wall_w = max(0.1, w - wall_t * 2)
    markers = [
        _make_marker(
            label="Front Wall",
            room_type="wall",
            object_type="wall",
            floor_id=floor_id,
            floor_level=floor_level,
            elevation=elevation,
            position={"x": x + w / 2, "y": wall_h / 2, "z": z},
            size={"w": horizontal_wall_w, "h": wall_h, "d": wall_t},
        ),
        _make_marker(
            label="Rear Wall",
            room_type="wall",
            object_type="wall",
            floor_id=floor_id,
            floor_level=floor_level,
            elevation=elevation,
            position={"x": x + w / 2, "y": wall_h / 2, "z": z + d},
            size={"w": horizontal_wall_w, "h": wall_h, "d": wall_t},
        ),
        _make_marker(
            label="Left Wall",
            room_type="wall",
            object_type="wall",
            floor_id=floor_id,
            floor_level=floor_level,
            elevation=elevation,
            position={"x": x, "y": wall_h / 2, "z": z + d / 2},
            size={"w": wall_t, "h": wall_h, "d": d},
        ),
        _make_marker(
            label="Right Wall",
            room_type="wall",
            object_type="wall",
            floor_id=floor_id,
            floor_level=floor_level,
            elevation=elevation,
            position={"x": x + w, "y": wall_h / 2, "z": z + d / 2},
            size={"w": wall_t, "h": wall_h, "d": d},
        ),
        _make_marker(
            label="Exterior Window",
            room_type="window",
            object_type="window",
            floor_id=floor_id,
            floor_level=floor_level,
            elevation=elevation,
            position={"x": x + w - min(2.0, w / 2), "y": 1.7, "z": z + d + 0.7},
            size={"w": 1.4, "h": 1.0, "d": 0.12},
        ),
    ]
    if floor_level == 0:
        markers.append(
            _make_marker(
                label="Entry Door",
                room_type="door",
                object_type="door",
                floor_id=floor_id,
                floor_level=floor_level,
                elevation=elevation,
                position={"x": x + min(2.0, w / 2), "y": 1.1, "z": z - 0.7},
                size={"w": 1.0, "h": 2.2, "d": 0.12},
            )
        )
    return markers


def _generate_partition_walls(
    rooms: list[dict],
    *,
    floor_id: str,
    floor_level: int,
    elevation: float,
) -> list[dict]:
    """
    Generate thin partition wall meshes between every pair of adjacent rooms
    on the same floor.  Two rooms are considered adjacent when the gap between
    their nearest edges is <= _GAP (i.e. they were placed side-by-side).
    """
    wall_h = 2.8
    wall_t = 0.15
    adjacency_threshold = _GAP + 0.05  # small tolerance
    room_only = [r for r in rooms if r.get("objectType") == "room"]
    walls: list[dict] = []

    checked: set[tuple[str, str]] = set()
    for i, a in enumerate(room_only):
        ax1, ax2, az1, az2 = _room_bounds(a)
        for b in room_only[i + 1:]:
            pair = tuple(sorted([a["id"], b["id"]]))
            if pair in checked:
                continue
            checked.add(pair)
            bx1, bx2, bz1, bz2 = _room_bounds(b)

            x_gap = max(0.0, max(ax1, bx1) - min(ax2, bx2))
            z_gap = max(0.0, max(az1, bz1) - min(az2, bz2))

            # Adjacent along Z axis (rooms side-by-side in X direction)
            if z_gap <= adjacency_threshold and x_gap < 0.05:
                # shared X boundary
                wall_x = (min(ax2, bx2) + max(ax1, bx1)) / 2
                overlap_z1 = max(az1, bz1)
                overlap_z2 = min(az2, bz2)
                if overlap_z2 > overlap_z1:
                    walls.append(_make_marker(
                        label="Partition Wall",
                        room_type="wall",
                        object_type="wall",
                        floor_id=floor_id,
                        floor_level=floor_level,
                        elevation=elevation,
                        position={"x": wall_x, "y": wall_h / 2, "z": (overlap_z1 + overlap_z2) / 2},
                        size={"w": wall_t, "h": wall_h, "d": round(overlap_z2 - overlap_z1, 2)},
                    ))

            # Adjacent along X axis (rooms side-by-side in Z direction)
            elif x_gap <= adjacency_threshold and z_gap < 0.05:
                # shared Z boundary
                wall_z = (min(az2, bz2) + max(az1, bz1)) / 2
                overlap_x1 = max(ax1, bx1)
                overlap_x2 = min(ax2, bx2)
                if overlap_x2 > overlap_x1:
                    walls.append(_make_marker(
                        label="Partition Wall",
                        room_type="wall",
                        object_type="wall",
                        floor_id=floor_id,
                        floor_level=floor_level,
                        elevation=elevation,
                        position={"x": (overlap_x1 + overlap_x2) / 2, "y": wall_h / 2, "z": wall_z},
                        size={"w": round(overlap_x2 - overlap_x1, 2), "h": wall_h, "d": wall_t},
                    ))
    return walls


def _sort_by_adjacency(
    rooms: list[RoomSpec],
    must_pairs: set[frozenset],
) -> list[RoomSpec]:
    """Reorder rooms so MUST-adjacent pairs are placed consecutively."""
    ordered: list[RoomSpec] = []
    remaining = list(rooms)
    while remaining:
        room = remaining.pop(0)
        ordered.append(room)
        for i, other in enumerate(remaining):
            if frozenset({room.room_type, other.room_type}) in must_pairs:
                ordered.append(remaining.pop(i))
                break
    return ordered


def _assign_rooms_to_floors(
    specs: list[RoomSpec],
    total_floors: int,
    zone_assignments: dict[str, str] | None = None,
) -> list[list[RoomSpec]]:
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

    explicit_zones = zone_assignments or {}

    for room in specs:
        # Explicit zone assignment from Stage 5 constraints takes first priority
        zone_pref = explicit_zones.get(room.room_type)
        if zone_pref == "ground":
            floors[0].append(room)
            continue
        if zone_pref == "upper":
            add_to_next_upper(room)
            continue

        # Default floor distribution rules
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


def _layout_bounds(rooms: list[dict]) -> dict:
    if not rooms:
        return {"minX": 0.0, "maxX": 0.0, "minZ": 0.0, "maxZ": 0.0, "width": 0.0, "depth": 0.0}
    bounds = [_room_bounds(room) for room in rooms]
    min_x = min(bound[0] for bound in bounds)
    max_x = max(bound[1] for bound in bounds)
    min_z = min(bound[2] for bound in bounds)
    max_z = max(bound[3] for bound in bounds)
    return {
        "minX": round(min_x - 0.01, 2),
        "maxX": round(max_x + 0.01, 2),
        "minZ": round(min_z - 0.01, 2),
        "maxZ": round(max_z + 0.01, 2),
        "width": round(max_x - min_x + 0.02, 2),
        "depth": round(max_z - min_z + 0.02, 2),
    }


def _build_layout_candidate(
    *,
    room_specs: list[RoomSpec],
    prompt: str,
    building_type: str,
    total_floors: int,
    pattern_rules: LayoutPatternRules,
    total_area_sqm: float | None,
    template: BuildingTemplate,
    x_offset: float,
    zone_assignments: dict[str, str] | None = None,
    must_adjacency_pairs: set[frozenset] | None = None,
) -> dict:
    floor_specs = _assign_rooms_to_floors(room_specs, total_floors, zone_assignments)
    max_row_width = _max_row_width_for_layout(room_specs, total_floors, building_type)
    pending_floors: list[dict] = []
    floor_footprints: list[dict] = []
    floors: list[dict] = []
    flat_rooms: list[dict] = []

    for level, specs in enumerate(floor_specs):
        floor_id = f"floor_{level}"
        elevation = round(level * _FLOOR_HEIGHT, 2)
        rooms = _place_rooms(
            specs,
            pattern_rules,
            template,
            building_type,
            floor_id=floor_id,
            floor_level=level,
            elevation=elevation,
            x_offset=x_offset,
            max_row_width=max_row_width,
            must_adjacency_pairs=must_adjacency_pairs,
        )
        rooms = _repair_rooms(rooms, building_type=building_type)
        if total_floors > 1:
            rooms.insert(0, _add_stairs(floor_id, level, elevation, x_offset=x_offset))
        footprint = _footprint_for_rooms(rooms)
        pending_floors.append(
            {
                "id": floor_id,
                "name": _floor_name(level),
                "level": level,
                "elevation": elevation,
                "footprint": footprint,
                "rooms": rooms,
            }
        )
        floor_footprints.append(footprint)

    building_footprint = _shared_footprint(floor_footprints) if total_floors > 1 else (
        floor_footprints[0] if floor_footprints else {"x": 0.0, "z": 0.0, "w": 0.0, "d": 0.0}
    )

    for pending_floor in pending_floors:
        footprint = building_footprint if total_floors > 1 else pending_floor["footprint"]
        rooms = list(pending_floor["rooms"])
        rooms.extend(
            _architectural_markers(
                rooms,
                floor_id=pending_floor["id"],
                floor_level=pending_floor["level"],
                elevation=pending_floor["elevation"],
                footprint=footprint,
            )
        )
        rooms.extend(
            _generate_partition_walls(
                rooms,
                floor_id=pending_floor["id"],
                floor_level=pending_floor["level"],
                elevation=pending_floor["elevation"],
            )
        )

        floor = {
            "id": pending_floor["id"],
            "name": pending_floor["name"],
            "level": pending_floor["level"],
            "elevation": pending_floor["elevation"],
            "footprint": footprint,
            "rooms": rooms,
        }
        floors.append(floor)
        flat_rooms.extend(rooms)

    bounds = _layout_bounds(flat_rooms)
    layout = {
        "version": "1.0",
        "metadata": {
            "prompt":        prompt,
            "building_type": building_type,
            "buildingType":  building_type,
            "style":         "modern",
            "room_count":    len(room_specs),
            "totalFloors":   total_floors,
            "totalRooms":    len(room_specs),
            "totalObjects":   len(flat_rooms),
            "totalAreaSqm":  _room_area(room_specs),
            "requestedAreaSqm": total_area_sqm,
            "patternDataUsed": pattern_rules.pattern_data_used,
            "patternDataSource": pattern_rules.pattern_data_source,
            "appliedPatternCount": pattern_rules.applied_pattern_count,
            "ignoredPatternCount": pattern_rules.ignored_pattern_count,
            "zonesDetected": sorted({pattern_rules.zone_for(room.room_type) for room in room_specs}),
            "template": template.name,
            "templateStrategy": template.layout_pattern_strategy,
            "candidateCount": 1,
        },
        "building": {
            "floorHeight": _FLOOR_HEIGHT,
            "footprint": building_footprint,
            "bounds": bounds,
        },
        "floors": floors,
        "rooms": flat_rooms,
    }
    layout["insights"] = score_layout_quality(
        layout,
        required_room_types={room.room_type for room in room_specs},
        pattern_rules=pattern_rules,
    ).to_dict()
    return layout


def generate_layout(
    room_specs: list[RoomSpec],
    prompt: str = "",
    building_type: str = "apartment",
    total_floors: int = 1,
    pattern_rules: LayoutPatternRules | None = None,
    total_area_sqm: float | None = None,
    adjacency_constraints: list[AdjacencyConstraint] | None = None,
    zone_assignments: dict[str, str] | None = None,
    vastu_requested: bool = False,
) -> dict:
    total_floors = max(1, total_floors)
    template = get_building_template(building_type)
    room_specs = apply_template_defaults(room_specs, building_type)
    pattern_rules = pattern_rules or fallback_layout_rules(
        building_type,
        {room.room_type for room in room_specs},
    )
    room_specs = _size_room_specs(room_specs, pattern_rules, total_area_sqm)

    must_pairs: set[frozenset] = {
        frozenset({c.room_a, c.room_b})
        for c in (adjacency_constraints or [])
        if c.strength == "MUST"
    }

    base_offset = _STAIRS_SIZE["w"] + _GAP if total_floors > 1 else 0.0
    candidates = [
        _build_layout_candidate(
            room_specs=room_specs,
            prompt=prompt,
            building_type=building_type,
            total_floors=total_floors,
            pattern_rules=pattern_rules,
            total_area_sqm=total_area_sqm,
            template=template,
            x_offset=base_offset + offset,
            zone_assignments=zone_assignments,
            must_adjacency_pairs=must_pairs or None,
        )
        for offset in (0.0, 0.5, 1.0)
    ]
    best = max(candidates, key=lambda candidate: candidate["insights"]["score"])
    best["metadata"]["candidateCount"] = len(candidates)

    if vastu_requested:
        from app.services.parser.vastu import check_vastu_compliance
        bounds = best.get("building", {}).get("bounds", {})
        placed = best.get("rooms", [])
        vastu_result = check_vastu_compliance(placed, bounds)
        best["metadata"]["vastu"] = {
            "is_requested": vastu_result.is_requested,
            "compliance_score": vastu_result.compliance_score,
            "brahmasthan_clear": vastu_result.brahmasthan_clear,
            "violations": [
                {
                    "room_type": v.room_type,
                    "current_direction": v.current_direction,
                    "recommended_direction": v.recommended_direction,
                    "severity": v.severity,
                    "message": v.message,
                }
                for v in vastu_result.violations
            ],
            "suggestions": vastu_result.suggestions,
        }

    return best
