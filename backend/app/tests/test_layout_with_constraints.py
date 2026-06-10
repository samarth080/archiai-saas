"""Tests for constraint-aware layout generation (Stage 8)."""

from app.services.layout_service import _assign_rooms_to_floors, _sort_by_adjacency, generate_layout
from app.services.parser.constraint_extractor import AdjacencyConstraint
from app.services.prompt_service import RoomSpec


def _spec(room_type: str, w: float = 4.0, d: float = 4.0) -> RoomSpec:
    return RoomSpec(label=room_type.replace("_", " ").title(), room_type=room_type, w=w, h=3.0, d=d)


# ── _sort_by_adjacency ────────────────────────────────────────────────────────

def test_sort_by_adjacency_clusters_must_pair():
    rooms = [_spec("kitchen"), _spec("bathroom"), _spec("dining_room")]
    must = {frozenset({"kitchen", "dining_room"})}
    result = _sort_by_adjacency(rooms, must)
    types = [r.room_type for r in result]
    kitchen_idx = types.index("kitchen")
    dining_idx = types.index("dining_room")
    assert abs(kitchen_idx - dining_idx) == 1


def test_sort_by_adjacency_preserves_all_rooms():
    rooms = [_spec("kitchen"), _spec("bedroom"), _spec("bathroom")]
    result = _sort_by_adjacency(rooms, {frozenset({"kitchen", "bedroom"})})
    assert len(result) == 3
    assert {r.room_type for r in result} == {"kitchen", "bedroom", "bathroom"}


def test_sort_by_adjacency_no_pairs_unchanged_length():
    rooms = [_spec("living_room"), _spec("kitchen"), _spec("bedroom")]
    result = _sort_by_adjacency(rooms, set())
    assert len(result) == 3


# ── _assign_rooms_to_floors with zone_assignments ─────────────────────────────

def test_zone_assignment_ground_overrides_default():
    specs = [_spec("master_bedroom"), _spec("bedroom")]
    floors = _assign_rooms_to_floors(specs, 2, zone_assignments={"master_bedroom": "ground"})
    ground_types = {r.room_type for r in floors[0]}
    assert "master_bedroom" in ground_types


def test_zone_assignment_upper_overrides_default():
    specs = [_spec("kitchen"), _spec("living_room")]
    floors = _assign_rooms_to_floors(specs, 2, zone_assignments={"kitchen": "upper"})
    upper_types = {r.room_type for r in floors[1]}
    assert "kitchen" in upper_types


def test_zone_assignment_none_uses_default_logic():
    specs = [_spec("living_room"), _spec("bedroom")]
    floors = _assign_rooms_to_floors(specs, 2, zone_assignments=None)
    ground_types = {r.room_type for r in floors[0]}
    upper_types = {r.room_type for r in floors[1]}
    assert "living_room" in ground_types
    assert "bedroom" in upper_types or "master_bedroom" in upper_types


# ── generate_layout with adjacency_constraints + zone_assignments ─────────────

def test_generate_layout_accepts_adjacency_constraints():
    specs = [_spec("kitchen"), _spec("dining_room"), _spec("bedroom")]
    constraints = [AdjacencyConstraint("kitchen", "dining_room", "MUST")]
    layout = generate_layout(
        specs,
        building_type="apartment",
        adjacency_constraints=constraints,
    )
    assert layout["metadata"]["totalRooms"] == 3


def test_generate_layout_accepts_zone_assignments():
    specs = [_spec("bedroom"), _spec("living_room"), _spec("kitchen")]
    layout = generate_layout(
        specs,
        building_type="apartment",
        total_floors=2,
        zone_assignments={"bedroom": "upper"},
    )
    upper_rooms = [
        r for floor in layout["floors"]
        if floor["level"] == 1
        for r in floor["rooms"]
        if r.get("objectType") == "room"
    ]
    assert any(r["roomType"] == "bedroom" for r in upper_rooms)


def test_generate_layout_no_constraints_unchanged_behavior():
    specs = [_spec("living_room"), _spec("kitchen"), _spec("bedroom")]
    layout = generate_layout(specs, building_type="apartment")
    assert layout["metadata"]["totalRooms"] == 3
    assert len(layout["floors"]) == 1
