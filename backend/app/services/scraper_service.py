from datetime import datetime, timezone
from html.parser import HTMLParser

from scrapling import AsyncFetcher
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from scrapling import StealthyFetcher
except ImportError:  # pragma: no cover - the [fetchers] extra's browser deps are optional at runtime
    StealthyFetcher = None

from app.models.layout_pattern import LayoutPattern
from app.models.scraped_record import ScrapedRecord
from app.models.scraper_run import ScraperRun
from app.models.scraper_source import ScraperSource
from app.services.robots_txt_checker import (
    ROBOTS_USER_AGENT,
    RobotsTxtChecker,
    default_robots_checker,
)
from app.services.scraper_cleaning_service import extract_layout_metadata


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


_BLOCKED_STATUS_CODES = {403, 429, 503}
_BLOCKED_MARKERS = ("captcha", "access denied", "are you a robot", "checking your browser")


def _looks_blocked(status: int, html_content: str) -> bool:
    if status in _BLOCKED_STATUS_CODES:
        return True
    return any(marker in html_content[:2000].lower() for marker in _BLOCKED_MARKERS)


async def fetch_public_page(url: str) -> str:
    """
    Fetch a public page's HTML. Tries a plain (fast, no-browser) request first;
    escalates to a real stealthy browser session only if that looks blocked or
    failed — JS-rendered / anti-bot-protected sites (e.g. ArchDaily, Dezeen)
    often need the browser to even serve real content. The escalation needs
    `scrapling install` to have downloaded its browser binaries; if that
    hasn't been run, StealthyFetcher import fails at module load and this
    function simply skips the escalation rather than crashing.
    """
    headers = {"User-Agent": f"{ROBOTS_USER_AGENT}/0.1 (+public-text-reference-pipeline)"}
    response = await AsyncFetcher.get(url, timeout=15, headers=headers, follow_redirects=True)
    html_content = str(response.html_content)

    if (response.status >= 400 or _looks_blocked(response.status, html_content)) and StealthyFetcher is not None:
        response = await StealthyFetcher.async_fetch(url, headless=True, network_idle=True, timeout=20000)
        html_content = str(response.html_content)

    if response.status >= 400:
        raise ScraperFetchError(f"Failed to fetch {url}: HTTP {response.status}")

    content_type = (response.headers or {}).get("content-type", "")
    if content_type and not any(value in content_type for value in ("html", "text")):
        raise ScraperFetchError("Only public text and HTML sources are supported")
    return html_content


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
        patterns = extract_layout_metadata(
            raw_text,
            source_url=source.base_url,
            accessed_at=checked_at,
        )
        db.add_all(LayoutPattern(source_id=source.id, **pattern) for pattern in patterns)
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
