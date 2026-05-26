from httpx import AsyncClient
from sqlalchemy import select

from app.models.activity_log import ActivityLog
from app.models.design import Design
from app.models.design_version import DesignVersion
from app.tests.conftest import TestSessionLocal


async def _register_and_token(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Design User", "email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


async def test_generate_design_returns_multi_floor_layout_and_logs_activity(client: AsyncClient):
    token = await _register_and_token(client, "design@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Generated Project", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = project.json()["id"]

    response = await client.post(
        "/api/design/generate",
        json={
            "projectId": project_id,
            "prompt": "2 floor, 3 bedroom layout with kitchen, living room, bathroom",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["totalFloors"] == 2
    assert len(data["floors"]) == 2
    assert any(room["roomType"] == "stairs" for room in data["rooms"])
    assert data["designId"]
    assert data["designVersionId"]

    async with TestSessionLocal() as session:
        activity_result = await session.scalars(select(ActivityLog.action))
        assert "design.generated" in activity_result.all()

        design = await session.get(Design, data["designId"])
        version = await session.get(DesignVersion, data["designVersionId"])
        assert design is not None
        assert version is not None
        assert design.layout_json["metadata"]["totalFloors"] == 2
        assert version.layout_json["metadata"]["totalFloors"] == 2
        assert version.version_number == 1


async def test_generate_design_requires_auth(client: AsyncClient):
    response = await client.post(
        "/api/design/generate",
        json={"prompt": "2 bedroom apartment with kitchen"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"
