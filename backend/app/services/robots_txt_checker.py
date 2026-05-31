from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx

ROBOTS_USER_AGENT = "ArchiAIReferenceBot"
FetchText = Callable[[str], Awaitable[tuple[int, str]]]


@dataclass(frozen=True)
class RobotsCheckResult:
    allowed: bool
    reason: str
    robots_txt_url: str | None = None


async def _fetch_text(url: str) -> tuple[int, str]:
    headers = {"User-Agent": f"{ROBOTS_USER_AGENT}/0.1 (+public-text-reference-pipeline)"}
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(url)
        return response.status_code, response.text


class RobotsTxtChecker:
    def __init__(self, fetch_text: FetchText | None = None) -> None:
        self._fetch_text = fetch_text or _fetch_text

    async def check_url(self, url: str) -> RobotsCheckResult:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return RobotsCheckResult(False, "Invalid public URL")

        robots_txt_url = urlunsplit((parsed.scheme, parsed.netloc, "/robots.txt", "", ""))
        try:
            status_code, robots_text = await self._fetch_text(robots_txt_url)
        except (httpx.HTTPError, OSError, TimeoutError) as exc:
            return RobotsCheckResult(
                False,
                f"Robots.txt check failed: {exc}",
                robots_txt_url,
            )

        if status_code == 404:
            return RobotsCheckResult(True, "Robots.txt not found; public text path allowed", robots_txt_url)
        if status_code >= 400:
            return RobotsCheckResult(
                False,
                f"Robots.txt check returned HTTP {status_code}",
                robots_txt_url,
            )

        parser = RobotFileParser()
        parser.set_url(robots_txt_url)
        parser.parse(robots_text.splitlines())
        if not parser.can_fetch(ROBOTS_USER_AGENT, url):
            return RobotsCheckResult(False, "Disallowed by robots.txt", robots_txt_url)
        return RobotsCheckResult(True, "Allowed by robots.txt", robots_txt_url)


default_robots_checker = RobotsTxtChecker()
