"""Workflow Phase 4 — authenticated API and persistence orchestration."""

import json
from pathlib import Path

from httpx import AsyncClient
from sqlalchemy import select

from app.models.design import Design
from app.models.design_version import DesignVersion
from app.schemas.requirements import RequirementsSpec
from app.services.layout_engine.engine import generate_plan
from app.services.llm_client import LLMUnavailable
from app.tests.conftest import TestSessionLocal

FIXTURES = Path(__file__).parent / "fixtures" / "requirements"


def _spec(name: str = "2bhk") -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


async def _register(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/auth/register",
        json={"name": "MVP User", "email": email, "password": "password123"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


async def _project(client: AsyncClient, token: str, title: str = "MVP Project") -> str:
    response = await client.post(
        "/api/projects",
        json={"title": title},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_mvp_pipeline_endpoints_require_access_token(client: AsyncClient):
    spec = _spec()
    plan = generate_plan(RequirementsSpec.model_validate(spec)).model_dump(mode="json")

    responses = [
        await client.post("/api/extract", json={"prompt": "2 bedroom house"}),
        await client.post(
            "/api/generate",
            json={"requirements": spec, "useDefaults": False},
        ),
        await client.post("/api/validate", json={"layout": plan}),
    ]

    assert [response.status_code for response in responses] == [401, 401, 401]
    assert all(response.json()["code"] == "UNAUTHORIZED" for response in responses)


async def test_extract_returns_deterministic_route_summary_and_optional_fields(
    client: AsyncClient,
    monkeypatch,
):
    token = await _register(client, "mvp-extract@example.com")
    extracted = RequirementsSpec.model_validate(_spec())

    async def fake_extract(prompt: str) -> RequirementsSpec:
        assert prompt == "Design a two bedroom apartment"
        return extracted

    monkeypatch.setattr("app.api.mvp.router.extract_requirements", fake_extract)

    response = await client.post(
        "/api/extract",
        json={"prompt": "Design a two bedroom apartment"},
        headers=_auth(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["requirements"] == extracted.model_dump(mode="json")
    assert body["route"] == "generate"
    assert body["questions"] == []
    assert body["optional_missing"] == []
    assert "2 bedrooms" in body["understood_summary"]
    assert "Plot: 9 × 12 m" in body["understood_summary"]


async def test_extract_maps_local_model_outage_to_standard_503(
    client: AsyncClient,
    monkeypatch,
):
    token = await _register(client, "mvp-llm-down@example.com")

    async def unavailable(_: str) -> RequirementsSpec:
        raise LLMUnavailable("LM Studio is down")

    monkeypatch.setattr("app.api.mvp.router.extract_requirements", unavailable)

    response = await client.post(
        "/api/extract",
        json={"prompt": "Design a two bedroom house"},
        headers=_auth(token),
    )

    assert response.status_code == 503
    assert response.json() == {
        "error": "AI service unavailable. Start LM Studio and try again.",
        "code": "SERVICE_UNAVAILABLE",
        "status": 503,
    }


async def test_generate_persists_all_canonical_artifacts_and_legacy_canvas_layout(
    client: AsyncClient,
):
    token = await _register(client, "mvp-generate@example.com")
    project_id = await _project(client, token)
    spec = _spec()

    response = await client.post(
        "/api/generate",
        json={
            "prompt": "Two bedroom apartment",
            "requirements": spec,
            "useDefaults": False,
            "projectId": project_id,
        },
        headers=_auth(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["quality"] == {"valid": True, "hard_violations": []}
    assert body["layout"]["plot"] == {
        "width_m": 9.0,
        "depth_m": 12.0,
        "facing": "east",
    }
    assert body["designId"]
    assert body["designVersionId"]

    async with TestSessionLocal() as session:
        design = await session.get(Design, body["designId"])
        version = await session.get(DesignVersion, body["designVersionId"])

        assert design is not None
        assert version is not None
        assert version.requirements_json == spec
        assert version.canonical_layout_json == body["layout"]
        assert version.quality_json == body["quality"]
        assert design.layout_json["metadata"]["pipeline"] == "mvp"
        object_types = {item["objectType"] for item in design.layout_json["rooms"]}
        assert {"room", "wall", "door"} <= object_types

    latest = await client.get(
        f"/api/design/project/{project_id}/latest",
        headers=_auth(token),
    )
    assert latest.status_code == 200
    assert latest.json()["designId"] == body["designId"]

    fetched = await client.get(
        f"/api/versions/{body['designVersionId']}",
        headers=_auth(token),
    )
    assert fetched.status_code == 200
    assert fetched.json()["layout"] == body["layout"]
    assert fetched.json()["requirements"] == spec


async def test_generate_returns_structured_plot_clarification_when_program_does_not_fit(
    client: AsyncClient,
):
    token = await _register(client, "mvp-small-plot@example.com")
    spec = _spec()
    spec["plot"] = {"width_m": 4.0, "depth_m": 4.0}

    response = await client.post(
        "/api/generate",
        json={"requirements": spec, "useDefaults": False},
        headers=_auth(token),
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["route"] == "conflict"
    assert "plot" in error["questions"][0].lower()
    assert response.json()["code"] == "UNPROCESSABLE_ENTITY"


async def test_generate_with_defaults_returns_explicit_assumptions(client: AsyncClient):
    token = await _register(client, "mvp-defaults@example.com")
    spec = _spec("1bhk")

    response = await client.post(
        "/api/generate",
        json={"requirements": spec, "useDefaults": True},
        headers=_auth(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["defaults_applied"] == ["9×12 m plot", "east facing"]
    assert body["requirements"]["plot"] == {"width_m": 9.0, "depth_m": 12.0}
    assert body["requirements"]["facing"] == "east"
    assert body["requirements"]["missing_info"] == []


async def test_validate_recomputes_hard_violations(client: AsyncClient):
    token = await _register(client, "mvp-validate@example.com")
    plan = generate_plan(RequirementsSpec.model_validate(_spec())).model_dump(mode="json")
    plan["rooms"][1]["x"] = plan["rooms"][0]["x"]
    plan["rooms"][1]["y"] = plan["rooms"][0]["y"]

    response = await client.post(
        "/api/validate",
        json={"layout": plan},
        headers=_auth(token),
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert "overlap" in {
        violation["code"] for violation in response.json()["hard_violations"]
    }


async def test_version_save_recomputes_quality_and_enforces_project_access(
    client: AsyncClient,
):
    owner = await _register(client, "mvp-version-owner@example.com")
    intruder = await _register(client, "mvp-version-intruder@example.com")
    project_id = await _project(client, owner, "Versioned MVP")
    spec = _spec()

    generated = await client.post(
        "/api/generate",
        json={
            "prompt": "Two bedroom apartment",
            "requirements": spec,
            "useDefaults": False,
            "projectId": project_id,
        },
        headers=_auth(owner),
    )
    assert generated.status_code == 200
    plan = generated.json()["layout"]
    forged_quality = {
        "valid": False,
        "hard_violations": [
            {"code": "forged", "room_ids": [], "message": "client says invalid"}
        ],
    }
    payload = {
        "prompt": "Saved after an edit",
        "requirements": spec,
        "layout": plan,
        "quality": forged_quality,
    }

    forbidden = await client.post(
        f"/api/projects/{project_id}/versions",
        json=payload,
        headers=_auth(intruder),
    )
    assert forbidden.status_code == 403

    saved = await client.post(
        f"/api/projects/{project_id}/versions",
        json=payload,
        headers=_auth(owner),
    )
    assert saved.status_code == 201
    assert saved.json()["versionNumber"] == 2
    assert saved.json()["quality"] == {"valid": True, "hard_violations": []}

    hidden = await client.get(
        f"/api/versions/{saved.json()['id']}",
        headers=_auth(intruder),
    )
    assert hidden.status_code == 403


async def test_duplicate_project_preserves_canonical_mvp_artifacts(
    client: AsyncClient,
):
    token = await _register(client, "mvp-duplicate@example.com")
    project_id = await _project(client, token, "Canonical source")
    spec = _spec()

    generated = await client.post(
        "/api/generate",
        json={
            "prompt": "Two bedroom apartment",
            "requirements": spec,
            "projectId": project_id,
        },
        headers=_auth(token),
    )
    assert generated.status_code == 200

    duplicate = await client.post(
        f"/api/projects/{project_id}/duplicate",
        headers=_auth(token),
    )
    assert duplicate.status_code == 201

    async with TestSessionLocal() as session:
        copied_version = await session.scalar(
            select(DesignVersion).where(
                DesignVersion.project_id == duplicate.json()["id"]
            )
        )
        assert copied_version is not None
        assert copied_version.requirements_json == generated.json()["requirements"]
        assert copied_version.canonical_layout_json == generated.json()["layout"]
        assert copied_version.quality_json == generated.json()["quality"]

    fetched = await client.get(
        f"/api/versions/{copied_version.id}",
        headers=_auth(token),
    )
    assert fetched.status_code == 200
    assert fetched.json()["layout"] == generated.json()["layout"]


async def test_extract_rejects_prompts_over_two_thousand_characters(client: AsyncClient):
    token = await _register(client, "mvp-long-prompt@example.com")

    response = await client.post(
        "/api/extract",
        json={"prompt": "x" * 2001},
        headers=_auth(token),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "UNPROCESSABLE_ENTITY"
