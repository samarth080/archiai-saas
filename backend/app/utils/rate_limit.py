"""A small in-process rate limiter (Phase 0 H1).

Deliberately dependency-free — a sliding-window log keyed per (bucket, identity).
Identity is the authenticated user when a valid bearer token is present, else the
client IP, so many users behind one NAT don't starve each other and one user
can't bypass a per-user limit by rotating IPs.

Limitation: state is per-process. With multiple workers each holds its own
counters (the effective limit is limit x workers); a shared store (Redis) would
be needed for exactness. That's an acceptable MVP trade-off — abuse is still
bounded, and slowapi would have the same limitation without Redis.
"""
import time

from fastapi import HTTPException, Request

from app.utils.jwt import decode_token


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}

    def reset(self) -> None:
        """Clear all counters (used by the test fixture between tests)."""
        self._hits.clear()

    def allow(self, key: str, limit: int, window_seconds: float) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        bucket = self._hits.get(key)
        if bucket is None:
            bucket = []
            self._hits[key] = bucket
        # Drop timestamps that have aged out of the window.
        drop = 0
        for stamp in bucket:
            if stamp > cutoff:
                break
            drop += 1
        if drop:
            del bucket[:drop]
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


rate_limiter = RateLimiter()


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _identity(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth[:7].lower() == "bearer ":
        try:
            payload = decode_token(auth[7:].strip())
        except ValueError:
            payload = None
        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"
    return f"ip:{_client_ip(request)}"


def rate_limit(name: str, limit: int, window_seconds: float = 60.0, *, by_ip: bool = False):
    """Build a FastAPI dependency enforcing `limit` requests per window.

    `by_ip` pins the bucket to the client IP even when a valid bearer token is
    present. Credential endpoints must use it: otherwise an attacker exhausts
    the IP bucket, then attaches a token from a throwaway account of their own
    to mint a fresh bucket, multiplying their brute-force budget from one IP.
    """

    async def dependency(request: Request) -> None:
        identity = f"ip:{_client_ip(request)}" if by_ip else _identity(request)
        key = f"{name}:{identity}"
        if not rate_limiter.allow(key, limit, window_seconds):
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down and try again shortly.",
            )

    dependency.__name__ = f"rate_limit_{name}"
    return dependency
