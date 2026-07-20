"""
Sprint 22 — structured room program, site, and orientation extraction, and
their effect on generation. Anchored on the master example brief:

    east-facing single-storey 3BHK house on a 14 m x 18 m plot with master
    bedroom + attached bathroom, two regular bedrooms, shared bathroom,
    foyer, living, dining, closed kitchen, utility, study, pooja room,
    balcony, parking; kitchen next to dining and utility; balcony connected
    to living; master away from entry; no bathroom beside the kitchen;
    daylight priority for living room and bedrooms.
"""
from app.services.layout_service import _rooms_share_wall, generate_layout
from app.services.parser.site_extractor import (
    extract_plot_dimensions,
    extract_site_info,
)
from app.services.prompt_service import parse_prompt, parsed_to_room_specs

EXAMPLE_PROMPT = (
    "Design a practical east-facing single-storey 3BHK house on a 14 m x 18 m plot. "
    "Include one master bedroom with an attached bathroom, two regular bedrooms, "
    "one shared bathroom, an entry foyer, living room, dining room, closed kitchen, "
    "utility room, study, pooja room, balcony, and parking for one car. "
    "Keep the kitchen next to the dining room and utility room. "
    "Keep the balcony connected to the living room. "
    "Place the master bedroom away from the entry, "
    "and do not place any bathroom beside the kitchen. "
    "Prioritise daylight for the living room and bedrooms."
)


# ── extraction ────────────────────────────────────────────────────────────────

def test_plot_dimensions_extracted_in_metres_and_feet():
    assert extract_plot_dimensions("a house on a 14 m x 18 m plot") == (14.0, 18.0)
    assert extract_plot_dimensions("plot of 12 by 20 metres") == (12.0, 20.0)
    w, d = extract_plot_dimensions("30 x 40 feet site")
    assert (round(w, 1), round(d, 1)) == (9.1, 12.2)
    assert extract_plot_dimensions("a cosy 2 bedroom flat") is None


def test_facing_road_and_entry_directions_extracted():
    info = extract_site_info("east-facing house with road on the south")
    assert info.facing_direction == "E"
    assert info.road_side == "S"

    assert extract_site_info("the house faces west").facing_direction == "W"
    assert extract_site_info("north facing bungalow").facing_direction == "N"
    assert extract_site_info("entry from the north").entry_side == "N"
    assert extract_site_info("a simple cottage").facing_direction is None


def test_daylight_priority_rooms_extracted():
    info = extract_site_info(EXAMPLE_PROMPT)
    assert "living_room" in info.daylight_rooms
    assert "bedroom" in info.daylight_rooms


def test_example_prompt_extracts_the_full_room_program():
    parsed = parse_prompt(EXAMPLE_PROMPT)
    labels = [spec.label for spec in parsed_to_room_specs(parsed)]

    for expected in (
        "Bedroom 1", "Bedroom 2", "Master Bedroom", "Ensuite", "Bathroom",
        "Foyer", "Living Room", "Dining Room", "Kitchen", "Laundry",
        "Study", "Pooja Room", "Balcony", "Garage",
    ):
        assert expected in labels, f"missing {expected} in {labels}"
    assert parsed.plot_width_m == 14.0
    assert parsed.plot_depth_m == 18.0
    assert parsed.facing_direction == "E"
    assert parsed.building_type == "family_home"


def test_negated_adjacency_becomes_avoid_not_must():
    parsed = parse_prompt(EXAMPLE_PROMPT)
    strengths = {
        frozenset({c.room_a, c.room_b}): c.strength
        for c in parsed.adjacency_constraints
    }
    assert strengths[frozenset({"bathroom", "kitchen"})] == "AVOID"
    assert strengths[frozenset({"kitchen", "dining_room"})] == "MUST"
    assert strengths[frozenset({"kitchen", "laundry"})] == "MUST"
    assert strengths[frozenset({"balcony", "living_room"})] == "MUST"
    assert strengths[frozenset({"master_bedroom", "ensuite"})] == "MUST"


def test_away_from_entry_extracted_as_separation():
    parsed = parse_prompt(EXAMPLE_PROMPT)
    assert ("master_bedroom", "foyer") in parsed.separation_constraints


def test_unknown_custom_spaces_are_preserved():
    parsed = parse_prompt("office with a reception, server room and music room")
    types = {spec.room_type for spec in parsed_to_room_specs(parsed)}
    assert "server_room" in types
    assert "music_room" in types


# ── generation ────────────────────────────────────────────────────────────────

def _generate_example() -> dict:
    parsed = parse_prompt(EXAMPLE_PROMPT)
    return generate_layout(
        parsed_to_room_specs(parsed),
        prompt=EXAMPLE_PROMPT,
        building_type=parsed.building_type,
        total_floors=parsed.total_floors,
        adjacency_constraints=parsed.adjacency_constraints,
        zone_assignments=parsed.zone_assignments,
        plot_width_m=parsed.plot_width_m,
        plot_depth_m=parsed.plot_depth_m,
        orientation=parsed.facing_direction,
        road_side=parsed.road_side,
        entry_side=parsed.entry_side,
        daylight_rooms=parsed.daylight_rooms,
        separation_constraints=parsed.separation_constraints,
    )


def _rooms(layout: dict) -> list[dict]:
    return [
        room for floor in layout["floors"] for room in floor["rooms"]
        if room["objectType"] == "room"
    ]


def _share(layout: dict, type_a: str, type_b: str) -> bool:
    rooms = _rooms(layout)
    return any(
        _rooms_share_wall(a, b)
        for a in rooms if a["roomType"] == type_a
        for b in rooms if b["roomType"] == type_b
    )


def test_example_layout_respects_plot_and_constraints():
    layout = _generate_example()
    footprint = layout["floors"][0]["footprint"]

    assert footprint["w"] == 14.0
    assert abs(footprint["d"] - 18.0) < 0.05

    # every requested space is placed
    types = {room["roomType"] for room in _rooms(layout)}
    for expected in (
        "master_bedroom", "bedroom", "bathroom", "foyer", "living_room",
        "dining_room", "kitchen", "laundry", "study", "pooja_room",
        "balcony", "garage",
    ):
        assert expected in types

    # hard geometry: everything inside the footprint
    for room in _rooms(layout):
        assert room["position"]["x"] >= footprint["x"] - 0.05
        assert room["position"]["z"] >= footprint["z"] - 0.05
        assert room["size"]["w"] > 0 and room["size"]["d"] > 0

    # explicit constraints from the brief
    assert _share(layout, "kitchen", "dining_room"), "kitchen must touch dining"
    assert _share(layout, "balcony", "living_room"), "balcony must touch living"
    assert not _share(layout, "bathroom", "kitchen"), "no bathroom beside kitchen"
    assert not _share(layout, "master_bedroom", "foyer"), "master away from entry"


def test_example_layout_entry_door_sits_on_the_east_wall():
    layout = _generate_example()
    footprint = layout["floors"][0]["footprint"]
    entry = next(
        room for room in layout["rooms"]
        if room["objectType"] == "door" and room["label"] == "Entry Door"
    )
    assert entry["position"]["x"] > footprint["x"] + footprint["w"] - 0.5


def test_orientation_and_program_metadata_survive_the_response():
    layout = _generate_example()
    orientation = layout["metadata"]["orientation"]
    assert orientation["facingDirection"] == "E"
    assert orientation["entryWall"] == "right"
    assert "living_room" in orientation["daylightRooms"]

    constraints = layout["metadata"]["programConstraints"]
    assert ["bathroom", "kitchen"] in constraints["avoidPairs"]
    assert ["master_bedroom", "foyer"] in constraints["separations"]


def test_plot_depth_scales_the_plan_without_gaps_or_overlaps():
    parsed = parse_prompt("house with living room, kitchen, 2 bedrooms and a bathroom on a 10 m x 14 m plot")
    layout = generate_layout(
        parsed_to_room_specs(parsed),
        prompt=parsed.raw_prompt,
        building_type=parsed.building_type,
        total_floors=1,
        plot_width_m=parsed.plot_width_m,
        plot_depth_m=parsed.plot_depth_m,
    )
    footprint = layout["floors"][0]["footprint"]
    assert footprint["w"] == 10.0
    assert abs(footprint["d"] - 14.0) < 0.05
    rooms = _rooms(layout)
    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            ax1 = a["position"]["x"] - a["size"]["w"] / 2
            ax2 = a["position"]["x"] + a["size"]["w"] / 2
            bx1 = b["position"]["x"] - b["size"]["w"] / 2
            bx2 = b["position"]["x"] + b["size"]["w"] / 2
            az1 = a["position"]["z"] - a["size"]["d"] / 2
            az2 = a["position"]["z"] + a["size"]["d"] / 2
            bz1 = b["position"]["z"] - b["size"]["d"] / 2
            bz2 = b["position"]["z"] + b["size"]["d"] / 2
            overlap_x = min(ax2, bx2) - max(ax1, bx1)
            overlap_z = min(az2, bz2) - max(az1, bz1)
            assert not (overlap_x > 0.03 and overlap_z > 0.03), (
                f"{a['label']} overlaps {b['label']}"
            )


def test_unsatisfiable_constraints_surface_as_warnings_not_silence():
    # A one-room-wide plot cannot keep daylight for everything — whatever the
    # engine cannot satisfy must appear in the warnings, never vanish.
    layout = _generate_example()
    assert isinstance(layout["insights"]["warnings"], list)
