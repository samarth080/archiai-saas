"""
Sprint 15 — Layout Quality & Visual Improvements tests.

Covers:
- Multi-pass overlap repair (rooms must not overlap after _repair_rooms)
- Bounds enforcement (no room outside computed building footprint)
- Partition wall generation
- Quality scorer building-completeness check (100/100 should be rare)
- Quality scorer correctly penalises overlapping rooms
"""

import pytest

from app.services.layout_service import (
    _repair_rooms,
    _rooms_overlap,
    generate_layout,
)
from app.services.layout_quality_service import score_layout_quality
from app.services.prompt_service import RoomSpec


# ── helpers ───────────────────────────────────────────────────────────────────

def _room(room_type, x, z, w, d, floor=0):
    return {
        "id": f"{room_type}_{x}_{z}",
        "label": room_type.replace("_", " ").title(),
        "roomType": room_type,
        "objectType": "room",
        "floorId": f"floor_{floor}",
        "floorLevel": floor,
        "zone": "private",
        "position": {"x": x, "y": 1.5, "z": z},
        "size": {"w": w, "h": 3.0, "d": d},
        "color": "#f472b6",
    }


def _stair(x, z, floor=0):
    return {
        "id": f"stair_{floor}",
        "label": "Stairs",
        "roomType": "stairs",
        "objectType": "stair",
        "floorId": f"floor_{floor}",
        "floorLevel": floor,
        "zone": "circulation",
        "position": {"x": x, "y": 1.6, "z": z},
        "size": {"w": 2.0, "h": 3.2, "d": 3.0},
        "color": "#9ca3af",
    }


# ── overlap repair ────────────────────────────────────────────────────────────

class TestRepairRooms:
    def test_no_overlap_unchanged(self):
        rooms = [
            _room("living_room", 3.0, 3.0, 5.0, 4.0),
            _room("kitchen",     3.0, 9.0, 4.0, 3.5),
        ]
        repaired = _repair_rooms(rooms, building_type="apartment")
        assert not _rooms_overlap(repaired[0], repaired[1])

    def test_simple_z_overlap_resolved(self):
        """Two rooms sharing the same Z band must be separated after repair."""
        rooms = [
            _room("bedroom", 3.0, 2.0, 4.0, 4.0),
            _room("bathroom", 3.0, 2.5, 3.0, 3.0),  # clearly overlaps above
        ]
        repaired = _repair_rooms(rooms, building_type="apartment")
        assert not _rooms_overlap(repaired[0], repaired[1])

    def test_multiple_overlapping_rooms_all_resolved(self):
        """A chain of 4 overlapping rooms must all be de-overlapped."""
        rooms = [
            _room("r1", 3.0, 2.0, 4.0, 4.0),
            _room("r2", 3.0, 2.5, 4.0, 4.0),
            _room("r3", 3.0, 3.0, 4.0, 4.0),
            _room("r4", 3.0, 3.5, 4.0, 4.0),
        ]
        repaired = _repair_rooms(rooms, building_type="apartment")
        for i, a in enumerate(repaired):
            for b in repaired[i + 1:]:
                assert not _rooms_overlap(a, b), f"{a['roomType']} overlaps {b['roomType']}"

    def test_rooms_stay_non_negative_after_repair(self):
        rooms = [_room("entry", 0.5, 0.5, 2.0, 2.0)]
        repaired = _repair_rooms(rooms, building_type="apartment")
        for room in repaired:
            assert room["position"]["x"] >= room["size"]["w"] / 2
            assert room["position"]["z"] >= room["size"]["d"] / 2

    def test_different_floors_not_repaired_against_each_other(self):
        """Rooms on different floors may share X/Z — that is correct."""
        rooms = [
            _room("bedroom", 3.0, 3.0, 4.0, 4.0, floor=0),
            _room("bedroom", 3.0, 3.0, 4.0, 4.0, floor=1),
        ]
        repaired = _repair_rooms(rooms, building_type="apartment")
        # Same-X/Z positions are fine for different floors
        floor0 = next(r for r in repaired if r["floorLevel"] == 0)
        floor1 = next(r for r in repaired if r["floorLevel"] == 1)
        # _rooms_overlap already returns False for different floors, just confirm positions
        assert floor0["position"]["z"] == 3.0
        assert floor1["position"]["z"] == 3.0


# ── generate_layout produces no overlaps ─────────────────────────────────────

class TestGenerateLayoutNoOverlap:
    def _room_objects(self, layout):
        return [r for r in layout["rooms"] if r.get("objectType") == "room"]

    def _overlapping_pairs(self, rooms):
        pairs = []
        for i, a in enumerate(rooms):
            for b in rooms[i + 1:]:
                if _rooms_overlap(a, b):
                    pairs.append((a["label"], b["label"]))
        return pairs

    def test_single_floor_no_overlap(self):
        specs = [
            RoomSpec("Living Room", "living_room", 5.0, 3.0, 4.0),
            RoomSpec("Kitchen",     "kitchen",     4.0, 3.0, 3.5),
            RoomSpec("Bedroom 1",   "bedroom",     3.5, 3.0, 3.0),
            RoomSpec("Bedroom 2",   "bedroom",     3.5, 3.0, 3.0),
            RoomSpec("Bathroom",    "bathroom",    2.0, 3.0, 1.8),
        ]
        layout = generate_layout(specs, building_type="apartment", total_floors=1)
        rooms = self._room_objects(layout)
        assert self._overlapping_pairs(rooms) == []

    def test_two_floor_no_overlap(self):
        specs = [
            RoomSpec("Living Room",    "living_room",    5.0, 3.0, 4.0),
            RoomSpec("Kitchen",        "kitchen",        4.0, 3.0, 3.5),
            RoomSpec("Bedroom 1",      "bedroom",        3.5, 3.0, 3.0),
            RoomSpec("Bedroom 2",      "bedroom",        3.5, 3.0, 3.0),
            RoomSpec("Bedroom 3",      "bedroom",        3.5, 3.0, 3.0),
            RoomSpec("Bathroom 1",     "bathroom",       2.0, 3.0, 1.8),
            RoomSpec("Bathroom 2",     "bathroom",       2.0, 3.0, 1.8),
            RoomSpec("Master Bedroom", "master_bedroom", 4.5, 3.0, 3.5),
        ]
        layout = generate_layout(specs, building_type="house", total_floors=2)
        rooms = self._room_objects(layout)
        overlaps = self._overlapping_pairs(rooms)
        assert overlaps == [], f"Overlapping pairs found: {overlaps}"

    def test_five_bedroom_two_floor_no_overlap(self):
        """Regression test for the specific failure case in screenshot."""
        specs = [
            RoomSpec("Living Room",    "living_room",    5.0, 3.0, 4.0),
            RoomSpec("Kitchen",        "kitchen",        4.0, 3.0, 3.5),
            RoomSpec("Dining Room",    "dining_room",    4.0, 3.0, 3.5),
            RoomSpec("Bedroom 1",      "bedroom",        3.5, 3.0, 3.0),
            RoomSpec("Bedroom 2",      "bedroom",        3.5, 3.0, 3.0),
            RoomSpec("Bedroom 3",      "bedroom",        3.5, 3.0, 3.0),
            RoomSpec("Bedroom 4",      "bedroom",        3.5, 3.0, 3.0),
            RoomSpec("Bedroom 5",      "bedroom",        3.5, 3.0, 3.0),
            RoomSpec("Bathroom 1",     "bathroom",       2.0, 3.0, 1.8),
            RoomSpec("Bathroom 2",     "bathroom",       2.0, 3.0, 1.8),
            RoomSpec("Bathroom 3",     "bathroom",       2.0, 3.0, 1.8),
            RoomSpec("Bathroom 4",     "bathroom",       2.0, 3.0, 1.8),
            RoomSpec("Bathroom 5",     "bathroom",       2.0, 3.0, 1.8),
            RoomSpec("Master Bedroom", "master_bedroom", 4.5, 3.0, 3.5),
        ]
        layout = generate_layout(specs, building_type="house", total_floors=2)
        rooms = self._room_objects(layout)
        overlaps = self._overlapping_pairs(rooms)
        assert overlaps == [], f"Overlapping pairs on 5-bed 2-story: {overlaps}"


# ── partition walls ───────────────────────────────────────────────────────────

class TestPartitionWalls:
    def test_partition_walls_generated_for_single_floor(self):
        specs = [
            RoomSpec("Living Room", "living_room", 5.0, 3.0, 4.0),
            RoomSpec("Kitchen",     "kitchen",     4.0, 3.0, 3.5),
        ]
        layout = generate_layout(specs, building_type="apartment", total_floors=1)
        wall_objects = [r for r in layout["rooms"] if r.get("objectType") == "wall"]
        assert len(wall_objects) > 0, "No wall objects generated"

    def test_partition_walls_have_correct_object_type(self):
        specs = [RoomSpec("Bedroom", "bedroom", 3.5, 3.0, 3.0)]
        layout = generate_layout(specs, building_type="apartment", total_floors=1)
        walls = [r for r in layout["rooms"] if r.get("objectType") == "wall"]
        for wall in walls:
            assert "position" in wall
            assert "size" in wall
            assert wall["size"]["h"] > 0

    def test_multi_floor_has_walls_on_each_floor(self):
        specs = [
            RoomSpec("Living Room", "living_room", 5.0, 3.0, 4.0),
            RoomSpec("Kitchen",     "kitchen",     4.0, 3.0, 3.5),
            RoomSpec("Bedroom",     "bedroom",     3.5, 3.0, 3.0),
            RoomSpec("Bathroom",    "bathroom",    2.0, 3.0, 1.8),
        ]
        layout = generate_layout(specs, building_type="apartment", total_floors=2)
        floors = layout.get("floors", [])
        for floor in floors:
            floor_rooms = floor.get("rooms", [])
            floor_walls = [r for r in floor_rooms if r.get("objectType") == "wall"]
            assert len(floor_walls) > 0, f"Floor {floor['level']} has no walls"


# ── quality scoring ───────────────────────────────────────────────────────────

class TestQualityScoring:
    def _minimal_layout(self, room_types, building_type="apartment", floor_level=0):
        """Build a minimal valid layout dict from room_types list."""
        rooms = []
        x = 3.0
        for rt in room_types:
            rooms.append({
                "id": rt,
                "label": rt.replace("_", " ").title(),
                "roomType": rt,
                "objectType": "room",
                "floorId": "floor_0",
                "floorLevel": floor_level,
                "zone": "private",
                "position": {"x": x, "y": 1.5, "z": 3.0},
                "size": {"w": 3.0, "h": 3.0, "d": 3.0},
                "color": "#f472b6",
            })
            x += 3.6
        return {
            "version": "1.0",
            "metadata": {
                "buildingType": building_type,
                "template": building_type,
                "totalFloors": 1,
                "zonesDetected": ["private"],
            },
            "building": {
                "floorHeight": 3.2,
                "bounds": {"minX": 0.0, "maxX": 30.0, "minZ": 0.0, "maxZ": 20.0},
            },
            "floors": [{"id": "floor_0", "level": 0, "elevation": 0.0, "footprint": {"x": 0, "z": 0, "w": 30, "d": 20}, "rooms": rooms}],
            "rooms": rooms,
        }

    def test_overlapping_rooms_score_below_100(self):
        """Two rooms occupying the same position must reduce the score."""
        rooms = [
            {
                "id": "r1", "label": "Room 1", "roomType": "bedroom",
                "objectType": "room", "floorId": "floor_0", "floorLevel": 0,
                "zone": "private",
                "position": {"x": 5.0, "y": 1.5, "z": 5.0},
                "size": {"w": 4.0, "h": 3.0, "d": 4.0}, "color": "#f472b6",
            },
            {
                "id": "r2", "label": "Room 2", "roomType": "bathroom",
                "objectType": "room", "floorId": "floor_0", "floorLevel": 0,
                "zone": "service",
                "position": {"x": 5.0, "y": 1.5, "z": 5.0},  # same spot
                "size": {"w": 3.0, "h": 3.0, "d": 3.0}, "color": "#60a5fa",
            },
        ]
        layout = {
            "version": "1.0",
            "metadata": {"buildingType": "apartment", "template": "apartment", "totalFloors": 1, "zonesDetected": ["private", "service"]},
            "building": {"floorHeight": 3.2, "bounds": {"minX": 0.0, "maxX": 20.0, "minZ": 0.0, "maxZ": 20.0}},
            "floors": [{"id": "floor_0", "level": 0, "elevation": 0.0, "footprint": {"x": 0, "z": 0, "w": 20, "d": 20}, "rooms": rooms}],
            "rooms": rooms,
        }
        result = score_layout_quality(layout)
        assert result.score < 100, f"Expected <100 for overlapping rooms, got {result.score}"
        assert any("overlap" in w.lower() for w in result.warnings)

    def test_three_bhk_score_reflects_missing_expected_rooms(self):
        """A 3-bedroom apartment missing kitchen/dining should not score 100."""
        layout = generate_layout(
            [
                RoomSpec("Bedroom 1", "bedroom", 3.5, 3.0, 3.0),
                RoomSpec("Bedroom 2", "bedroom", 3.5, 3.0, 3.0),
                RoomSpec("Bedroom 3", "bedroom", 3.5, 3.0, 3.0),
            ],
            building_type="apartment",
            total_floors=1,
        )
        result = score_layout_quality(
            layout,
            required_room_types={"bedroom", "kitchen", "bathroom", "living_room"},
        )
        assert result.score < 100, f"Missing kitchen+living+bathroom should reduce score, got {result.score}"

    def test_complete_apartment_scores_high(self):
        """A properly complete apartment layout should score at least 70."""
        specs = [
            RoomSpec("Living Room", "living_room", 5.0, 3.0, 4.0),
            RoomSpec("Kitchen",     "kitchen",     4.0, 3.0, 3.5),
            RoomSpec("Bedroom",     "bedroom",     3.5, 3.0, 3.0),
            RoomSpec("Bathroom",    "bathroom",    2.0, 3.0, 1.8),
        ]
        layout = generate_layout(specs, building_type="apartment", total_floors=1)
        result = score_layout_quality(
            layout,
            required_room_types={s.room_type for s in specs},
        )
        assert result.score >= 70, f"Complete layout should score >=70, got {result.score}"

    def test_generated_3bhk_does_not_trivially_score_100(self):
        """
        Regression: 'a 3bhk flat' full pipeline should NOT score 100/100
        because the quality criteria should include realistic penalties.
        """
        from app.services.prompt_service import parse_prompt, parsed_to_room_specs
        parsed = parse_prompt("a 3bhk flat")
        specs = parsed_to_room_specs(parsed)
        layout = generate_layout(
            specs,
            building_type=parsed.building_type,
            total_floors=parsed.total_floors,
        )
        score = layout["insights"]["score"]
        # A 3bhk generated without a dining room should not score 100 — dining_room
        # is expected in any complete apartment layout.
        assert score < 100, f"3bhk flat trivially scored {score}/100 — scorer is too lenient"

    def test_building_completeness_penalises_no_bathroom_in_apartment(self):
        """An apartment with no bathroom should score below 90."""
        layout = self._minimal_layout(
            ["living_room", "kitchen", "bedroom", "dining_room"],
            building_type="apartment",
        )
        result = score_layout_quality(
            layout,
            required_room_types={"living_room", "kitchen", "bedroom", "dining_room", "bathroom"},
        )
        assert result.score < 90, f"Apartment without bathroom scored {result.score}"

    def test_quality_score_clamped_0_to_100(self):
        """Score must never exceed 100 or drop below 0."""
        specs = [RoomSpec("Bedroom", "bedroom", 3.5, 3.0, 3.0)]
        layout = generate_layout(specs)
        score = layout["insights"]["score"]
        assert 0 <= score <= 100
