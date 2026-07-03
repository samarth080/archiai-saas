import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.config.settings import Settings

_DB = "sqlite+aiosqlite:///:memory:"
_STRONG = "s" * 48


def test_production_rejects_placeholder_secret():
    with pytest.raises(ValidationError):
        Settings(ENV="production", SECRET_KEY="replace-with-a-long-random-secret", DATABASE_URL=_DB)


def test_production_rejects_short_secret():
    with pytest.raises(ValidationError):
        Settings(ENV="production", SECRET_KEY="tooshort", DATABASE_URL=_DB)


def test_production_rejects_wildcard_origin():
    with pytest.raises(ValidationError):
        Settings(ENV="production", SECRET_KEY=_STRONG, ALLOWED_ORIGINS="*", DATABASE_URL=_DB)


def test_production_accepts_strong_secret():
    settings = Settings(ENV="production", SECRET_KEY=_STRONG, DATABASE_URL=_DB)
    assert settings.is_production is True


def test_development_allows_placeholder_secret():
    settings = Settings(ENV="development", SECRET_KEY="dev", DATABASE_URL=_DB)
    assert settings.is_production is False


def test_allowed_origins_parses_csv():
    settings = Settings(
        ENV="development",
        SECRET_KEY="dev",
        DATABASE_URL=_DB,
        ALLOWED_ORIGINS="http://a.com, http://b.com ,",
    )
    assert settings.allowed_origins_list == ["http://a.com", "http://b.com"]


async def test_security_headers_absent_in_development(client: AsyncClient):
    response = await client.get("/api/health")
    assert "content-security-policy" not in response.headers


async def test_security_headers_present_in_production(client: AsyncClient, monkeypatch):
    from app.config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "ENV", "production")
    response = await client.get("/api/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("content-security-policy") is not None
    assert response.headers.get("referrer-policy") == "no-referrer"
