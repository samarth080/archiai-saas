"""
Sprint 17 Phase 3 — Scrapling-backed fetcher.

fetch_public_page tries a plain (fast, no-browser) request first via
Scrapling's AsyncFetcher, and only escalates to a real stealthy browser
session (StealthyFetcher) when the plain request looks blocked or failed.
These tests mock at the AsyncFetcher/StealthyFetcher boundary (not
fetch_public_page itself) so the escalation logic is actually exercised,
unlike the rest of the scraper test suite which monkeypatches
fetch_public_page wholesale.
"""
from importlib import import_module
from types import SimpleNamespace

import pytest

from app.services import scraper_service as _scraper_service_module

# AsyncFetcher.get is the primary fetch path with no fallback (unlike
# StealthyFetcher, which fetch_public_page already treats as optional) — if
# scrapling itself failed to import (module-level try/except in
# scraper_service.py), there is no real class left to monkeypatch.get()
# onto, so these tests can't exercise real request/escalation behavior in
# this environment. See test_fetch_public_page_raises_when_scrapling_
# unavailable below for the one thing that IS testable regardless.
_SCRAPLING_UNAVAILABLE = _scraper_service_module.AsyncFetcher is None
_SKIP_REASON = "scrapling failed to import in this environment (see scraper_service.py)"


def _response(status: int, html: str = "<html><body>ok</body></html>", content_type: str = "text/html"):
    return SimpleNamespace(status=status, html_content=html, headers={"content-type": content_type})


@pytest.mark.skipif(_SCRAPLING_UNAVAILABLE, reason=_SKIP_REASON)
async def test_fetch_public_page_returns_html_on_successful_static_fetch(monkeypatch):
    scraper_service = import_module("app.services.scraper_service")

    async def fake_get(url, **kwargs):
        return _response(200, "<html><body>Static content</body></html>")

    monkeypatch.setattr(scraper_service.AsyncFetcher, "get", fake_get)

    html = await scraper_service.fetch_public_page("https://example.com/article")

    assert "Static content" in html


@pytest.mark.skipif(_SCRAPLING_UNAVAILABLE, reason=_SKIP_REASON)
async def test_fetch_public_page_escalates_when_static_fetch_is_blocked(monkeypatch):
    scraper_service = import_module("app.services.scraper_service")
    escalated = {"called": False}

    async def fake_get(url, **kwargs):
        return _response(403, "<html><body>Access Denied</body></html>")

    async def fake_stealthy(url, **kwargs):
        escalated["called"] = True
        return _response(200, "<html><body>Real content via browser</body></html>")

    monkeypatch.setattr(scraper_service.AsyncFetcher, "get", fake_get)
    monkeypatch.setattr(scraper_service.StealthyFetcher, "async_fetch", fake_stealthy)

    html = await scraper_service.fetch_public_page("https://example.com/protected")

    assert escalated["called"] is True
    assert "Real content via browser" in html


@pytest.mark.skipif(_SCRAPLING_UNAVAILABLE, reason=_SKIP_REASON)
async def test_fetch_public_page_escalates_on_captcha_marker_even_with_200_status(monkeypatch):
    scraper_service = import_module("app.services.scraper_service")
    escalated = {"called": False}

    async def fake_get(url, **kwargs):
        return _response(200, "<html><body>Please complete the CAPTCHA to continue</body></html>")

    async def fake_stealthy(url, **kwargs):
        escalated["called"] = True
        return _response(200, "<html><body>Real content</body></html>")

    monkeypatch.setattr(scraper_service.AsyncFetcher, "get", fake_get)
    monkeypatch.setattr(scraper_service.StealthyFetcher, "async_fetch", fake_stealthy)

    await scraper_service.fetch_public_page("https://example.com/captcha-wall")

    assert escalated["called"] is True


@pytest.mark.skipif(_SCRAPLING_UNAVAILABLE, reason=_SKIP_REASON)
async def test_fetch_public_page_does_not_escalate_on_clean_response(monkeypatch):
    scraper_service = import_module("app.services.scraper_service")

    async def fake_get(url, **kwargs):
        return _response(200, "<html><body>Perfectly normal page</body></html>")

    async def unexpected_stealthy(url, **kwargs):
        raise AssertionError("Should not escalate a clean 200 response")

    monkeypatch.setattr(scraper_service.AsyncFetcher, "get", fake_get)
    monkeypatch.setattr(scraper_service.StealthyFetcher, "async_fetch", unexpected_stealthy)

    html = await scraper_service.fetch_public_page("https://example.com/normal")

    assert "Perfectly normal page" in html


@pytest.mark.skipif(_SCRAPLING_UNAVAILABLE, reason=_SKIP_REASON)
async def test_fetch_public_page_raises_after_persistent_failure(monkeypatch):
    scraper_service = import_module("app.services.scraper_service")

    async def fake_get(url, **kwargs):
        return _response(403, "<html><body>Access Denied</body></html>")

    async def fake_stealthy(url, **kwargs):
        return _response(500, "<html><body>Still blocked</body></html>")

    monkeypatch.setattr(scraper_service.AsyncFetcher, "get", fake_get)
    monkeypatch.setattr(scraper_service.StealthyFetcher, "async_fetch", fake_stealthy)

    with pytest.raises(scraper_service.ScraperFetchError, match="Failed to fetch"):
        await scraper_service.fetch_public_page("https://example.com/always-blocked")


@pytest.mark.skipif(_SCRAPLING_UNAVAILABLE, reason=_SKIP_REASON)
async def test_fetch_public_page_rejects_non_html_content_type(monkeypatch):
    scraper_service = import_module("app.services.scraper_service")

    async def fake_get(url, **kwargs):
        return _response(200, "binary-ish", content_type="application/pdf")

    monkeypatch.setattr(scraper_service.AsyncFetcher, "get", fake_get)

    with pytest.raises(scraper_service.ScraperFetchError, match="Only public text and HTML"):
        await scraper_service.fetch_public_page("https://example.com/file.pdf")


async def test_fetch_public_page_raises_clear_error_when_scrapling_unavailable(monkeypatch):
    # The one thing about the "scrapling failed to import" path that's
    # testable regardless of environment: fetch_public_page must fail with
    # a clear ScraperFetchError, not an opaque AttributeError from calling
    # .get() on None.
    scraper_service = import_module("app.services.scraper_service")
    monkeypatch.setattr(scraper_service, "AsyncFetcher", None)

    with pytest.raises(scraper_service.ScraperFetchError, match="scrapling is not available"):
        await scraper_service.fetch_public_page("https://example.com/anything")


def test_looks_blocked_detects_status_codes_and_markers():
    scraper_service = import_module("app.services.scraper_service")

    assert scraper_service._looks_blocked(403, "<html>anything</html>") is True
    assert scraper_service._looks_blocked(429, "<html>anything</html>") is True
    assert scraper_service._looks_blocked(200, "<html>Are you a robot?</html>") is True
    assert scraper_service._looks_blocked(200, "<html>Perfectly normal page</html>") is False
