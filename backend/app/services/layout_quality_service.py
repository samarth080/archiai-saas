from dataclasses import asdict, dataclass

from app.services.layout_pattern_service import LayoutPatternRules, fallback_layout_rules


@dataclass(frozen=True)
class LayoutQualityScore:
    score: int
    reasons: list[str]
    warnings: list[str]
    suggestions: list[str]
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


def _label_room_type(room_type: str) -> str:
    return room_type.replace("_", " ").title()


def _overlap_in_xz(a: dict, b: dict) -> bool:
    if a.get("floorLevel") != b.get("floorLevel"):
        return False
    ax1 = a["position"]["x"] - a["size"]["w"] / 2
    ax2 = a["position"]["x"] + a["size"]["w"] / 2
    az1 = a["position"]["z"] - a["size"]["d"] / 2
    az2 = a["position"]["z"] + a["size"]["d"] / 2
    bx1 = b["position"]["x"] - b["size"]["w"] / 2
    bx2 = b["position"]["x"] + b["size"]["w"] / 2
    bz1 = b["position"]["z"] - b["size"]["d"] / 2
    bz2 = b["position"]["z"] + b["size"]["d"] / 2
    return ax1 < bx2 and ax2 > bx1 and az1 < bz2 and az2 > bz1


def _outside_footprint(room: dict, footprint: dict) -> bool:
    if not footprint:
        return False
    min_x = footprint["x"]
    max_x = footprint["x"] + footprint["w"]
    min_z = footprint["z"]
    max_z = footprint["z"] + footprint["d"]
    return (
        room["position"]["x"] - room["size"]["w"] / 2 < min_x
        or room["position"]["x"] + room["size"]["w"] / 2 > max_x
        or room["position"]["z"] - room["size"]["d"] / 2 < min_z
        or room["position"]["z"] + room["size"]["d"] / 2 > max_z
    )


def score_layout_quality(
    layout: dict,
    *,
    required_room_types: set[str] | None = None,
    pattern_rules: LayoutPatternRules | None = None,
) -> LayoutQualityScore:
    rooms = layout.get("rooms", [])
    metadata = layout.get("metadata", {})
    building_type = metadata.get("buildingType") or metadata.get("building_type") or "apartment"
    architectural_rooms = [room for room in rooms if room.get("objectType") == "room"]
    overlap_checked_rooms = [
        room
        for room in rooms
        if room.get("objectType") in {"room", "stair"}
    ]
    room_types = {room.get("roomType", "unknown") for room in architectural_rooms}
    rules = pattern_rules or fallback_layout_rules(building_type, room_types)
    required_room_types = required_room_types or room_types
    rooms_by_type = _rooms_by_type(architectural_rooms)
    score = 100
    reasons: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []
    applied_rules = [
        f"template:{metadata.get('template', building_type)}",
        f"zones:{','.join(metadata.get('zonesDetected', []))}",
    ]
    applied_rules.extend(f"pattern:{pattern}" for pattern in rules.layout_patterns)
    if rules.pattern_data_used:
        applied_rules.append(f"pattern-data:{rules.pattern_data_source}")
    else:
        applied_rules.append("pattern-data:fallback-defaults")

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

    floor_levels = {floor.get("level") for floor in layout.get("floors", [])}
    invalid_floor_rooms = [
        room.get("label", room.get("roomType", "unknown"))
        for room in rooms
        if floor_levels and room.get("floorLevel") not in floor_levels
    ]
    if invalid_floor_rooms:
        score -= min(20, len(invalid_floor_rooms) * 5)
        warnings.append(f"Rooms assigned to invalid floors: {', '.join(invalid_floor_rooms)}")
        suggestions.append("Move invalid rooms back onto one of the generated floors")
    else:
        reasons.append("Room floor assignments are valid")

    overlap_issues: list[str] = []
    for index, room in enumerate(overlap_checked_rooms):
        for other in overlap_checked_rooms[index + 1:]:
            if _overlap_in_xz(room, other):
                room_label = room.get("label", room.get("roomType"))
                other_label = other.get("label", other.get("roomType"))
                overlap_issues.append(f"{room_label} overlaps {other_label}")
    if overlap_issues:
        score -= min(25, len(overlap_issues) * 8)
        warnings.append(f"Room overlaps detected: {', '.join(overlap_issues)}")
        suggestions.append("Move overlapping rooms apart before saving or exporting")
    else:
        reasons.append("Rooms do not overlap within each floor")

    footprints = {
        floor.get("level"): floor.get("footprint", {})
        for floor in layout.get("floors", [])
    }
    overflow_rooms = [
        room.get("label", room.get("roomType", "unknown"))
        for room in rooms
        if room.get("floorLevel") in footprints and _outside_footprint(room, footprints[room.get("floorLevel")])
    ]
    if overflow_rooms:
        score -= min(20, len(overflow_rooms) * 5)
        warnings.append(f"Rooms outside floor footprint: {', '.join(overflow_rooms)}")
        suggestions.append("Keep rooms inside the visible floor plate")
    elif footprints:
        reasons.append("Rooms stay inside floor footprints")

    missing_rooms = sorted(required_room_types - room_types)
    if missing_rooms:
        score -= min(30, len(missing_rooms) * 8)
        readable_missing = ", ".join(_label_room_type(room_type) for room_type in missing_rooms)
        warnings.append(f"Missing required rooms: {readable_missing}")
        suggestions.append(f"Add the missing required rooms: {readable_missing}")
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
        suggestions.append("Resize flagged rooms toward their typical area ranges")
    else:
        reasons.append("Room sizes are within expected ranges")

    if zone_issues:
        score -= min(15, len(zone_issues) * 2)
        warnings.append(f"Rooms outside expected zones: {', '.join(zone_issues)}")
        suggestions.append("Move flagged rooms back into their public, private, service, or circulation zones")
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
                adjacency_issues.add(f"{_label_room_type(room_type)} near {_label_room_type(target_type)}")
        for target_type in rule.avoid_adjacent_to:
            pair = tuple(sorted((room_type, target_type)))
            if target_type not in rooms_by_type:
                continue
            if any(_edge_gap(a, b) <= 1.0 for a in rooms_by_type[room_type] for b in rooms_by_type[target_type]):
                avoid_issues.add(f"{_label_room_type(room_type)} next to {_label_room_type(target_type)}")

    if adjacency_issues:
        score -= min(15, len(adjacency_issues) * 2)
        warnings.append(f"Preferred adjacency not met: {', '.join(sorted(adjacency_issues))}")
        suggestions.append("Move preferred room pairs closer together")
    else:
        reasons.append("Preferred adjacency rules are satisfied where applicable")

    if avoid_issues:
        score -= min(20, len(avoid_issues) * 5)
        warnings.append(f"Avoid-adjacency violations: {', '.join(sorted(avoid_issues))}")
        suggestions.append("Separate rooms that should not sit directly beside each other")
    else:
        reasons.append("No avoid-adjacency violations detected")

    total_floors = metadata.get("totalFloors", 1)
    stairs_by_floor = {
        room.get("floorLevel")
        for room in rooms
        if room.get("roomType") == "stairs"
    }
    if total_floors > 1 and len(stairs_by_floor) != total_floors:
        score -= 10
        warnings.append("Multi-floor layout is missing consistent stair placeholders")
        suggestions.append("Add one aligned stair object to every generated floor")
    elif total_floors > 1:
        reasons.append("Multi-floor stair placeholders are present")

    if metadata.get("template"):
        reasons.append(f"Building template '{metadata['template']}' is applied")
    else:
        score -= 5
        warnings.append("Building template metadata is missing")
        suggestions.append("Regenerate the layout so a building template can be applied")

    return LayoutQualityScore(
        score=max(0, min(100, score)),
        reasons=reasons,
        warnings=warnings,
        suggestions=suggestions,
        applied_rules=applied_rules,
    )
