"""
Sprint 15 — Tiled floor plan layout tests.

The tiled algorithm should:
- Produce rooms that share walls (no visible gaps)
- Fill the building width exactly (sum of room widths == building_width)
- Group rooms into front (public) / corridor / back (private) zone rows
- Generate a clean rectangular building footprint
- Keep multi-floor layouts aligned on the same building width
"""

import pytest

from app.services.layout_service import (
    _tile_rooms,
    _fill_row,
    generate_layout,
    _rooms_overlap,
    _TILED_BUILDING_TYPES,
)
from app.services.layout_pattern_service import fallback_layout_rules
from app.services.prompt_service import RoomSpec


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_specs(*room_types) -> list[RoomSpec]:
    defaults = {
        "living_room":    (5.0, 4.0),
        "kitchen":        (4.0, 3.5),
        "dining_room":    (4.0, 3.5),
        "bedroom":        (3.5, 3.0),
        "master_bedroom": (4.5, 3.5),
        "bathroom":       (2.0, 1.8),
        "hallway":        (6.0, 1.5),
        "entry":          (2.5, 2.0),
        "storage":        (2.0, 2.0),
    }
    specs = []
    count: dict[str, int] = {}
    for rt in room_types:
        count[rt] = count.get(rt, 0) + 1
        w, d = defaults.get(rt, (3.0, 3.0))
        label = rt.replace("_", " ").title()
        if count[rt] > 1:
            label = f"{label} {count[rt]}"
        specs.append(RoomSpec(label=label, room_type=rt, w=w, h=3.0, d=d))
    return specs


def _room_objects(layout: dict) -> list[dict]:
    return [r for r in layout["rooms"] if r.get("objectType") == "room"]


def _floor_rooms(layout: dict, level: int) -> list[dict]:
    floor = next(f for f in layout["floors"] if f["level"] == level)
    return [r for r in floor["rooms"] if r.get("objectType") == "room"]


# ── _fill_row: rooms fill exact width ────────────────────────────────────────

class TestFillRow:
    def _rules(self):
        return fallback_layout_rules("apartment", {"bedroom", "bathroom", "living_room"})

    def test_single_room_fills_width(self):
        specs = _make_specs("living_room")
        rules = self._rules()
        placed = _fill_row(specs, 0.0, 4.0, 10.0, floor_id="floor_0", floor_level=0, elevation=0.0, rules=rules)
        assert len(placed) == 1
        assert abs(placed[0]["size"]["w"] - 10.0) < 0.1

    def test_two_rooms_fill_width_exactly(self):
        specs = _make_specs("living_room", "kitchen")
        rules = self._rules()
        placed = _fill_row(specs, 0.0, 4.0, 12.0, floor_id="floor_0", floor_level=0, elevation=0.0, rules=rules)
        total = sum(r["size"]["w"] for r in placed)
        assert abs(total - 12.0) < 0.2, f"Width mismatch: {total} != 12.0"

    def test_rooms_touching_no_gap(self):
        specs = _make_specs("bedroom", "bedroom", "bathroom")
        rules = self._rules()
        placed = _fill_row(specs, 0.0, 3.5, 10.0, floor_id="floor_0", floor_level=0, elevation=0.0, rules=rules)
        # Sort by x to check adjacency
        placed.sort(key=lambda r: r["position"]["x"])
        for i in range(len(placed) - 1):
            right_edge_a = placed[i]["position"]["x"] + placed[i]["size"]["w"] / 2
            left_edge_b = placed[i + 1]["position"]["x"] - placed[i + 1]["size"]["w"] / 2
            gap = left_edge_b - right_edge_a
            assert gap < 0.05, f"Gap between rooms: {gap:.3f}m — rooms should share walls"

    def test_all_rooms_same_depth(self):
        specs = _make_specs("bedroom", "bedroom", "bathroom")
        rules = self._rules()
        placed = _fill_row(specs, 0.0, 3.5, 10.0, floor_id="floor_0", floor_level=0, elevation=0.0, rules=rules)
        depths = [r["size"]["d"] for r in placed]
        assert all(abs(d - 3.5) < 0.05 for d in depths), f"Depths should be uniform: {depths}"


# ── _tile_rooms: zone-row structure ──────────────────────────────────────────

class TestTileRooms:
    def _rules(self, building_type="apartment"):
        return fallback_layout_rules(building_type, set())

    def test_tiled_rooms_have_no_gaps(self):
        specs = _make_specs("living_room", "kitchen", "dining_room", "bedroom", "bedroom", "bathroom")
        rules = self._rules()
        placed, footprint = _tile_rooms(specs, rules, "apartment", "floor_0", 0, 0.0)
        rooms_only = [r for r in placed if r.get("objectType") == "room"]
        # No two rooms on the same floor should overlap
        for i, a in enumerate(rooms_only):
            for b in rooms_only[i + 1:]:
                assert not _rooms_overlap(a, b), f"{a['label']} overlaps {b['label']}"

    def test_public_rooms_at_lower_z_than_private(self):
        specs = _make_specs("living_room", "kitchen", "master_bedroom", "bedroom")
        rules = self._rules()
        placed, _ = _tile_rooms(specs, rules, "apartment", "floor_0", 0, 0.0)
        rooms_by_type = {r["roomType"]: r for r in placed if r.get("objectType") == "room"}
        if "living_room" in rooms_by_type and "master_bedroom" in rooms_by_type:
            living_z = rooms_by_type["living_room"]["position"]["z"]
            bedroom_z = rooms_by_type["master_bedroom"]["position"]["z"]
            assert living_z < bedroom_z, "Living room should be in front (lower z) of bedroom"

    def test_tiled_footprint_contains_all_rooms(self):
        specs = _make_specs("living_room", "kitchen", "bedroom", "bathroom")
        rules = self._rules()
        placed, footprint = _tile_rooms(specs, rules, "apartment", "floor_0", 0, 0.0)
        rooms_only = [r for r in placed if r.get("objectType") == "room"]
        for room in rooms_only:
            x1 = room["position"]["x"] - room["size"]["w"] / 2
            x2 = room["position"]["x"] + room["size"]["w"] / 2
            z1 = room["position"]["z"] - room["size"]["d"] / 2
            z2 = room["position"]["z"] + room["size"]["d"] / 2
            assert x1 >= footprint["x"] - 0.1, f"Room {room['label']} left edge outside footprint"
            assert x2 <= footprint["x"] + footprint["w"] + 0.1, f"Room {room['label']} right edge outside footprint"
            assert z1 >= footprint["z"] - 0.1, f"Room {room['label']} front edge outside footprint"
            assert z2 <= footprint["z"] + footprint["d"] + 0.1, f"Room {room['label']} rear edge outside footprint"

    def test_target_width_is_respected(self):
        specs = _make_specs("living_room", "kitchen", "bedroom")
        rules = self._rules()
        placed, footprint = _tile_rooms(specs, rules, "apartment", "floor_0", 0, 0.0, target_width=12.0)
        assert abs(footprint["w"] - 12.0) < 0.2, f"Footprint width {footprint['w']} should be ~12.0"

    def test_empty_specs_returns_empty(self):
        rules = self._rules()
        placed, footprint = _tile_rooms([], rules, "apartment", "floor_0", 0, 0.0)
        assert placed == []
        assert footprint["w"] == 0.0


# ── generate_layout uses tiler for residential ────────────────────────────────

class TestGenerateLayoutTiled:
    def _room_objects(self, layout):
        return [r for r in layout["rooms"] if r.get("objectType") == "room"]

    def test_apartment_uses_tiled_layout(self):
        specs = _make_specs("living_room", "kitchen", "bedroom", "bedroom", "bathroom")
        layout = generate_layout(specs, building_type="apartment", total_floors=1)
        rooms = self._room_objects(layout)
        # All rooms should share walls (max gap between adjacent rooms < 0.1m)
        rooms.sort(key=lambda r: r["position"]["x"])
        for i in range(len(rooms) - 1):
            a, b = rooms[i], rooms[i + 1]
            if abs(a["position"]["z"] - b["position"]["z"]) < 0.5:
                right_a = a["position"]["x"] + a["size"]["w"] / 2
                left_b = b["position"]["x"] - b["size"]["w"] / 2
                gap = left_b - right_a
                assert gap < 0.2, f"Gap between {a['label']} and {b['label']}: {gap:.2f}m"

    def test_two_floor_apartment_same_width_both_floors(self):
        """All floors of a multi-storey tiled layout must have the same building width."""
        specs = _make_specs(
            "living_room", "kitchen", "dining_room",
            "master_bedroom", "bedroom", "bedroom",
            "bathroom", "bathroom",
        )
        layout = generate_layout(specs, building_type="apartment", total_floors=2)
        floor_widths = [f["footprint"]["w"] for f in layout["floors"] if f["footprint"]["w"] > 0]
        assert len(floor_widths) == 2
        assert abs(floor_widths[0] - floor_widths[1]) < 0.5, (
            f"Floor widths differ: {floor_widths} — multi-floor should align"
        )

    def test_house_uses_tiled_layout(self):
        assert "house" in _TILED_BUILDING_TYPES

    def test_commercial_types_use_tiled_layout(self):
        """Sprint 16: commercial types now tile too, so they fill their footprint."""
        from app.services.layout_service import _TILED_BUILDING_TYPES as _TBT
        assert {"office", "clinic", "restaurant", "retail", "classroom"}.issubset(_TBT)

    def test_tiled_layout_has_no_overlapping_rooms(self):
        specs = _make_specs(
            "living_room", "kitchen", "dining_room",
            "master_bedroom", "bedroom", "bedroom", "bedroom",
            "bathroom", "bathroom", "bathroom",
        )
        layout = generate_layout(specs, building_type="house", total_floors=2)
        rooms = self._room_objects(layout)
        for i, a in enumerate(rooms):
            for b in rooms[i + 1:]:
                assert not _rooms_overlap(a, b), f"Overlap: {a['label']} / {b['label']}"

    def test_3bhk_flat_prompt_quality_not_trivially_100(self):
        from app.services.prompt_service import parse_prompt, parsed_to_room_specs
        parsed = parse_prompt("a 3bhk flat")
        specs = parsed_to_room_specs(parsed)
        layout = generate_layout(specs, building_type=parsed.building_type, total_floors=parsed.total_floors)
        score = layout["insights"]["score"]
        assert score < 100, f"3bhk trivially scored {score}/100"
