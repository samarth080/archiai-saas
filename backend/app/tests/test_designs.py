from httpx import AsyncClient
from sqlalchemy import func, select

from app.models.activity_log import ActivityLog
from app.models.design import Design
from app.models.design_version import DesignVersion
from app.models.project import Project
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


async def test_latest_design_returns_saved_layout(client: AsyncClient):
    token = await _register_and_token(client, "latest-design@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Latest Design", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = project.json()["id"]

    generated = await client.post(
        "/api/design/generate",
        json={"projectId": project_id, "prompt": "2 bedroom apartment with kitchen"},
        headers={"Authorization": f"Bearer {token}"},
    )

    latest = await client.get(
        f"/api/design/project/{project_id}/latest",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert latest.status_code == 200
    assert latest.json()["designId"] == generated.json()["designId"]
    assert latest.json()["rooms"] == generated.json()["rooms"]


async def test_save_design_updates_layout_and_creates_new_version(client: AsyncClient):
    token = await _register_and_token(client, "save-design@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Save Design", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = project.json()["id"]
    generated = await client.post(
        "/api/design/generate",
        json={"projectId": project_id, "prompt": "2 bedroom apartment with kitchen"},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = generated.json()
    data["rooms"][0]["label"] = "Edited Room"

    saved = await client.put(
        f"/api/design/{data['designId']}",
        json={"layout": data},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert saved.status_code == 200
    assert saved.json()["rooms"][0]["label"] == "Edited Room"

    async with TestSessionLocal() as session:
        version_count = await session.scalar(
            select(func.count()).select_from(DesignVersion).where(
                DesignVersion.design_id == data["designId"]
            )
        )
        assert version_count == 2

        activity_result = await session.scalars(select(ActivityLog.action))
        assert "layout.saved" in activity_result.all()


async def test_manual_save_stores_version_metadata_and_thumbnail(client: AsyncClient):
    token = await _register_and_token(client, "manual-version@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Manual Version", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = project.json()["id"]
    generated = await client.post(
        "/api/design/generate",
        json={"projectId": project_id, "prompt": "1 bedroom apartment with kitchen"},
        headers={"Authorization": f"Bearer {token}"},
    )
    layout = generated.json()
    layout["rooms"][0]["label"] = "Named Save Room"

    saved = await client.put(
        f"/api/design/{layout['designId']}",
        json={
            "layout": layout,
            "versionName": "Client review",
            "changeSummary": "Moved the main room",
            "thumbnailUrl": "data:image/png;base64,abc123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert saved.status_code == 200

    async with TestSessionLocal() as session:
        latest_version = await session.scalar(
            select(DesignVersion)
            .where(DesignVersion.design_id == layout["designId"])
            .order_by(DesignVersion.version_number.desc())
        )
        project_row = await session.get(Project, project_id)

        assert latest_version is not None
        assert latest_version.version_number == 2
        assert latest_version.version_name == "Client review"
        assert latest_version.version_type == "manual"
        assert latest_version.change_summary == "Moved the main room"
        assert latest_version.layout_json["rooms"][0]["label"] == "Named Save Room"
        assert project_row is not None
        assert project_row.thumbnail_url == "data:image/png;base64,abc123"
