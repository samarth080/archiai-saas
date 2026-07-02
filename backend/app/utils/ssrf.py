"""SSRF (server-side request forgery) protection for outbound fetches.

Any URL the server is about to fetch on a client's behalf — currently only the
scraper/data-pipeline — must first pass `assert_public_url`. It enforces an
http(s) scheme and resolves the hostname, rejecting the request if *any*
resolved address falls in a private, loopback, link-local (incl. the
169.254.169.254 cloud-metadata endpoint), reserved, multicast, or unspecified
range, for both IPv4 and IPv6. Resolution failures fail closed (rejected).

Because DNS is resolved here and again per redirect hop, this also blunts
DNS-rebinding: a hostname that resolves to a public IP at source-create time
but a private one at fetch time is caught at fetch time.
"""
import asyncio
import ipaddress
import socket
from typing import Callable, Iterable
from urllib.parse import urlsplit

# A resolver returns getaddrinfo-style 5-tuples so tests can inject fakes.
Resolver = Callable[[str, int | None], Iterable[tuple]]

_ALLOWED_SCHEMES = {"http", "https"}
_MAX_URL_LENGTH = 2048


class UnsafeURLError(ValueError):
    """Raised when a URL is not safe to fetch server-side."""


def _ip_is_public(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    # Collapse IPv4-mapped/6to4/Teredo IPv6 to their embedded IPv4 first, so an
    # attacker can't smuggle 127.0.0.1 in as ::ffff:127.0.0.1.
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped
        elif ip.sixtofour is not None:
            ip = ip.sixtofour
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _resolve(host: str, resolver: Resolver | None) -> set[str]:
    resolve = resolver or socket.getaddrinfo
    try:
        results = resolve(host, None)
    except (socket.gaierror, OSError, UnicodeError) as exc:
        raise UnsafeURLError(f"Could not resolve host '{host}'") from exc
    addresses: set[str] = set()
    for entry in results:
        sockaddr = entry[4]
        if sockaddr and sockaddr[0]:
            addresses.add(sockaddr[0])
    if not addresses:
        raise UnsafeURLError(f"Could not resolve host '{host}'")
    return addresses


def assert_public_url(url: str, *, resolver: Resolver | None = None) -> str:
    """Return the URL unchanged if safe to fetch, else raise UnsafeURLError."""
    if not url or len(url) > _MAX_URL_LENGTH:
        raise UnsafeURLError("URL is missing or too long")

    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise UnsafeURLError("Only http and https URLs may be fetched")

    host = parsed.hostname
    if not host:
        raise UnsafeURLError("URL has no host")

    for address in _resolve(host, resolver):
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise UnsafeURLError(f"Unresolvable address for '{host}'") from exc
        if not _ip_is_public(ip):
            raise UnsafeURLError(
                f"Refusing to fetch '{host}': resolves to non-public address {address}"
            )
    return url.strip()


async def assert_public_url_async(url: str, *, resolver: Resolver | None = None) -> str:
    """Async wrapper — runs the blocking DNS resolution off the event loop."""
    return await asyncio.to_thread(assert_public_url, url, resolver=resolver)
