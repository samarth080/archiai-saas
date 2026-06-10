"""Tests for the Vastu compliance module (Stage 9)."""

import pytest

from app.services.parser.vastu import (
    VastuResult,
    add_vastu_special_rooms,
    check_vastu_compliance,
    get_vastu_direction,
    is_vastu_requested,
)
from app.services.prompt_service import parse_prompt


# ── trigger detection ─────────────────────────────────────────────────────────

def test_vastu_keyword_detected():
    assert is_vastu_requested("3bhk vastu compliant home") is True


def test_vaastu_variant_detected():
    assert is_vastu_requested("vaastu house") is True


def test_no_vastu_keyword():
    assert is_vastu_requested("modern apartment") is False


def test_vastu_not_triggered_on_unrelated_text():
    assert is_vastu_requested("vast open living space") is False


# ── direction mapping (Three.js coordinate space) ─────────────────────────────

def test_east_direction():
    assert get_vastu_direction({"x": 5, "z": 0}, {"x": 0, "z": 0}) == "east"


def test_north_direction():
    assert get_vastu_direction({"x": 0, "z": -5}, {"x": 0, "z": 0}) == "north"


def test_south_direction():
    assert get_vastu_direction({"x": 0, "z": 5}, {"x": 0, "z": 0}) == "south"


def test_west_direction():
    assert get_vastu_direction({"x": -5, "z": 0}, {"x": 0, "z": 0}) == "west"


def test_southeast_direction():
    assert get_vastu_direction({"x": 5, "z": 5}, {"x": 0, "z": 0}) == "southeast"


def test_northeast_direction():
    assert get_vastu_direction({"x": 5, "z": -5}, {"x": 0, "z": 0}) == "northeast"


# ── compliance check ─────────────────────────────────────────────────────────

def _make_room(room_type: str, x: float, z: float) -> dict:
    return {
        "roomType": room_type,
        "objectType": "room",
        "position": {"x": x, "z": z},
        "size": {"w": 3.0, "d": 3.0},
    }


_BOUNDS = {"minX": -10.0, "maxX": 10.0, "minZ": -10.0, "maxZ": 10.0}


def test_kitchen_in_southeast_no_violation():
    # SE is the correct direction for kitchen
    rooms = [_make_room("kitchen", 7, 7)]  # +x, +z → southeast
    result = check_vastu_compliance(rooms, _BOUNDS)
    kitchen_violations = [v for v in result.violations if v.room_type == "kitchen"]
    assert kitchen_violations == []


def test_kitchen_in_northeast_is_critical_violation():
    # NE is forbidden for kitchen
    rooms = [_make_room("kitchen", 7, -7)]  # +x, -z → northeast
    result = check_vastu_compliance(rooms, _BOUNDS)
    violations = [v for v in result.violations if v.room_type == "kitchen"]
    assert len(violations) == 1
    assert violations[0].severity == "critical"


def test_compliance_score_reduced_by_violations():
    # Kitchen in NE (forbidden) should lower score below 1.0
    rooms = [_make_room("kitchen", 7, -7)]
    result = check_vastu_compliance(rooms, _BOUNDS)
    assert result.compliance_score < 1.0


def test_no_violations_score_is_1():
    # Empty room list → no violations
    result = check_vastu_compliance([], _BOUNDS)
    assert result.compliance_score == 1.0
    assert result.violations == []


def test_brahmasthan_clear_when_no_central_room():
    rooms = [_make_room("bedroom", 8, 8)]  # far from centre
    result = check_vastu_compliance(rooms, _BOUNDS)
    assert result.brahmasthan_clear is True


def test_non_room_objects_ignored():
    walls = [{"roomType": "wall", "objectType": "wall", "position": {"x": 5, "z": -5}}]
    result = check_vastu_compliance(walls, _BOUNDS)
    assert result.violations == []


def test_compliance_score_clamped_to_zero():
    # Many violations shouldn't go below 0
    many_violations = [
        _make_room("kitchen", 7, -7),    # NE — critical
        _make_room("bathroom", 7, -7),   # NE — critical
        _make_room("staircase", 7, -7),  # NE — critical
        _make_room("garage", 7, -7),     # NE — critical
        _make_room("master_bedroom", 7, 7),  # SE — moderate
    ]
    result = check_vastu_compliance(many_violations, _BOUNDS)
    assert result.compliance_score >= 0.0


# ── special rooms added when Vastu requested ─────────────────────────────────

def test_pooja_room_added_when_vastu_requested():
    result = parse_prompt("3bhk vastu compliant home")
    assert result.vastu_requested is True
    assert any(r.room_type == "pooja_room" for r in result.rooms)


def test_pooja_room_not_added_without_vastu():
    result = parse_prompt("3bhk apartment")
    assert result.vastu_requested is False
    assert all(r.room_type != "pooja_room" for r in result.rooms)


def test_pooja_room_not_duplicated_if_already_present():
    from app.services.prompt_service import RoomRequirement
    from app.services.parser.size_resolver import resolve_size

    dims = resolve_size("pooja_room", "small")
    existing = [
        RoomRequirement("bedroom", 2, 12.0, 3.2, 3.8),
        RoomRequirement("pooja_room", 1, dims["area_m2"], dims["width"], dims["depth"]),
    ]
    result = add_vastu_special_rooms(existing, "vastu home")
    pooja_count = sum(1 for r in result if r.room_type == "pooja_room")
    assert pooja_count == 1


# ── generate_layout vastu metadata ───────────────────────────────────────────

def test_generate_layout_includes_vastu_metadata_when_requested():
    from app.services.layout_service import generate_layout
    from app.services.prompt_service import RoomSpec

    specs = [
        RoomSpec("Kitchen", "kitchen", 3.7, 3.0, 5.9),
        RoomSpec("Bedroom", "bedroom", 3.5, 3.0, 4.2),
        RoomSpec("Bathroom", "bathroom", 2.1, 3.0, 2.5),
    ]
    layout = generate_layout(specs, building_type="apartment", vastu_requested=True)
    assert "vastu" in layout["metadata"]
    assert layout["metadata"]["vastu"]["is_requested"] is True
    assert "compliance_score" in layout["metadata"]["vastu"]
    assert "violations" in layout["metadata"]["vastu"]


def test_generate_layout_no_vastu_metadata_when_not_requested():
    from app.services.layout_service import generate_layout
    from app.services.prompt_service import RoomSpec

    specs = [RoomSpec("Bedroom", "bedroom", 3.5, 3.0, 4.2)]
    layout = generate_layout(specs, building_type="apartment", vastu_requested=False)
    assert "vastu" not in layout["metadata"]
