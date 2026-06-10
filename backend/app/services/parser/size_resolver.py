import math

from app.services.parser.data.size_rules import BASE_SIZES, LONG_ROOM_TYPES, SIZE_KEY_MULTIPLIERS

_DEFAULT_BASE_SQM = 12.0


def resolve_size(
    room_type: str,
    size_key: str = "medium",
    size_modifier: float = 1.0,
    occupancy_m2: float | None = None,
) -> dict:
    """
    Return {"area_m2": float, "width": float, "depth": float}.

    Priority:
    1. occupancy_m2 when provided (derived from "seats N" / "for N people")
    2. base_size × size_key_multiplier × size_modifier

    Aspect ratios:
    - Long room types (kitchen, dining, office…): 1:1.6
    - All others: 1:1.2
    """
    base = BASE_SIZES.get(room_type, _DEFAULT_BASE_SQM)
    area = occupancy_m2 if occupancy_m2 is not None else (
        base * SIZE_KEY_MULTIPLIERS.get(size_key, 1.0) * size_modifier
    )
    ratio = 1.6 if room_type in LONG_ROOM_TYPES else 1.2
    width = round(math.sqrt(area / ratio), 1)
    depth = round(width * ratio, 1)
    return {"area_m2": round(area, 1), "width": width, "depth": depth}
