"""Serializable building-program contract and final-layout validation.

This module is the boundary between prompt understanding, deterministic
geometry, persistence, and editor presentation. It converts ParsedRequirements
plus ProgramGraph into stable JSON metadata and compares that requested program
with the final post-processed candidate.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING, Any

from app.services.parser.building_inference import extract_bhk
from app.services.parser.data.room_vocabulary import ROOM_TERMS
from app.services.parser.data.synonyms import SYNONYMS
from app.services.parser.normaliser import normalise
from app.services.parser.room_extractor import ROOM_LOOKUP
from app.services.planning.graph_scoring import (
    GraphSatisfaction,
    score_graph_satisfaction,
)
from app.services.planning.program_graph import ProgramGraph

if TYPE_CHECKING:
    from app.services.prompt_service import ParsedRequirements

_OUTDOOR_TYPES = frozenset({"garden", "courtyard", "yard"})
_SEMI_OUTDOOR_TYPES = frozenset({"balcony", "terrace", "porch", "veranda"})
_EXTERIOR_REQUIRED_TYPES = frozenset({"balcony", "terrace", "porch", "veranda"})
_EDGE_TOLERANCE_M = 0.15


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _aliases_for(room_type: str) -> list[str]:
    aliases = {term.replace("_", " ") for term in ROOM_TERMS.get(room_type, ())}
    aliases.add(room_type.replace("_", " "))
    for source in SYNONYMS:
        canonical = normalise(source)
        resolved = ROOM_LOOKUP.get(canonical) or ROOM_LOOKUP.get(canonical.rstrip("s"))
        if resolved == room_type:
            aliases.add(source.replace("_", " "))
    aliases |= {
        f"{alias}s"
        for alias in list(aliases)
        if alias and not alias.endswith("s")
    }
    return sorted(aliases, key=lambda alias: (-len(alias), alias))


def _original_label(prompt: str, room_type: str) -> str:
    for alias in _aliases_for(room_type):
        match = re.search(rf"\b{re.escape(alias)}\b", prompt, flags=re.IGNORECASE)
        if match:
            return prompt[match.start():match.end()]
    return _humanize(room_type)


def _constraint_type(relation_type: str, strength: str) -> str:
    if strength == "AVOID":
        return "avoidAdjacent"
    if relation_type == "separated":
        return "mustBeSeparated"
    if relation_type == "connected_by_door":
        return "mustBeConnected" if strength == "MUST" else "shouldBeConnected"
    if relation_type == "near":
        return "near"
    if relation_type == "adjacent":
        return "mustBeAdjacent" if strength == "MUST" else "shouldBeAdjacent"
    return relation_type


def _indoor_outdoor_type(space_type: str) -> str:
    if space_type in _OUTDOOR_TYPES:
        return "outdoor"
    if space_type in _SEMI_OUTDOOR_TYPES:
        return "semi_outdoor"
    return "indoor"


def build_program_metadata(
    parsed: "ParsedRequirements",
    graph: ProgramGraph,
) -> dict[str, Any]:
    nodes_by_type: dict[str, list] = {}
    for node in graph.nodes:
        nodes_by_type.setdefault(node.space_type, []).append(node)

    requested_spaces: list[dict[str, Any]] = []
    seen_types: set[str] = set()
    for index, requirement in enumerate(parsed.rooms):
        if requirement.room_type in seen_types:
            continue
        seen_types.add(requirement.room_type)
        nodes = nodes_by_type.get(requirement.room_type, [])
        representative = nodes[0] if nodes else None
        requested_spaces.append(
            {
                "id": f"request-{index + 1}-{requirement.room_type}",
                "originalLabel": _original_label(
                    parsed.raw_prompt,
                    requirement.room_type,
                ),
                "normalizedType": requirement.room_type,
                "count": requirement.count,
                "category": representative.type if representative else "space",
                "zone": requirement.zone,
                "indoorOutdoorType": _indoor_outdoor_type(requirement.room_type),
                "minimumArea": (
                    representative.min_area_sqm if representative else None
                ),
                "preferredArea": requirement.area_m2,
                "maximumArea": (
                    representative.max_area_sqm if representative else None
                ),
                "minimumWidth": (
                    representative.min_width_m if representative else None
                ),
                "minimumDepth": (
                    representative.min_depth_m if representative else None
                ),
                "preferredAspectRatio": (
                    representative.preferred_aspect_ratio if representative else None
                ),
                "floorPreference": requirement.floor_preference,
                "daylightPriority": (
                    "high"
                    if requirement.room_type in parsed.daylight_rooms
                    else (representative.daylight_need if representative else "none")
                ),
                "privacyPriority": (
                    representative.privacy_level if representative else 0
                ),
                "exteriorEdgePreference": (
                    "required"
                    if requirement.room_type in _EXTERIOR_REQUIRED_TYPES
                    else (
                        "preferred"
                        if requirement.room_type in parsed.daylight_rooms
                        else "none"
                    )
                ),
                "source": requirement.source,
                "instanceIds": [node.id for node in nodes],
                "instanceLabels": [node.label for node in nodes],
            }
        )

    nodes_by_id = {node.id: node for node in graph.nodes}
    constraints: list[dict[str, Any]] = []
    for index, edge in enumerate(graph.edges):
        node_a = nodes_by_id.get(edge.node_a)
        node_b = nodes_by_id.get(edge.node_b)
        constraints.append(
            {
                "id": f"constraint-{index + 1}",
                "type": _constraint_type(edge.relation_type, edge.strength),
                "relationType": edge.relation_type,
                "strength": edge.strength,
                "nodeA": edge.node_a,
                "nodeB": edge.node_b,
                "spaceA": node_a.space_type if node_a else None,
                "spaceB": node_b.space_type if node_b else None,
                "labelA": node_a.label if node_a else edge.node_a,
                "labelB": node_b.label if node_b else edge.node_b,
                "reason": edge.reason,
            }
        )

    bhk = extract_bhk(normalise(parsed.raw_prompt))
    return {
        "version": 1,
        "buildingType": parsed.building_type,
        "programType": f"{bhk['bedroom']}BHK" if bhk else None,
        "floors": parsed.total_floors,
        "requestedSpaceCount": sum(space["count"] for space in requested_spaces),
        "requestedSpaces": requested_spaces,
        "constraints": constraints,
        "site": {
            "plotWidth": parsed.plot_width_m,
            "plotDepth": parsed.plot_depth_m,
            "plotArea": (
                round(parsed.plot_width_m * parsed.plot_depth_m, 2)
                if parsed.plot_width_m and parsed.plot_depth_m
                else None
            ),
            "facingDirection": parsed.facing_direction,
            "frontSide": parsed.facing_direction,
            "roadSide": parsed.road_side,
            "entrySide": parsed.entry_side,
            "daylightRoomTypes": list(parsed.daylight_rooms),
        },
    }


def _space_objects(layout: dict) -> list[dict]:
    objects: dict[str, dict] = {}

    def add(room: dict) -> None:
        if room.get("objectType") != "room":
            return
        key = str(room.get("id") or f"{room.get('label')}:{len(objects)}")
        objects.setdefault(key, room)

    for floor in layout.get("floors") or []:
        for room in floor.get("rooms") or []:
            add(room)
    for room in layout.get("rooms") or []:
        add(room)
    return list(objects.values())


def _footprints_by_level(layout: dict) -> dict[int, dict]:
    return {
        int(floor.get("level", 0)): floor["footprint"]
        for floor in layout.get("floors") or []
        if isinstance(floor.get("footprint"), dict)
    }


def _touches_exterior(room: dict, footprints: dict[int, dict]) -> bool:
    footprint = footprints.get(int(room.get("floorLevel", 0)))
    if not footprint:
        return False
    try:
        x = float(room["position"]["x"])
        z = float(room["position"]["z"])
        width = float(room["size"]["w"])
        depth = float(room["size"]["d"])
        fp_x = float(footprint.get("x", 0))
        fp_z = float(footprint.get("z", 0))
        fp_w = float(footprint["w"])
        fp_d = float(footprint["d"])
    except (KeyError, TypeError, ValueError):
        return False
    return any(
        gap <= _EDGE_TOLERANCE_M
        for gap in (
            abs((x - width / 2) - fp_x),
            abs((x + width / 2) - (fp_x + fp_w)),
            abs((z - depth / 2) - fp_z),
            abs((z + depth / 2) - (fp_z + fp_d)),
        )
    )


def _entry_check(parsed: "ParsedRequirements", layout: dict) -> dict | None:
    desired = (parsed.entry_side or parsed.facing_direction or "").upper()
    if desired not in {"N", "S", "E", "W"}:
        return None
    entry = next(
        (
            obj
            for obj in layout.get("rooms") or []
            if obj.get("objectType") == "door" and obj.get("label") == "Entry Door"
        ),
        None,
    )
    footprint = _footprints_by_level(layout).get(0)
    if entry is None or footprint is None:
        return {
            "id": "orientation-entry",
            "relationType": "preferredOrientation",
            "strength": "MUST",
            "nodeA": "entry",
            "nodeB": desired,
            "label": f"Main entry on {desired} / front side",
            "status": "missing_dependency",
            "reason": "The entry door or ground-floor footprint is missing.",
        }

    x = float(entry["position"]["x"])
    z = float(entry["position"]["z"])
    fp_x = float(footprint.get("x", 0))
    fp_z = float(footprint.get("z", 0))
    fp_w = float(footprint["w"])
    fp_d = float(footprint["d"])
    expected_coordinate = {
        "E": fp_x + fp_w,
        "W": fp_x,
        "N": fp_z + fp_d,
        "S": fp_z,
    }[desired]
    actual_coordinate = x if desired in {"E", "W"} else z
    satisfied = abs(actual_coordinate - expected_coordinate) <= 0.5
    return {
        "id": "orientation-entry",
        "relationType": "preferredOrientation",
        "strength": "MUST",
        "nodeA": "entry",
        "nodeB": desired,
        "label": f"Main entry on {desired} / front side",
        "status": "satisfied" if satisfied else "failed",
        "reason": (
            "The entry follows the requested orientation."
            if satisfied
            else "The main entry is not on the requested front side."
        ),
    }


def validate_program(
    parsed: "ParsedRequirements",
    graph: ProgramGraph,
    layout: dict,
    *,
    program: dict[str, Any] | None = None,
    graph_satisfaction: GraphSatisfaction | None = None,
) -> dict[str, Any]:
    program = program or build_program_metadata(parsed, graph)
    graph_satisfaction = graph_satisfaction or score_graph_satisfaction(graph, layout)
    generated_rooms = _space_objects(layout)
    generated_counts = Counter(
        str(room.get("roomType") or "generic") for room in generated_rooms
    )

    space_checks: list[dict[str, Any]] = []
    missing_spaces: list[dict[str, Any]] = []
    requested_counts: Counter[str] = Counter()
    for requested in program["requestedSpaces"]:
        room_type = requested["normalizedType"]
        requested_count = int(requested["count"])
        generated_count = generated_counts.get(room_type, 0)
        requested_counts[room_type] += requested_count
        if generated_count == requested_count:
            status = "satisfied"
        elif generated_count == 0:
            status = "failed"
        elif generated_count < requested_count:
            status = "partial"
        else:
            status = "warning"
        check = {
            "id": requested["id"],
            "originalLabel": requested["originalLabel"],
            "normalizedType": room_type,
            "requestedCount": requested_count,
            "generatedCount": generated_count,
            "status": status,
        }
        space_checks.append(check)
        if generated_count < requested_count:
            missing_spaces.append(
                {
                    "normalizedType": room_type,
                    "label": requested["originalLabel"],
                    "count": requested_count - generated_count,
                }
            )

    extra_spaces = [
        {
            "normalizedType": room_type,
            "label": _humanize(room_type),
            "count": count - requested_counts.get(room_type, 0),
            "kind": (
                "generated_support"
                if room_type in {"hallway", "corridor", "stairs"}
                else "extra"
            ),
        }
        for room_type, count in sorted(generated_counts.items())
        if count > requested_counts.get(room_type, 0)
    ]

    constraint_checks = [check.as_dict() for check in graph_satisfaction.checks]
    footprints = _footprints_by_level(layout)
    for room in generated_rooms:
        room_type = str(room.get("roomType") or "")
        if room_type in parsed.daylight_rooms:
            exterior = _touches_exterior(room, footprints)
            constraint_checks.append(
                {
                    "id": f"daylight-{room.get('id')}",
                    "relationType": "prefersDaylight",
                    "strength": "SHOULD",
                    "nodeA": str(room.get("label") or room_type),
                    "nodeB": "exterior",
                    "label": f"Daylight access: {room.get('label') or _humanize(room_type)}",
                    "status": "satisfied" if exterior else "warning",
                    "reason": (
                        "The space touches an exterior edge."
                        if exterior
                        else "The space has limited exterior exposure."
                    ),
                }
            )
        if room_type in _EXTERIOR_REQUIRED_TYPES:
            exterior = _touches_exterior(room, footprints)
            constraint_checks.append(
                {
                    "id": f"exterior-{room.get('id')}",
                    "relationType": "requiresExteriorWall",
                    "strength": "MUST",
                    "nodeA": str(room.get("label") or room_type),
                    "nodeB": "exterior",
                    "label": f"Exterior edge: {room.get('label') or _humanize(room_type)}",
                    "status": "satisfied" if exterior else "failed",
                    "reason": (
                        "The outdoor space touches the building perimeter."
                        if exterior
                        else "The outdoor space is landlocked inside the footprint."
                    ),
                }
            )

    entry_check = _entry_check(parsed, layout)
    if entry_check:
        constraint_checks.append(entry_check)

    status_counts = Counter(
        [check["status"] for check in space_checks]
        + [check["status"] for check in constraint_checks]
    )
    if status_counts["failed"] or status_counts["missing_dependency"]:
        overall_status = "failed"
    elif status_counts["warning"] or status_counts["partial"]:
        overall_status = "warning"
    else:
        overall_status = "satisfied"

    return {
        "version": 1,
        "overallStatus": overall_status,
        "summary": {
            "requestedSpaceCount": sum(requested_counts.values()),
            "generatedSpaceCount": len(generated_rooms),
            "missingSpaceCount": sum(item["count"] for item in missing_spaces),
            "extraSpaceCount": sum(item["count"] for item in extra_spaces),
            "satisfiedCount": status_counts["satisfied"],
            "warningCount": status_counts["warning"] + status_counts["partial"],
            "failedCount": status_counts["failed"],
            "notEvaluatedCount": (
                status_counts["not_evaluated"]
                + status_counts["missing_dependency"]
            ),
        },
        "spaces": space_checks,
        "missingSpaces": missing_spaces,
        "extraSpaces": extra_spaces,
        "constraintChecks": constraint_checks,
    }
