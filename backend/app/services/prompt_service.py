import re
from dataclasses import dataclass, field
from math import sqrt

from app.services.layout_vocabulary_service import (
    BUILDING_TYPE_ALIASES,
    find_building_type_in_text,
)

WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

SQFT_TO_SQM = 0.092903

ORDINAL_TO_NUM = {
    "first": 1, "second": 2, "third": 3,
}

ROOM_DEFAULTS: dict[str, dict] = {
    "living_room":    {"label": "Living Room",   "w": 5.0, "d": 5.0},
    "kitchen":        {"label": "Kitchen",        "w": 4.0, "d": 4.0},
    "master_bedroom": {"label": "Master Bedroom", "w": 5.0, "d": 5.0},
    "bedroom":        {"label": "Bedroom",        "w": 4.0, "d": 4.0},
    "bathroom":       {"label": "Bathroom",       "w": 3.0, "d": 3.0},
    "dining_room":    {"label": "Dining Room",    "w": 4.0, "d": 4.0},
    "office":         {"label": "Office",         "w": 4.0, "d": 4.0},
    "study":          {"label": "Home Office",    "w": 3.0, "d": 3.0},
    "workspace":      {"label": "Open Workspace", "w": 6.0, "d": 5.0},
    "meeting_room":   {"label": "Meeting Room",   "w": 4.0, "d": 3.0},
    "reception":      {"label": "Reception",      "w": 3.5, "d": 3.5},
    "waiting_room":   {"label": "Waiting Room",   "w": 4.0, "d": 4.0},
    "consultation_room": {"label": "Consultation Room", "w": 3.5, "d": 3.5},
    "classroom":      {"label": "Classroom",      "w": 7.0, "d": 6.0},
    "retail_display": {"label": "Display Area",   "w": 7.0, "d": 6.0},
    "checkout":       {"label": "Checkout",       "w": 3.0, "d": 2.0},
    "storage":        {"label": "Storage",        "w": 3.0, "d": 3.0},
    "entry":          {"label": "Entry",          "w": 2.5, "d": 2.5},
    "hallway":        {"label": "Hallway",        "w": 3.0, "d": 2.0},
    "balcony":        {"label": "Balcony",        "w": 4.0, "d": 2.0},
    "garage":         {"label": "Garage",         "w": 5.0, "d": 6.0},
    "utility":        {"label": "Utility Room",   "w": 3.0, "d": 3.0},
}

# Longer/more specific phrases first to avoid partial matches
ROOM_PATTERNS: list[tuple[str, list[str]]] = [
    ("consultation_room", ["consultation room", "consult room", "exam room"]),
    ("meeting_room",   ["meeting room", "conference room"]),
    ("waiting_room",   ["waiting room", "waiting area"]),
    ("retail_display", ["display area", "retail display", "sales floor"]),
    ("master_bedroom", ["master bedroom", "master bed", "primary bedroom"]),
    ("living_room",    ["living room", "lounge", "sitting room", "family room"]),
    ("dining_room",    ["dining room", "dining area", "dining"]),
    ("reception",      ["reception", "front desk"]),
    ("checkout",       ["checkout", "cash register", "till"]),
    ("workspace",      ["open workspace", "workspace", "work area"]),
    ("study",          ["home office", "study"]),
    ("bathroom",       ["bathroom", "bath room", "en suite", "ensuite", "toilet", "washroom", "wc"]),
    ("kitchen",        ["kitchen", "kitchenette"]),
    ("classroom",      ["classroom"]),
    ("bedroom",        ["bedroom", "bed room", "guest bedroom", "guest room", "kids room"]),
    ("office",         ["office"]),
    ("hallway",        ["hallway", "hall", "corridor", "passage", "passageway"]),
    ("entry",          ["entry", "entrance", "foyer", "lobby"]),
    ("balcony",        ["balcony", "terrace", "porch"]),
    ("garage",         ["garage", "car park", "parking"]),
    ("storage",        ["storage", "store room", "stock room"]),
    ("utility",        ["utility room", "laundry"]),
]

SIZE_MODIFIERS: dict[str, float] = {
    "large": 1.4, "big": 1.4, "spacious": 1.4, "open": 1.4,
    "small": 0.7, "compact": 0.7, "tiny": 0.7, "cosy": 0.7, "cozy": 0.7,
}

BUILDING_KEYWORDS: dict[str, list[str]] = {
    building_type: list(aliases)
    for building_type, aliases in BUILDING_TYPE_ALIASES.items()
}

_COUNT_ALTS = "|".join(WORD_TO_NUM.keys())
_MODIFIER_LOOKBACK = 25


@dataclass
class RoomSpec:
    label: str
    room_type: str
    w: float
    h: float
    d: float


def detect_building_type(prompt: str) -> str:
    return find_building_type_in_text(prompt) or "apartment"


def _parse_number(raw: str) -> int | None:
    token = raw.lower()
    if token.isdigit():
        return int(token)
    return WORD_TO_NUM.get(token) or ORDINAL_TO_NUM.get(token)


def extract_total_floors(prompt: str) -> int:
    text = prompt.lower()

    g_plus = re.search(r"\bg\s*\+\s*(\d+)\b", text, re.IGNORECASE)
    if g_plus:
        return int(g_plus.group(1)) + 1

    ground_plus = re.search(
        r"\bground\s+plus\s+(first|second|third|one|two|three|\d+)\b",
        text,
        re.IGNORECASE,
    )
    if ground_plus:
        extra_floors = _parse_number(ground_plus.group(1))
        if extra_floors is not None:
            return extra_floors + 1

    floor_phrase = re.search(
        r"\b(" + _COUNT_ALTS + r"|\d+)\s+(?:floors?|storeys?|story|stories)\b",
        text,
        re.IGNORECASE,
    )
    if floor_phrase:
        total = _parse_number(floor_phrase.group(1))
        if total is not None:
            return max(1, total)

    return 1


def extract_total_area_sqm(prompt: str) -> float | None:
    match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(sqm|sq\.?\s*m|m2|square metres?|square meters?|sqft|sq\.?\s*ft|ft2|square feet)\b",
        prompt,
        re.IGNORECASE,
    )
    if not match:
        return None
    area = float(match.group(1))
    unit = match.group(2).lower().replace(".", "").replace(" ", "")
    if unit in {"sqft", "ft2", "squarefeet"}:
        area *= SQFT_TO_SQM
    return round(area, 2)


def extract_rooms(prompt: str) -> list[RoomSpec]:
    text = prompt.lower()
    text = re.sub(r"\bopen[\s-]+plan\s+kitchen\s+living\b", "open plan kitchen and living room", text)
    specs: list[RoomSpec] = []

    for room_type, keywords in ROOM_PATTERNS:
        for keyword in keywords:
            pattern = re.compile(
                r"(?:(" + _COUNT_ALTS + r"|\d+)\s+)?" + re.escape(keyword) + r"s?\b",
                re.IGNORECASE,
            )
            matches = list(pattern.finditer(text))
            if not matches:
                continue

            count = 0
            size_factor = 1.0
            for m in matches:
                raw = m.group(1)
                if raw is None:
                    count += 1
                elif raw.isdigit():
                    count += int(raw)
                else:
                    count += WORD_TO_NUM.get(raw.lower(), 1)

                if size_factor == 1.0:
                    window = text[max(0, m.start() - _MODIFIER_LOOKBACK) : m.start()]
                    for word, factor in SIZE_MODIFIERS.items():
                        if re.search(r"\b" + re.escape(word) + r"\b", window):
                            size_factor = factor
                            break

            defaults = ROOM_DEFAULTS[room_type]
            f = sqrt(size_factor)
            w = round(defaults["w"] * f, 1)
            d = round(defaults["d"] * f, 1)
            label_base = defaults["label"]

            for i in range(count):
                label = f"{label_base} {i + 1}" if count > 1 else label_base
                specs.append(RoomSpec(label=label, room_type=room_type, w=w, h=3.0, d=d))

            # Blank matched positions so later room types don't re-match them
            for m in reversed(matches):
                text = text[: m.start()] + " " * (m.end() - m.start()) + text[m.end() :]

            break  # Skip remaining keywords for this room type

    return specs


# ── Advanced parser pipeline (Stages 1-6) ─────────────────────────────────────

from app.services.parser.building_inference import infer_building  # noqa: E402
from app.services.parser.constraint_extractor import (  # noqa: E402
    AdjacencyConstraint,
    extract_constraints,
)
from app.services.parser.merger import merge_rooms  # noqa: E402
from app.services.parser.room_extractor import extract_explicit_rooms  # noqa: E402
from app.services.parser.size_resolver import resolve_size  # noqa: E402


@dataclass
class RoomRequirement:
    room_type: str
    count: int
    area_m2: float
    width: float
    depth: float
    floor_preference: str = "any"   # "ground" | "upper" | "any"
    zone: str = "other"
    size_key: str = "medium"
    is_compound: bool = False
    source: str = "explicit"        # "explicit" | "inferred" | "bhk" | "style"


@dataclass
class ParsedRequirements:
    building_type: str
    style_hints: dict
    total_floors: int
    rooms: list[RoomRequirement]
    adjacency_constraints: list[AdjacencyConstraint]
    exclusions: list[str]
    zone_assignments: dict[str, str]
    raw_prompt: str
    confidence: float = 1.0
    vastu_requested: bool = False


_PUBLIC_ROOM_TYPES: frozenset[str] = frozenset({
    "living_room", "open_plan_living", "kitchen", "dining_room", "foyer",
    "reception", "waiting_room", "retail_display", "checkout", "dining_area",
    "bar", "sales_floor", "classroom",
})
_PRIVATE_ROOM_TYPES: frozenset[str] = frozenset({
    "master_bedroom", "bedroom", "kids_room", "ensuite", "office",
    "consultation_room", "workspace", "meeting_room", "pooja_room",
    "meditation_room",
})
_SERVICE_ROOM_TYPES: frozenset[str] = frozenset({
    "bathroom", "laundry", "storage", "garage", "mudroom",
    "utility", "staircase", "hallway",
})


def _zone_for(room_type: str) -> str:
    if room_type in _PUBLIC_ROOM_TYPES:
        return "public"
    if room_type in _PRIVATE_ROOM_TYPES:
        return "private"
    if room_type in _SERVICE_ROOM_TYPES:
        return "service"
    return "other"


def _floor_pref_for(room_type: str, zone_assignments: dict[str, str]) -> str:
    mapping = {"ground": "ground", "upper": "upper", "basement": "basement"}
    return mapping.get(zone_assignments.get(room_type, ""), "any")


def _compute_confidence(explicit_count: int, inferred_count: int) -> float:
    total = explicit_count + inferred_count
    if total == 0:
        return 0.5
    return round(min(1.0, explicit_count / total + 0.3), 2)


def parse_prompt(prompt: str) -> "ParsedRequirements":
    """Run all 6 parser stages and return structured requirements."""
    # Stage 2 — building type + template rooms
    building = infer_building(prompt)

    # Stage 3 — explicit rooms from the prompt text
    explicit = extract_explicit_rooms(prompt)

    # Stage 4 — merge inferred template with explicit rooms
    merged = merge_rooms(
        building.inferred_rooms,
        explicit,
        style_hints=building.style_hints,
        exclusions=[],
    )

    present_types: set[str] = {room.room_type for room in merged}

    # Stage 5 — relational constraints (adjacency, exclusions, zones)
    constraints = extract_constraints(prompt, present_room_types=present_types)

    # Apply exclusions before sizing
    merged = [r for r in merged if r.room_type not in constraints.exclusions]

    # Stage 6 — resolve real-world dimensions for each room
    rooms: list[RoomRequirement] = []
    for m in merged:
        dims = resolve_size(m.room_type, m.size_key, 1.0, None)
        rooms.append(
            RoomRequirement(
                room_type=m.room_type,
                count=m.count,
                area_m2=dims["area_m2"],
                width=dims["width"],
                depth=dims["depth"],
                floor_preference=_floor_pref_for(m.room_type, constraints.zone_assignments),
                zone=_zone_for(m.room_type),
                size_key=m.size_key,
                is_compound=m.is_compound,
                source=m.source,
            )
        )

    explicit_count = sum(r.count for r in rooms if r.source == "explicit")
    inferred_count = sum(r.count for r in rooms if r.source in ("inferred", "bhk"))

    # Floor count: explicit "N floors/storeys" wins; fall back to building template
    explicit_floors = extract_total_floors(prompt)
    total_floors = explicit_floors if explicit_floors > 1 else building.total_floors

    # Optional Vastu stage — only when user explicitly requests it
    from app.services.parser.vastu import add_vastu_special_rooms, is_vastu_requested
    vastu_req = is_vastu_requested(prompt)
    if vastu_req:
        rooms = add_vastu_special_rooms(rooms, prompt)

    return ParsedRequirements(
        building_type=building.building_type,
        style_hints=building.style_hints,
        total_floors=total_floors,
        rooms=rooms,
        adjacency_constraints=constraints.adjacency,
        exclusions=constraints.exclusions,
        zone_assignments=constraints.zone_assignments,
        raw_prompt=prompt,
        confidence=_compute_confidence(explicit_count, inferred_count),
        vastu_requested=vastu_req,
    )


def parsed_to_room_specs(parsed: "ParsedRequirements") -> list[RoomSpec]:
    """Convert ParsedRequirements into list[RoomSpec] for layout_service."""
    specs: list[RoomSpec] = []
    for room in parsed.rooms:
        label_base = room.room_type.replace("_", " ").title()
        for i in range(room.count):
            label = f"{label_base} {i + 1}" if room.count > 1 else label_base
            specs.append(
                RoomSpec(
                    label=label,
                    room_type=room.room_type,
                    w=room.width,
                    h=3.0,
                    d=room.depth,
                )
            )
    return specs
