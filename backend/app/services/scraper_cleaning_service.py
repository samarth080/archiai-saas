import re
from datetime import datetime

from app.services.layout_vocabulary_service import (
    BUILDING_TYPE_ALIASES,
    ROOM_TYPE_ALIASES,
    contains_alias,
    find_building_type_in_text,
    room_types_in_text,
)


SQFT_TO_SQM = 0.092903

BUILDING_TYPES = BUILDING_TYPE_ALIASES
ROOM_TYPES = ROOM_TYPE_ALIASES

ZONE_KEYWORDS = {
    "private": ("private zone", "private room", "private rooms", "private area"),
    "public": ("public zone", "public room", "public rooms", "public area"),
    "service": ("service zone", "service room", "service rooms", "service area"),
}


def normalize_text(text: str) -> str:
    """Normalize whitespace without changing source wording."""
    text = re.sub(r"\\[nrt]", " ", text)
    return " ".join(text.split())


def _contains_alias(text: str, aliases: tuple[str, ...]) -> bool:
    return contains_alias(text, aliases)


def _split_sentences(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", normalized) if sentence.strip()]


def _find_building_type(text: str) -> str | None:
    return find_building_type_in_text(text)


def _find_area_range(text: str) -> tuple[float, float] | None:
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*"
        r"(sqm|sq\.?\s*m|m2|square metres?|square meters?|sqft|sq\.?\s*ft|ft2|square feet)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None

    minimum = float(match.group(1))
    maximum = float(match.group(2))
    unit = match.group(3).lower().replace(".", "").replace(" ", "")
    if unit in {"sqft", "ft2", "squarefeet"}:
        minimum *= SQFT_TO_SQM
        maximum *= SQFT_TO_SQM

    return round(minimum, 2), round(maximum, 2)


def _find_zone(text: str) -> str | None:
    lowered = text.lower()
    return next((zone for zone, phrases in ZONE_KEYWORDS.items() if any(phrase in lowered for phrase in phrases)), None)


def _room_types_in_text(text: str, *, exclude: str | None = None) -> list[str]:
    return room_types_in_text(text, exclude=exclude)


def _relationship_rooms(sentences: list[str], room_type: str, *, avoid: bool) -> list[str]:
    matched: set[str] = set()
    for sentence in sentences:
        lowered = sentence.lower()
        is_avoidance = any(keyword in lowered for keyword in ("avoid", "not next to", "away from", "separate from"))
        if is_avoidance != avoid:
            continue
        if not _contains_alias(lowered, ROOM_TYPES[room_type]):
            continue

        if avoid:
            relationship_text = lowered
        else:
            relation = re.search(r"\b(?:near|adjacent to|next to|connected to)\b(.+)", lowered)
            if not relation:
                continue
            relationship_text = relation.group(1)

        matched.update(_room_types_in_text(relationship_text, exclude=room_type))
    return sorted(matched)


def _join_matching(sentences: list[str], keywords: tuple[str, ...]) -> str | None:
    notes = [sentence for sentence in sentences if any(keyword in sentence.lower() for keyword in keywords)]
    return " ".join(notes) or None


def _layout_pattern(text: str) -> str | None:
    lowered = text.lower()
    if "open plan" in lowered or "open-plan" in lowered:
        return "open_plan"
    if "public zone" in lowered and "private" in lowered:
        return "public_private_split"
    if "central corridor" in lowered:
        return "central_corridor"
    return None


def extract_layout_metadata(
    raw_text: str,
    *,
    source_url: str,
    accessed_at: datetime,
) -> list[dict]:
    """Extract sparse source-derived layout references using controlled vocabulary matches."""
    normalized = normalize_text(raw_text)
    sentences = _split_sentences(normalized)
    building_type = _find_building_type(normalized)
    layout_pattern = _layout_pattern(normalized)
    circulation_notes = _join_matching(sentences, ("corridor", "hallway", "circulation"))
    door_window_notes = _join_matching(sentences, ("door", "window", "opening", "natural light"))
    accessibility_notes = _join_matching(sentences, ("accessible", "accessibility", "wheelchair", "step-free"))
    egress_notes = _join_matching(sentences, ("egress", "exit", "escape route"))

    records: list[dict] = []
    for room_type, aliases in ROOM_TYPES.items():
        room_sentences = [sentence for sentence in sentences if _contains_alias(sentence, aliases)]
        if not room_sentences:
            continue

        room_text = " ".join(room_sentences)
        area = _find_area_range(room_text)
        adjacent_to = _relationship_rooms(room_sentences, room_type, avoid=False)
        avoid_adjacent_to = _relationship_rooms(room_sentences, room_type, avoid=True)
        zone = _find_zone(room_text)
        confidence = "high" if area else "medium" if any((zone, adjacent_to, avoid_adjacent_to)) else "low"

        records.append(
            {
                "source_url": source_url,
                "accessed_at": accessed_at,
                "building_type": building_type,
                "layout_pattern": layout_pattern,
                "room_type": room_type,
                "typical_area_sqm_min": area[0] if area else None,
                "typical_area_sqm_max": area[1] if area else None,
                "zone": zone,
                "adjacent_to": adjacent_to,
                "avoid_adjacent_to": avoid_adjacent_to,
                "room_to_total_area_ratio_min": None,
                "room_to_total_area_ratio_max": None,
                "circulation_notes": circulation_notes,
                "door_window_notes": door_window_notes,
                "accessibility_notes": accessibility_notes,
                "egress_notes": egress_notes,
                "placement_notes": room_text,
                "confidence": confidence,
            }
        )
    return records
