"""Bridge the canonical MVP LayoutPlan to the existing canvas JSON shape.

The new pipeline uses NW-corner ``x/y`` rectangles.  The current editor uses
center-based ``x/z`` boxes.  Keeping this conversion in one deterministic
boundary lets Design, DesignVersion, share, and project-loading flows continue
to consume their established schema while canonical artifacts remain intact.
"""

from math import hypot, radians

from app.config.mvp_defaults import WALL_HEIGHT_M
from app.schemas.layout_plan import Door, LayoutPlan, Wall
from app.services.layout_service import ROOM_COLORS
from app.services.parser.vastu import is_vastu_requested

_FALLBACK_COLOR = "#94a3b8"
_ROOM_COLOR_ALIASES = {
    "dining": "dining_room",
    "parking": "garage",
}


def _rotation(degrees: int = 0) -> dict[str, float]:
    return {"x": 0.0, "y": radians(degrees), "z": 0.0}


def _room_color(room_type: str) -> str:
    key = _ROOM_COLOR_ALIASES.get(room_type, room_type)
    return ROOM_COLORS.get(key, _FALLBACK_COLOR)


def _bounded_center(origin: float, span: float, plot_span: float) -> float:
    """Round a canvas centre without letting independent rounding cross bounds."""

    half = span / 2
    rounded = round(origin + half, 3)
    return min(plot_span - half, max(half, rounded))


def _wall_object(wall: Wall, index: int) -> dict:
    horizontal = abs(wall.x2 - wall.x1) >= abs(wall.y2 - wall.y1)
    length = hypot(wall.x2 - wall.x1, wall.y2 - wall.y1)
    return {
        "id": wall.id,
        "label": f"Wall {index}",
        "roomType": "wall",
        "objectType": "wall",
        "floorId": "floor_0",
        "floorLevel": 0,
        "position": {
            "x": round((wall.x1 + wall.x2) / 2, 3),
            "y": WALL_HEIGHT_M / 2,
            "z": round((wall.y1 + wall.y2) / 2, 3),
        },
        "size": {
            "w": round(length if horizontal else wall.thickness, 3),
            "h": WALL_HEIGHT_M,
            "d": round(wall.thickness if horizontal else length, 3),
        },
        "rotation": _rotation(),
        "color": ROOM_COLORS["wall"],
    }


def _door_object(door: Door, wall: Wall, index: int) -> dict:
    dx = wall.x2 - wall.x1
    dy = wall.y2 - wall.y1
    length = hypot(dx, dy)
    at = min(door.offset + door.width / 2, length)
    unit_x = dx / length if length else 0.0
    unit_y = dy / length if length else 0.0
    horizontal = abs(dx) >= abs(dy)
    marker_thickness = max(wall.thickness * 1.5, 0.16)
    return {
        "id": door.id,
        "label": f"Door {index}",
        "roomType": "door",
        "objectType": "door",
        "floorId": "floor_0",
        "floorLevel": 0,
        "hostWallId": wall.id,
        "position": {
            "x": round(wall.x1 + unit_x * at, 3),
            "y": 1.05,
            "z": round(wall.y1 + unit_y * at, 3),
        },
        "size": {
            "w": round(door.width if horizontal else marker_thickness, 3),
            "h": 2.1,
            "d": round(marker_thickness if horizontal else door.width, 3),
        },
        "rotation": _rotation(),
        "color": ROOM_COLORS["door"],
    }


def layout_plan_to_canvas(
    plan: LayoutPlan,
    *,
    prompt: str | None = None,
    building_type: str = "house",
    requirements: dict | None = None,
    quality: dict | None = None,
) -> dict:
    """Convert a canonical plan to byte-stable legacy canvas JSON."""

    room_objects = [
        {
            "id": room.id,
            "label": room.label,
            "roomType": room.type,
            "objectType": "room",
            "floorId": "floor_0",
            "floorLevel": 0,
            "position": {
                "x": _bounded_center(room.x, room.w, plan.plot.width_m),
                "y": WALL_HEIGHT_M / 2,
                "z": _bounded_center(room.y, room.h, plan.plot.depth_m),
            },
            "size": {"w": room.w, "h": WALL_HEIGHT_M, "d": room.h},
            "rotation": _rotation(room.rotation),
            "color": _room_color(room.type),
        }
        for room in plan.rooms
    ]
    wall_objects = [
        _wall_object(wall, index)
        for index, wall in enumerate(plan.walls, start=1)
    ]
    walls_by_id = {wall.id: wall for wall in plan.walls}
    door_objects = [
        _door_object(door, walls_by_id[door.wall_ref], index)
        for index, door in enumerate(plan.doors, start=1)
        if door.wall_ref in walls_by_id
    ]
    objects = [*room_objects, *wall_objects, *door_objects]
    footprint = {
        # Existing canvas footprints store their minimum X/Z corner, not their
        # centre. The canonical plan already starts at the NW origin (0, 0).
        "x": 0.0,
        "z": 0.0,
        "w": plan.plot.width_m,
        "d": plan.plot.depth_m,
    }
    total_area = round(sum(room.w * room.h for room in plan.rooms), 3)
    metadata = {
        "pipeline": "mvp",
        "prompt": prompt,
        "building_type": building_type,
        "buildingType": building_type,
        "style": "concept",
        "room_count": len(room_objects),
        "totalFloors": 1,
        "totalRooms": len(room_objects),
        "totalObjects": len(objects),
        "totalAreaSqm": total_area,
        "placementEngine": "mvp_subdivision",
        "candidateCount": 1,
        # The frontend needs the original opt-in intent when it re-scores an
        # edited plan after save/reload. Never infer Vastu from room content.
        "mvpVastuEnabled": is_vastu_requested(prompt or ""),
    }
    if requirements is not None:
        metadata["mvpRequirements"] = requirements
    if quality is not None:
        metadata["mvpQuality"] = quality

    return {
        "version": "1.0",
        "metadata": metadata,
        "building": {
            "floorHeight": WALL_HEIGHT_M,
            "footprint": footprint,
        },
        "floors": [
            {
                "id": "floor_0",
                "name": "Ground Floor",
                "level": 0,
                "elevation": 0.0,
                "footprint": footprint,
                "rooms": objects,
            }
        ],
        "rooms": objects,
    }
