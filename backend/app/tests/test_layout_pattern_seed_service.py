import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.models.layout_pattern import LayoutPattern
from app.models.scraper_source import ScraperSource
from app.models.user import User
from app.services.layout_pattern_seed_service import (
    MVP_LAYOUT_PATTERN_SEEDS,
    SEED_SOURCE_URL,
    seed_mvp_layout_patterns,
)
from app.services.layout_pattern_service import get_layout_pattern_rules
from app.services.layout_service import generate_layout
from app.services.prompt_service import RoomSpec
from app.services.scraper_management_service import delete_scraper_source
from app.tests.conftest import TestSessionLocal


async def _create_user(session, email: str = "seed-owner@example.com") -> User:
    user = User(name="Seed Owner", email=email, hashed_password="unused")
    session.add(user)
    await session.flush()
    return user


async def test_seed_service_creates_expected_clearly_labeled_mvp_patterns():
    async with TestSessionLocal() as session:
        user = await _create_user(session)

        result = await seed_mvp_layout_patterns(session, created_by=user.id)
        patterns = (
            await session.execute(
                select(LayoutPattern).where(LayoutPattern.source_url == SEED_SOURCE_URL)
            )
        ).scalars().all()
        source = await session.get(ScraperSource, result.source_id)

    assert result.created == len(MVP_LAYOUT_PATTERN_SEEDS)
    assert result.existing == 0
    assert len(patterns) == len(MVP_LAYOUT_PATTERN_SEEDS)
    assert source.base_url == SEED_SOURCE_URL
    assert source.data_type == "structured_seed"
    assert source.source_category == "dev_seed_layout_patterns"
    assert {pattern.confidence for pattern in patterns} == {"seed"}
    assert all(pattern.accessed_at is not None for pattern in patterns)
    assert all(pattern.placement_notes.startswith("MVP seed only:") for pattern in patterns)


async def test_seed_service_is_idempotent():
    async with TestSessionLocal() as session:
        user = await _create_user(session)

        first = await seed_mvp_layout_patterns(session, created_by=user.id)
        second = await seed_mvp_layout_patterns(session, created_by=user.id)
        count = await session.scalar(select(func.count()).select_from(LayoutPattern))

    assert first.created == len(MVP_LAYOUT_PATTERN_SEEDS)
    assert second.created == 0
    assert second.existing == len(MVP_LAYOUT_PATTERN_SEEDS)
    assert count == len(MVP_LAYOUT_PATTERN_SEEDS)


async def test_seed_patterns_are_used_without_claiming_source_derived_provenance():
    async with TestSessionLocal() as session:
        user = await _create_user(session)
        await seed_mvp_layout_patterns(session, created_by=user.id)

        rules = await get_layout_pattern_rules(session, "retail", {"storage"})

    assert rules.pattern_data_used is True
    assert rules.pattern_data_source == "seed"
    assert rules.room_size_range("storage") == (6.0, 20.0)
    assert rules.zone_for("storage") == "service"
    assert rules.adjacency_for("storage") == ("retail_display",)
    assert rules.avoid_adjacency_for("storage") == ("entry",)

    layout = generate_layout(
        [RoomSpec("Storage", "storage", 3.0, 3.0, 3.0)],
        building_type="retail",
        pattern_rules=rules,
    )
    assert layout["metadata"]["patternDataUsed"] is True
    assert layout["metadata"]["patternDataSource"] == "seed"
    assert "pattern-data:seed" in layout["insights"]["appliedRules"]


async def test_seed_source_with_pattern_rows_cannot_be_deleted():
    async with TestSessionLocal() as session:
        user = await _create_user(session)
        result = await seed_mvp_layout_patterns(session, created_by=user.id)

        with pytest.raises(HTTPException, match="recorded runs or patterns"):
            await delete_scraper_source(session, result.source_id)
