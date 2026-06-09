"""End-to-end tests for the 6-stage parse_prompt pipeline."""

from app.services.prompt_service import ParsedRequirements, parse_prompt, parsed_to_room_specs


# ── building type and floor inference ─────────────────────────────────────────

def test_family_home_detected():
    result = parse_prompt("3 bedroom family home")
    assert result.building_type == "family_home"
    assert result.total_floors == 1


def test_two_storey_home_floors():
    result = parse_prompt("two storey house")
    assert result.total_floors == 2


def test_explicit_floor_count_wins():
    result = parse_prompt("apartment with 3 floors")
    assert result.total_floors == 3


def test_bhk_apartment():
    result = parse_prompt("3bhk apartment")
    assert result.building_type == "apartment"
    bedroom_count = sum(r.count for r in result.rooms if r.room_type == "bedroom")
    assert bedroom_count == 3


# ── rooms produced ────────────────────────────────────────────────────────────

def test_rooms_have_positive_dimensions():
    result = parse_prompt("2 bedroom apartment with kitchen")
    for room in result.rooms:
        assert room.width > 0, room.room_type
        assert room.depth > 0, room.room_type
        assert room.area_m2 > 0, room.room_type


def test_rooms_have_zone_assigned():
    result = parse_prompt("3 bedroom family home")
    for room in result.rooms:
        assert room.zone in ("public", "private", "service", "other"), room.room_type


# ── exclusions ────────────────────────────────────────────────────────────────

def test_exclusion_removes_room_from_list():
    result = parse_prompt("family home with no garage")
    assert all(r.room_type != "garage" for r in result.rooms)
    assert "garage" in result.exclusions


def test_exclusion_dont_want():
    result = parse_prompt("apartment, don't want a balcony")
    assert all(r.room_type != "balcony" for r in result.rooms)


# ── adjacency constraints ─────────────────────────────────────────────────────

def test_master_bedroom_with_ensuite_adjacency():
    result = parse_prompt("master bedroom with ensuite")
    pairs = {frozenset({c.room_a, c.room_b}) for c in result.adjacency_constraints}
    assert frozenset({"master_bedroom", "ensuite"}) in pairs


def test_next_to_adjacency():
    result = parse_prompt("kitchen next to the dining room")
    pairs = {frozenset({c.room_a, c.room_b}) for c in result.adjacency_constraints}
    assert frozenset({"kitchen", "dining_room"}) in pairs


# ── zone assignments ──────────────────────────────────────────────────────────

def test_bedrooms_upstairs_zone_assignment():
    result = parse_prompt("two storey house with bedrooms upstairs")
    assert result.zone_assignments.get("bedroom") == "upper"


def test_floor_preference_propagated_to_room_requirement():
    result = parse_prompt("two storey house with bedrooms upstairs")
    bedroom_rooms = [r for r in result.rooms if r.room_type == "bedroom"]
    assert all(r.floor_preference == "upper" for r in bedroom_rooms)


# ── parsed_to_room_specs expansion ───────────────────────────────────────────

def test_room_specs_expand_count():
    result = parse_prompt("3 bedroom apartment")
    specs = parsed_to_room_specs(result)
    bedroom_specs = [s for s in specs if s.room_type == "bedroom"]
    assert len(bedroom_specs) == 3


def test_room_specs_label_numbered_for_multiples():
    result = parse_prompt("2 bedroom apartment")
    specs = parsed_to_room_specs(result)
    bedroom_specs = [s for s in specs if s.room_type == "bedroom"]
    labels = {s.label for s in bedroom_specs}
    assert "Bedroom 1" in labels
    assert "Bedroom 2" in labels


def test_room_specs_dimensions_from_size_resolver():
    result = parse_prompt("apartment")
    specs = parsed_to_room_specs(result)
    for spec in specs:
        assert spec.w > 0
        assert spec.d > 0


# ── confidence score ──────────────────────────────────────────────────────────

def test_confidence_is_float_between_0_and_1():
    result = parse_prompt("modern 3 bedroom apartment with open plan kitchen")
    assert 0.0 <= result.confidence <= 1.0


# ── gist acceptance criteria ─────────────────────────────────────────────────

def test_gist_full_prompt():
    result = parse_prompt(
        "3 bedroom family home, modern, open plan kitchen-dining, master with ensuite, no garage"
    )
    assert result.building_type == "family_home"
    assert result.total_floors == 1
    assert "garage" in result.exclusions
    pairs = {frozenset({c.room_a, c.room_b}) for c in result.adjacency_constraints}
    assert frozenset({"master_bedroom", "ensuite"}) in pairs
