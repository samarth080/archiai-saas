import re
from dataclasses import dataclass, field

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
    patterns = [
        re.compile(
            rf"\b(?P<count>\d+)\s+(?P<room>{ROOM_TOKEN_PATTERN})s?\b",
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


def extract_explicit_rooms(prompt: str) -> list[ExtractedRoom]:
    text = normalise(prompt)
    counted_rooms = _extract_counted_rooms(text)
    single_rooms = _extract_single_rooms(text, counted_rooms)
    return counted_rooms + single_rooms
