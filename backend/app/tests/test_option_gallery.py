"""
Sprint 17 Phase 4 — option gallery.

generate_layout already builds multiple full candidate layouts per request
(tile vs bsp for tiled types, x-offset variants for the row-band fallback)
and previously discarded everything except the winner. The /generate
endpoint now surfaces the rest as `alternatives` so the frontend can offer
them as pickable options instead of just the one the scorer chose.
"""
from httpx import AsyncClient


async def _register_and_token(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Gallery User", "email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


async def test_generate_endpoint_returns_alternative_layouts(client: AsyncClient):
    token = await _register_and_token(client, "gallery@example.com")

    response = await client.post(
        "/api/design/generate",
        json={"prompt": "apartment with living room, kitchen, dining room and bathroom"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "alternatives" in data
    assert len(data["alternatives"]) >= 1
    for alt in data["alternatives"]:
        assert alt["rooms"]
        assert "designId" not in alt
        assert "designVersionId" not in alt


async def test_alternatives_are_not_persisted_to_the_saved_design(client: AsyncClient):
    token = await _register_and_token(client, "gallery-persist@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Gallery Project", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = project.json()["id"]

    response = await client.post(
        "/api/design/generate",
        json={
            "projectId": project_id,
            "prompt": "apartment with living room, kitchen, dining room and bathroom",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    design_id = response.json()["designId"]

    latest = await client.get(
        f"/api/design/project/{project_id}/latest",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert latest.status_code == 200
    assert latest.json()["designId"] == design_id
    # The persisted/reloaded layout_json never carried alternatives, so the
    # reload response shouldn't surface a stale/duplicated gallery either.
    assert latest.json().get("alternatives") is None


async def test_alternative_layouts_score_no_higher_than_the_winner(client: AsyncClient):
    token = await _register_and_token(client, "gallery-score@example.com")

    response = await client.post(
        "/api/design/generate",
        json={"prompt": "3 bedroom apartment with living room, kitchen, dining room and 2 bathrooms"},
        headers={"Authorization": f"Bearer {token}"},
    )

    data = response.json()
    winner_score = data["insights"]["score"]
    for alt in data["alternatives"]:
        assert alt["insights"]["score"] <= winner_score
