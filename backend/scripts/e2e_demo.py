"""Live Phase 4 smoke: local LLM extract -> generate -> persist -> fetch.

Usage (choose one authentication method):
    ARCHIAI_ACCESS_TOKEN=... python scripts/e2e_demo.py
    ARCHIAI_DEMO_EMAIL=... ARCHIAI_DEMO_PASSWORD=... python scripts/e2e_demo.py

Optional environment variables: ARCHIAI_API_URL, ARCHIAI_PROJECT_ID, and
ARCHIAI_DEMO_PROMPT. No credential or token is stored by this script.
"""

import json
import os
import sys
import urllib.error
import urllib.request


def _request(
    base_url: str,
    token: str | None,
    method: str,
    path: str,
    payload: dict | None = None,
    *,
    authenticated: bool = True,
) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if authenticated and token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"{method} {path} failed ({exc.code}): {detail}"
        ) from exc


def main() -> int:
    base_url = os.getenv("ARCHIAI_API_URL", "http://localhost:8000").rstrip("/")
    token = os.getenv("ARCHIAI_ACCESS_TOKEN")
    email = os.getenv("ARCHIAI_DEMO_EMAIL")
    password = os.getenv("ARCHIAI_DEMO_PASSWORD")
    project_id = os.getenv("ARCHIAI_PROJECT_ID")
    prompt = os.getenv(
        "ARCHIAI_DEMO_PROMPT",
        (
            "Design a 3BHK house on a 30x40 feet plot, east facing, "
            "with a pooja room and an attached bathroom for the master bedroom"
        ),
    )

    if not token:
        if not email or not password:
            raise RuntimeError(
                "Set ARCHIAI_ACCESS_TOKEN, or both ARCHIAI_DEMO_EMAIL and "
                "ARCHIAI_DEMO_PASSWORD."
            )
        login = _request(
            base_url,
            None,
            "POST",
            "/api/auth/login",
            {"email": email, "password": password},
            authenticated=False,
        )
        token = login["access_token"]

    if not project_id:
        project = _request(
            base_url,
            token,
            "POST",
            "/api/projects",
            {"title": "Local MVP end-to-end demo"},
        )
        project_id = project["id"]

    extracted = _request(
        base_url,
        token,
        "POST",
        "/api/extract",
        {"prompt": prompt},
    )
    if extracted["route"] != "generate":
        raise RuntimeError(
            f"Extraction requires clarification: {extracted['route']} "
            f"{extracted.get('questions', [])}"
        )

    generated = _request(
        base_url,
        token,
        "POST",
        "/api/generate",
        {
            "prompt": prompt,
            "requirements": extracted["requirements"],
            "useDefaults": True,
            "projectId": project_id,
        },
    )
    version_id = generated["designVersionId"]
    stored = _request(
        base_url,
        token,
        "GET",
        f"/api/versions/{version_id}",
    )

    assert generated["quality"]["valid"] is True
    assert stored["layout"] == generated["layout"]
    assert stored["requirements"] == generated["requirements"]

    print(
        json.dumps(
            {
                "status": "ok",
                "projectId": project_id,
                "designVersionId": version_id,
                "route": extracted["route"],
                "rooms": len(generated["layout"]["rooms"]),
                "hardViolations": len(
                    generated["quality"]["hard_violations"]
                ),
                "defaultsApplied": generated["defaults_applied"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, RuntimeError) as exc:
        print(f"MVP E2E failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
