from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.layout_pattern import LayoutPattern
from app.services.layout_vocabulary_service import normalize_building_type, normalize_room_type


DEFAULT_ROOM_RULES: dict[str, dict] = {
    "living_room": {"area": (16.0, 30.0), "zone": "public", "adjacent_to": ("entry", "kitchen", "dining_room")},
    "kitchen": {"area": (8.0, 18.0), "zone": "service", "adjacent_to": ("living_room", "dining_room"), "avoid": ("bedroom",)},
    "dining_room": {"area": (8.0, 18.0), "zone": "public", "adjacent_to": ("living_room", "kitchen")},
    "master_bedroom": {"area": (14.0, 24.0), "zone": "private", "adjacent_to": ("bathroom",), "avoid": ("kitchen", "garage")},
    "bedroom": {"area": (10.0, 16.0), "zone": "private", "adjacent_to": ("bathroom", "hallway"), "avoid": ("kitchen", "garage")},
    "bathroom": {"area": (4.0, 8.0), "zone": "service", "adjacent_to": ("bedroom", "hallway"), "avoid": ("kitchen",)},
    "study": {"area": (7.0, 14.0), "zone": "private", "adjacent_to": ("hallway",)},
    "office": {"area": (7.0, 14.0), "zone": "private", "adjacent_to": ("hallway",)},
    "workspace": {"area": (18.0, 60.0), "zone": "public", "adjacent_to": ("reception", "meeting_room")},
    "meeting_room": {"area": (10.0, 24.0), "zone": "private", "adjacent_to": ("workspace",)},
    "reception": {"area": (8.0, 18.0), "zone": "public", "adjacent_to": ("entry", "waiting_room", "workspace")},
    "waiting_room": {"area": (10.0, 24.0), "zone": "public", "adjacent_to": ("entry", "reception")},
    "consultation_room": {"area": (9.0, 16.0), "zone": "private", "adjacent_to": ("waiting_room", "hallway")},
    "classroom": {"area": (30.0, 65.0), "zone": "public", "adjacent_to": ("hallway",)},
    "retail_display": {"area": (20.0, 80.0), "zone": "public", "adjacent_to": ("entry", "checkout")},
    "checkout": {"area": (5.0, 12.0), "zone": "public", "adjacent_to": ("entry", "retail_display")},
    "storage": {"area": (4.0, 16.0), "zone": "service", "adjacent_to": ("kitchen", "workspace", "retail_display")},
    "utility": {"area": (5.0, 12.0), "zone": "service", "adjacent_to": ("storage",)},
    "entry": {"area": (4.0, 10.0), "zone": "circulation", "adjacent_to": ("living_room", "reception", "retail_display")},
    "hallway": {"area": (5.0, 14.0), "zone": "circulation", "adjacent_to": ("bedroom", "bathroom", "classroom")},
    "balcony": {"area": (5.0, 12.0), "zone": "public", "adjacent_to": ("living_room",)},
    "garage": {"area": (22.0, 36.0), "zone": "service", "avoid": ("bedroom",)},
}

DEFAULT_LAYOUT_PATTERNS = {
    "apartment": ("public_private_split",),
    "studio": ("compact_open_plan",),
    "house": ("public_ground_private_upper",),
    "office": ("entry_work_support",),
    "clinic": ("waiting_consultation_split",),
    "classroom": ("corridor_connected_learning",),
    "retail": ("public_display_rear_support",),
}

SUPPORTED_PATTERN_CONFIDENCES = {"high", "medium", "seed"}
SUPPORTED_ZONES = {"public", "private", "service", "circulation", "other"}
MAX_REASONABLE_ROOM_AREA_SQM = 250.0


@dataclass(frozen=True)
class RoomPatternRule:
    room_type: str
    typical_area_sqm_min: float
    typical_area_sqm_max: float
    zone: str
    adjacent_to: tuple[str, ...] = ()
    avoid_adjacent_to: tuple[str, ...] = ()
    room_to_total_area_ratio_min: float | None = None
    room_to_total_area_ratio_max: float | None = None
    pattern_data_used: bool = False


@dataclass(frozen=True)
class LayoutPatternRules:
    building_type: str
    room_rules: dict[str, RoomPatternRule]
    layout_patterns: tuple[str, ...]
    pattern_data_used: bool = False
    pattern_data_source: str = "fallback-defaults"
    applied_pattern_count: int = 0
    ignored_pattern_count: int = 0

    def room_size_range(self, room_type: str) -> tuple[float, float]:
        rule = self.rule_for(room_type)
        return rule.typical_area_sqm_min, rule.typical_area_sqm_max

    def zone_for(self, room_type: str) -> str:
        return self.rule_for(room_type).zone

    def adjacency_for(self, room_type: str) -> tuple[str, ...]:
        return self.rule_for(room_type).adjacent_to

    def avoid_adjacency_for(self, room_type: str) -> tuple[str, ...]:
        return self.rule_for(room_type).avoid_adjacent_to

    def rule_for(self, room_type: str) -> RoomPatternRule:
        return self.room_rules.get(room_type) or _fallback_room_rule(room_type)


@dataclass(frozen=True)
class LayoutPatternAudit:
    pattern_id: str | None
    usable: bool
    warnings: tuple[str, ...]


def audit_layout_pattern(pattern: LayoutPattern) -> LayoutPatternAudit:
    warnings: list[str] = []

    if not pattern.room_type:
        warnings.append("Missing room type")

    if pattern.confidence not in SUPPORTED_PATTERN_CONFIDENCES:
        warnings.append("Pattern confidence is not trusted for generation")

    if pattern.zone is not None and pattern.zone not in SUPPORTED_ZONES:
        warnings.append(f"Unsupported zone: {pattern.zone}")

    min_area = pattern.typical_area_sqm_min
    max_area = pattern.typical_area_sqm_max
    if min_area is not None or max_area is not None:
        if min_area is None or max_area is None:
            warnings.append("Room area range is incomplete")
        elif min_area <= 0 or max_area <= 0:
            warnings.append("Room area range must be positive")
        elif min_area > max_area:
            warnings.append("Room area minimum is greater than maximum")
        elif max_area > MAX_REASONABLE_ROOM_AREA_SQM:
            warnings.append("Room area range is unrealistically large")

    min_ratio = pattern.room_to_total_area_ratio_min
    max_ratio = pattern.room_to_total_area_ratio_max
    if min_ratio is not None or max_ratio is not None:
        if min_ratio is None or max_ratio is None:
            warnings.append("Room-to-total-area ratio range is incomplete")
        elif min_ratio <= 0 or max_ratio <= 0 or min_ratio > max_ratio or max_ratio > 1:
            warnings.append("Room-to-total-area ratio range is invalid")

    for field_name, value in (
        ("adjacent_to", pattern.adjacent_to),
        ("avoid_adjacent_to", pattern.avoid_adjacent_to),
    ):
        if not isinstance(value, list):
            warnings.append(f"{field_name} must be a list")

    return LayoutPatternAudit(
        pattern_id=pattern.id,
        usable=not warnings,
        warnings=tuple(warnings),
    )


def _is_usable_layout_pattern(pattern: LayoutPattern) -> bool:
    return audit_layout_pattern(pattern).usable


def _fallback_room_rule(room_type: str) -> RoomPatternRule:
    defaults = DEFAULT_ROOM_RULES.get(room_type, {"area": (8.0, 16.0), "zone": "service"})
    return RoomPatternRule(
        room_type=room_type,
        typical_area_sqm_min=defaults["area"][0],
        typical_area_sqm_max=defaults["area"][1],
        zone=defaults["zone"],
        adjacent_to=tuple(defaults.get("adjacent_to", ())),
        avoid_adjacent_to=tuple(defaults.get("avoid", ())),
    )


def fallback_layout_rules(
    building_type: str,
    room_types: set[str] | list[str] | tuple[str, ...],
) -> LayoutPatternRules:
    normalized_building_type = normalize_building_type(building_type) or building_type
    normalized_room_types = {
        normalize_room_type(room_type) or room_type
        for room_type in room_types
    }
    return LayoutPatternRules(
        building_type=normalized_building_type,
        room_rules={room_type: _fallback_room_rule(room_type) for room_type in normalized_room_types},
        layout_patterns=DEFAULT_LAYOUT_PATTERNS.get(normalized_building_type, (normalized_building_type,)),
        pattern_data_source="fallback-defaults",
        applied_pattern_count=0,
        ignored_pattern_count=0,
    )


def _merge_pattern(fallback: RoomPatternRule, pattern: LayoutPattern) -> RoomPatternRule:
    return RoomPatternRule(
        room_type=fallback.room_type,
        typical_area_sqm_min=pattern.typical_area_sqm_min or fallback.typical_area_sqm_min,
        typical_area_sqm_max=pattern.typical_area_sqm_max or fallback.typical_area_sqm_max,
        zone=pattern.zone or fallback.zone,
        adjacent_to=tuple(pattern.adjacent_to or fallback.adjacent_to),
        avoid_adjacent_to=tuple(pattern.avoid_adjacent_to or fallback.avoid_adjacent_to),
        room_to_total_area_ratio_min=pattern.room_to_total_area_ratio_min,
        room_to_total_area_ratio_max=pattern.room_to_total_area_ratio_max,
        pattern_data_used=True,
    )


async def get_layout_pattern_rules(
    db: AsyncSession,
    building_type: str,
    room_types: set[str] | list[str] | tuple[str, ...],
) -> LayoutPatternRules:
    normalized_building_type = normalize_building_type(building_type) or building_type
    normalized_room_types = {
        normalize_room_type(room_type) or room_type
        for room_type in room_types
    }
    rules = fallback_layout_rules(normalized_building_type, normalized_room_types)
    result = await db.execute(
        select(LayoutPattern)
        .where(LayoutPattern.room_type.in_(normalized_room_types))
        .where(or_(LayoutPattern.building_type == normalized_building_type, LayoutPattern.building_type.is_(None)))
    )
    patterns = result.scalars().all()
    confidence_order = {"high": 3, "medium": 2, "seed": 1}
    patterns.sort(
        key=lambda pattern: (
            pattern.building_type == building_type,
            confidence_order.get(pattern.confidence, 0),
            pattern.created_at,
        ),
        reverse=True,
    )

    room_rules = dict(rules.room_rules)
    used_rooms: set[str] = set()
    used_confidences: set[str] = set()
    applied_pattern_count = 0
    ignored_pattern_count = 0
    layout_patterns = list(rules.layout_patterns)
    for pattern in patterns:
        if not _is_usable_layout_pattern(pattern):
            ignored_pattern_count += 1
            continue
        if pattern.room_type not in used_rooms:
            room_rules[pattern.room_type] = _merge_pattern(rules.rule_for(pattern.room_type), pattern)
            used_rooms.add(pattern.room_type)
            used_confidences.add(pattern.confidence)
            applied_pattern_count += 1
        if pattern.layout_pattern and pattern.layout_pattern not in layout_patterns:
            layout_patterns.append(pattern.layout_pattern)

    return LayoutPatternRules(
        building_type=normalized_building_type,
        room_rules=room_rules,
        layout_patterns=tuple(layout_patterns),
        pattern_data_used=bool(used_rooms),
        pattern_data_source=(
            "source-derived"
            if used_confidences & {"high", "medium"}
            else "seed"
            if used_confidences
            else "fallback-defaults"
        ),
        applied_pattern_count=applied_pattern_count,
        ignored_pattern_count=ignored_pattern_count,
    )
