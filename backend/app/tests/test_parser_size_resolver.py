import math

import pytest

from app.services.parser.size_resolver import resolve_size


def test_master_bedroom_large_area():
    # 20.0 base × 1.3 large multiplier = 26.0
    room = resolve_size("master_bedroom", "large", 1.0, None)
    assert room["area_m2"] == pytest.approx(26.0, rel=0.02)


def test_medium_uses_base_size():
    room = resolve_size("bedroom", "medium", 1.0, None)
    assert room["area_m2"] == 12.0


def test_small_multiplier():
    room = resolve_size("bathroom", "small", 1.0, None)
    assert room["area_m2"] == pytest.approx(6.0 * 0.75, rel=0.02)


def test_xlarge_multiplier():
    room = resolve_size("living_room", "xlarge", 1.0, None)
    assert room["area_m2"] == pytest.approx(24.0 * 1.8, rel=0.02)


def test_size_modifier_scales_area():
    base = resolve_size("kitchen", "medium", 1.0, None)
    scaled = resolve_size("kitchen", "medium", 1.4, None)
    assert scaled["area_m2"] == pytest.approx(base["area_m2"] * 1.4, rel=0.02)


def test_occupancy_overrides_size_key():
    room = resolve_size("dining_room", "small", 1.0, occupancy_m2=30.0)
    assert room["area_m2"] == 30.0


def test_width_depth_product_approximates_area():
    for room_type in ("living_room", "bedroom", "kitchen", "bathroom", "office"):
        room = resolve_size(room_type, "medium", 1.0, None)
        product = room["width"] * room["depth"]
        assert product == pytest.approx(room["area_m2"], rel=0.05), room_type


def test_long_room_has_larger_depth_ratio():
    kitchen = resolve_size("kitchen", "medium", 1.0, None)
    bedroom = resolve_size("bedroom", "medium", 1.0, None)
    assert kitchen["depth"] / kitchen["width"] > bedroom["depth"] / bedroom["width"]


def test_unknown_room_type_uses_default():
    room = resolve_size("mystery_room", "medium", 1.0, None)
    assert room["area_m2"] == 12.0


def test_all_dimensions_positive():
    room = resolve_size("ensuite", "small", 1.0, None)
    assert room["width"] > 0
    assert room["depth"] > 0
    assert room["area_m2"] > 0
