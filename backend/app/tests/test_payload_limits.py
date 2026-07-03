import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.schemas.design import SaveDesignRequest


async def _token(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/auth/register",
        json={"name": "Payload User", "email": email, "password": "password123"},
    )
    return response.json()["access_token"]


async def test_generate_rejects_oversize_prompt(client: AsyncClient):
    token = await _token(client, "big-prompt@example.com")
    response = await client.post(
        "/api/design/generate",
        json={"prompt": "a" * 2001},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "UNPROCESSABLE_ENTITY"


def test_oversize_layout_json_rejected_by_schema():
    huge_layout = {"rooms": [{"label": "x" * 100} for _ in range(30_000)]}
    with pytest.raises(ValidationError):
        SaveDesignRequest(layout=huge_layout)


def test_normal_layout_accepted_by_schema():
    layout = {"version": "1.0", "rooms": [{"id": "a", "label": "Bedroom"}]}
    assert SaveDesignRequest(layout=layout).layout == layout


async def test_request_body_size_guard_returns_413(client: AsyncClient):
    # ~3.2 MB body — over the 3 MB request-body cap, rejected before parsing.
    oversized = (
        b'{"name":"' + b"a" * (3 * 1024 * 1024 + 1024)
        + b'","email":"huge@example.com","password":"password123"}'
    )
    response = await client.post(
        "/api/auth/register",
        content=oversized,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "PAYLOAD_TOO_LARGE"
