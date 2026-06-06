from dataclasses import dataclass

from app.services.prompt_service import RoomSpec


@dataclass(frozen=True)
class TemplateRoom:
    room_type: str
    label: str
    w: float
    d: float
    minimum_count: int = 1


@dataclass(frozen=True)
class BuildingTemplate:
    name: str
    default_rooms: tuple[TemplateRoom, ...]
    zone_priorities: tuple[str, ...]
    adjacency_priorities: tuple[tuple[str, str], ...]
    layout_pattern_strategy: str
    multi_floor_behavior: str
    fill_missing_defaults: bool = False


BUILDING_TEMPLATES: dict[str, BuildingTemplate] = {
    "apartment": BuildingTemplate(
        name="apartment",
        default_rooms=(
            TemplateRoom("living_room", "Living Room", 5.0, 5.0),
            TemplateRoom("kitchen", "Kitchen", 4.0, 4.0),
            TemplateRoom("bathroom", "Bathroom", 3.0, 3.0),
        ),
        zone_priorities=("public", "private", "service", "circulation"),
        adjacency_priorities=(("living_room", "kitchen"), ("kitchen", "dining_room"), ("bedroom", "bathroom")),
        layout_pattern_strategy="public_private_split",
        multi_floor_behavior="keep_public_ground_when_multiple_floors",
    ),
    "studio": BuildingTemplate(
        name="studio",
        default_rooms=(
            TemplateRoom("living_room", "Living Room", 4.5, 4.5),
            TemplateRoom("kitchen", "Kitchen", 3.0, 3.0),
            TemplateRoom("bathroom", "Bathroom", 2.5, 2.5),
        ),
        zone_priorities=("public", "service", "private", "circulation"),
        adjacency_priorities=(("living_room", "kitchen"),),
        layout_pattern_strategy="compact_open_plan",
        multi_floor_behavior="prefer_single_floor",
    ),
    "house": BuildingTemplate(
        name="house",
        default_rooms=(
            TemplateRoom("living_room", "Living Room", 5.0, 5.0),
            TemplateRoom("kitchen", "Kitchen", 4.0, 4.0),
            TemplateRoom("bathroom", "Bathroom", 3.0, 3.0),
        ),
        zone_priorities=("public", "circulation", "private", "service"),
        adjacency_priorities=(("living_room", "entry"), ("kitchen", "dining_room"), ("bedroom", "bathroom")),
        layout_pattern_strategy="public_ground_private_upper",
        multi_floor_behavior="prefer_private_rooms_upstairs",
    ),
    "office": BuildingTemplate(
        name="office",
        default_rooms=(
            TemplateRoom("entry", "Entry", 2.5, 2.5),
            TemplateRoom("reception", "Reception", 3.5, 3.5),
            TemplateRoom("workspace", "Open Workspace", 6.0, 5.0),
            TemplateRoom("meeting_room", "Meeting Room", 4.0, 3.0),
            TemplateRoom("storage", "Storage", 2.5, 2.5),
        ),
        zone_priorities=("circulation", "public", "semi_private", "private", "service"),
        adjacency_priorities=(("entry", "reception"), ("reception", "workspace"), ("workspace", "meeting_room")),
        layout_pattern_strategy="entry_work_support",
        multi_floor_behavior="keep_reception_ground",
        fill_missing_defaults=True,
    ),
    "clinic": BuildingTemplate(
        name="clinic",
        default_rooms=(
            TemplateRoom("entry", "Entry", 2.5, 2.5),
            TemplateRoom("reception", "Reception", 3.5, 3.5),
            TemplateRoom("waiting_room", "Waiting Room", 4.0, 4.0),
            TemplateRoom("consultation_room", "Consultation Room", 3.5, 3.5),
            TemplateRoom("bathroom", "Bathroom", 2.5, 2.5),
        ),
        zone_priorities=("circulation", "public", "private", "service"),
        adjacency_priorities=(("entry", "reception"), ("reception", "waiting_room"), ("waiting_room", "consultation_room")),
        layout_pattern_strategy="waiting_consultation_split",
        multi_floor_behavior="keep_public_reception_ground",
        fill_missing_defaults=True,
    ),
    "restaurant": BuildingTemplate(
        name="restaurant",
        default_rooms=(
            TemplateRoom("entry", "Entry", 2.5, 2.5),
            TemplateRoom("reception", "Host Stand", 3.0, 2.5),
            TemplateRoom("dining_room", "Dining Area", 7.0, 6.0),
            TemplateRoom("kitchen", "Kitchen", 5.0, 4.0),
            TemplateRoom("bathroom", "Bathroom", 2.5, 2.5),
            TemplateRoom("storage", "Storage", 3.0, 3.0),
        ),
        zone_priorities=("circulation", "public", "service"),
        adjacency_priorities=(("entry", "reception"), ("reception", "dining_room"), ("dining_room", "kitchen"), ("kitchen", "storage")),
        layout_pattern_strategy="public_dining_rear_service",
        multi_floor_behavior="keep_public_dining_ground",
        fill_missing_defaults=True,
    ),
    "classroom": BuildingTemplate(
        name="classroom",
        default_rooms=(
            TemplateRoom("entry", "Entry", 2.5, 2.5),
            TemplateRoom("hallway", "Hallway", 5.0, 2.0),
            TemplateRoom("classroom", "Classroom", 7.0, 6.0),
            TemplateRoom("bathroom", "Bathroom", 2.5, 2.5),
        ),
        zone_priorities=("circulation", "public", "service"),
        adjacency_priorities=(("entry", "hallway"), ("hallway", "classroom")),
        layout_pattern_strategy="corridor_connected_learning",
        multi_floor_behavior="repeat_classroom_cluster_per_floor",
        fill_missing_defaults=True,
    ),
    "retail": BuildingTemplate(
        name="retail",
        default_rooms=(
            TemplateRoom("entry", "Entry", 2.5, 2.5),
            TemplateRoom("retail_display", "Display Area", 7.0, 6.0),
            TemplateRoom("checkout", "Checkout", 3.0, 2.0),
            TemplateRoom("storage", "Storage", 3.0, 3.0),
        ),
        zone_priorities=("circulation", "public", "service"),
        adjacency_priorities=(("entry", "retail_display"), ("retail_display", "checkout"), ("retail_display", "storage")),
        layout_pattern_strategy="public_display_rear_support",
        multi_floor_behavior="keep_customer_area_ground",
        fill_missing_defaults=True,
    ),
}


def get_building_template(building_type: str) -> BuildingTemplate:
    return BUILDING_TEMPLATES.get(building_type, BUILDING_TEMPLATES["apartment"])


def apply_template_defaults(specs: list[RoomSpec], building_type: str) -> list[RoomSpec]:
    template = get_building_template(building_type)
    if not template.fill_missing_defaults:
        return list(specs)

    result = list(specs)
    counts: dict[str, int] = {}
    for room in specs:
        counts[room.room_type] = counts.get(room.room_type, 0) + 1

    for default in template.default_rooms:
        missing = max(0, default.minimum_count - counts.get(default.room_type, 0))
        for index in range(missing):
            label = default.label if default.minimum_count == 1 else f"{default.label} {index + 1}"
            result.append(
                RoomSpec(
                    label=label,
                    room_type=default.room_type,
                    w=default.w,
                    h=3.0,
                    d=default.d,
                )
            )
    return result
