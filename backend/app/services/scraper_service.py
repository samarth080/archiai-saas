from datetime import datetime, timezone
from html.parser import HTMLParser

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scraped_record import ScrapedRecord
from app.models.scraper_run import ScraperRun
from app.models.scraper_source import ScraperSource
from app.services.robots_txt_checker import (
    ROBOTS_USER_AGENT,
    RobotsTxtChecker,
    default_robots_checker,
)


class ScraperBlockedError(ValueError):
    pass


class ScraperFetchError(ValueError):
    pass


class _VisibleTextParser(HTMLParser):
    _ignored_tags = {"script", "style", "svg", "noscript"}
    _ignored_void_tags = {"img"}

    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in self._ignored_void_tags:
            return
        if tag.lower() in self._ignored_tags:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._ignored_tags and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            text = " ".join(data.split())
            if text:
                self._chunks.append(text)

    def text(self) -> str:
        return " ".join(self._chunks)


def extract_visible_text(html: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(html)
    return parser.text()


async def fetch_public_page(url: str) -> str:
    headers = {"User-Agent": f"{ROBOTS_USER_AGENT}/0.1 (+public-text-reference-pipeline)"}
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if content_type and not any(value in content_type for value in ("html", "text")):
            raise ScraperFetchError("Only public text and HTML sources are supported")
        return response.text


async def scrape_public_text(
    url: str,
    checker: RobotsTxtChecker = default_robots_checker,
) -> str:
    policy = await checker.check_url(url)
    if not policy.allowed:
        raise ScraperBlockedError(policy.reason)
    html = await fetch_public_page(url)
    text = extract_visible_text(html)
    if not text:
        raise ScraperFetchError("No public text content found")
    return text


async def run_source_scraper(
    db: AsyncSession,
    source: ScraperSource,
) -> ScraperRun:
    run = ScraperRun(source_id=source.id, status="running")
    db.add(run)
    await db.flush()

    try:
        raw_text = await scrape_public_text(source.base_url)
        checked_at = datetime.now(timezone.utc)
        source.is_permitted = True
        source.last_checked = checked_at
        record = ScrapedRecord(
            source_id=source.id,
            run_id=run.id,
            source_url=source.base_url,
            accessed_at=checked_at,
            raw_text=raw_text,
            raw_metadata_json={"data_type": source.data_type},
        )
        db.add(record)
        run.status = "completed"
        run.records_collected = 1
        run.completed_at = checked_at
    except Exception as exc:
        source.is_permitted = False
        source.last_checked = datetime.now(timezone.utc)
        run.status = "failed"
        run.error_message = str(exc)
        run.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(run)
    return run
