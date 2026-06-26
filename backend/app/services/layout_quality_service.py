from dataclasses import asdict, dataclass

from app.services.layout_pattern_service import LayoutPatternRules, fallback_layout_rules

# Minimum room sets expected per building type — absence of these rooms is penalised
_BUILDING_EXPECTED_ROOMS: dict[str, set[str]] = {
    "apartment":       {"living_room", "kitchen", "bathroom", "dining_room"},
    "studio":          {"kitchen", "bathroom"},
    "house":           {"living_room", "kitchen", "bathroom", "bedroom", "dining_room"},
    "two_storey_home": {"living_room", "kitchen", "bathroom", "bedroom", "dining_room"},
    "office":          {"workspace", "bathroom"},
    "clinic":          {"reception", "waiting_room", "bathroom"},
    "restaurant":      {"dining_room", "kitchen", "bathroom"},
    "retail":          {"retail_display", "checkout"},
    "school":          {"classroom", "bathroom"},
}


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
    _eps = 0.02
    return ax1 + _eps < bx2 and ax2 - _eps > bx1 and az1 + _eps < bz2 and az2 - _eps > bz1


def _outside_footprint(room: dict, footprint: dict) -> bool:
    if not footprint:
        return False
    _fp_eps = 0.02
    min_x = footprint["x"] - _fp_eps
    max_x = footprint["x"] + footprint["w"] + _fp_eps
    min_z = footprint["z"] - _fp_eps
    max_z = footprint["z"] + footprint["d"] + _fp_eps
    return (
        room["position"]["x"] - room["size"]["w"] / 2 < min_x
        or room["position"]["x"] + room["size"]["w"] / 2 > max_x
        or room["position"]["z"] - room["size"]["d"] / 2 < min_z
        or room["position"]["z"] + room["size"]["d"] / 2 > max_z
    )


def _near_any(source_rooms: list[dict], target_rooms: list[dict], max_gap: float = 1.0) -> bool:
    return any(_edge_gap(source, target) <= max_gap for source in source_rooms for target in target_rooms)


def _floor_unreachable_rooms(rooms: list[dict]) -> list[str]:
    """
    Real circulation check (Sprint 17 Phase 2): for each floor, verify every
    architectural room is reachable from that floor's entry point by walking
    interior doors — not just visually divided by walls, but actually
    walkable. The entry point is the room typed 'entry' on the ground floor,
    or the room nearest the stairs on upper floors, falling back to the first
    room if neither exists. Returns the labels of any room left unreachable.
    """
    architectural = [r for r in rooms if r.get("objectType") == "room"]
    doors = [r for r in rooms if r.get("objectType") == "door" and r.get("label") != "Entry Door"]
    stairs = [r for r in rooms if r.get("objectType") == "stair"]
    levels = sorted({r.get("floorLevel") for r in architectural})

    unreachable: list[str] = []
    for level in levels:
        floor_rooms = [r for r in architectural if r.get("floorLevel") == level]
        if len(floor_rooms) <= 1:
            continue

        bounds = [_room_bounds(r) for r in floor_rooms]
        graph: dict[int, set[int]] = {i: set() for i in range(len(floor_rooms))}
        for door in doors:
            if door.get("floorLevel") != level:
                continue
            dx, dz = door["position"]["x"], door["position"]["z"]
            touching = [
                i for i, (x1, x2, z1, z2) in enumerate(bounds)
                if x1 - 0.3 <= dx <= x2 + 0.3 and z1 - 0.3 <= dz <= z2 + 0.3
            ]
            for i in touching:
                for j in touching:
                    if i != j:
                        graph[i].add(j)

        start = next((i for i, r in enumerate(floor_rooms) if r.get("roomType") == "entry"), None)
        if start is None:
            floor_stairs = [s for s in stairs if s.get("floorLevel") == level]
            if floor_stairs:
                start = min(
                    range(len(floor_rooms)),
                    key=lambda i: min(_edge_gap(floor_rooms[i], stair) for stair in floor_stairs),
                )
            else:
                start = 0

        seen = {start}
        queue = [start]
        while queue:
            current = queue.pop()
            for neighbour in graph[current]:
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)

        unreachable.extend(
            room.get("label", room.get("roomType", "room"))
            for i, room in enumerate(floor_rooms)
            if i not in seen
        )
    return unreachable


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
            if _rooms_overlap(room, other):
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
        for room in overlap_checked_rooms
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
    avoid_checked_pairs: set[tuple[str, str]] = set()
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
            if target_type not in rooms_by_type or pair in avoid_checked_pairs:
                continue
            if any(_edge_gap(a, b) <= 1.0 for a in rooms_by_type[room_type] for b in rooms_by_type[target_type]):
                avoid_checked_pairs.add(pair)
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

    unreachable_rooms = _floor_unreachable_rooms(rooms)
    if unreachable_rooms:
        score -= min(20, len(unreachable_rooms) * 8)
        warnings.append(f"Rooms not reachable via interior doors: {', '.join(unreachable_rooms)}")
        suggestions.append("Add a door connecting the unreachable room to the rest of the floor")
    elif architectural_rooms:
        reasons.append("Every room is reachable from the entry via interior doors")

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

    # Building-type completeness: penalise missing rooms expected for this building category
    expected = _BUILDING_EXPECTED_ROOMS.get(building_type, set())
    missing_expected = sorted(expected - room_types)
    if missing_expected:
        penalty = min(25, len(missing_expected) * 8)
        score -= penalty
        readable = ", ".join(_label_room_type(rt) for rt in missing_expected)
        warnings.append(f"Layout missing expected {building_type} rooms: {readable}")
        suggestions.append(f"Add {readable} to complete a typical {building_type} layout")
    elif expected:
        reasons.append(f"All expected {building_type} rooms are present")

    # Adjacency density: penalise when there are very few satisfied adjacency rules
    # This prevents layouts with only 1-2 rooms from scoring perfectly on adjacency
    total_adjacency_pairs = len(checked_pairs)
    unsatisfied = len(adjacency_issues)
    if total_adjacency_pairs > 0:
        satisfaction_rate = (total_adjacency_pairs - unsatisfied) / total_adjacency_pairs
        if satisfaction_rate < 0.5 and total_adjacency_pairs >= 3:
            score -= 5
            warnings.append(
                f"Low adjacency satisfaction: {int(satisfaction_rate * 100)}% of preferred pairs met"
            )

    return LayoutQualityScore(
        score=max(0, min(100, score)),
        reasons=reasons,
        warnings=warnings,
        suggestions=suggestions,
        applied_rules=applied_rules,
    )
