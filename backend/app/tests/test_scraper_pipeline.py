from datetime import datetime, timezone
from importlib import import_module

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.tests.conftest import TestSessionLocal


SOURCE_PAYLOAD = {
    "name": "Public layout guidance",
    "base_url": "https://example.com/public-layout-guide",
    "robots_txt_url": "https://example.com/robots.txt",
    "data_type": "text/html",
    "source_category": "layout_pattern_reference",
}

SAMPLE_LAYOUT_TEXT = """
Apartment layout guidance

Bedrooms are private rooms, typically 10-16 sqm, near a bathroom and corridor.
Avoid placing bedrooms next to the kitchen or garage.
The living room belongs in the public zone near the entry and dining room.
Corridors should connect rooms to common spaces.
Bedrooms and living rooms should have windows on external walls for natural light.
"""


async def _register_and_token(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/auth/register",
        json={"name": "Pipeline User", "email": email, "password": "password123"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_authenticated_user_can_create_and_list_scraper_sources(client: AsyncClient):
    token = await _register_and_token(client, "scraper-source@example.com")

    created = await client.post(
        "/api/scraper/sources",
        json=SOURCE_PAYLOAD,
        headers=_headers(token),
    )
    listed = await client.get("/api/scraper/sources", headers=_headers(token))

    assert created.status_code == 201
    assert created.json()["base_url"] == SOURCE_PAYLOAD["base_url"]
    assert listed.status_code == 200
    assert [source["id"] for source in listed.json()] == [created.json()["id"]]


async def test_scraper_run_returns_status_and_updates_record_count(client: AsyncClient, monkeypatch):
    token = await _register_and_token(client, "scraper-run@example.com")
    source = await client.post(
        "/api/scraper/sources",
        json=SOURCE_PAYLOAD,
        headers=_headers(token),
    )
    assert source.status_code == 201

    scraper_service = import_module("app.services.scraper_service")

    async def allowed(_url: str):
        robots_module = import_module("app.services.robots_txt_checker")
        return robots_module.RobotsCheckResult(allowed=True, reason="Allowed by robots.txt")

    async def fetch_page(_url: str):
        return "<html><body><p>Bedroom is typically 10-16 sqm.</p></body></html>"

    monkeypatch.setattr(scraper_service.default_robots_checker, "check_url", allowed)
    monkeypatch.setattr(scraper_service, "fetch_public_page", fetch_page)

    response = await client.post(
        "/api/scraper/run",
        json={"source_id": source.json()["id"]},
        headers=_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["records_collected"] == 1


async def test_robots_txt_checker_allows_public_path():
    robots_module = import_module("app.services.robots_txt_checker")

    async def fetch_text(_url: str):
        return 200, "User-agent: *\nDisallow: /private\nAllow: /public"

    checker = robots_module.RobotsTxtChecker(fetch_text=fetch_text)
    result = await checker.check_url("https://example.com/public/layout-guide")

    assert result.allowed is True
    assert result.robots_txt_url == "https://example.com/robots.txt"


async def test_robots_txt_checker_blocks_disallowed_path():
    robots_module = import_module("app.services.robots_txt_checker")

    async def fetch_text(_url: str):
        return 200, "User-agent: *\nDisallow: /private"

    checker = robots_module.RobotsTxtChecker(fetch_text=fetch_text)
    result = await checker.check_url("https://example.com/private/layout-guide")

    assert result.allowed is False
    assert "disallow" in result.reason.lower()


async def test_robots_txt_checker_handles_missing_file_safely():
    robots_module = import_module("app.services.robots_txt_checker")

    async def fetch_text(_url: str):
        return 404, ""

    checker = robots_module.RobotsTxtChecker(fetch_text=fetch_text)
    result = await checker.check_url("https://example.com/public/layout-guide")

    assert result.allowed is True
    assert "not found" in result.reason.lower()


async def test_robots_txt_checker_blocks_invalid_url():
    robots_module = import_module("app.services.robots_txt_checker")
    checker = robots_module.RobotsTxtChecker()

    result = await checker.check_url("not-a-url")

    assert result.allowed is False
    assert "invalid" in result.reason.lower()


async def test_robots_txt_checker_blocks_network_error():
    robots_module = import_module("app.services.robots_txt_checker")

    async def fetch_text(_url: str):
        raise OSError("network unavailable")

    checker = robots_module.RobotsTxtChecker(fetch_text=fetch_text)
    result = await checker.check_url("https://example.com/public/layout-guide")

    assert result.allowed is False
    assert "failed" in result.reason.lower()


async def test_scraper_runner_refuses_disallowed_source(monkeypatch):
    scraper_service = import_module("app.services.scraper_service")
    robots_module = import_module("app.services.robots_txt_checker")

    async def blocked(_url: str):
        return robots_module.RobotsCheckResult(allowed=False, reason="Disallowed by robots.txt")

    async def unexpected_fetch(_url: str):
        raise AssertionError("Blocked source must not be fetched")

    monkeypatch.setattr(scraper_service.default_robots_checker, "check_url", blocked)
    monkeypatch.setattr(scraper_service, "fetch_public_page", unexpected_fetch)

    with pytest.raises(scraper_service.ScraperBlockedError, match="Disallowed"):
        await scraper_service.scrape_public_text("https://example.com/private/layout-guide")


async def test_scraper_runner_extracts_visible_text_without_images(monkeypatch):
    scraper_service = import_module("app.services.scraper_service")
    robots_module = import_module("app.services.robots_txt_checker")

    async def allowed(_url: str):
        return robots_module.RobotsCheckResult(allowed=True, reason="Allowed by robots.txt")

    async def fetch_page(_url: str):
        return """
        <html><body>
          <h1>Apartment guidance</h1>
          <img src="copyrighted-plan.png" alt="Do not collect this drawing">
          <script>private_tracking_data()</script>
          <p>Bedroom is typically 10-16 sqm.</p>
        </body></html>
        """

    monkeypatch.setattr(scraper_service.default_robots_checker, "check_url", allowed)
    monkeypatch.setattr(scraper_service, "fetch_public_page", fetch_page)

    text = await scraper_service.scrape_public_text("https://example.com/public-layout-guide")

    assert text == "Apartment guidance Bedroom is typically 10-16 sqm."
    assert "copyrighted-plan" not in text
    assert "private_tracking_data" not in text


async def test_run_source_scraper_stores_raw_record_provenance(monkeypatch):
    scraper_service = import_module("app.services.scraper_service")
    scraper_models = import_module("app.models.scraper_source")
    record_models = import_module("app.models.scraped_record")
    pattern_models = import_module("app.models.layout_pattern")
    user_models = import_module("app.models.user")

    async def scrape_text(_url: str):
        return "Bedroom is typically 10-16 sqm."

    monkeypatch.setattr(scraper_service, "scrape_public_text", scrape_text)

    async with TestSessionLocal() as session:
        user = user_models.User(
            name="Pipeline User",
            email="direct-runner@example.com",
            hashed_password="not-used-in-service-test",
        )
        session.add(user)
        await session.flush()
        source = scraper_models.ScraperSource(
            name="Public guide",
            base_url="https://example.com/public-layout-guide",
            robots_txt_url="https://example.com/robots.txt",
            data_type="text/html",
            source_category="room_size_reference",
            created_by=user.id,
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)

        run = await scraper_service.run_source_scraper(session, source)
        record = await session.scalar(
            select(record_models.ScrapedRecord).where(record_models.ScrapedRecord.run_id == run.id)
        )
        pattern = await session.scalar(
            select(pattern_models.LayoutPattern).where(pattern_models.LayoutPattern.source_id == source.id)
        )

        assert run.status == "completed"
        assert run.records_collected == 1
        assert record.source_id == source.id
        assert record.source_url == source.base_url
        assert record.accessed_at is not None
        assert pattern.room_type == "bedroom"
        assert pattern.typical_area_sqm_min == 10
        assert pattern.source_url == source.base_url
        assert pattern.accessed_at is not None


def test_raw_scraped_record_normalisation():
    cleaning_service = import_module("app.services.scraper_cleaning_service")

    normalized = cleaning_service.normalize_text(" Bedroom   area\\n\\n  10 - 16 sqm. ")

    assert normalized == "Bedroom area 10 - 16 sqm."


def test_metadata_extraction_finds_layout_learning_fields():
    cleaning_service = import_module("app.services.scraper_cleaning_service")

    metadata = cleaning_service.extract_layout_metadata(
        SAMPLE_LAYOUT_TEXT,
        source_url="https://example.com/public-layout-guide",
        accessed_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
    )

    bedroom = next(record for record in metadata if record["room_type"] == "bedroom")
    assert bedroom["building_type"] == "apartment"
    assert bedroom["typical_area_sqm_min"] == 10
    assert bedroom["typical_area_sqm_max"] == 16
    assert bedroom["zone"] == "private"
    assert bedroom["adjacent_to"] == ["bathroom", "corridor"]
    assert bedroom["avoid_adjacent_to"] == ["garage", "kitchen"]
    assert bedroom["source_url"] == "https://example.com/public-layout-guide"
    assert bedroom["accessed_at"] == datetime(2026, 5, 31, tzinfo=timezone.utc)


def test_metadata_extraction_captures_opening_and_circulation_notes():
    cleaning_service = import_module("app.services.scraper_cleaning_service")

    metadata = cleaning_service.extract_layout_metadata(
        SAMPLE_LAYOUT_TEXT,
        source_url="https://example.com/public-layout-guide",
        accessed_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
    )

    bedroom = next(record for record in metadata if record["room_type"] == "bedroom")
    assert "corridor" in bedroom["circulation_notes"].lower()
    assert "windows" in bedroom["door_window_notes"].lower()


def test_metadata_extraction_converts_square_feet_to_square_metres():
    cleaning_service = import_module("app.services.scraper_cleaning_service")

    metadata = cleaning_service.extract_layout_metadata(
        "House bedroom reference: bedrooms are typically 100-150 sqft.",
        source_url="https://example.com/public-layout-guide",
        accessed_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
    )

    bedroom = next(record for record in metadata if record["room_type"] == "bedroom")
    assert bedroom["typical_area_sqm_min"] == 9.29
    assert bedroom["typical_area_sqm_max"] == 13.94


async def test_processed_layout_pattern_persists_source_and_access_timestamp(client: AsyncClient, monkeypatch):
    token = await _register_and_token(client, "scraper-pattern@example.com")
    source = await client.post(
        "/api/scraper/sources",
        json=SOURCE_PAYLOAD,
        headers=_headers(token),
    )
    assert source.status_code == 201

    scraper_service = import_module("app.services.scraper_service")
    robots_module = import_module("app.services.robots_txt_checker")

    async def allowed(_url: str):
        return robots_module.RobotsCheckResult(allowed=True, reason="Allowed by robots.txt")

    async def fetch_page(_url: str):
        return f"<html><body><p>{SAMPLE_LAYOUT_TEXT}</p></body></html>"

    monkeypatch.setattr(scraper_service.default_robots_checker, "check_url", allowed)
    monkeypatch.setattr(scraper_service, "fetch_public_page", fetch_page)
    run = await client.post(
        "/api/scraper/run",
        json={"source_id": source.json()["id"]},
        headers=_headers(token),
    )
    assert run.status_code == 200

    patterns = await client.get("/api/scraper/patterns", headers=_headers(token))

    assert patterns.status_code == 200
    bedroom = next(item for item in patterns.json() if item["room_type"] == "bedroom")
    assert bedroom["source_url"] == SOURCE_PAYLOAD["base_url"]
    assert bedroom["accessed_at"] is not None


async def test_scraper_run_is_logged_and_latest_status_is_available(client: AsyncClient, monkeypatch):
    token = await _register_and_token(client, "scraper-status@example.com")
    source = await client.post(
        "/api/scraper/sources",
        json=SOURCE_PAYLOAD,
        headers=_headers(token),
    )
    assert source.status_code == 201

    scraper_service = import_module("app.services.scraper_service")
    robots_module = import_module("app.services.robots_txt_checker")

    async def allowed(_url: str):
        return robots_module.RobotsCheckResult(allowed=True, reason="Allowed by robots.txt")

    async def fetch_page(_url: str):
        return "<html><body><p>Bedroom is typically 10-16 sqm.</p></body></html>"

    monkeypatch.setattr(scraper_service.default_robots_checker, "check_url", allowed)
    monkeypatch.setattr(scraper_service, "fetch_public_page", fetch_page)
    completed = await client.post(
        "/api/scraper/run",
        json={"source_id": source.json()["id"]},
        headers=_headers(token),
    )
    status = await client.get("/api/scraper/status", headers=_headers(token))

    assert completed.status_code == 200
    assert status.status_code == 200
    assert status.json()["id"] == completed.json()["id"]
    assert status.json()["status"] == "completed"


async def test_scraper_api_requires_authentication(client: AsyncClient):
    response = await client.get("/api/scraper/sources")

    assert response.status_code == 401
