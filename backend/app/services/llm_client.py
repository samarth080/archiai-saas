"""LM Studio (OpenAI-compatible) client.

``chat_structured`` is the only model-call boundary for MVP extraction. Calls
are serialized because the development RTX 4060 serves one model request at a
time; callers receive typed operational errors rather than raw httpx failures.

LM Studio runs on the HOST (desktop app, direct GPU access), not in Docker.
From inside the backend container it is reached via
``http://host.docker.internal:1234/v1`` (settings.LLM_BASE_URL); LM Studio's
"Serve on Local Network" must be enabled or the server binds localhost-only and
is unreachable from containers.
"""
import asyncio
import json
from collections.abc import Callable
from typing import Any

import httpx

from app.config.settings import settings


class LLMError(RuntimeError):
    """Base class for expected local-model service failures."""


class LLMTimeout(LLMError):
    """LM Studio accepted the connection but did not answer in time."""


class LLMUnavailable(LLMError):
    """LM Studio is down, has no model loaded, or rejected the request."""


class LLMInvalidOutput(LLMError):
    """LM Studio answered, but not with the requested JSON object."""


# One process-wide queue protects the single local GPU from concurrent model
# inference. It intentionally wraps both model discovery and completion.
_gpu_semaphore = asyncio.Semaphore(1)

# Private seam used by unit tests to install httpx.MockTransport without adding
# another dependency such as respx.
_client_factory: Callable[..., httpx.AsyncClient] = httpx.AsyncClient


def _raise_for_status(response: httpx.Response, operation: str) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise LLMUnavailable(
            f"LM Studio {operation} failed with HTTP {response.status_code}."
        ) from exc


async def _loaded_model_id(client: httpx.AsyncClient) -> str:
    """Return an exact model id advertised by LM Studio's ``/models`` route."""
    response = await client.get(f"{settings.LLM_BASE_URL.rstrip('/')}/models")
    _raise_for_status(response, "model discovery")
    try:
        payload = response.json()
        model_ids = [
            item["id"]
            for item in payload["data"]
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise LLMInvalidOutput(
            "LM Studio /models returned an invalid response envelope."
        ) from exc

    if not model_ids:
        raise LLMUnavailable("LM Studio is reachable, but no model is loaded.")

    configured = settings.LLM_MODEL.strip()
    if configured:
        if configured not in model_ids:
            raise LLMUnavailable(
                f"Configured LLM_MODEL '{configured}' is not loaded in LM Studio."
            )
        return configured
    return model_ids[0]


def _parse_completion(response: httpx.Response) -> dict[str, Any]:
    _raise_for_status(response, "structured completion")
    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise LLMInvalidOutput(
            "LM Studio returned an invalid chat-completion envelope."
        ) from exc

    if not isinstance(content, str):
        raise LLMInvalidOutput("LM Studio completion content was not a JSON string.")
    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMInvalidOutput("LM Studio completion was not valid JSON.") from exc
    if not isinstance(result, dict):
        raise LLMInvalidOutput("LM Studio completion must be a JSON object.")
    return result


async def chat_structured(
    system: str,
    user: str,
    schema: dict[str, Any],
    timeout_s: float = settings.LLM_TIMEOUT_S,
) -> dict[str, Any]:
    """Call LM Studio with strict JSON-schema output and return one JSON object."""
    async with _gpu_semaphore:
        try:
            async with _client_factory(timeout=timeout_s) as client:
                model_id = await _loaded_model_id(client)
                response = await client.post(
                    f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions",
                    json={
                        "model": model_id,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "temperature": 0,
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "requirements",
                                "schema": schema,
                                "strict": True,
                            },
                        },
                    },
                )
        except LLMError:
            raise
        except httpx.TimeoutException as exc:
            raise LLMTimeout(
                f"LM Studio did not respond within {timeout_s:g} seconds."
            ) from exc
        except httpx.RequestError as exc:
            raise LLMUnavailable(
                "LM Studio is unavailable. Start its local server and load a model."
            ) from exc

        return _parse_completion(response)


async def llm_reachable(timeout_s: float = 2.0) -> bool:
    """True if the LM Studio server answers GET /models. Never raises."""
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.get(f"{settings.LLM_BASE_URL.rstrip('/')}/models")
        return response.status_code == 200
    except Exception:
        return False
