from httpx import AsyncClient


async def _register_and_token(client: AsyncClient, email: str, name: str = "User") -> str:
    response = await client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": "password123"},
    )
    return response.json()["access_token"]


async def _create_workspace(
    client: AsyncClient,
    token: str,
    name: str = "Studio Workspace",
) -> dict:
    response = await client.post(
        "/api/workspaces",
        json={"name": name, "description": "Shared concepts"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()


async def _add_member(
    client: AsyncClient,
    token: str,
    workspace_id: str,
    email: str,
    role: str = "editor",
) -> dict:
    response = await client.post(
        f"/api/workspaces/{workspace_id}/members",
        json={"email": email, "role": role},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()


async def test_create_workspace_adds_creator_as_owner(client: AsyncClient):
    token = await _register_and_token(client, "workspace-owner@example.com")

    response = await client.post(
        "/api/workspaces",
        json={"name": "Design Team", "description": "Shared workspace"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    workspace = response.json()
    assert workspace["name"] == "Design Team"
    assert workspace["description"] == "Shared workspace"
    assert workspace["current_user_role"] == "owner"

    members = await client.get(
        f"/api/workspaces/{workspace['id']}/members",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert members.status_code == 200
    assert len(members.json()) == 1
    assert members.json()[0]["role"] == "owner"
    assert members.json()[0]["email"] == "workspace-owner@example.com"


async def test_list_workspaces_returns_only_current_users_memberships(client: AsyncClient):
    token_a = await _register_and_token(client, "workspace-list-a@example.com")
    token_b = await _register_and_token(client, "workspace-list-b@example.com")
    workspace_a = await _create_workspace(client, token_a, "Workspace A")
    await _create_workspace(client, token_b, "Workspace B")

    response = await client.get(
        "/api/workspaces",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 200
    assert [workspace["id"] for workspace in response.json()] == [workspace_a["id"]]


async def test_workspace_member_can_fetch_detail(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-detail-owner@example.com")
    member_token = await _register_and_token(client, "workspace-detail-member@example.com")
    workspace = await _create_workspace(client, owner_token)
    await _add_member(
        client,
        owner_token,
        workspace["id"],
        "workspace-detail-member@example.com",
    )

    response = await client.get(
        f"/api/workspaces/{workspace['id']}",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == workspace["id"]
    assert response.json()["current_user_role"] == "editor"


async def test_non_member_cannot_fetch_workspace_detail(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-private-owner@example.com")
    intruder_token = await _register_and_token(client, "workspace-private-other@example.com")
    workspace = await _create_workspace(client, owner_token)

    response = await client.get(
        f"/api/workspaces/{workspace['id']}",
        headers={"Authorization": f"Bearer {intruder_token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


async def test_owner_and_admin_can_update_workspace(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-update-owner@example.com")
    admin_token = await _register_and_token(client, "workspace-update-admin@example.com")
    workspace = await _create_workspace(client, owner_token)
    await _add_member(
        client,
        owner_token,
        workspace["id"],
        "workspace-update-admin@example.com",
        role="admin",
    )

    owner_update = await client.put(
        f"/api/workspaces/{workspace['id']}",
        json={"name": "Owner Updated"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    admin_update = await client.put(
        f"/api/workspaces/{workspace['id']}",
        json={"description": "Admin Updated"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert owner_update.status_code == 200
    assert owner_update.json()["name"] == "Owner Updated"
    assert admin_update.status_code == 200
    assert admin_update.json()["description"] == "Admin Updated"


async def test_editor_and_viewer_cannot_update_workspace(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-rbac-owner@example.com")
    editor_token = await _register_and_token(client, "workspace-rbac-editor@example.com")
    viewer_token = await _register_and_token(client, "workspace-rbac-viewer@example.com")
    workspace = await _create_workspace(client, owner_token)
    await _add_member(client, owner_token, workspace["id"], "workspace-rbac-editor@example.com")
    await _add_member(
        client,
        owner_token,
        workspace["id"],
        "workspace-rbac-viewer@example.com",
        role="viewer",
    )

    for token in (editor_token, viewer_token):
        response = await client.put(
            f"/api/workspaces/{workspace['id']}",
            json={"name": "Forbidden"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


async def test_only_owner_can_delete_workspace(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-delete-owner@example.com")
    admin_token = await _register_and_token(client, "workspace-delete-admin@example.com")
    workspace = await _create_workspace(client, owner_token)
    await _add_member(
        client,
        owner_token,
        workspace["id"],
        "workspace-delete-admin@example.com",
        role="admin",
    )

    forbidden = await client.delete(
        f"/api/workspaces/{workspace['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    deleted = await client.delete(
        f"/api/workspaces/{workspace['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert forbidden.status_code == 403
    assert deleted.status_code == 204


async def test_owner_can_add_existing_user_by_email(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-add-owner@example.com")
    await _register_and_token(client, "workspace-add-member@example.com", name="Member")
    workspace = await _create_workspace(client, owner_token)

    member = await _add_member(
        client,
        owner_token,
        workspace["id"],
        "workspace-add-member@example.com",
    )

    assert member["email"] == "workspace-add-member@example.com"
    assert member["name"] == "Member"
    assert member["role"] == "editor"


async def test_add_member_returns_clear_error_when_user_does_not_exist(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-missing-owner@example.com")
    workspace = await _create_workspace(client, owner_token)

    response = await client.post(
        f"/api/workspaces/{workspace['id']}/members",
        json={"email": "missing@example.com", "role": "editor"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "User not found"


async def test_duplicate_workspace_member_returns_conflict(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-duplicate-owner@example.com")
    await _register_and_token(client, "workspace-duplicate-member@example.com")
    workspace = await _create_workspace(client, owner_token)
    await _add_member(
        client,
        owner_token,
        workspace["id"],
        "workspace-duplicate-member@example.com",
    )

    response = await client.post(
        f"/api/workspaces/{workspace['id']}/members",
        json={"email": "workspace-duplicate-member@example.com", "role": "viewer"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"


async def test_admin_can_update_member_role_and_remove_member(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-member-owner@example.com")
    admin_token = await _register_and_token(client, "workspace-member-admin@example.com")
    await _register_and_token(client, "workspace-member-editor@example.com")
    workspace = await _create_workspace(client, owner_token)
    await _add_member(
        client,
        owner_token,
        workspace["id"],
        "workspace-member-admin@example.com",
        role="admin",
    )
    editor = await _add_member(
        client,
        owner_token,
        workspace["id"],
        "workspace-member-editor@example.com",
    )

    changed = await client.put(
        f"/api/workspaces/{workspace['id']}/members/{editor['id']}/role",
        json={"role": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    removed = await client.delete(
        f"/api/workspaces/{workspace['id']}/members/{editor['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert changed.status_code == 200
    assert changed.json()["role"] == "viewer"
    assert removed.status_code == 204


async def test_editor_cannot_manage_members(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-editor-owner@example.com")
    editor_token = await _register_and_token(client, "workspace-editor-member@example.com")
    await _register_and_token(client, "workspace-editor-target@example.com")
    workspace = await _create_workspace(client, owner_token)
    await _add_member(
        client,
        owner_token,
        workspace["id"],
        "workspace-editor-member@example.com",
    )

    response = await client.post(
        f"/api/workspaces/{workspace['id']}/members",
        json={"email": "workspace-editor-target@example.com", "role": "viewer"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 403


async def test_owner_membership_cannot_be_demoted_or_removed(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-protect-owner@example.com")
    workspace = await _create_workspace(client, owner_token)
    members = await client.get(
        f"/api/workspaces/{workspace['id']}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    owner_member = members.json()[0]

    changed = await client.put(
        f"/api/workspaces/{workspace['id']}/members/{owner_member['id']}/role",
        json={"role": "viewer"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    removed = await client.delete(
        f"/api/workspaces/{workspace['id']}/members/{owner_member['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert changed.status_code == 422
    assert removed.status_code == 422


async def test_workspace_activity_returns_team_actions_newest_first(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-activity-owner@example.com")
    await _register_and_token(client, "workspace-activity-member@example.com")
    workspace = await _create_workspace(client, owner_token)
    member = await _add_member(
        client,
        owner_token,
        workspace["id"],
        "workspace-activity-member@example.com",
    )
    await client.put(
        f"/api/workspaces/{workspace['id']}/members/{member['id']}/role",
        json={"role": "viewer"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    response = await client.get(
        f"/api/workspaces/{workspace['id']}/activity",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 200
    assert [entry["action"] for entry in response.json()] == [
        "workspace.member_role_changed",
        "workspace.member_added",
        "workspace.created",
    ]


async def test_non_member_cannot_read_workspace_activity(client: AsyncClient):
    owner_token = await _register_and_token(client, "workspace-log-owner@example.com")
    intruder_token = await _register_and_token(client, "workspace-log-intruder@example.com")
    workspace = await _create_workspace(client, owner_token)

    response = await client.get(
        f"/api/workspaces/{workspace['id']}/activity",
        headers={"Authorization": f"Bearer {intruder_token}"},
    )

    assert response.status_code == 403
