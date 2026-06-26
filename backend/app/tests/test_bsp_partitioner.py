"""
Sprint 17 Phase 2 — BSP space partitioner.

_bsp_partition_rect generalises _fill_row's 1D (width-only) proportional
split into a true 2D recursive space partition: it can cut a rectangle
along either axis, so rooms in the same band can end up with different
depths as well as different widths. It competes with the plain tiler as
an alternate full-layout candidate (placement_style="bsp" vs "tile") and
the higher-scoring one wins — it never makes a generated layout worse.
"""
import pytest
from httpx import AsyncClient

from app.services.layout_service import (
    _bsp_partition_rect,
    _build_layout_candidate,
    apply_template_defaults,
    generate_layout,
    get_building_template,
)
from app.services.layout_pattern_service import fallback_layout_rules
from app.services.prompt_service import RoomSpec, detect_building_type, extract_rooms, extract_total_floors


def test_bsp_fully_tiles_its_rectangle_with_no_gaps_or_overlaps():
    specs = [
        RoomSpec("Bedroom 1", "bedroom", 4.0, 3.0, 4.0),
        RoomSpec("Bedroom 2", "bedroom", 4.0, 3.0, 4.0),
        RoomSpec("Bathroom", "bathroom", 2.0, 3.0, 2.0),
        RoomSpec("Storage", "storage", 2.0, 3.0, 2.0),
    ]
    rules = fallback_layout_rules("apartment", {"bedroom", "bathroom", "storage"})
    rooms = _bsp_partition_rect(specs, 0.0, 0.0, 9.0, 6.0, floor_id="floor_0", floor_level=0, elevation=0.0, rules=rules)

    assert len(rooms) == len(specs)
    total_area = sum(r["size"]["w"] * r["size"]["d"] for r in rooms)
    assert total_area == pytest.approx(9.0 * 6.0, abs=0.5)

    for i, a in enumerate(rooms):
        ax1, ax2 = a["position"]["x"] - a["size"]["w"] / 2, a["position"]["x"] + a["size"]["w"] / 2
        az1, az2 = a["position"]["z"] - a["size"]["d"] / 2, a["position"]["z"] + a["size"]["d"] / 2
        for b in rooms[i + 1:]:
            bx1, bx2 = b["position"]["x"] - b["size"]["w"] / 2, b["position"]["x"] + b["size"]["w"] / 2
            bz1, bz2 = b["position"]["z"] - b["size"]["d"] / 2, b["position"]["z"] + b["size"]["d"] / 2
            overlap = ax1 + 0.02 < bx2 and ax2 - 0.02 > bx1 and az1 + 0.02 < bz2 and az2 - 0.02 > bz1
            assert not overlap, f"{a['label']} overlaps {b['label']}"


def test_bsp_gives_rooms_different_depths_when_areas_are_heterogeneous():
    """
    A plain row-fill (_fill_row) forces every room in a band to the SAME
    depth. With one big room and one small room sharing a narrow band, BSP
    should switch to a depth-axis cut so the small room doesn't inherit an
    oversized depth it doesn't need.
    """
    specs = [
        RoomSpec("Bedroom 1", "bedroom", 4.0, 3.0, 4.0),
        RoomSpec("Bedroom 2", "bedroom", 4.0, 3.0, 4.0),
        RoomSpec("Bathroom", "bathroom", 2.0, 3.0, 2.0),
    ]
    rules = fallback_layout_rules("apartment", {"bedroom", "bathroom"})
    rooms = _bsp_partition_rect(specs, 0.0, 0.0, 7.0, 6.0, floor_id="floor_0", floor_level=0, elevation=0.0, rules=rules)

    depths = {r["label"]: r["size"]["d"] for r in rooms}
    assert len(set(depths.values())) > 1, f"expected varied depths, got {depths}"


def test_bsp_handles_single_room_and_empty_list():
    rules = fallback_layout_rules("apartment", {"bedroom"})
    single = _bsp_partition_rect(
        [RoomSpec("Bedroom", "bedroom", 4.0, 3.0, 4.0)], 0.0, 0.0, 5.0, 5.0,
        floor_id="floor_0", floor_level=0, elevation=0.0, rules=rules,
    )
    assert len(single) == 1
    assert single[0]["size"] == {"w": 5.0, "h": 3.0, "d": 5.0}

    empty = _bsp_partition_rect([], 0.0, 0.0, 5.0, 5.0, floor_id="floor_0", floor_level=0, elevation=0.0, rules=rules)
    assert empty == []


def _generate(prompt: str) -> dict:
    return generate_layout(
        extract_rooms(prompt),
        prompt=prompt,
        building_type=detect_building_type(prompt),
        total_floors=extract_total_floors(prompt),
    )


def test_tiled_building_types_produce_two_competing_candidates():
    layout = _generate("apartment with living room, kitchen, dining room and bathroom")

    assert layout["metadata"]["candidateCount"] == 2
    assert layout["metadata"]["placementEngine"] in ("tile", "bsp")


def test_row_band_fallback_types_are_unaffected_by_bsp():
    """Building types outside _TILED_BUILDING_TYPES never run BSP at all."""
    specs = [RoomSpec("Generic Room", "unknown_type", 4.0, 3.0, 4.0)]
    candidate = _build_layout_candidate(
        room_specs=specs,
        prompt="",
        building_type="totally_unrecognised_type",
        total_floors=1,
        pattern_rules=fallback_layout_rules("totally_unrecognised_type", {"unknown_type"}),
        total_area_sqm=None,
        template=get_building_template("totally_unrecognised_type"),
        x_offset=0.0,
        placement_style="bsp",
    )
    assert candidate["metadata"]["placementEngine"] == "row"


def test_winning_engine_never_scores_lower_than_the_tile_only_baseline():
    prompts = [
        "3 bedroom apartment with living room, kitchen, dining room and 2 bathrooms",
        "small clinic with reception, waiting room and two consultation rooms",
        "2 floor house with living room, kitchen, bathroom and 3 bedrooms upstairs",
    ]
    for prompt in prompts:
        specs = apply_template_defaults(extract_rooms(prompt), detect_building_type(prompt))
        building_type = detect_building_type(prompt)
        rules = fallback_layout_rules(building_type, {s.room_type for s in specs})
        template = get_building_template(building_type)

        tile_only = _build_layout_candidate(
            room_specs=specs, prompt=prompt, building_type=building_type,
            total_floors=extract_total_floors(prompt), pattern_rules=rules,
            total_area_sqm=None, template=template, x_offset=0.0, placement_style="tile",
        )
        bsp = _build_layout_candidate(
            room_specs=specs, prompt=prompt, building_type=building_type,
            total_floors=extract_total_floors(prompt), pattern_rules=rules,
            total_area_sqm=None, template=template, x_offset=0.0, placement_style="bsp",
        )
        best = _generate(prompt)
        assert best["insights"]["score"] >= tile_only["insights"]["score"]
        assert best["insights"]["score"] >= bsp["insights"]["score"]


async def test_generate_endpoint_exposes_placement_engine_and_candidate_count(client: AsyncClient):
    resp = await client.post(
        "/api/auth/register",
        json={"name": "BSP User", "email": "bsp-user@example.com", "password": "password123"},
    )
    token = resp.json()["access_token"]

    response = await client.post(
        "/api/design/generate",
        json={"prompt": "apartment with living room, kitchen, dining room and bathroom"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["candidateCount"] == 2
    assert metadata["placementEngine"] in ("tile", "bsp")
