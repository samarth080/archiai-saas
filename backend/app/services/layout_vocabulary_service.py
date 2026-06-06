import re


BUILDING_TYPE_ALIASES: dict[str, tuple[str, ...]] = {
    "studio": ("studio apartment", "studio flat", "studio"),
    "clinic": ("clinic", "clinics", "medical practice", "healthcare practice"),
    "restaurant": ("restaurant", "restaurants", "cafe", "cafes", "diner", "diners", "food court"),
    "classroom": ("classroom", "classrooms", "school room", "teaching room"),
    "retail": ("retail", "shop", "shops", "store", "stores"),
    "apartment": (
        "apartment",
        "apartments",
        "flat",
        "flats",
        "unit",
        "units",
        "condo",
        "condominium",
    ),
    "house": (
        "house",
        "houses",
        "home",
        "homes",
        "residence",
        "residences",
        "villa",
        "villas",
        "bungalow",
        "cottage",
    ),
    "office": ("office building", "office", "offices", "workspace", "workplace"),
}

ROOM_TYPE_ALIASES: dict[str, tuple[str, ...]] = {
    "consultation_room": ("consultation room", "consult room", "exam room", "examination room"),
    "meeting_room": ("meeting room", "conference room", "boardroom"),
    "waiting_room": ("waiting room", "waiting area"),
    "retail_display": ("display area", "retail display", "sales floor", "showroom"),
    "master_bedroom": ("master bedroom", "master bed", "primary bedroom", "main bedroom"),
    "living_room": ("living room", "living rooms", "lounge", "lounges", "sitting room", "family room"),
    "dining_room": ("dining room", "dining rooms", "dining area", "dining"),
    "reception": ("reception", "front desk"),
    "checkout": ("checkout", "cash register", "till"),
    "workspace": ("open workspace", "workspace", "work area"),
    "study": ("home office", "study", "studies"),
    "bathroom": (
        "bathroom",
        "bathrooms",
        "bath room",
        "bath rooms",
        "en suite",
        "ensuite",
        "toilet",
        "toilets",
        "washroom",
        "washrooms",
        "wc",
    ),
    "kitchen": ("kitchen", "kitchens", "kitchenette"),
    "classroom": ("classroom", "classrooms"),
    "bedroom": ("bedroom", "bedrooms", "bed room", "bed rooms", "guest bedroom", "guest room", "kids room"),
    "office": ("office", "offices"),
    "hallway": ("hallway", "hallways", "hall", "corridor", "corridors", "passage", "passageway"),
    "entry": ("entry", "entries", "entrance", "entrances", "foyer", "foyers", "lobby"),
    "balcony": ("balcony", "balconies", "terrace", "terraces", "porch"),
    "garage": ("garage", "garages", "car park", "parking"),
    "storage": ("storage", "store room", "stock room", "utility closet"),
    "utility": ("utility room", "utility", "utilities", "laundry", "laundry room"),
}


def contains_alias(text: str, aliases: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(alias)}\b", text, re.IGNORECASE) for alias in aliases)


def normalize_building_type(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower().replace("-", " ")
    for building_type, aliases in BUILDING_TYPE_ALIASES.items():
        if lowered == building_type or contains_alias(lowered, aliases):
            return building_type
    return None


def normalize_room_type(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower().replace("-", " ")
    for room_type, aliases in ROOM_TYPE_ALIASES.items():
        if lowered == room_type or contains_alias(lowered, aliases):
            return room_type
    return None


def find_building_type_in_text(text: str) -> str | None:
    lowered = text.lower()
    for building_type, aliases in BUILDING_TYPE_ALIASES.items():
        if contains_alias(lowered, aliases):
            return building_type
    return None


def room_types_in_text(text: str, *, exclude: str | None = None) -> list[str]:
    normalized_exclude = normalize_room_type(exclude) if exclude else None
    return sorted(
        room_type
        for room_type, aliases in ROOM_TYPE_ALIASES.items()
        if room_type != normalized_exclude and contains_alias(text, aliases)
    )
