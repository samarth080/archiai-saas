from httpx import AsyncClient


async def test_health_allows_localhost_dev_origins(client: AsyncClient):
    for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        response = await client.options(
            "/api/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
