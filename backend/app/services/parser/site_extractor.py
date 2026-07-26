"""
Stage 5b — site and orientation extraction.

Pulls plot dimensions, facing direction, road/entry sides, and daylight
priorities out of the prompt so generation can respect them instead of
treating "east-facing … on a 14 m × 18 m plot" as decoration.
"""
import re
from dataclasses import dataclass, field

from app.services.parser.constraint_extractor import _ROOM_PAT, _resolve

_FT_TO_M = 0.3048

_DIRECTIONS = {"north": "N", "south": "S", "east": "E", "west": "W"}
_DIR_PAT = r"(north|south|east|west)"

# "14 m x 18 m plot", "plot of 14 by 18 metres", "30 x 40 feet site/lot/land"
_DIMS_UNIT = r"(?:m|meters?|metres?|ft|feet|foot)"
_PLOT_WORDS = r"(?:plot|site|lot|land|parcel)"
_PLOT_DIM_PATTERNS = [
    re.compile(
        rf"(?P<w>\d+(?:\.\d+)?)\s*(?:{_DIMS_UNIT})?\s*(?:x|×|by)\s*"
        rf"(?P<d>\d+(?:\.\d+)?)\s*(?P<unit>{_DIMS_UNIT})\b[^.;]{{0,30}}?\b{_PLOT_WORDS}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_PLOT_WORDS}\b[^.;]{{0,30}}?(?P<w>\d+(?:\.\d+)?)\s*(?:{_DIMS_UNIT})?\s*(?:x|×|by)\s*"
        rf"(?P<d>\d+(?:\.\d+)?)\s*(?P<unit>{_DIMS_UNIT})?",
        re.IGNORECASE,
    ),
]

_FACING_PATTERNS = [
    re.compile(rf"\b{_DIR_PAT}[\s-]facing\b", re.IGNORECASE),
    re.compile(rf"\bfacing\s+(?:the\s+)?{_DIR_PAT}\b", re.IGNORECASE),
    re.compile(rf"\bfaces\s+(?:the\s+)?{_DIR_PAT}\b", re.IGNORECASE),
]

_ROAD_PATTERNS = [
    re.compile(rf"\broad\s+(?:is\s+)?(?:on|to|at|along)\s+(?:the\s+)?{_DIR_PAT}\b", re.IGNORECASE),
    re.compile(rf"\b{_DIR_PAT}[\s-]side\s+road\b", re.IGNORECASE),
    re.compile(rf"\bfrontage\s+(?:on|to)\s+(?:the\s+)?{_DIR_PAT}\b", re.IGNORECASE),
]

_ENTRY_PATTERNS = [
    re.compile(rf"\b(?:entry|entrance|main\s+door)\s+(?:from|on|at)\s+(?:the\s+)?{_DIR_PAT}\b", re.IGNORECASE),
]

_DAYLIGHT_KEYWORDS = re.compile(
    r"\b(?:daylight|natural\s+light|sunlight|sun\s+light|morning\s+sun|well[\s-]lit)\b",
    re.IGNORECASE,
)
_ROOM_TOKEN = re.compile(rf"\b(?P<room>{_ROOM_PAT})s?\b", re.IGNORECASE)


@dataclass
class SiteInfo:
    plot_width_m: float | None = None
    plot_depth_m: float | None = None
    facing_direction: str | None = None  # "N" | "S" | "E" | "W"
    road_side: str | None = None
    entry_side: str | None = None
    daylight_rooms: list[str] = field(default_factory=list)


def extract_plot_dimensions(prompt: str) -> tuple[float, float] | None:
    for pattern in _PLOT_DIM_PATTERNS:
        match = pattern.search(prompt)
        if not match:
            continue
        width = float(match.group("w"))
        depth = float(match.group("d"))
        unit = (match.group("unit") or "m").lower()
        if unit.startswith(("ft", "fee", "foo")):
            width *= _FT_TO_M
            depth *= _FT_TO_M
        if 2.0 <= width <= 200.0 and 2.0 <= depth <= 200.0:
            return (round(width, 2), round(depth, 2))
    return None


def _first_direction(prompt: str, patterns: list[re.Pattern]) -> str | None:
    for pattern in patterns:
        match = pattern.search(prompt)
        if match:
            return _DIRECTIONS[match.group(1).lower()]
    return None


def extract_daylight_rooms(prompt: str) -> list[str]:
    """Room types named in any sentence that mentions daylight/natural light."""
    rooms: list[str] = []
    for sentence in re.split(r"[.;!?]", prompt):
        if not _DAYLIGHT_KEYWORDS.search(sentence):
            continue
        for match in _ROOM_TOKEN.finditer(sentence.lower().replace(" room", "_room")):
            resolved = _resolve(match.group("room"))
            if resolved and resolved not in rooms:
                rooms.append(resolved)
    return rooms


def extract_site_info(prompt: str) -> SiteInfo:
    dims = extract_plot_dimensions(prompt)
    facing = _first_direction(prompt, _FACING_PATTERNS)
    road = _first_direction(prompt, _ROAD_PATTERNS)
    entry = _first_direction(prompt, _ENTRY_PATTERNS)
    return SiteInfo(
        plot_width_m=dims[0] if dims else None,
        plot_depth_m=dims[1] if dims else None,
        facing_direction=facing,
        road_side=road or facing,
        entry_side=entry or facing,
        daylight_rooms=extract_daylight_rooms(prompt),
    )
