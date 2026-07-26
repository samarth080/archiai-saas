from copy import deepcopy

from app.services.layout_service import generate_layout
from app.services.planning import (
    build_program_metadata,
    from_parser_output,
    score_graph_satisfaction,
    validate_program,
)
from app.services.prompt_service import parse_prompt, parsed_to_room_specs
from app.tests.test_site_program_extraction import EXAMPLE_PROMPT


def _example_contract() -> tuple[dict, dict, object]:
    parsed = parse_prompt(EXAMPLE_PROMPT)
    specs = parsed_to_room_specs(parsed)
    graph = from_parser_output(parsed, specs)
    layout = generate_layout(
        specs,
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
    program = build_program_metadata(parsed, graph)
    validation = validate_program(
        parsed,
        graph,
        layout,
        program=program,
        graph_satisfaction=score_graph_satisfaction(graph, layout),
    )
    return program, validation, parsed


def test_program_contract_preserves_counts_original_labels_and_site():
    program, _, _ = _example_contract()
    spaces = {
        space["normalizedType"]: space for space in program["requestedSpaces"]
    }

    assert program["buildingType"] == "family_home"
    assert program["programType"] == "3BHK"
    assert program["requestedSpaceCount"] == 14
    assert program["site"]["plotWidth"] == 14.0
    assert program["site"]["plotDepth"] == 18.0
    assert program["site"]["facingDirection"] == "E"

    assert spaces["bedroom"]["count"] == 2
    assert spaces["bedroom"]["originalLabel"].lower() == "regular bedrooms"
    assert spaces["bathroom"]["originalLabel"].lower() == "shared bathroom"
    assert spaces["ensuite"]["originalLabel"].lower() == "attached bathroom"
    assert spaces["laundry"]["originalLabel"].lower() == "utility room"
    assert spaces["garage"]["originalLabel"].lower() == "parking"
    assert spaces["balcony"]["indoorOutdoorType"] == "semi_outdoor"
    assert spaces["living_room"]["minimumArea"] < spaces["living_room"]["preferredArea"]
    assert spaces["living_room"]["maximumArea"] > spaces["living_room"]["preferredArea"]


def test_program_validation_surfaces_all_anchor_constraint_families():
    _, validation, _ = _example_contract()
    checks = validation["constraintChecks"]

    def check(label_fragment: str) -> dict:
        return next(item for item in checks if label_fragment in item["label"])

    assert validation["summary"]["requestedSpaceCount"] == 14
    assert validation["summary"]["generatedSpaceCount"] == 14
    assert validation["missingSpaces"] == []

    assert check("Kitchen / Dining Room")["status"] == "satisfied"
    assert check("Kitchen / Laundry")["status"] == "satisfied"
    assert check("Balcony / Living Room")["status"] == "satisfied"
    assert check("Master Bedroom / Ensuite")["status"] == "satisfied"
    assert check("Bathroom / Kitchen")["status"] == "satisfied"
    assert check("Ensuite / Kitchen")["relationType"] == "adjacent"
    assert check("Master Bedroom / Foyer")["status"] == "satisfied"
    assert check("Exterior edge: Balcony")["status"] == "satisfied"
    assert check("Main entry on E / front side")["status"] == "satisfied"
    assert any(item["label"].startswith("Daylight access:") for item in checks)


def test_program_validation_reports_missing_and_generated_support_spaces():
    parsed = parse_prompt("house with a living room and kitchen")
    specs = parsed_to_room_specs(parsed)
    graph = from_parser_output(parsed, specs)
    layout = generate_layout(
        specs,
        prompt=parsed.raw_prompt,
        building_type=parsed.building_type,
        total_floors=1,
    )
    broken = deepcopy(layout)
    broken["rooms"] = [
        room
        for room in broken["rooms"]
        if room.get("roomType") != "kitchen"
    ]
    for floor in broken["floors"]:
        floor["rooms"] = [
            room
            for room in floor["rooms"]
            if room.get("roomType") != "kitchen"
        ]
    support = deepcopy(next(room for room in broken["rooms"] if room["objectType"] == "room"))
    support["id"] = "support-hallway"
    support["label"] = "Hallway"
    support["roomType"] = "hallway"
    broken["rooms"].append(support)
    broken["floors"][0]["rooms"].append(support)

    validation = validate_program(parsed, graph, broken)

    assert validation["missingSpaces"] == [
        {"normalizedType": "kitchen", "label": "kitchen", "count": 1}
    ]
    assert {
        "normalizedType": "hallway",
        "label": "Hallway",
        "count": 1,
        "kind": "generated_support",
    } in validation["extraSpaces"]
    assert validation["overallStatus"] == "failed"
