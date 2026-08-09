from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from jose import jwt

from app.config.settings import settings
from app.utils.jwt import ALGORITHM, TOKEN_TYPE_ACCESS


async def _register(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/auth/register",
        json={"name": "Token User", "email": email, "password": "password123"},
    )
    assert response.status_code == 201
    return response.json()


async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["name"] == "Test User"


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"name": "Test User", "email": "dup@example.com", "password": "password123"}
    await client.post("/api/auth/register", json=payload)
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["error"] == "Email already registered"
    assert data["code"] == "CONFLICT"


async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"name": "Login User", "email": "login@example.com", "password": "securepass"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "securepass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"name": "User", "email": "wrongpass@example.com", "password": "correctpass"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "wrongpass@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "Invalid email or password"
    assert data["code"] == "UNAUTHORIZED"


async def test_login_unknown_email(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "somepass12"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "Invalid email or password"
    assert data["code"] == "UNAUTHORIZED"


async def test_me_valid_token(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"name": "Me User", "email": "me@example.com", "password": "mypassword"},
    )
    token = reg.json()["access_token"]
    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


async def test_me_no_token(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "Not authenticated"
    assert data["code"] == "UNAUTHORIZED"


async def test_me_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/auth/me", headers={"Authorization": "Bearer thisisnotavalidtoken"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "Not authenticated"
    assert data["code"] == "UNAUTHORIZED"


# ── Token lifecycle (Phase 0 C2) ─────────────────────────────────────────────


async def test_register_and_login_return_refresh_token(client: AsyncClient):
    data = await _register(client, "refresh-issued@example.com")
    assert data["refresh_token"]
    assert data["access_token"] != data["refresh_token"]


async def test_refresh_issues_new_access_token_and_rotates(client: AsyncClient):
    data = await _register(client, "rotate@example.com")
    old_refresh = data["refresh_token"]

    refreshed = await client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    body = refreshed.json()
    assert body["access_token"]
    assert body["refresh_token"] != old_refresh

    # The rotated-out (old) refresh token can no longer be used.
    reused = await client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 401

    # The new refresh token works.
    again = await client.post("/api/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert again.status_code == 200


async def test_refresh_rejects_access_token(client: AsyncClient):
    data = await _register(client, "wrongtype@example.com")
    response = await client.post("/api/auth/refresh", json={"refresh_token": data["access_token"]})
    assert response.status_code == 401


async def test_access_route_rejects_refresh_token(client: AsyncClient):
    data = await _register(client, "refresh-on-access@example.com")
    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {data['refresh_token']}"}
    )
    assert response.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient):
    data = await _register(client, "logout@example.com")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    logout = await client.post(
        "/api/auth/logout", json={"refresh_token": data["refresh_token"]}, headers=headers
    )
    assert logout.status_code == 200

    reused = await client.post("/api/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert reused.status_code == 401


async def test_login_is_rate_limited(client: AsyncClient):
    creds = {"email": "nobody-rl@example.com", "password": "whatever12"}
    # Login limit is 10/min per IP; the 11th attempt within the window is 429.
    statuses = []
    for _ in range(11):
        response = await client.post("/api/auth/login", json=creds)
        statuses.append(response.status_code)

    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429
    blocked = await client.post("/api/auth/login", json=creds)
    assert blocked.json()["code"] == "TOO_MANY_REQUESTS"


async def test_login_rate_limit_cannot_be_reset_with_an_attackers_own_token(
    client: AsyncClient,
):
    """The login bucket is keyed on IP only. Before this, attaching a valid
    bearer token switched the bucket to `user:<that token's sub>`, so an
    attacker could mint a fresh 10-attempt budget per throwaway account from
    the same IP."""
    attacker = await _register(client, "bucket-attacker@example.com")
    creds = {"email": "bucket-victim@example.com", "password": "whatever12"}

    for _ in range(11):
        await client.post("/api/auth/login", json=creds)

    retried = await client.post(
        "/api/auth/login",
        json=creds,
        headers={"Authorization": f"Bearer {attacker['access_token']}"},
    )
    assert retried.status_code == 429


async def test_expired_access_token_rejected(client: AsyncClient):
    await _register(client, "expired@example.com")
    expired = jwt.encode(
        {
            "sub": "some-user",
            "type": TOKEN_TYPE_ACCESS,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
