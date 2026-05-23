from httpx import AsyncClient


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
