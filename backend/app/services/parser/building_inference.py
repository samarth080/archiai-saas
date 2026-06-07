import re
from dataclasses import dataclass

from app.services.parser.data.building_templates import BUILDING_TEMPLATES, BUILDING_TYPES, STYLE_HINTS
from app.services.parser.normaliser import normalise


BHK_PATTERN = re.compile(r"\b(\d+)\s*bhk\b", re.IGNORECASE)

BUILDING_TYPE_PRIORITY = {
    "two_storey_home": 90,
    "townhouse": 85,
    "villa": 80,
    "studio_apartment": 75,
    "restaurant": 70,
    "clinic": 70,
    "school": 70,
    "warehouse": 70,
    "retail": 65,
    "office": 65,
    "family_home": 50,
    "apartment": 40,
}


@dataclass(frozen=True)
class TemplateRoom:
    room_type: str
    count: int
    size_key: str = "medium"
    source: str = "inferred"


@dataclass(frozen=True)
class BuildingInference:
    building_type: str
    total_floors: int
    style_hints: dict
    inferred_rooms: list[TemplateRoom]


def extract_bhk(text: str) -> dict[str, int] | None:
    match = BHK_PATTERN.search(text)
    if not match:
        return None

    bedroom_count = int(match.group(1))
    return {
        "bedroom": bedroom_count,
        "living_room": 1,
        "kitchen": 1,
        "bathroom": max(1, bedroom_count - 1),
    }


def infer_building_type(prompt: str) -> str:
    text = normalise(prompt)
    if extract_bhk(text):
        return "apartment"

    matches: list[tuple[int, int, int, str]] = []
    for building_type, config in BUILDING_TYPES.items():
        for keyword in config["keywords"]:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                priority = BUILDING_TYPE_PRIORITY.get(building_type, 0)
                matches.append((priority, len(keyword), -text.index(keyword), building_type))
    if not matches:
        return "apartment"

    return sorted(matches, reverse=True)[0][3]


def detect_style_hints(prompt: str) -> dict:
    text = normalise(prompt)
    hints: dict = {}
    for keyword, values in STYLE_HINTS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            hints.update(values)
    return hints


def infer_template_rooms(prompt: str) -> list[TemplateRoom]:
    text = normalise(prompt)
    bhk = extract_bhk(text)
    if bhk:
        return [
            TemplateRoom(room_type=room_type, count=count, source="bhk")
            for room_type, count in bhk.items()
        ]

    building_type = infer_building_type(text)
    template = BUILDING_TEMPLATES.get(building_type, BUILDING_TEMPLATES["apartment"])
    return [
        TemplateRoom(room_type=room_type, count=count, size_key=size_key)
        for room_type, count, size_key in template
    ]


def infer_building(prompt: str) -> BuildingInference:
    building_type = infer_building_type(prompt)
    config = BUILDING_TYPES.get(building_type, BUILDING_TYPES["apartment"])
    return BuildingInference(
        building_type=building_type,
        total_floors=config["floors"],
        style_hints=detect_style_hints(prompt),
        inferred_rooms=infer_template_rooms(prompt),
    )
