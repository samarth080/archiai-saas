import re
from dataclasses import dataclass
from math import sqrt

WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

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
    "hallway":        {"label": "Hallway",        "w": 3.0, "d": 2.0},
    "balcony":        {"label": "Balcony",        "w": 4.0, "d": 2.0},
    "garage":         {"label": "Garage",         "w": 5.0, "d": 6.0},
    "utility":        {"label": "Utility Room",   "w": 3.0, "d": 3.0},
}

# Longer/more specific phrases first to avoid partial matches
ROOM_PATTERNS: list[tuple[str, list[str]]] = [
    ("master_bedroom", ["master bedroom", "master bed", "primary bedroom"]),
    ("living_room",    ["living room", "lounge", "sitting room", "family room"]),
    ("dining_room",    ["dining room", "dining area", "dining"]),
    ("bathroom",       ["bathroom", "bath room", "en suite", "ensuite", "toilet", "washroom", "wc"]),
    ("kitchen",        ["kitchen", "kitchenette"]),
    ("bedroom",        ["bedroom", "bed room", "guest bedroom", "guest room", "kids room"]),
    ("office",         ["office", "study", "home office", "workspace"]),
    ("hallway",        ["hallway", "hall", "corridor", "foyer", "entrance"]),
    ("balcony",        ["balcony", "terrace", "porch"]),
    ("garage",         ["garage", "car park", "parking"]),
    ("utility",        ["utility room", "laundry", "storage"]),
]

SIZE_MODIFIERS: dict[str, float] = {
    "large": 1.4, "big": 1.4, "spacious": 1.4, "open": 1.4,
    "small": 0.7, "compact": 0.7, "tiny": 0.7, "cosy": 0.7, "cozy": 0.7,
}

BUILDING_KEYWORDS: dict[str, list[str]] = {
    "apartment": ["apartment", "flat", "condo"],
    "house":     ["house", "home", "villa", "cottage"],
    "office":    ["office building", "workspace", "studio"],
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
    text = prompt.lower()
    for building_type, keywords in BUILDING_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return building_type
    return "apartment"


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


def extract_rooms(prompt: str) -> list[RoomSpec]:
    text = prompt.lower()
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
