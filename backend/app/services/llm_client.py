"""LM Studio (OpenAI-compatible) client.

Phase 0 ships only reachability probing for /api/health; Phase 2 adds
``chat_structured`` (schema-constrained extraction with the single-GPU
semaphore, timeouts, and typed errors) on top of this module.

LM Studio runs on the HOST (desktop app, direct GPU access), not in Docker.
From inside the backend container it is reached via
``http://host.docker.internal:1234/v1`` (settings.LLM_BASE_URL); LM Studio's
"Serve on Local Network" must be enabled or the server binds localhost-only and
is unreachable from containers.
"""
import httpx

from app.config.settings import settings


async def llm_reachable(timeout_s: float = 2.0) -> bool:
    """True if the LM Studio server answers GET /models. Never raises."""
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.get(f"{settings.LLM_BASE_URL.rstrip('/')}/models")
        return response.status_code == 200
    except Exception:
        return False
