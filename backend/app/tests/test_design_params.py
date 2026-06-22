"""
Sprint 17 Phase 0/2 — DesignParams: explicit parametric overrides alongside
the prompt. plot_width_m, floors, vastu, and orientation are all wired into
the engine; plot_depth_m is accepted and recorded for a later phase (it
needs the BSP partitioner to apply without distorting room proportions).
"""
from httpx import AsyncClient

from app.services.layout_service import generate_layout
from app.services.prompt_service import detect_building_type, extract_rooms, extract_total_floors


def _generate(prompt: str, **kwargs) -> dict:
    return generate_layout(
        extract_rooms(prompt),
        prompt=prompt,
        building_type=detect_building_type(prompt),
        total_floors=extract_total_floors(prompt),
        **kwargs,
    )


def test_without_plot_width_behaves_as_before():
    prompt = "2 bedroom apartment with living room, kitchen, dining and bathroom"
    layout = _generate(prompt)

    assert "designParams" not in layout["metadata"]
    assert layout["floors"][0]["footprint"]["w"] > 0


def test_plot_width_overrides_inferred_footprint():
    prompt = "2 bedroom apartment with living room, kitchen, dining and bathroom"
    layout = _generate(prompt, plot_width_m=12.0)

    assert layout["floors"][0]["footprint"]["w"] == 12.0
    assert layout["metadata"]["designParams"] == {"plotWidthM": 12.0}


def test_plot_width_is_clamped_to_a_sane_range():
    prompt = "small clinic with reception, waiting room and two consultation rooms"

    too_narrow = _generate(prompt, plot_width_m=1.0)
    too_wide = _generate(prompt, plot_width_m=100.0)

    assert too_narrow["floors"][0]["footprint"]["w"] == 4.0
    assert too_wide["floors"][0]["footprint"]["w"] == 40.0


def test_plot_width_holds_across_multiple_floors():
    prompt = "2 floor house with living room, kitchen, bathroom and 3 bedrooms upstairs"
    layout = _generate(prompt, plot_width_m=10.0)

    widths = {floor["footprint"]["w"] for floor in layout["floors"]}
    assert widths == {10.0}


def _entry_door(layout: dict) -> dict:
    return next(
        room for room in layout["rooms"]
        if room["objectType"] == "door" and room["label"] == "Entry Door"
    )


def test_orientation_moves_the_entry_door_to_the_matching_wall():
    prompt = "apartment with living room, kitchen, dining room and bathroom"

    default_layout = _generate(prompt)
    north_layout = _generate(prompt, orientation="N")
    east_layout = _generate(prompt, orientation="E")

    default_entry = _entry_door(default_layout)
    north_entry = _entry_door(north_layout)
    east_entry = _entry_door(east_layout)

    footprint = default_layout["floors"][0]["footprint"]
    # Default (no orientation, and "S") puts the entry on the front (low-Z) wall.
    assert default_entry["position"]["z"] < footprint["z"]
    # "N" puts it on the rear (high-Z) wall instead.
    assert north_entry["position"]["z"] > footprint["z"] + footprint["d"]
    # "E" puts it on the right (high-X) wall.
    assert east_entry["position"]["x"] > footprint["x"] + footprint["w"]


def test_orientation_is_echoed_in_metadata():
    prompt = "apartment with living room, kitchen and bathroom"
    layout = _generate(prompt, orientation="w")

    assert layout["metadata"]["designParams"] == {"orientation": "W"}


def test_orientation_does_not_remove_exterior_windows():
    prompt = "apartment with living room, kitchen, dining room and bathroom"
    layout = _generate(prompt, orientation="E")

    windows = [room for room in layout["rooms"] if room["objectType"] == "window"]
    assert len(windows) == 3  # the three walls that aren't the entry wall


async def _register_and_token(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Params User", "email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


async def test_generate_endpoint_applies_plot_width_design_param(client: AsyncClient):
    token = await _register_and_token(client, "design-params@example.com")

    response = await client.post(
        "/api/design/generate",
        json={
            "prompt": "2 bedroom apartment with living room, kitchen and bathroom",
            "designParams": {"plotWidthM": 9.5},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["floors"][0]["footprint"]["w"] == 9.5
    assert data["metadata"]["designParams"] == {"plotWidthM": 9.5}


async def test_generate_endpoint_applies_orientation_design_param(client: AsyncClient):
    token = await _register_and_token(client, "design-params-orientation@example.com")

    response = await client.post(
        "/api/design/generate",
        json={
            "prompt": "apartment with living room, kitchen, dining room and bathroom",
            "designParams": {"orientation": "N"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["designParams"] == {"orientation": "N"}
    entry = next(r for r in data["rooms"] if r["objectType"] == "door" and r["label"] == "Entry Door")
    footprint = data["floors"][0]["footprint"]
    assert entry["position"]["z"] > footprint["z"] + footprint["d"]


async def test_generate_endpoint_floors_design_param_overrides_prompt(client: AsyncClient):
    token = await _register_and_token(client, "design-params-floors@example.com")

    response = await client.post(
        "/api/design/generate",
        json={
            "prompt": "apartment with living room, kitchen and bathroom",
            "designParams": {"floors": 2},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["totalFloors"] == 2
    assert len(data["floors"]) == 2


async def test_generate_endpoint_without_design_params_is_unaffected(client: AsyncClient):
    token = await _register_and_token(client, "design-params-none@example.com")

    response = await client.post(
        "/api/design/generate",
        json={"prompt": "2 bedroom apartment with living room, kitchen and bathroom"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["designParams"] is None
