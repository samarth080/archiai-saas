"""
Sprint 16 — Unified Space-Filling Layouts & Adjacency Reasoning.

These tests exercise the PRODUCTION parse path (parse_prompt → generate_layout),
which is where the real-world behaviour the user sees is produced:
- every building type tiles (no blank bands inside the boundary walls),
- the parser's relational language shapes adjacency,
- commercial prompts no longer inherit residential rooms.
"""
import pytest

from app.services.layout_service import generate_layout
from app.services.prompt_service import parse_prompt, parsed_to_room_specs


def _generate(prompt: str) -> dict:
    parsed = parse_prompt(prompt)
    specs = parsed_to_room_specs(parsed)
    return generate_layout(
        specs,
        prompt=prompt,
        building_type=parsed.building_type,
        total_floors=parsed.total_floors,
        adjacency_constraints=parsed.adjacency_constraints,
        zone_assignments=parsed.zone_assignments,
    )


def _rooms(layout: dict) -> list[dict]:
    return [r for r in layout["rooms"] if r["objectType"] == "room"]


def _find(layout: dict, room_type: str) -> dict:
    return next(r for r in layout["rooms"] if r["roomType"] == room_type)


def _room_types(layout: dict) -> set[str]:
    return {r["roomType"] for r in _rooms(layout)}


def _edge_gap(a: dict, b: dict) -> float:
    if a["floorLevel"] != b["floorLevel"]:
        return float("inf")
    x_gap = max(0.0, abs(a["position"]["x"] - b["position"]["x"]) - (a["size"]["w"] + b["size"]["w"]) / 2)
    z_gap = max(0.0, abs(a["position"]["z"] - b["position"]["z"]) - (a["size"]["d"] + b["size"]["d"]) / 2)
    return round(x_gap + z_gap, 2)


def _ground_floor_utilization(layout: dict) -> float:
    footprint = layout["floors"][0]["footprint"]
    fa = footprint["w"] * footprint["d"]
    ra = sum(
        r["size"]["w"] * r["size"]["d"]
        for r in _rooms(layout)
        if r["floorLevel"] == 0
    )
    return ra / fa if fa else 0.0


def _overlaps(a: dict, b: dict) -> bool:
    if a["floorLevel"] != b["floorLevel"]:
        return False
    _eps = 0.02
    ax1, ax2 = a["position"]["x"] - a["size"]["w"] / 2, a["position"]["x"] + a["size"]["w"] / 2
    az1, az2 = a["position"]["z"] - a["size"]["d"] / 2, a["position"]["z"] + a["size"]["d"] / 2
    bx1, bx2 = b["position"]["x"] - b["size"]["w"] / 2, b["position"]["x"] + b["size"]["w"] / 2
    bz1, bz2 = b["position"]["z"] - b["size"]["d"] / 2, b["position"]["z"] + b["size"]["d"] / 2
    return ax1 + _eps < bx2 and ax2 - _eps > bx1 and az1 + _eps < bz2 and az2 - _eps > bz1


# ── Phase 1 — every type tiles, no blank space ──────────────────────────────────

COMMERCIAL_PROMPTS = [
    "small office with reception, meeting room, open workspace and storage",
    "clinic with reception, waiting room and two consultation rooms",
    "retail store with display area, storage and checkout",
    "restaurant with dining room, kitchen, bathroom and storage",
    "school with four classrooms, corridor and bathroom",
]


@pytest.mark.parametrize("prompt", COMMERCIAL_PROMPTS)
def test_commercial_layouts_fill_their_footprint(prompt: str):
    """The ground floor's rooms should fill the footprint (no big blank band)."""
    layout = _generate(prompt)
    assert _ground_floor_utilization(layout) >= 0.8


@pytest.mark.parametrize("prompt", COMMERCIAL_PROMPTS)
def test_commercial_rooms_do_not_overlap(prompt: str):
    layout = _generate(prompt)
    rooms = [r for r in layout["rooms"] if r["objectType"] in {"room", "stair"}]
    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            assert not _overlaps(a, b), f"{a['label']} overlaps {b['label']}"


# ── Phase 2 — adjacency reasoning ───────────────────────────────────────────────

def test_kitchen_and_dining_share_a_wall():
    layout = _generate("apartment with living room, kitchen and dining room")
    assert _edge_gap(_find(layout, "kitchen"), _find(layout, "dining_room")) <= 1.0


def test_master_bedroom_ensuite_is_adjacent():
    layout = _generate("apartment with master bedroom with ensuite, living room and kitchen")
    masters = [r for r in _rooms(layout) if r["roomType"] == "master_bedroom"]
    bathrooms = [r for r in _rooms(layout) if r["roomType"] == "bathroom"]
    assert masters and bathrooms
    assert any(_edge_gap(m, b) <= 1.0 for m in masters for b in bathrooms)


def test_reception_and_waiting_share_a_wall():
    layout = _generate("clinic with reception, waiting room and two consultation rooms")
    assert _edge_gap(_find(layout, "reception"), _find(layout, "waiting_room")) <= 1.0


def test_relational_language_shapes_adjacency():
    """'next to X is Y' and 'behind' relational phrasing must be honoured."""
    prompt = (
        "clinic with reception. the doctor's office is just behind the reception. "
        "next to the doctor's office is the washroom"
    )
    layout = _generate(prompt)
    consultation = _find(layout, "consultation_room")
    reception = _find(layout, "reception")
    bathroom = _find(layout, "bathroom")
    assert _edge_gap(consultation, reception) <= 2.0  # buffered by the corridor at most
    assert _edge_gap(consultation, bathroom) <= 1.0


# ── Multi-floor commercial ──────────────────────────────────────────────────────

def test_multi_floor_commercial_shares_width_and_aligns_stairs():
    layout = _generate("two storey office with reception, open workspace, meeting rooms and storage")
    assert layout["metadata"]["totalFloors"] == 2
    widths = [f["footprint"]["w"] for f in layout["floors"] if f["footprint"]["w"] > 0]
    assert len(widths) == 2
    assert abs(widths[0] - widths[1]) < 0.5

    stairs = [r for r in layout["rooms"] if r["roomType"] == "stairs"]
    levels = {s["floorLevel"] for s in stairs}
    assert levels == {0, 1}
    xs = [round(s["position"]["x"], 1) for s in stairs]
    assert max(xs) - min(xs) < 0.5  # stairs vertically aligned across floors


# ── Parser correctness (Gap A + B) ──────────────────────────────────────────────

def test_clinic_has_no_residential_rooms():
    """A clinic must not inherit bedrooms/kitchen/living room from a fallback."""
    layout = _generate("clinic with reception, waiting room and two consultation rooms")
    types = _room_types(layout)
    assert {"bedroom", "master_bedroom", "kitchen", "living_room"}.isdisjoint(types)
    assert {"reception", "waiting_room", "consultation_room"}.issubset(types)


def test_school_has_classrooms_not_bedrooms():
    layout = _generate("school with four classrooms and corridor")
    types = _room_types(layout)
    assert "classroom" in types
    assert {"bedroom", "kitchen", "living_room"}.isdisjoint(types)


@pytest.mark.parametrize(
    ("phrase", "expected_type"),
    [
        ("seating area", "waiting_room"),
        ("waiting area", "waiting_room"),
        ("washroom", "bathroom"),
        ("doctor's office", "consultation_room"),
    ],
)
def test_natural_language_synonyms_resolve(phrase: str, expected_type: str):
    from app.services.parser.normaliser import normalise
    from app.services.parser.constraint_extractor import _resolve

    token = normalise(phrase)
    # normalise may already canonicalise to the room token; resolve the result.
    resolved = _resolve(token) or _resolve(token.replace(" ", "_"))
    assert resolved == expected_type
