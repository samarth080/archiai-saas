from dataclasses import asdict, dataclass

from app.services.layout_pattern_service import LayoutPatternRules, fallback_layout_rules


@dataclass(frozen=True)
class LayoutQualityScore:
    score: int
    reasons: list[str]
    warnings: list[str]
    applied_rules: list[str]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["appliedRules"] = data.pop("applied_rules")
        return data


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


def _rooms_by_type(rooms: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for room in rooms:
        grouped.setdefault(room.get("roomType", "unknown"), []).append(room)
    return grouped


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


def _near_any(source_rooms: list[dict], target_rooms: list[dict], max_gap: float = 1.0) -> bool:
    return any(_edge_gap(source, target) <= max_gap for source in source_rooms for target in target_rooms)


def score_layout_quality(
    layout: dict,
    *,
    required_room_types: set[str] | None = None,
    pattern_rules: LayoutPatternRules | None = None,
) -> LayoutQualityScore:
    rooms = layout.get("rooms", [])
    metadata = layout.get("metadata", {})
    building_type = metadata.get("buildingType") or metadata.get("building_type") or "apartment"
    architectural_rooms = [room for room in rooms if room.get("roomType") != "stairs"]
    room_types = {room.get("roomType", "unknown") for room in architectural_rooms}
    rules = pattern_rules or fallback_layout_rules(building_type, room_types)
    required_room_types = required_room_types or room_types
    rooms_by_type = _rooms_by_type(architectural_rooms)
    score = 100
    reasons: list[str] = []
    warnings: list[str] = []
    applied_rules = [
        f"template:{metadata.get('template', building_type)}",
        f"zones:{','.join(metadata.get('zonesDetected', []))}",
    ]
    applied_rules.extend(f"pattern:{pattern}" for pattern in rules.layout_patterns)
    if rules.pattern_data_used:
        applied_rules.append(f"pattern-data:{rules.pattern_data_source}")
    else:
        applied_rules.append("pattern-data:fallback-defaults")

    overlap_pairs: list[str] = []
    for index, room in enumerate(architectural_rooms):
        for other in architectural_rooms[index + 1:]:
            if _rooms_overlap(room, other):
                overlap_pairs.append(f"{room.get('label', room.get('roomType'))} / {other.get('label', other.get('roomType'))}")
    if overlap_pairs:
        score -= min(30, len(overlap_pairs) * 10)
        warnings.append(f"Overlapping rooms detected: {', '.join(overlap_pairs)}")
    else:
        reasons.append("Rooms do not overlap")

    bounds = layout.get("building", {}).get("bounds")
    if bounds:
        outside = []
        for room in architectural_rooms:
            min_x, max_x, min_z, max_z = _room_bounds(room)
            if min_x < bounds["minX"] or max_x > bounds["maxX"] or min_z < bounds["minZ"] or max_z > bounds["maxZ"]:
                outside.append(room.get("label", room.get("roomType", "room")))
        if outside:
            score -= min(20, len(outside) * 5)
            warnings.append(f"Rooms outside building bounds: {', '.join(outside)}")
        else:
            reasons.append("Rooms stay inside computed building bounds")

    schema_valid = (
        layout.get("version") == "1.0"
        and isinstance(layout.get("floors"), list)
        and isinstance(rooms, list)
        and all("position" in room and "size" in room and "floorLevel" in room for room in rooms)
    )
    if schema_valid:
        reasons.append("Layout schema is valid and backward-compatible")
    else:
        score -= 20
        warnings.append("Layout schema is incomplete")

    missing_rooms = sorted(required_room_types - room_types)
    if missing_rooms:
        score -= min(30, len(missing_rooms) * 8)
        warnings.append(f"Missing required rooms: {', '.join(missing_rooms)}")
    else:
        reasons.append("Required rooms are present")

    size_issues: list[str] = []
    zone_issues: list[str] = []
    for room in architectural_rooms:
        room_type = room.get("roomType", "unknown")
        rule = rules.rule_for(room_type)
        area = room["size"]["w"] * room["size"]["d"]
        if not rule.typical_area_sqm_min <= area <= rule.typical_area_sqm_max:
            size_issues.append(room.get("label", room_type))
        if room.get("zone") != rule.zone:
            zone_issues.append(room.get("label", room_type))

    if size_issues:
        score -= min(20, len(size_issues) * 3)
        warnings.append(f"Rooms outside expected size ranges: {', '.join(size_issues)}")
    else:
        reasons.append("Room sizes are within expected ranges")

    if zone_issues:
        score -= min(15, len(zone_issues) * 2)
        warnings.append(f"Rooms outside expected zones: {', '.join(zone_issues)}")
    else:
        reasons.append("Room zones match resolved rules")

    adjacency_issues: set[str] = set()
    avoid_issues: set[str] = set()
    checked_pairs: set[tuple[str, str]] = set()
    for room_type in room_types:
        rule = rules.rule_for(room_type)
        for target_type in rule.adjacent_to:
            pair = tuple(sorted((room_type, target_type)))
            if target_type not in rooms_by_type or pair in checked_pairs:
                continue
            checked_pairs.add(pair)
            if not any(_edge_gap(a, b) <= 1.0 for a in rooms_by_type[room_type] for b in rooms_by_type[target_type]):
                adjacency_issues.add(f"{room_type} near {target_type}")
        for target_type in rule.avoid_adjacent_to:
            pair = tuple(sorted((room_type, target_type)))
            if target_type not in rooms_by_type:
                continue
            if any(_edge_gap(a, b) <= 1.0 for a in rooms_by_type[room_type] for b in rooms_by_type[target_type]):
                avoid_issues.add(f"{room_type} next to {target_type}")

    if adjacency_issues:
        score -= min(15, len(adjacency_issues) * 2)
        warnings.append(f"Preferred adjacency not met: {', '.join(sorted(adjacency_issues))}")
    else:
        reasons.append("Preferred adjacency rules are satisfied where applicable")

    if avoid_issues:
        score -= min(20, len(avoid_issues) * 5)
        warnings.append(f"Avoid-adjacency violations: {', '.join(sorted(avoid_issues))}")
    else:
        reasons.append("No avoid-adjacency violations detected")

    entries = rooms_by_type.get("entry", [])
    private_entry_violations = []
    for private_type in ("bedroom", "master_bedroom", "consultation_room", "office", "storage", "utility"):
        if entries and private_type in rooms_by_type and _near_any(entries, rooms_by_type[private_type]):
            private_entry_violations.append(private_type)
    if private_entry_violations:
        score -= min(25, len(private_entry_violations) * 8)
        warnings.append(f"Private/service rooms too close to entry: {', '.join(private_entry_violations)}")
    elif entries:
        reasons.append("Private and service rooms are buffered from the entry")

    if building_type == "clinic":
        clinic_flow_issues = []
        if entries and rooms_by_type.get("reception") and not _near_any(entries, rooms_by_type["reception"]):
            clinic_flow_issues.append("entry near reception")
        if rooms_by_type.get("reception") and rooms_by_type.get("waiting_room") and not _near_any(rooms_by_type["reception"], rooms_by_type["waiting_room"]):
            clinic_flow_issues.append("reception near waiting")
        if rooms_by_type.get("waiting_room") and rooms_by_type.get("consultation_room") and not _near_any(rooms_by_type["waiting_room"], rooms_by_type["consultation_room"]):
            clinic_flow_issues.append("waiting near consultation")
        bathroom_access = (
            rooms_by_type.get("bathroom")
            and (
                _near_any(rooms_by_type.get("waiting_room", []), rooms_by_type["bathroom"], max_gap=2.0)
                or _near_any(rooms_by_type.get("hallway", []), rooms_by_type["bathroom"], max_gap=2.0)
            )
        )
        if rooms_by_type.get("bathroom") and not bathroom_access:
            clinic_flow_issues.append("bathroom accessible from waiting/circulation")
        if clinic_flow_issues:
            score -= min(25, len(clinic_flow_issues) * 6)
            warnings.append(f"Clinic flow issues: {', '.join(clinic_flow_issues)}")
        else:
            reasons.append("Clinic public-to-private flow is clear")

    if building_type == "restaurant" and entries and rooms_by_type.get("kitchen"):
        if _near_any(entries, rooms_by_type["kitchen"], max_gap=1.0):
            score -= 15
            warnings.append("Restaurant kitchen is too close to the public entry")
        else:
            reasons.append("Restaurant kitchen is buffered from the public entry")

    total_floors = metadata.get("totalFloors", 1)
    stairs_by_floor = {
        room.get("floorLevel")
        for room in rooms
        if room.get("roomType") == "stairs"
    }
    if total_floors > 1 and len(stairs_by_floor) != total_floors:
        score -= 10
        warnings.append("Multi-floor layout is missing consistent stair placeholders")
    elif total_floors > 1:
        reasons.append("Multi-floor stair placeholders are present")

    if metadata.get("template"):
        reasons.append(f"Building template '{metadata['template']}' is applied")
    else:
        score -= 5
        warnings.append("Building template metadata is missing")

    return LayoutQualityScore(
        score=max(0, min(100, score)),
        reasons=reasons,
        warnings=warnings,
        applied_rules=applied_rules,
    )
