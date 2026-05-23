from httpx import AsyncClient


async def _register_and_token(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"name": "User", "email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


async def test_create_project_success(client: AsyncClient):
    token = await _register_and_token(client, "proj1@example.com")
    response = await client.post(
        "/api/projects",
        json={"title": "My First Project", "description": "A test project"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My First Project"
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data


async def test_create_project_no_token(client: AsyncClient):
    response = await client.post(
        "/api/projects",
        json={"title": "No Auth Project"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "UNAUTHORIZED"


async def test_list_projects_scoped_to_user(client: AsyncClient):
    token_a = await _register_and_token(client, "user_a@example.com")
    token_b = await _register_and_token(client, "user_b@example.com")

    await client.post(
        "/api/projects",
        json={"title": "User A Project"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    await client.post(
        "/api/projects",
        json={"title": "User B Project"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    response = await client.get(
        "/api/projects", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0]["title"] == "User A Project"


async def test_get_project_success(client: AsyncClient):
    token = await _register_and_token(client, "get_proj@example.com")
    created = await client.post(
        "/api/projects",
        json={"title": "Fetch Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = created.json()["id"]

    response = await client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Fetch Me"


async def test_get_project_wrong_user(client: AsyncClient):
    token_a = await _register_and_token(client, "owner@example.com")
    token_b = await _register_and_token(client, "intruder@example.com")

    created = await client.post(
        "/api/projects",
        json={"title": "Private Project"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    project_id = created.json()["id"]

    response = await client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


async def test_update_project_success(client: AsyncClient):
    token = await _register_and_token(client, "update_proj@example.com")
    created = await client.post(
        "/api/projects",
        json={"title": "Old Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = created.json()["id"]

    response = await client.put(
        f"/api/projects/{project_id}",
        json={"title": "New Title", "description": "Updated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["description"] == "Updated"


async def test_delete_project_success(client: AsyncClient):
    token = await _register_and_token(client, "delete_proj@example.com")
    created = await client.post(
        "/api/projects",
        json={"title": "To Be Deleted"},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = created.json()["id"]

    response = await client.delete(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    get_response = await client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404


async def test_delete_project_wrong_user(client: AsyncClient):
    token_a = await _register_and_token(client, "del_owner@example.com")
    token_b = await _register_and_token(client, "del_intruder@example.com")

    created = await client.post(
        "/api/projects",
        json={"title": "Protected Project"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    project_id = created.json()["id"]

    response = await client.delete(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
