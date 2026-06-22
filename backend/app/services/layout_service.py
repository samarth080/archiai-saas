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
    # 5mm tolerance: shared walls (ax2 ≈ bx1) must not count as overlaps
    _eps = 0.02
    return ax1 + _eps < bx2 and ax2 - _eps > bx1 and az1 + _eps < bz2 and az2 - _eps > bz1


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


def _add_stairs(
    floor_id: str,
    floor_level: int,
    elevation: float,
    x_offset: float = 0.0,
    x_pos: float | None = None,
) -> dict:
    stair_w = _STAIRS_SIZE["w"]
    stair_d = _STAIRS_SIZE["d"]
    if x_pos is None:
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


_ORIENTATION_ENTRY_WALL: dict[str, str] = {
    "S": "front", "N": "rear", "E": "right", "W": "left",
}


def _architectural_markers(
    rooms: list[dict],
    *,
    floor_id: str,
    floor_level: int,
    elevation: float,
    footprint: dict,
    orientation: str | None = None,
) -> list[dict]:
    if not rooms or not footprint["w"] or not footprint["d"]:
        return []

    x = footprint["x"]
    z = footprint["z"]
    w = footprint["w"]
    d = footprint["d"]
    wall_h = 2.8
    wall_t = 0.18
    # Boundary walls wrap the floor plate: their inner face sits on the footprint
    # edge so they never overlap the edge rooms (which fill the plate exactly in
    # the tiled engine).  Centre-lines are offset outward by half the thickness.
    off = wall_t / 2
    horizontal_wall_w = max(0.1, w + wall_t * 2)
    vertical_wall_d = max(0.1, d + wall_t * 2)
    markers = [
        _make_marker(
            label="Front Wall",
            room_type="wall",
            object_type="wall",
            floor_id=floor_id,
            floor_level=floor_level,
            elevation=elevation,
            position={"x": x + w / 2, "y": wall_h / 2, "z": z - off},
            size={"w": horizontal_wall_w, "h": wall_h, "d": wall_t},
        ),
        _make_marker(
            label="Rear Wall",
            room_type="wall",
            object_type="wall",
            floor_id=floor_id,
            floor_level=floor_level,
            elevation=elevation,
            position={"x": x + w / 2, "y": wall_h / 2, "z": z + d + off},
            size={"w": horizontal_wall_w, "h": wall_h, "d": wall_t},
        ),
        _make_marker(
            label="Left Wall",
            room_type="wall",
            object_type="wall",
            floor_id=floor_id,
            floor_level=floor_level,
            elevation=elevation,
            position={"x": x - off, "y": wall_h / 2, "z": z + d / 2},
            size={"w": wall_t, "h": wall_h, "d": vertical_wall_d},
        ),
        _make_marker(
            label="Right Wall",
            room_type="wall",
            object_type="wall",
            floor_id=floor_id,
            floor_level=floor_level,
            elevation=elevation,
            position={"x": x + w + off, "y": wall_h / 2, "z": z + d / 2},
            size={"w": wall_t, "h": wall_h, "d": vertical_wall_d},
        ),
    ]

    # The entry/road-facing wall is chosen from DesignParams.orientation when
    # given (S/N/E/W); it defaults to the front wall, matching prior behaviour.
    # Windows go on the other three exterior walls for cross-floor daylight,
    # one per wall, sized to that wall's span.
    entry_wall = _ORIENTATION_ENTRY_WALL.get((orientation or "S").upper(), "front")
    exterior_offset = 0.7  # metres beyond the wall face — keeps the marker clear of the wall mesh
    window_specs = {
        "front": {"x": x + w - min(2.0, w / 2), "y": 1.7, "z": z - exterior_offset},
        "rear": {"x": x + w - min(2.0, w / 2), "y": 1.7, "z": z + d + exterior_offset},
        "left": {"x": x - exterior_offset, "y": 1.7, "z": z + d - min(2.0, d / 2)},
        "right": {"x": x + w + exterior_offset, "y": 1.7, "z": z + d - min(2.0, d / 2)},
    }
    window_sizes = {
        "front": {"w": 1.4, "h": 1.0, "d": 0.12},
        "rear": {"w": 1.4, "h": 1.0, "d": 0.12},
        "left": {"w": 0.12, "h": 1.0, "d": 1.4},
        "right": {"w": 0.12, "h": 1.0, "d": 1.4},
    }
    for wall_side, position in window_specs.items():
        if wall_side == entry_wall:
            continue
        markers.append(
            _make_marker(
                label="Exterior Window",
                room_type="window",
                object_type="window",
                floor_id=floor_id,
                floor_level=floor_level,
                elevation=elevation,
                position=position,
                size=window_sizes[wall_side],
            )
        )

    if floor_level == 0:
        entry_positions = {
            "front": {"x": x + min(2.0, w / 2), "y": 1.1, "z": z - exterior_offset},
            "rear": {"x": x + min(2.0, w / 2), "y": 1.1, "z": z + d + exterior_offset},
            "left": {"x": x - exterior_offset, "y": 1.1, "z": z + min(2.0, d / 2)},
            "right": {"x": x + w + exterior_offset, "y": 1.1, "z": z + min(2.0, d / 2)},
        }
        entry_sizes = {
            "front": {"w": 1.0, "h": 2.2, "d": 0.12},
            "rear": {"w": 1.0, "h": 2.2, "d": 0.12},
            "left": {"w": 0.12, "h": 2.2, "d": 1.0},
            "right": {"w": 0.12, "h": 2.2, "d": 1.0},
        }
        markers.append(
            _make_marker(
                label="Entry Door",
                room_type="door",
                object_type="door",
                floor_id=floor_id,
                floor_level=floor_level,
                elevation=elevation,
                position=entry_positions[entry_wall],
                size=entry_sizes[entry_wall],
            )
        )
    return markers


_DOOR_WIDTH = 0.9     # metres
_DOOR_HEIGHT = 2.1    # metres
_DOOR_THICKNESS = 0.12  # metres — matches the existing window/entry-door markers
_MIN_DOORWAY_SPAN = 1.2  # metres — shorter shared walls don't get a door opening


def _wants_direct_door(a: dict, b: dict, *, has_corridor: bool) -> bool:
    """
    Decide whether two adjacent rooms should get a doorway directly between
    them, or whether they should only be reachable via the corridor.

    Without a corridor on the floor there's no alternative circulation path,
    so every adjacent pair gets a door (matches pre-corridor layouts). With a
    corridor, the corridor itself always gets a door to whatever it touches;
    open-plan public rooms (living/kitchen/dining/etc.) still flow into each
    other directly; but two private/service cells (e.g. an office and a
    bathroom sitting side by side in the same row) should each open onto the
    corridor, not into one another.
    """
    a_type = a.get("roomType")
    b_type = b.get("roomType")
    if a_type in _TILED_CORRIDOR_TYPES or b_type in _TILED_CORRIDOR_TYPES:
        return True
    if not has_corridor:
        return True
    return a_type in _TILED_FRONT_TYPES and b_type in _TILED_FRONT_TYPES


def _generate_partition_walls(
    rooms: list[dict],
    *,
    floor_id: str,
    floor_level: int,
    elevation: float,
) -> list[dict]:
    """
    Generate thin partition wall meshes between every pair of adjacent rooms
    on the same floor, plus a door marker centred on each wall long enough to
    fit one. Two rooms are considered adjacent when the gap between their
    nearest edges is <= _GAP (i.e. they were placed side-by-side); a doorway
    along that shared wall is what makes the floor plan actually walkable.

    Not every adjacent wall gets a doorway, though — see _wants_direct_door.
    Private/service rooms sitting beside each other in the same row (e.g. an
    office next to a bathroom) should each connect to the corridor, not to
    each other directly; the wall between them stays solid.
    """
    wall_h = 2.8
    wall_t = 0.15
    adjacency_threshold = _GAP + 0.05  # small tolerance
    room_only = [r for r in rooms if r.get("objectType") == "room"]
    has_corridor = any(r.get("roomType") in _TILED_CORRIDOR_TYPES for r in room_only)
    markers: list[dict] = []

    checked: set[tuple[str, str]] = set()
    for i, a in enumerate(room_only):
        ax1, ax2, az1, az2 = _room_bounds(a)
        for b in room_only[i + 1:]:
            pair = tuple(sorted([a["id"], b["id"]]))
            if pair in checked:
                continue
            checked.add(pair)
            bx1, bx2, bz1, bz2 = _room_bounds(b)
            wants_door = _wants_direct_door(a, b, has_corridor=has_corridor)

            # overlap_* is positive when the rooms' spans overlap on that axis,
            # negative (a gap) when they don't. When one room is narrower than
            # another and sits fully within its span on one axis (e.g. an
            # office narrower than the corridor it's stacked against), BOTH
            # axes can come out near zero — so the branch must be chosen by
            # which axis has the larger real overlap (the shared wall span),
            # not just by which gap happens to be small.
            overlap_x = min(ax2, bx2) - max(ax1, bx1)
            overlap_z = min(az2, bz2) - max(az1, bz1)
            x_gap = max(0.0, -overlap_x)
            z_gap = max(0.0, -overlap_z)

            # Adjacent along Z axis (rooms side-by-side in X direction)
            if overlap_z >= overlap_x and z_gap <= adjacency_threshold:
                # shared X boundary — a vertical wall running along Z
                wall_x = (min(ax2, bx2) + max(ax1, bx1)) / 2
                overlap_z1 = max(az1, bz1)
                overlap_z2 = min(az2, bz2)
                span = overlap_z2 - overlap_z1
                if span > 0:
                    wall_z = (overlap_z1 + overlap_z2) / 2
                    markers.append(_make_marker(
                        label="Partition Wall",
                        room_type="wall",
                        object_type="wall",
                        floor_id=floor_id,
                        floor_level=floor_level,
                        elevation=elevation,
                        position={"x": wall_x, "y": wall_h / 2, "z": wall_z},
                        size={"w": wall_t, "h": wall_h, "d": round(span, 2)},
                    ))
                    if wants_door and span >= _MIN_DOORWAY_SPAN:
                        markers.append(_make_marker(
                            label="Interior Door",
                            room_type="door",
                            object_type="door",
                            floor_id=floor_id,
                            floor_level=floor_level,
                            elevation=elevation,
                            position={"x": wall_x, "y": _DOOR_HEIGHT / 2, "z": wall_z},
                            size={"w": _DOOR_THICKNESS, "h": _DOOR_HEIGHT, "d": min(_DOOR_WIDTH, span)},
                        ))

            # Adjacent along X axis (rooms side-by-side in Z direction)
            elif overlap_x >= overlap_z and x_gap <= adjacency_threshold:
                # shared Z boundary — a horizontal wall running along X
                wall_z = (min(az2, bz2) + max(az1, bz1)) / 2
                overlap_x1 = max(ax1, bx1)
                overlap_x2 = min(ax2, bx2)
                span = overlap_x2 - overlap_x1
                if span > 0:
                    wall_x = (overlap_x1 + overlap_x2) / 2
                    markers.append(_make_marker(
                        label="Partition Wall",
                        room_type="wall",
                        object_type="wall",
                        floor_id=floor_id,
                        floor_level=floor_level,
                        elevation=elevation,
                        position={"x": wall_x, "y": wall_h / 2, "z": wall_z},
                        size={"w": round(span, 2), "h": wall_h, "d": wall_t},
                    ))
                    if wants_door and span >= _MIN_DOORWAY_SPAN:
                        markers.append(_make_marker(
                            label="Interior Door",
                            room_type="door",
                            object_type="door",
                            floor_id=floor_id,
                            floor_level=floor_level,
                            elevation=elevation,
                            position={"x": wall_x, "y": _DOOR_HEIGHT / 2, "z": wall_z},
                            size={"w": min(_DOOR_WIDTH, span), "h": _DOOR_HEIGHT, "d": _DOOR_THICKNESS},
                        ))
    return markers


# ── Zone classification for tiled layout ─────────────────────────────────────

_TILED_FRONT_TYPES: frozenset[str] = frozenset({
    "entry", "living_room", "open_plan_living", "dining_room", "kitchen",
    "foyer", "reception", "waiting_room", "retail_display", "checkout",
    "dining_area", "bar", "classroom",
})
_TILED_CORRIDOR_TYPES: frozenset[str] = frozenset({"hallway", "corridor"})
_TILED_PRIVATE_TYPES: frozenset[str] = frozenset({
    "bedroom", "master_bedroom", "kids_room", "office", "study", "workspace",
    "meeting_room", "consultation_room", "pooja_room", "meditation_room",
})
_TILED_SERVICE_TYPES: frozenset[str] = frozenset({
    "bathroom", "storage", "utility", "laundry", "garage", "staircase",
})

# Building types that use the tiled floor-plan algorithm.  As of Sprint 16 this
# is effectively every building type the parser can emit — residential and
# commercial alike — so layouts always fill their footprint with zero blank
# bands.  _place_rooms / _repair_rooms remain only as a fallback for any type
# not listed here.
_TILED_BUILDING_TYPES: frozenset[str] = frozenset({
    # residential — note both vocabularies' names (detect_building_type vs the
    # parser's infer_building_type) are listed so the production parse path tiles
    # too: e.g. "studio"/"studio_apartment", "house"/"family_home".
    "apartment", "studio", "studio_apartment", "house", "family_home",
    "two_storey_home", "bungalow", "villa", "townhouse",
    # commercial / institutional
    "office", "clinic", "restaurant", "retail", "classroom", "school", "hotel",
})

_MIN_BUILDING_WIDTH = 7.0   # metres
_MAX_BUILDING_WIDTH = 22.0  # metres
_CORRIDOR_DEPTH = 1.5       # metres — corridor/hallway row height

# Wider bounds for an explicit user-supplied plot width (DesignParams), since a
# real plot can legitimately be narrower or wider than what the program-area
# heuristic would infer.
_PLOT_WIDTH_MIN = 4.0   # metres
_PLOT_WIDTH_MAX = 40.0  # metres

# Residential layouts insert an implicit privacy corridor between the public
# (front) and private (back) rows so bedrooms are buffered from living areas.
# Commercial layouts skip it: reception should flow straight into the work area
# (e.g. reception→workspace, waiting→consultation share a wall, no dead hallway).
# Clinics are included too: a clinic has a real circulation corridor off which
# consultation rooms open, keeping them buffered from the public entry.
_IMPLICIT_CORRIDOR_BUILDING_TYPES: frozenset[str] = frozenset({
    "apartment", "studio", "house", "two_storey_home",
    "bungalow", "villa", "townhouse",
    "clinic",
})


# Adjacency constraints may reference room types that are placed as a different
# concrete room (an "ensuite" is realised as a bathroom).  Normalise so pair
# matching against actual room specs works.
_PAIR_TYPE_ALIASES: dict[str, str] = {"ensuite": "bathroom"}


def _normalise_pair_types(pair: frozenset) -> frozenset:
    return frozenset(_PAIR_TYPE_ALIASES.get(t, t) for t in pair)


def _tiled_room_obj(
    spec: RoomSpec,
    x: float,
    z: float,
    w: float,
    d: float,
    *,
    floor_id: str,
    floor_level: int,
    elevation: float,
    rules: LayoutPatternRules,
) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "label": spec.label,
        "roomType": spec.room_type,
        "objectType": "room",
        "floorId": floor_id,
        "floorLevel": floor_level,
        "zone": rules.zone_for(spec.room_type),
        "position": {"x": round(x + w / 2, 2), "y": round(elevation + spec.h / 2, 2), "z": round(z + d / 2, 2)},
        "size": {"w": round(w, 2), "h": spec.h, "d": round(d, 2)},
        "color": ROOM_COLORS.get(spec.room_type, "#94a3b8"),
    }


def _fill_row(
    specs: list[RoomSpec],
    row_z: float,
    row_depth: float,
    building_width: float,
    *,
    floor_id: str,
    floor_level: int,
    elevation: float,
    rules: LayoutPatternRules,
) -> list[dict]:
    """
    Partition `building_width` among the row's rooms so they share walls and fill
    it exactly.  Width is allocated proportional to each room's TARGET AREA (not
    its pre-sized width): since the row depth is uniform, area-proportional widths
    keep each room's final area close to its intended size — a large room (e.g. an
    open workspace) gets a correspondingly wide column instead of being squeezed.

    A minimum width (and aspect floor relative to the row depth) is guaranteed; any
    width borrowed to honour it is taken from the widest room so the row still fills
    exactly without producing wafer-thin strips.
    """
    if not specs:
        return []
    n = len(specs)
    areas = [max(s.w * s.d, 0.1) for s in specs]
    total_area = sum(areas)
    if total_area <= 0:
        return []

    widths = [area / total_area * building_width for area in areas]

    # Minimum usable width: never thinner than 1.5m, and not a thin strip against
    # the row depth, but never more than an equal share (so it stays solvable).
    min_w = min(max(1.5, 0.6 * row_depth), building_width / n)
    for i in range(n):
        if widths[i] < min_w:
            deficit = min_w - widths[i]
            widths[i] = min_w
            donor = max(range(n), key=lambda k: widths[k])
            if donor != i:
                widths[donor] = max(min_w, widths[donor] - deficit)
    # Renormalise so the row fills building_width exactly after clamping.
    scale = building_width / sum(widths)
    widths = [w * scale for w in widths]

    result = []
    current_x = 0.0
    for i, (spec, w) in enumerate(zip(specs, widths)):
        # Last room absorbs any residual rounding so the row ends flush.
        if i == n - 1:
            w = building_width - current_x
        result.append(
            _tiled_room_obj(
                spec, current_x, row_z, w, row_depth,
                floor_id=floor_id, floor_level=floor_level, elevation=elevation, rules=rules,
            )
        )
        current_x += w
    return result


_STAIR_STRIP_W = _STAIRS_SIZE["w"] + 0.2  # metres reserved at building right edge for stairs


def _tile_rooms(
    specs: list[RoomSpec],
    rules: LayoutPatternRules,
    building_type: str,
    floor_id: str,
    floor_level: int,
    elevation: float,
    target_width: float | None = None,
    stair_reserve: float = 0.0,
    must_pairs: set[frozenset] | None = None,
    should_pairs: set[frozenset] | None = None,
) -> tuple[list[dict], dict]:
    """
    Tile rooms into a pre-defined rectangular footprint.
    Rooms share walls (zero gap between them), grouped into front/corridor/back
    zone rows that together fill the building rectangle.

    stair_reserve: width (m) reserved on the right edge for stairs.  Rooms fill
    building_width - stair_reserve; the footprint still covers the full width.

    must_pairs / should_pairs: room-type adjacency constraints from the parser.
    Linked rooms are ordered to share a wall within their zone row (Sprint 16).

    Returns (placed_rooms, footprint_dict).
    """
    must_pairs = must_pairs or set()
    # SHOULD links also drive interleaving; normalise "ensuite" → "bathroom"
    # since the placed service room is a bathroom, not a distinct ensuite room.
    should_pairs = {_normalise_pair_types(pair) for pair in (should_pairs or set())}
    must_pairs = {_normalise_pair_types(pair) for pair in must_pairs}

    # Classify into zone groups
    front: list[RoomSpec] = []
    corridor: list[RoomSpec] = []
    private: list[RoomSpec] = []
    service: list[RoomSpec] = []
    other: list[RoomSpec] = []

    for spec in specs:
        rt = spec.room_type
        if rt in _TILED_FRONT_TYPES:
            front.append(spec)
        elif rt in _TILED_CORRIDOR_TYPES:
            corridor.append(spec)
        elif rt in _TILED_PRIVATE_TYPES:
            private.append(spec)
        elif rt in _TILED_SERVICE_TYPES:
            service.append(spec)
        else:
            other.append(spec)

    # If no front rooms, put all rooms in one row
    if not front and not private:
        front = list(specs)
        private = []
        service = []
        corridor = []

    # Order each zone row by building flow priority, then pull adjacency-linked
    # pairs together so constrained rooms share a wall.
    front = _order_zone_rooms(front, building_type, must_pairs, should_pairs)
    private = _order_zone_rooms(private, building_type, must_pairs, should_pairs)
    other = _order_zone_rooms(other, building_type, must_pairs, should_pairs)

    # Compute building width from total area if not provided
    total_area = sum(s.w * s.d for s in specs)
    if not total_area:
        return [], {"x": 0.0, "z": 0.0, "w": 0.0, "d": 0.0}

    if target_width is not None:
        building_width = target_width
    else:
        aspect = 1.6  # width:depth target ratio
        building_width = round(sqrt(total_area * aspect), 1)
        building_width = max(_MIN_BUILDING_WIDTH, min(building_width, _MAX_BUILDING_WIDTH))

    # Rooms fill fill_width; stair_reserve carves a right-edge strip for stairs
    fill_width = max(building_width - stair_reserve, 5.0)

    # Compute zone row depths from weighted average room depth, constrained to
    # realistic min/max (a row must be deep enough to be usable)
    def zone_depth(zone_specs: list[RoomSpec], min_d: float = 2.5, max_d: float = 7.0) -> float:
        if not zone_specs:
            return 0.0
        avg = sum(s.d for s in zone_specs) / len(zone_specs)
        return round(max(min_d, min(avg, max_d)), 2)

    front_depth = zone_depth(front, min_d=3.0, max_d=6.5) if front else 0.0
    private_depth = zone_depth(private + service, min_d=2.5, max_d=6.5) if private or service else 0.0
    has_implicit_corridor = (
        building_type in _IMPLICIT_CORRIDOR_BUILDING_TYPES
        and bool(front)
        and bool(private)
        and not corridor
    )
    corridor_depth = _CORRIDOR_DEPTH if has_implicit_corridor else (zone_depth(corridor, 1.2, 2.0) if corridor else 0.0)
    other_depth = zone_depth(other) if other else 0.0

    # Interleave service rooms with private rooms so bathrooms sit beside
    # bedrooms.  A service room that is adjacency-linked to a private room
    # (e.g. an ensuite bathroom constrained to a master bedroom) is attached
    # directly after that private room; the rest fall back to a positional rule.
    linked_pairs = must_pairs | should_pairs

    def interleave_service(priv: list[RoomSpec], svc: list[RoomSpec]) -> list[RoomSpec]:
        if not svc:
            return priv
        svc_remaining = list(svc)
        merged: list[RoomSpec] = []
        for i, room in enumerate(priv):
            merged.append(room)
            linked_idx = next(
                (
                    j
                    for j, s in enumerate(svc_remaining)
                    if frozenset({room.room_type, s.room_type}) in linked_pairs
                ),
                None,
            )
            if linked_idx is not None:
                merged.append(svc_remaining.pop(linked_idx))
            elif (i + 1) % 2 == 0 and svc_remaining:
                merged.append(svc_remaining.pop(0))
        merged.extend(svc_remaining)  # any remaining service rooms
        return merged

    back_row = interleave_service(private, service)

    # Build rows: front → corridor → back → other
    placed: list[dict] = []
    current_z = 0.0

    if front:
        placed.extend(_fill_row(front, current_z, front_depth, fill_width, floor_id=floor_id, floor_level=floor_level, elevation=elevation, rules=rules))
        current_z += front_depth

    if has_implicit_corridor or corridor:
        # Implicit corridor: render as a hallway-coloured strip
        hallway_spec = corridor[0] if corridor else RoomSpec("Hallway", "hallway", fill_width, 3.0, _CORRIDOR_DEPTH)
        placed.extend(_fill_row([hallway_spec], current_z, corridor_depth, fill_width, floor_id=floor_id, floor_level=floor_level, elevation=elevation, rules=rules))
        current_z += corridor_depth

    if back_row:
        placed.extend(_fill_row(back_row, current_z, private_depth, fill_width, floor_id=floor_id, floor_level=floor_level, elevation=elevation, rules=rules))
        current_z += private_depth

    if other:
        placed.extend(_fill_row(other, current_z, other_depth, fill_width, floor_id=floor_id, floor_level=floor_level, elevation=elevation, rules=rules))
        current_z += other_depth

    building_depth = current_z
    footprint = {"x": 0.0, "z": 0.0, "w": round(building_width, 2), "d": round(building_depth, 2)}
    return placed, footprint


def _chain_by_adjacency(
    rooms: list[RoomSpec],
    must_pairs: set[frozenset],
    should_pairs: set[frozenset],
) -> list[RoomSpec]:
    """
    Reorder rooms so adjacency-linked pairs are placed consecutively, preserving
    the incoming (flow-priority) order as the seed.  MUST links are pulled first,
    SHOULD links second, so the strongest constraints win the adjacent slot.
    """
    ordered: list[RoomSpec] = []
    remaining = list(rooms)
    while remaining:
        room = remaining.pop(0)
        ordered.append(room)
        partner_idx: int | None = None
        for pairs in (must_pairs, should_pairs):
            if not pairs:
                continue
            partner_idx = next(
                (
                    i
                    for i, other in enumerate(remaining)
                    if frozenset({room.room_type, other.room_type}) in pairs
                ),
                None,
            )
            if partner_idx is not None:
                break
        if partner_idx is not None:
            ordered.append(remaining.pop(partner_idx))
    return ordered


def _sort_by_adjacency(
    rooms: list[RoomSpec],
    must_pairs: set[frozenset],
) -> list[RoomSpec]:
    """Reorder rooms so MUST-adjacent pairs are placed consecutively."""
    return _chain_by_adjacency(rooms, must_pairs, set())


def _order_zone_rooms(
    rooms: list[RoomSpec],
    building_type: str,
    must_pairs: set[frozenset],
    should_pairs: set[frozenset],
) -> list[RoomSpec]:
    """
    Order a single zone row: primary by building flow priority (so e.g. entry
    leads, large public rooms sit behind the entry), then pull adjacency-linked
    pairs together so constrained rooms share a wall.
    """
    if not rooms:
        return rooms
    ordered = sorted(rooms, key=lambda room: _flow_priority(building_type, room))
    if must_pairs or should_pairs:
        ordered = _chain_by_adjacency(ordered, must_pairs, should_pairs)
    return ordered


# Residential building types distribute rooms by privacy (public down, bedrooms
# up).  Everything else distributes "work" rooms evenly across all floors so no
# floor is left near-empty while sharing the building's full width.
_RESIDENTIAL_BUILDING_TYPES: frozenset[str] = frozenset({
    "apartment", "studio", "studio_apartment", "house", "family_home",
    "two_storey_home", "bungalow", "villa", "townhouse",
})

# Public-facing rooms that belong on the ground floor of a multi-storey commercial
# building (entrance sequence, retail front).
_GROUND_ANCHORED_TYPES: frozenset[str] = frozenset({
    "entry", "reception", "waiting_room", "foyer", "lobby",
    "retail_display", "checkout",
})


def _assign_commercial_floors(
    specs: list[RoomSpec],
    total_floors: int,
    floors: list[list[RoomSpec]],
    explicit_zones: dict[str, str],
) -> list[list[RoomSpec]]:
    """Distribute commercial rooms so every floor is filled: public rooms anchor
    to the ground floor, work rooms round-robin across all floors, and each
    occupied floor gets its own bathroom."""
    bathroom_template = next((room for room in specs if room.room_type == "bathroom"), None)
    next_floor = 0
    next_upper = 0
    upper_levels = list(range(1, total_floors))

    for room in specs:
        if room.room_type == "bathroom":
            continue  # placed per-floor at the end
        zone_pref = explicit_zones.get(room.room_type)
        if zone_pref == "ground" or room.room_type in _GROUND_ANCHORED_TYPES:
            floors[0].append(room)
            continue
        if zone_pref == "upper" and upper_levels:
            floors[upper_levels[next_upper % len(upper_levels)]].append(room)
            next_upper += 1
            continue
        # Round-robin over every floor (including ground) for even fill.
        floors[next_floor % total_floors].append(room)
        next_floor += 1

    if bathroom_template:
        for level in range(total_floors):
            if floors[level] and not any(r.room_type == "bathroom" for r in floors[level]):
                floors[level].append(
                    RoomSpec(
                        label="Bathroom",
                        room_type="bathroom",
                        w=bathroom_template.w,
                        h=bathroom_template.h,
                        d=bathroom_template.d,
                    )
                )
    return floors


def _assign_rooms_to_floors(
    specs: list[RoomSpec],
    total_floors: int,
    zone_assignments: dict[str, str] | None = None,
    building_type: str = "apartment",
) -> list[list[RoomSpec]]:
    floors: list[list[RoomSpec]] = [[] for _ in range(total_floors)]
    if total_floors <= 1:
        floors[0].extend(specs)
        return floors

    explicit_zones = zone_assignments or {}
    if building_type not in _RESIDENTIAL_BUILDING_TYPES:
        return _assign_commercial_floors(specs, total_floors, floors, explicit_zones)

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

    # Every floor with bedrooms should also have its own bathroom
    bathroom_template = next((room for room in specs if room.room_type == "bathroom"), None)
    if bathroom_template:
        for level in upper_levels:
            has_bedroom = any(room.room_type in {"bedroom", "master_bedroom"} for room in floors[level])
            has_bathroom = any(room.room_type == "bathroom" for room in floors[level])
            if has_bedroom and not has_bathroom:
                floors[level].append(
                    RoomSpec(
                        label="Bathroom",
                        room_type="bathroom",
                        w=bathroom_template.w,
                        h=bathroom_template.h,
                        d=bathroom_template.d,
                    )
                )

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
    should_adjacency_pairs: set[frozenset] | None = None,
    plot_width_m: float | None = None,
    orientation: str | None = None,
) -> dict:
    use_tiler = building_type in _TILED_BUILDING_TYPES
    floor_specs = _assign_rooms_to_floors(room_specs, total_floors, zone_assignments, building_type)

    # For tiled layouts pre-compute a shared target width from the widest floor
    # so all storeys have the same footprint width. An explicit plot_width_m
    # (from DesignParams) overrides the program-area heuristic.
    tiled_target_width: float | None = None
    tiled_stair_reserve = _STAIR_STRIP_W if (use_tiler and total_floors > 1) else 0.0
    if use_tiler:
        if plot_width_m is not None:
            tiled_target_width = max(_PLOT_WIDTH_MIN, min(round(plot_width_m, 1), _PLOT_WIDTH_MAX))
        else:
            per_floor_areas = [sum(s.w * s.d for s in specs) for specs in floor_specs if specs]
            if per_floor_areas:
                max_area = max(per_floor_areas)
                computed = round(sqrt(max_area * 1.6), 1)
                tiled_target_width = max(_MIN_BUILDING_WIDTH, min(computed, _MAX_BUILDING_WIDTH))

    max_row_width = _max_row_width_for_layout(room_specs, total_floors, building_type)
    pending_floors: list[dict] = []
    floor_footprints: list[dict] = []
    floors: list[dict] = []
    flat_rooms: list[dict] = []

    for level, specs in enumerate(floor_specs):
        floor_id = f"floor_{level}"
        elevation = round(level * _FLOOR_HEIGHT, 2)

        if use_tiler:
            rooms, tiled_footprint = _tile_rooms(
                specs,
                pattern_rules,
                building_type,
                floor_id,
                level,
                elevation,
                target_width=tiled_target_width,
                stair_reserve=tiled_stair_reserve,
                must_pairs=must_adjacency_pairs,
                should_pairs=should_adjacency_pairs,
            )
        else:
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
            if use_tiler and tiled_target_width is not None:
                stair_x = round(tiled_target_width - _STAIR_STRIP_W / 2, 2)
                rooms.insert(0, _add_stairs(floor_id, level, elevation, x_pos=stair_x))
            else:
                rooms.insert(0, _add_stairs(floor_id, level, elevation, x_offset=x_offset))

        footprint = (
            {"x": 0.0, "z": 0.0, "w": tiled_footprint["w"], "d": tiled_footprint["d"]}
            if use_tiler and rooms
            else _footprint_for_rooms(rooms)
        )
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
                orientation=orientation,
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
    plot_width_m: float | None = None,
    orientation: str | None = None,
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
    should_pairs: set[frozenset] = {
        frozenset({c.room_a, c.room_b})
        for c in (adjacency_constraints or [])
        if c.strength == "SHOULD"
    }

    base_offset = _STAIRS_SIZE["w"] + _GAP if total_floors > 1 else 0.0
    # Tiled building types produce a single deterministic layout; row-based types
    # try three x-offset variants and pick the highest-scoring one.
    offsets = (0.0,) if building_type in _TILED_BUILDING_TYPES else (0.0, 0.5, 1.0)
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
            should_adjacency_pairs=should_pairs or None,
            plot_width_m=plot_width_m,
            orientation=orientation,
        )
        for offset in offsets
    ]
    best = max(candidates, key=lambda candidate: candidate["insights"]["score"])
    best["metadata"]["candidateCount"] = len(candidates)

    design_params_echo: dict = {}
    if plot_width_m is not None:
        design_params_echo["plotWidthM"] = plot_width_m
    if orientation is not None:
        design_params_echo["orientation"] = orientation.upper()
    if design_params_echo:
        best["metadata"]["designParams"] = design_params_echo

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
