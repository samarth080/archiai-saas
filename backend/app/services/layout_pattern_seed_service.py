from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.layout_pattern import LayoutPattern
from app.models.scraper_source import ScraperSource

SEED_SOURCE_URL = "seed:mvp-patterns"

MVP_LAYOUT_PATTERN_SEEDS: tuple[dict, ...] = (
    {
        "building_type": "apartment",
        "layout_pattern": "public_private_split",
        "room_type": "bedroom",
        "typical_area_sqm_min": 10.0,
        "typical_area_sqm_max": 16.0,
        "zone": "private",
        "adjacent_to": ["bathroom", "hallway"],
        "avoid_adjacent_to": ["kitchen", "garage"],
        "room_to_total_area_ratio_min": 0.12,
        "room_to_total_area_ratio_max": 0.2,
        "placement_notes": "MVP seed only: group bedrooms in a quieter private zone.",
    },
    {
        "building_type": "apartment",
        "layout_pattern": "public_private_split",
        "room_type": "bathroom",
        "typical_area_sqm_min": 4.0,
        "typical_area_sqm_max": 8.0,
        "zone": "service",
        "adjacent_to": ["bedroom", "hallway"],
        "avoid_adjacent_to": ["kitchen"],
        "room_to_total_area_ratio_min": 0.05,
        "room_to_total_area_ratio_max": 0.1,
        "placement_notes": "MVP seed only: keep bathrooms near bedrooms or circulation.",
    },
    {
        "building_type": "apartment",
        "layout_pattern": "public_private_split",
        "room_type": "kitchen",
        "typical_area_sqm_min": 8.0,
        "typical_area_sqm_max": 18.0,
        "zone": "service",
        "adjacent_to": ["living_room", "dining_room"],
        "avoid_adjacent_to": ["bedroom"],
        "room_to_total_area_ratio_min": 0.1,
        "room_to_total_area_ratio_max": 0.18,
        "placement_notes": "MVP seed only: keep kitchen close to living and dining areas.",
    },
    {
        "building_type": "apartment",
        "layout_pattern": "public_private_split",
        "room_type": "living_room",
        "typical_area_sqm_min": 16.0,
        "typical_area_sqm_max": 30.0,
        "zone": "public",
        "adjacent_to": ["entry", "kitchen", "dining_room"],
        "avoid_adjacent_to": [],
        "room_to_total_area_ratio_min": 0.2,
        "room_to_total_area_ratio_max": 0.35,
        "placement_notes": "MVP seed only: place the living room in the public arrival cluster.",
    },
    {
        "building_type": "studio",
        "layout_pattern": "compact_open_plan",
        "room_type": "living_room",
        "typical_area_sqm_min": 18.0,
        "typical_area_sqm_max": 32.0,
        "zone": "public",
        "adjacent_to": ["kitchen"],
        "avoid_adjacent_to": [],
        "room_to_total_area_ratio_min": 0.45,
        "room_to_total_area_ratio_max": 0.7,
        "placement_notes": "MVP seed only: use a compact open-plan living and sleeping area.",
    },
    {
        "building_type": "house",
        "layout_pattern": "public_ground_private_upper",
        "room_type": "living_room",
        "typical_area_sqm_min": 18.0,
        "typical_area_sqm_max": 34.0,
        "zone": "public",
        "adjacent_to": ["entry", "kitchen", "dining_room"],
        "avoid_adjacent_to": [],
        "room_to_total_area_ratio_min": 0.14,
        "room_to_total_area_ratio_max": 0.26,
        "placement_notes": "MVP seed only: prefer public rooms on the ground floor and bedrooms upstairs.",
    },
    {
        "building_type": "office",
        "layout_pattern": "entry_work_support",
        "room_type": "reception",
        "typical_area_sqm_min": 8.0,
        "typical_area_sqm_max": 18.0,
        "zone": "public",
        "adjacent_to": ["entry", "workspace"],
        "avoid_adjacent_to": [],
        "placement_notes": "MVP seed only: place reception close to the entry and work area.",
    },
    {
        "building_type": "office",
        "layout_pattern": "entry_work_support",
        "room_type": "meeting_room",
        "typical_area_sqm_min": 10.0,
        "typical_area_sqm_max": 24.0,
        "zone": "private",
        "adjacent_to": ["workspace"],
        "avoid_adjacent_to": [],
        "placement_notes": "MVP seed only: keep meeting rooms near the workspace.",
    },
    {
        "building_type": "clinic",
        "layout_pattern": "waiting_consultation_split",
        "room_type": "waiting_room",
        "typical_area_sqm_min": 10.0,
        "typical_area_sqm_max": 24.0,
        "zone": "public",
        "adjacent_to": ["entry", "reception"],
        "avoid_adjacent_to": [],
        "placement_notes": "MVP seed only: keep the waiting area near reception.",
    },
    {
        "building_type": "clinic",
        "layout_pattern": "waiting_consultation_split",
        "room_type": "consultation_room",
        "typical_area_sqm_min": 9.0,
        "typical_area_sqm_max": 16.0,
        "zone": "private",
        "adjacent_to": ["waiting_room", "hallway"],
        "avoid_adjacent_to": [],
        "placement_notes": "MVP seed only: separate consultation rooms from the public arrival area.",
    },
    {
        "building_type": "retail",
        "layout_pattern": "public_display_rear_support",
        "room_type": "retail_display",
        "typical_area_sqm_min": 20.0,
        "typical_area_sqm_max": 80.0,
        "zone": "public",
        "adjacent_to": ["entry", "checkout"],
        "avoid_adjacent_to": [],
        "placement_notes": "MVP seed only: keep the customer display area near entry and checkout.",
    },
    {
        "building_type": "retail",
        "layout_pattern": "public_display_rear_support",
        "room_type": "storage",
        "typical_area_sqm_min": 6.0,
        "typical_area_sqm_max": 20.0,
        "zone": "service",
        "adjacent_to": ["retail_display"],
        "avoid_adjacent_to": ["entry"],
        "placement_notes": "MVP seed only: keep storage in the rear support zone.",
    },
)


@dataclass(frozen=True)
class SeedLayoutPatternsResult:
    source_id: str
    created: int
    existing: int
    total: int


async def seed_mvp_layout_patterns(
    db: AsyncSession,
    *,
    created_by: str,
) -> SeedLayoutPatternsResult:
    """Create clearly labeled, idempotent MVP seed rows for local development."""
    source = await db.scalar(
        select(ScraperSource).where(ScraperSource.base_url == SEED_SOURCE_URL)
    )
    accessed_at = datetime.now(timezone.utc)
    if source is None:
        source = ScraperSource(
            name="MVP layout pattern seed data",
            base_url=SEED_SOURCE_URL,
            robots_txt_url=SEED_SOURCE_URL,
            is_permitted=True,
            data_type="structured_seed",
            source_category="dev_seed_layout_patterns",
            last_checked=accessed_at,
            created_by=created_by,
        )
        db.add(source)
        await db.flush()

    existing_patterns = (
        await db.execute(
            select(LayoutPattern).where(LayoutPattern.source_id == source.id)
        )
    ).scalars().all()
    existing_keys = {
        (pattern.building_type, pattern.layout_pattern, pattern.room_type)
        for pattern in existing_patterns
    }

    created = 0
    for seed in MVP_LAYOUT_PATTERN_SEEDS:
        key = (seed["building_type"], seed["layout_pattern"], seed["room_type"])
        if key in existing_keys:
            continue
        db.add(
            LayoutPattern(
                source_id=source.id,
                source_url=SEED_SOURCE_URL,
                accessed_at=accessed_at,
                confidence="seed",
                **seed,
            )
        )
        created += 1

    await db.commit()
    return SeedLayoutPatternsResult(
        source_id=source.id,
        created=created,
        existing=len(existing_keys),
        total=len(MVP_LAYOUT_PATTERN_SEEDS),
    )
