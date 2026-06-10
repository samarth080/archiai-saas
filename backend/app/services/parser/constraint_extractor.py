import re
from dataclasses import dataclass, field

from app.services.parser.data.room_vocabulary import ROOM_TERMS
from app.services.parser.normaliser import normalise


@dataclass(frozen=True)
class AdjacencyConstraint:
    room_a: str
    room_b: str
    strength: str  # "MUST" | "SHOULD"


@dataclass
class Constraints:
    adjacency: list[AdjacencyConstraint] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    zone_assignments: dict[str, str] = field(default_factory=dict)


# ── room token lookup ──────────────────────────────────────────────────────────

def _build_room_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for room_type, terms in ROOM_TERMS.items():
        for term in terms:
            lookup[term] = room_type
            if "_" in term:
                # add space variant so "meeting room" matches "meeting_room"
                lookup[term.replace("_", " ")] = room_type
    return lookup


_ROOM_LOOKUP: dict[str, str] = _build_room_lookup()
_ROOM_PAT = "|".join(
    re.escape(t) for t in sorted(_ROOM_LOOKUP, key=lambda t: (-len(t), t))
)


def _resolve(token: str) -> str | None:
    cleaned = token.strip()
    return _ROOM_LOOKUP.get(cleaned) or _ROOM_LOOKUP.get(cleaned.rstrip("s"))


# ── implicit adjacency pairs (always applied when both rooms are present) ──────

IMPLICIT_ADJACENCY: list[tuple[str, str]] = [
    ("master_bedroom", "ensuite"),
    ("kitchen", "dining_room"),
    ("foyer", "living_room"),
    ("kitchen", "laundry"),
    ("garage", "mudroom"),
    ("office", "meeting_room"),
]


# ── adjacency patterns ────────────────────────────────────────────────────────

_MUST_VERBS = (
    r"next to|beside|adjacent to|adjoining|connected to|attached to|next door to"
)
_SHOULD_VERBS = r"near|close to|by the|near the"

_ADJACENCY_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(
            rf"(?P<a>{_ROOM_PAT})s?\s+(?:{_MUST_VERBS})\s+(?:the\s+)?(?P<b>{_ROOM_PAT})s?",
            re.IGNORECASE,
        ),
        "MUST",
    ),
    (
        re.compile(
            rf"(?P<a>{_ROOM_PAT})s?\s+(?:{_SHOULD_VERBS})\s+(?:the\s+)?(?P<b>{_ROOM_PAT})s?",
            re.IGNORECASE,
        ),
        "SHOULD",
    ),
]

# "X with ensuite / attached bath / private bath" → forced adjacency
_WITH_ENSUITE_PATTERN = re.compile(
    rf"(?P<a>{_ROOM_PAT})s?\s+with\s+(?:an?\s+)?(?P<b>ensuite|attached\s+bath(?:room)?|private\s+bath(?:room)?)",
    re.IGNORECASE,
)


# ── exclusion patterns ────────────────────────────────────────────────────────

# normalise() converts "a"/"an" → "1" (NUMBER_WORDS), so allow digits too
_OPT_ARTICLE = r"(?:(?:an?|\d+)\s+)?"

_EXCLUSION_PATTERNS: list[re.Pattern] = [
    re.compile(rf"\bno\s+{_OPT_ARTICLE}(?P<room>{_ROOM_PAT})s?\b", re.IGNORECASE),
    re.compile(rf"\bwithout\s+{_OPT_ARTICLE}(?P<room>{_ROOM_PAT})s?\b", re.IGNORECASE),
    re.compile(
        rf"\bdon'?t\s+(?:want|need)\s+{_OPT_ARTICLE}(?P<room>{_ROOM_PAT})s?\b",
        re.IGNORECASE,
    ),
    re.compile(rf"\bexclude\s+(?:the\s+)?(?P<room>{_ROOM_PAT})s?\b", re.IGNORECASE),
    re.compile(rf"\bremove\s+(?:the\s+)?(?P<room>{_ROOM_PAT})s?\b", re.IGNORECASE),
]


# ── zone assignment patterns ──────────────────────────────────────────────────

_ZONE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(
            rf"(?P<room>{_ROOM_PAT})s?\s+"
            rf"(?:upstairs|on\s+(?:the\s+)?(?:1st|first|upper)\s+floor)",
            re.IGNORECASE,
        ),
        "upper",
    ),
    (
        re.compile(
            rf"(?P<room>{_ROOM_PAT})s?\s+(?:downstairs|on\s+(?:the\s+)?ground\s+floor)",
            re.IGNORECASE,
        ),
        "ground",
    ),
    (
        re.compile(
            rf"(?P<room>{_ROOM_PAT})s?\s+in\s+(?:the\s+)?basement",
            re.IGNORECASE,
        ),
        "basement",
    ),
]


# ── extraction helpers ────────────────────────────────────────────────────────

def _extract_explicit_adjacency(text: str) -> list[AdjacencyConstraint]:
    results: list[AdjacencyConstraint] = []
    seen: set[frozenset] = set()

    def _add(a_token: str, b_token: str, strength: str) -> None:
        a = _resolve(a_token)
        b = _resolve(b_token)
        if not a or not b or a == b:
            return
        key: frozenset = frozenset({a, b})
        if key not in seen:
            seen.add(key)
            results.append(AdjacencyConstraint(room_a=a, room_b=b, strength=strength))

    for pattern, strength in _ADJACENCY_PATTERNS:
        for match in pattern.finditer(text):
            _add(match.group("a"), match.group("b"), strength)

    for match in _WITH_ENSUITE_PATTERN.finditer(text):
        a = _resolve(match.group("a"))
        b_raw = match.group("b").lower()
        b = "ensuite" if any(kw in b_raw for kw in ("ensuite", "attached", "private")) else None
        if a and b:
            key = frozenset({a, b})
            if key not in seen:
                seen.add(key)
                results.append(AdjacencyConstraint(room_a=a, room_b=b, strength="MUST"))

    return results


def _add_implicit_adjacency(
    explicit: list[AdjacencyConstraint],
    present_room_types: set[str],
) -> list[AdjacencyConstraint]:
    seen: set[frozenset] = {frozenset({c.room_a, c.room_b}) for c in explicit}
    result = list(explicit)
    for a, b in IMPLICIT_ADJACENCY:
        if a in present_room_types and b in present_room_types:
            key: frozenset = frozenset({a, b})
            if key not in seen:
                seen.add(key)
                result.append(AdjacencyConstraint(room_a=a, room_b=b, strength="SHOULD"))
    return result


def _extract_exclusions(text: str) -> list[str]:
    exclusions: list[str] = []
    seen: set[str] = set()
    for pattern in _EXCLUSION_PATTERNS:
        for match in pattern.finditer(text):
            room_type = _resolve(match.group("room"))
            if room_type and room_type not in seen:
                seen.add(room_type)
                exclusions.append(room_type)
    return exclusions


def _extract_zone_assignments(text: str) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for pattern, zone in _ZONE_PATTERNS:
        for match in pattern.finditer(text):
            room_type = _resolve(match.group("room"))
            if room_type:
                assignments[room_type] = zone
    return assignments


# ── public API ────────────────────────────────────────────────────────────────

def extract_constraints(
    prompt: str,
    present_room_types: set[str] | None = None,
) -> Constraints:
    """
    Extract relational constraints from a layout prompt.

    present_room_types: when provided, implicit adjacency pairs are added for
    rooms that appear in this set. Omit to skip implicit adjacency — wire it in
    after Stage 4 merge produces the final room list.
    """
    text = normalise(prompt)
    explicit_adjacency = _extract_explicit_adjacency(text)
    adjacency = (
        _add_implicit_adjacency(explicit_adjacency, present_room_types)
        if present_room_types is not None
        else explicit_adjacency
    )
    return Constraints(
        adjacency=adjacency,
        exclusions=_extract_exclusions(text),
        zone_assignments=_extract_zone_assignments(text),
    )
