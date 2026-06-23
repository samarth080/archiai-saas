from datetime import datetime, timezone

from app.models.layout_pattern import LayoutPattern
from app.models.scraper_source import ScraperSource
from app.models.user import User
from app.services.layout_pattern_service import (
    audit_layout_pattern,
    fallback_layout_rules,
    get_layout_pattern_rules,
)
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
    assert rules.applied_pattern_count == 1
    assert rules.ignored_pattern_count == 0


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
    assert rules.applied_pattern_count == 0
    assert rules.ignored_pattern_count == 1


async def test_invalid_high_confidence_pattern_is_ignored_by_rule_resolver():
    async with TestSessionLocal() as session:
        user = User(name="Pattern User", email="pattern-invalid@example.com", hashed_password="unused")
        session.add(user)
        await session.flush()
        source = ScraperSource(
            name="Invalid public guidance",
            base_url="https://example.com/invalid-guide",
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
                accessed_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                building_type="apartment",
                room_type="bedroom",
                typical_area_sqm_min=40.0,
                typical_area_sqm_max=4.0,
                zone="sleeping-zone",
                adjacent_to=["bathroom"],
                avoid_adjacent_to=["kitchen"],
                confidence="high",
            )
        )
        await session.commit()

        rules = await get_layout_pattern_rules(session, "apartment", {"bedroom"})

    assert rules.pattern_data_used is False
    assert rules.room_size_range("bedroom") == (10.0, 16.0)
    assert rules.zone_for("bedroom") == "private"
    assert rules.ignored_pattern_count == 1


def test_pattern_audit_flags_missing_or_unsafe_scraped_data():
    pattern = LayoutPattern(
        source_id="source-id",
        source_url="https://example.com/bad-guide",
        accessed_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
        building_type=None,
        room_type=None,
        typical_area_sqm_min=-1.0,
        typical_area_sqm_max=400.0,
        zone="mystery",
        adjacent_to=[],
        avoid_adjacent_to=[],
        confidence="low",
    )

    audit = audit_layout_pattern(pattern)

    assert audit.usable is False
    assert "Missing room type" in audit.warnings
    assert "Pattern confidence is not trusted for generation" in audit.warnings
    assert "Unsupported zone: mystery" in audit.warnings
    assert "Room area range must be positive" in audit.warnings


async def test_pattern_rule_lookup_normalizes_requested_terms():
    async with TestSessionLocal() as session:
        user = User(name="Pattern User", email="pattern-normalized@example.com", hashed_password="unused")
        session.add(user)
        await session.flush()
        source = ScraperSource(
            name="Normalized guidance",
            base_url="https://example.com/normalized-guide",
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
                accessed_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                building_type="apartment",
                room_type="bathroom",
                typical_area_sqm_min=5.0,
                typical_area_sqm_max=7.0,
                zone="service",
                confidence="high",
            )
        )
        await session.commit()

        rules = await get_layout_pattern_rules(session, "flat", {"washroom"})

    assert rules.pattern_data_used is True
    assert rules.building_type == "apartment"
    assert rules.room_size_range("bathroom") == (5.0, 7.0)


async def test_high_confidence_source_pattern_beats_seed_pattern():
    async with TestSessionLocal() as session:
        user = User(name="Pattern User", email="pattern-weighted@example.com", hashed_password="unused")
        session.add(user)
        await session.flush()
        source = ScraperSource(
            name="Weighted guidance",
            base_url="https://example.com/weighted-guide",
            robots_txt_url="https://example.com/robots.txt",
            data_type="text/html",
            source_category="room_size_reference",
            created_by=user.id,
        )
        session.add(source)
        await session.flush()
        session.add_all(
            [
                LayoutPattern(
                    source_id=source.id,
                    source_url="seed:mvp-patterns",
                    accessed_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                    building_type="apartment",
                    room_type="kitchen",
                    typical_area_sqm_min=8.0,
                    typical_area_sqm_max=10.0,
                    zone="service",
                    confidence="seed",
                ),
                LayoutPattern(
                    source_id=source.id,
                    source_url=source.base_url,
                    accessed_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                    building_type="apartment",
                    room_type="kitchen",
                    typical_area_sqm_min=12.0,
                    typical_area_sqm_max=16.0,
                    zone="service",
                    confidence="high",
                ),
            ]
        )
        await session.commit()

        rules = await get_layout_pattern_rules(session, "apartment", {"kitchen"})

    assert rules.pattern_data_source == "source-derived"
    assert rules.room_size_range("kitchen") == (12.0, 16.0)
    assert rules.applied_pattern_count == 1
    assert rules.ignored_pattern_count == 0


async def test_multiple_same_tier_patterns_are_aggregated_with_the_median():
    """
    Sprint 17 Phase 3 — three independently scraped high-confidence sources
    disagreeing on bedroom area should produce the MEDIAN, a real
    statistical prior, not just whichever row the resolver happened to see
    first.
    """
    async with TestSessionLocal() as session:
        user = User(name="Pattern User", email="pattern-aggregate@example.com", hashed_password="unused")
        session.add(user)
        await session.flush()
        source = ScraperSource(
            name="Three sources",
            base_url="https://example.com/three-sources",
            robots_txt_url="https://example.com/robots.txt",
            data_type="text/html",
            source_category="room_size_reference",
            created_by=user.id,
        )
        session.add(source)
        await session.flush()
        session.add_all(
            [
                LayoutPattern(
                    source_id=source.id, source_url="https://a.example.com",
                    accessed_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                    building_type="apartment", room_type="bedroom",
                    typical_area_sqm_min=9.0, typical_area_sqm_max=13.0,
                    zone="private", adjacent_to=["bathroom"], confidence="high",
                ),
                LayoutPattern(
                    source_id=source.id, source_url="https://b.example.com",
                    accessed_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                    building_type="apartment", room_type="bedroom",
                    typical_area_sqm_min=11.0, typical_area_sqm_max=15.0,
                    zone="private", adjacent_to=["bathroom"], confidence="high",
                ),
                LayoutPattern(
                    source_id=source.id, source_url="https://c.example.com",
                    accessed_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                    building_type="apartment", room_type="bedroom",
                    typical_area_sqm_min=17.0, typical_area_sqm_max=23.0,
                    zone="private", adjacent_to=["hallway"], confidence="high",
                ),
            ]
        )
        await session.commit()

        rules = await get_layout_pattern_rules(session, "apartment", {"bedroom"})

    # Median of (9, 11, 17) = 11; median of (13, 15, 23) = 15.
    assert rules.room_size_range("bedroom") == (11.0, 15.0)
    assert rules.applied_pattern_count == 3
    # "bathroom" was reported by 2 of 3 sources (meets the support threshold
    # for n=3); "hallway" was reported by only 1 and gets dropped.
    assert rules.adjacency_for("bedroom") == ("bathroom",)


async def test_single_source_adjacency_is_kept_even_without_corroboration():
    """With only one or two sources there's nothing to corroborate against
    yet, so any mention should still count (matches the prior single-pattern
    behaviour) rather than being dropped for lack of support."""
    async with TestSessionLocal() as session:
        user = User(name="Pattern User", email="pattern-single@example.com", hashed_password="unused")
        session.add(user)
        await session.flush()
        source = ScraperSource(
            name="Single source",
            base_url="https://example.com/single-source",
            robots_txt_url="https://example.com/robots.txt",
            data_type="text/html",
            source_category="room_size_reference",
            created_by=user.id,
        )
        session.add(source)
        await session.flush()
        session.add(
            LayoutPattern(
                source_id=source.id, source_url=source.base_url,
                accessed_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                building_type="apartment", room_type="bedroom",
                typical_area_sqm_min=11.0, typical_area_sqm_max=15.0,
                zone="private", adjacent_to=["bathroom", "hallway"], confidence="high",
            )
        )
        await session.commit()

        rules = await get_layout_pattern_rules(session, "apartment", {"bedroom"})

    assert rules.adjacency_for("bedroom") == ("bathroom", "hallway")
