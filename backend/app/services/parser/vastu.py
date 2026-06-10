"""
Vastu Shastra compliance module.

Only activates when the user explicitly requests it (is_vastu_requested).
Never silently applies Vastu rules. Violations are advisory — adjacency
constraints always take priority over directional preferences.
"""

import math
from dataclasses import dataclass, field

# ── trigger keywords ──────────────────────────────────────────────────────────

VASTU_TRIGGER_KEYWORDS: tuple[str, ...] = (
    "vastu", "vaastu", "vastu shastra", "vastu compliant", "vastu friendly",
    "vastu approved", "as per vastu", "according to vastu",
    "vastu based", "vastu layout",
)

VASTU_ROOM_TRIGGERS: dict[str, str] = {
    "pooja":        "pooja_room",
    "puja":         "pooja_room",
    "prayer room":  "pooja_room",
    "mandir":       "pooja_room",
    "temple room":  "pooja_room",
    "meditation":   "meditation_room",
    "yoga room":    "meditation_room",
}

# ── directional rules ─────────────────────────────────────────────────────────

# Three.js / R3F coordinate system: -Z = north, +Z = south, +X = east, -X = west
_DIRECTIONS = ("north", "northeast", "east", "southeast",
               "south", "southwest", "west", "northwest")

VASTU_PREFERRED: dict[str, tuple[str, ...]] = {
    "north":     ("office", "living_room", "bathroom"),
    "northeast": ("pooja_room", "meditation_room", "office"),
    "east":      ("living_room", "dining_room", "bathroom", "bedroom"),
    "southeast": ("kitchen",),
    "south":     ("master_bedroom", "storage", "staircase"),
    "southwest": ("master_bedroom", "storage"),
    "west":      ("dining_room", "kids_room", "office"),
    "northwest": ("bedroom", "garage", "bathroom", "laundry"),
}

VASTU_FORBIDDEN: dict[str, tuple[str, ...]] = {
    "northeast": ("kitchen", "bathroom", "staircase", "garage"),
    "southeast": ("master_bedroom", "bedroom"),
    "southwest": ("kitchen", "bathroom"),
    "centre":    ("bedroom", "kitchen", "bathroom", "staircase"),
}

# Severity weights for score calculation
_SEVERITY_WEIGHTS = {"critical": 0.15, "moderate": 0.08, "minor": 0.03}


# ── dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class VastuViolation:
    room_type: str
    current_direction: str
    recommended_direction: str
    severity: str           # "critical" | "moderate" | "minor"
    message: str


@dataclass
class VastuResult:
    is_requested: bool
    violations: list[VastuViolation] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    compliance_score: float = 1.0
    brahmasthan_clear: bool = True


# ── public API ────────────────────────────────────────────────────────────────

def is_vastu_requested(prompt: str) -> bool:
    text = prompt.lower()
    return any(kw in text for kw in VASTU_TRIGGER_KEYWORDS)


def get_vastu_direction(room_position: dict, building_centre: dict) -> str:
    """
    Return the compass direction of room_position relative to building_centre.
    Uses Three.js coordinate space: -Z = north, +X = east.
    """
    dx = room_position["x"] - building_centre["x"]
    dz = room_position["z"] - building_centre["z"]
    if dx == 0 and dz == 0:
        return "centre"
    angle = math.degrees(math.atan2(dx, -dz)) % 360  # 0° = north, clockwise
    index = round(angle / 45) % 8
    return _DIRECTIONS[index]


def _building_centre(building_bounds: dict) -> dict:
    return {
        "x": (building_bounds.get("minX", 0) + building_bounds.get("maxX", 0)) / 2,
        "z": (building_bounds.get("minZ", 0) + building_bounds.get("maxZ", 0)) / 2,
    }


def _is_brahmasthan_clear(placed_rooms: list[dict], building_bounds: dict) -> bool:
    """Check that no room sits at the building centre (Brahmasthan)."""
    cx = (building_bounds.get("minX", 0) + building_bounds.get("maxX", 0)) / 2
    cz = (building_bounds.get("minZ", 0) + building_bounds.get("maxZ", 0)) / 2
    threshold = 1.5  # metres
    for room in placed_rooms:
        if room.get("objectType") != "room":
            continue
        pos = room.get("position", {})
        dist = math.sqrt((pos.get("x", 0) - cx) ** 2 + (pos.get("z", 0) - cz) ** 2)
        if dist < threshold:
            return False
    return True


def _preferred_direction(room_type: str) -> str:
    for direction, room_types in VASTU_PREFERRED.items():
        if room_type in room_types:
            return direction
    return "any"


def check_vastu_compliance(placed_rooms: list[dict], building_bounds: dict) -> VastuResult:
    """
    Analyse a placed layout for Vastu violations.
    placed_rooms: room dicts from layout JSON (objectType == "room").
    building_bounds: {"minX", "maxX", "minZ", "maxZ"} from layout["building"]["bounds"].
    """
    centre = _building_centre(building_bounds)
    violations: list[VastuViolation] = []
    suggestions: list[str] = []

    for room in placed_rooms:
        if room.get("objectType") != "room":
            continue
        room_type = room.get("roomType", "")
        pos = room.get("position", {})
        direction = get_vastu_direction(pos, centre)

        # Check forbidden directions
        forbidden_rooms = VASTU_FORBIDDEN.get(direction, ())
        if room_type in forbidden_rooms:
            preferred = _preferred_direction(room_type)
            severity = "critical" if direction in ("northeast", "centre") else "moderate"
            violations.append(VastuViolation(
                room_type=room_type,
                current_direction=direction,
                recommended_direction=preferred,
                severity=severity,
                message=(
                    f"{room_type.replace('_', ' ').title()} placed in {direction} — "
                    f"Vastu recommends {preferred} for this room."
                ),
            ))
            suggestions.append(
                f"Move {room_type.replace('_', ' ')} to the {preferred} sector."
            )

    brahmasthan_clear = _is_brahmasthan_clear(placed_rooms, building_bounds)
    if not brahmasthan_clear:
        violations.append(VastuViolation(
            room_type="centre",
            current_direction="centre",
            recommended_direction="centre",
            severity="critical",
            message="Brahmasthan (building centre) is occupied — it must remain open.",
        ))
        suggestions.append("Leave the central area of the building unbuilt (Brahmasthan).")

    score = 1.0
    for v in violations:
        score -= _SEVERITY_WEIGHTS.get(v.severity, 0.05)
    score = round(max(0.0, min(1.0, score)), 2)

    return VastuResult(
        is_requested=True,
        violations=violations,
        suggestions=suggestions,
        compliance_score=score,
        brahmasthan_clear=brahmasthan_clear,
    )


def add_vastu_special_rooms(
    rooms: list,          # list[RoomRequirement]
    prompt: str,
) -> list:
    """
    Add Vastu-specific rooms (pooja_room etc.) when requested and not already present.
    Returns the rooms list with any added entries.
    """
    from app.services.parser.size_resolver import resolve_size
    from app.services.prompt_service import RoomRequirement

    existing_types = {r.room_type for r in rooms}
    text = prompt.lower()

    # Always add pooja_room when Vastu requested and not already present
    if "pooja_room" not in existing_types:
        dims = resolve_size("pooja_room", "small")
        rooms = list(rooms) + [
            RoomRequirement(
                room_type="pooja_room",
                count=1,
                area_m2=dims["area_m2"],
                width=dims["width"],
                depth=dims["depth"],
                floor_preference="ground",
                zone="private",
                size_key="small",
                source="vastu",
            )
        ]

    # Add other explicitly triggered rooms
    for keyword, room_type in VASTU_ROOM_TRIGGERS.items():
        if keyword in text and room_type not in existing_types and room_type != "pooja_room":
            dims = resolve_size(room_type, "small")
            rooms = list(rooms) + [
                RoomRequirement(
                    room_type=room_type,
                    count=1,
                    area_m2=dims["area_m2"],
                    width=dims["width"],
                    depth=dims["depth"],
                    floor_preference="any",
                    zone="private",
                    size_key="small",
                    source="vastu",
                )
            ]
            existing_types.add(room_type)

    return rooms
