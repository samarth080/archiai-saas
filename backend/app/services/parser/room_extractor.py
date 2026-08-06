import re
from dataclasses import dataclass, field

from app.services.catalog.space_catalog import CATALOG
from app.services.parser.data.room_vocabulary import COMPOUND_LINK_WORDS, ROOM_TERMS
from app.services.parser.normaliser import normalise


@dataclass(frozen=True)
class ExtractedRoom:
    room_type: str
    count: int = 1
    raw_text: str = ""
    source: str = "explicit"
    features: dict = field(default_factory=dict)


def _room_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for room_type, terms in ROOM_TERMS.items():
        for term in terms:
            lookup[term] = room_type
    for room_type in CATALOG:
        if room_type == "kitchen_dining":
            continue
        lookup.setdefault(room_type, room_type)
        lookup.setdefault(room_type.replace("_", " "), room_type)
    return lookup


ROOM_LOOKUP = _room_lookup()
ROOM_TOKEN_PATTERN = "|".join(
    re.escape(term)
    for term in sorted(ROOM_LOOKUP, key=lambda term: (-len(term), term))
)
LINK_PATTERN = "|".join(re.escape(word) for word in COMPOUND_LINK_WORDS)


def _normalise_room_token(token: str) -> str:
    return ROOM_LOOKUP[token.rstrip("s")]


def _features_for(room_type: str, text: str, start: int, end: int) -> dict:
    context = text[max(0, start - 24) : min(len(text), end + 36)]
    features: dict = {}
    if room_type == "ensuite":
        features["attached"] = True
    if room_type == "bedroom" and re.search(r"\bguest\b", context):
        features["guest"] = True
    if room_type == "open_plan_living":
        features["open_plan"] = True
    return features


def _extract_counted_rooms(text: str) -> list[ExtractedRoom]:
    rooms: list[ExtractedRoom] = []
    occupied_spans: list[tuple[int, int]] = []
    # Plain descriptive adjectives allowed between a count and the room token
    # ("2 regular bedrooms", "3 spacious meeting rooms") — without this the
    # count is silently lost and the rooms collapse to a single mention.
    filler = (
        r"(?:(?:regular|standard|normal|additional|extra|separate|shared|"
        r"attached|spacious|compact|large|small|big|cozy|simple|identical|"
        r"more|other|new|private)\s+){0,2}"
    )
    patterns = [
        re.compile(
            rf"\b(?P<count>\d+)\s+{filler}(?P<room>{ROOM_TOKEN_PATTERN})s?\b",
            re.IGNORECASE,
        ),
        re.compile(
            rf"\b(?P<room>{ROOM_TOKEN_PATTERN})s?\s*(?:x|:)\s*(?P<count>\d+)\b",
            re.IGNORECASE,
        ),
    ]

    for pattern in patterns:
        for match in pattern.finditer(text):
            if any(match.start() < end and match.end() > start for start, end in occupied_spans):
                continue
            room_type = _normalise_room_token(match.group("room"))
            count = max(1, int(match.group("count")))
            rooms.append(
                ExtractedRoom(
                    room_type=room_type,
                    count=count,
                    raw_text=match.group(0),
                    features=_features_for(room_type, text, match.start(), match.end()),
                )
            )
            occupied_spans.append((match.start(), match.end()))

    return rooms


def _extract_single_rooms(text: str, excluded: list[ExtractedRoom]) -> list[ExtractedRoom]:
    excluded_raw = {room.raw_text for room in excluded}
    pattern = re.compile(rf"\b(?P<room>{ROOM_TOKEN_PATTERN})s?\b", re.IGNORECASE)
    rooms: list[ExtractedRoom] = []

    for match in pattern.finditer(text):
        if any(match.group(0) in raw for raw in excluded_raw):
            continue
        room_type = _normalise_room_token(match.group("room"))
        context = text[max(0, match.start() - 18) : min(len(text), match.end() + 24)]
        linked = re.search(rf"\b(?:{LINK_PATTERN})\b", context) is not None
        source = "compound" if linked else "explicit"
        rooms.append(
            ExtractedRoom(
                room_type=room_type,
                raw_text=match.group(0),
                source=source,
                features=_features_for(room_type, text, match.start(), match.end()),
            )
        )

    return rooms


# Words that read as "<adjective> room" rather than a distinct custom space.
_CUSTOM_ROOM_STOPWORDS: frozenset[str] = frozenset({
    "regular", "standard", "normal", "additional", "extra", "separate",
    "shared", "attached", "spacious", "compact", "large", "small", "big",
    "cozy", "simple", "more", "other", "new", "private", "closed", "open",
    "spare", "the", "each", "every", "one", "single", "double", "guest",
    "this", "that", "any", "main", "first", "second", "third",
})

_CUSTOM_ROOM_PATTERN = re.compile(
    r"\b(?:(?P<count>\d+)\s+)?(?P<name>[a-z]+)[\s_]room\b", re.IGNORECASE
)


def _extract_custom_rooms(text: str, known: list[ExtractedRoom]) -> list[ExtractedRoom]:
    """
    Preserve '<word> room' mentions the vocabulary doesn't know (music room,
    server room, …) as custom space types instead of silently dropping them —
    the sizing/zoning pipeline handles unknown types with sane defaults.
    """
    known_raw = " ".join(room.raw_text for room in known)
    rooms: list[ExtractedRoom] = []
    seen: set[str] = set()
    for match in _CUSTOM_ROOM_PATTERN.finditer(text):
        name = match.group("name").lower()
        phrase = f"{name} room"
        if name in _CUSTOM_ROOM_STOPWORDS:
            continue
        if f"{name}_room" in ROOM_LOOKUP or phrase in ROOM_LOOKUP or name in ROOM_LOOKUP:
            continue
        if phrase in known_raw or f"{name}_room" in known_raw:
            continue
        room_type = f"{name}_room"
        if room_type in seen:
            continue
        seen.add(room_type)
        rooms.append(
            ExtractedRoom(
                room_type=room_type,
                count=max(1, int(match.group("count") or 1)),
                raw_text=match.group(0),
                source="custom",
                features={},
            )
        )
    return rooms


def extract_explicit_rooms(prompt: str) -> list[ExtractedRoom]:
    text = normalise(prompt)
    counted_rooms = _extract_counted_rooms(text)
    single_rooms = _extract_single_rooms(text, counted_rooms)
    known = counted_rooms + single_rooms
    return known + _extract_custom_rooms(text, known)
