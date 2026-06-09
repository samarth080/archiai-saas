from app.services.parser.constraint_extractor import (
    AdjacencyConstraint,
    Constraints,
    extract_constraints,
)


# ── helpers ────────────────────────────────────────────────────────────────────

def _adj_pair(c: Constraints) -> set[frozenset]:
    return {frozenset({a.room_a, a.room_b}) for a in c.adjacency}


def _strength(c: Constraints, a: str, b: str) -> str | None:
    key = frozenset({a, b})
    match = next((x for x in c.adjacency if frozenset({x.room_a, x.room_b}) == key), None)
    return match.strength if match else None


# ── exclusion tests ────────────────────────────────────────────────────────────

def test_no_keyword_excludes_room():
    c = extract_constraints("family home with no garage")
    assert "garage" in c.exclusions


def test_without_keyword_excludes_room():
    c = extract_constraints("apartment without a balcony")
    assert "balcony" in c.exclusions


def test_dont_want_excludes_room():
    c = extract_constraints("house, don't want a garage")
    assert "garage" in c.exclusions


def test_dont_need_excludes_room():
    c = extract_constraints("flat, don't need a laundry")
    assert "laundry" in c.exclusions


def test_no_exclusions_when_absent():
    c = extract_constraints("3 bedroom house")
    assert c.exclusions == []


def test_exclusion_deduplicated():
    c = extract_constraints("no garage, without a garage")
    assert c.exclusions.count("garage") == 1


# ── explicit adjacency tests ──────────────────────────────────────────────────

def test_next_to_produces_must_constraint():
    c = extract_constraints("kitchen next to the dining room")
    assert frozenset({"kitchen", "dining_room"}) in _adj_pair(c)
    assert _strength(c, "kitchen", "dining_room") == "MUST"


def test_beside_produces_must_constraint():
    c = extract_constraints("office beside the meeting room")
    assert frozenset({"office", "meeting_room"}) in _adj_pair(c)


def test_adjacent_to_produces_must_constraint():
    c = extract_constraints("bathroom adjacent to the master bedroom")
    assert frozenset({"bathroom", "master_bedroom"}) in _adj_pair(c)
    assert _strength(c, "bathroom", "master_bedroom") == "MUST"


def test_with_ensuite_produces_must_adjacency():
    c = extract_constraints("master bedroom with ensuite")
    assert frozenset({"master_bedroom", "ensuite"}) in _adj_pair(c)
    assert _strength(c, "master_bedroom", "ensuite") == "MUST"


def test_near_produces_should_constraint():
    c = extract_constraints("kitchen near the laundry")
    assert frozenset({"kitchen", "laundry"}) in _adj_pair(c)
    assert _strength(c, "kitchen", "laundry") == "SHOULD"


def test_close_to_produces_should_constraint():
    c = extract_constraints("office close to the meeting room")
    assert frozenset({"office", "meeting_room"}) in _adj_pair(c)
    assert _strength(c, "office", "meeting_room") == "SHOULD"


def test_duplicate_constraint_not_added_twice():
    c = extract_constraints("kitchen next to dining room, kitchen beside the dining room")
    pairs = [a for a in c.adjacency if frozenset({a.room_a, a.room_b}) == frozenset({"kitchen", "dining_room"})]
    assert len(pairs) == 1


def test_no_self_adjacency():
    c = extract_constraints("bedroom next to bedroom")
    self_pairs = [a for a in c.adjacency if a.room_a == a.room_b]
    assert self_pairs == []


# ── implicit adjacency tests ──────────────────────────────────────────────────

def test_implicit_adjacency_added_when_both_rooms_present():
    c = extract_constraints("house", present_room_types={"master_bedroom", "ensuite"})
    assert frozenset({"master_bedroom", "ensuite"}) in _adj_pair(c)


def test_implicit_adjacency_strength_is_should():
    c = extract_constraints("house", present_room_types={"master_bedroom", "ensuite"})
    assert _strength(c, "master_bedroom", "ensuite") == "SHOULD"


def test_implicit_adjacency_not_added_when_room_missing():
    c = extract_constraints("house", present_room_types={"kitchen"})
    assert frozenset({"kitchen", "dining_room"}) not in _adj_pair(c)


def test_implicit_adjacency_skipped_without_present_rooms_arg():
    c = extract_constraints("a normal house")
    assert c.adjacency == []


def test_explicit_must_beats_implicit_should_no_duplicate():
    c = extract_constraints(
        "kitchen next to dining room",
        present_room_types={"kitchen", "dining_room"},
    )
    pairs = [a for a in c.adjacency if frozenset({a.room_a, a.room_b}) == frozenset({"kitchen", "dining_room"})]
    assert len(pairs) == 1
    assert pairs[0].strength == "MUST"


def test_multiple_implicit_pairs_added():
    c = extract_constraints(
        "house",
        present_room_types={"master_bedroom", "ensuite", "kitchen", "dining_room", "foyer", "living_room"},
    )
    pairs = _adj_pair(c)
    assert frozenset({"master_bedroom", "ensuite"}) in pairs
    assert frozenset({"kitchen", "dining_room"}) in pairs
    assert frozenset({"foyer", "living_room"}) in pairs


# ── zone assignment tests ────────────────────────────────────────────────────

def test_upstairs_assigns_upper_zone():
    c = extract_constraints("bedrooms upstairs")
    assert c.zone_assignments.get("bedroom") == "upper"


def test_on_first_floor_assigns_upper_zone():
    c = extract_constraints("bedrooms on the first floor")
    assert c.zone_assignments.get("bedroom") == "upper"


def test_downstairs_assigns_ground_zone():
    c = extract_constraints("kitchen downstairs")
    assert c.zone_assignments.get("kitchen") == "ground"


def test_on_ground_floor_assigns_ground_zone():
    c = extract_constraints("living room on the ground floor")
    assert c.zone_assignments.get("living_room") == "ground"


def test_basement_zone_assignment():
    c = extract_constraints("storage in the basement")
    assert c.zone_assignments.get("storage") == "basement"


def test_no_zone_assignments_when_absent():
    c = extract_constraints("3 bedroom house with kitchen")
    assert c.zone_assignments == {}


# ── combined / acceptance tests ───────────────────────────────────────────────

def test_full_constraint_extraction():
    prompt = "3 bedroom family home, master bedroom with ensuite, no garage, bedrooms upstairs"
    c = extract_constraints(
        prompt,
        present_room_types={"master_bedroom", "ensuite", "bedroom", "kitchen", "living_room"},
    )
    assert "garage" in c.exclusions
    assert frozenset({"master_bedroom", "ensuite"}) in _adj_pair(c)
    assert c.zone_assignments.get("bedroom") == "upper"


def test_gist_exclusion_example():
    c = extract_constraints("family home with no garage")
    assert "garage" in c.exclusions


def test_gist_adjacency_example():
    c = extract_constraints("kitchen next to the dining room")
    assert any(
        a.room_a == "kitchen" and a.room_b == "dining_room"
        or a.room_a == "dining_room" and a.room_b == "kitchen"
        for a in c.adjacency
    )
