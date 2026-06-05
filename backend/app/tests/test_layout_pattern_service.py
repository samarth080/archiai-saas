from datetime import datetime, timezone

from app.models.layout_pattern import LayoutPattern
from app.models.scraper_source import ScraperSource
from app.models.user import User
from app.services.layout_pattern_service import fallback_layout_rules, get_layout_pattern_rules
from app.tests.conftest import TestSessionLocal


def test_fallback_rules_are_available_without_database_patterns():
    rules = fallback_layout_rules("apartment", {"bedroom", "kitchen"})

    assert rules.pattern_data_used is False
    assert rules.room_size_range("bedroom") == (10.0, 16.0)
    assert rules.zone_for("kitchen") == "service"
    assert rules.adjacency_for("kitchen") == ("living_room", "dining_room", "storage")
    assert rules.avoid_adjacency_for("kitchen") == ("bedroom", "bathroom")
    assert rules.layout_patterns == ("public_private_split",)


async def test_database_pattern_overlays_fallback_rule():
    async with TestSessionLocal() as session:
        user = User(name="Pattern User", email="pattern@example.com", hashed_password="unused")
        session.add(user)
        await session.flush()
        source = ScraperSource(
            name="Public apartment guidance",
            base_url="https://example.com/layout-guide",
            robots_txt_url="https://example.com/robots.txt",
            data_type="text/html",
            source_category="room_size_reference",
            created_by=user.id,
        )
        session.add(source)
        await session.flush()
        session.add(
            LayoutPattern(
                source_id=source.id,
                source_url=source.base_url,
                accessed_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
                building_type="apartment",
                layout_pattern="quiet_private_zone",
                room_type="bedroom",
                typical_area_sqm_min=11.0,
                typical_area_sqm_max=15.0,
                zone="private",
                adjacent_to=["bathroom", "hallway"],
                avoid_adjacent_to=["garage", "kitchen"],
                confidence="high",
            )
        )
        await session.commit()

        rules = await get_layout_pattern_rules(session, "apartment", {"bedroom"})

    assert rules.pattern_data_used is True
    assert rules.room_size_range("bedroom") == (11.0, 15.0)
    assert rules.zone_for("bedroom") == "private"
    assert rules.adjacency_for("bedroom") == ("bathroom", "hallway")
    assert rules.avoid_adjacency_for("bedroom") == ("garage", "kitchen")
    assert "quiet_private_zone" in rules.layout_patterns


async def test_low_confidence_database_pattern_does_not_replace_fallback():
    async with TestSessionLocal() as session:
        user = User(name="Pattern User", email="pattern-low@example.com", hashed_password="unused")
        session.add(user)
        await session.flush()
        source = ScraperSource(
            name="Sparse public guidance",
            base_url="https://example.com/sparse-guide",
            robots_txt_url="https://example.com/robots.txt",
            data_type="text/html",
            source_category="room_size_reference",
            created_by=user.id,
        )
        session.add(source)
        await session.flush()
        session.add(
            LayoutPattern(
                source_id=source.id,
                source_url=source.base_url,
                accessed_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
                building_type="apartment",
                room_type="bedroom",
                typical_area_sqm_min=4.0,
                typical_area_sqm_max=40.0,
                zone="service",
                confidence="low",
            )
        )
        await session.commit()

        rules = await get_layout_pattern_rules(session, "apartment", {"bedroom"})

    assert rules.pattern_data_used is False
    assert rules.room_size_range("bedroom") == (10.0, 16.0)
    assert rules.zone_for("bedroom") == "private"
