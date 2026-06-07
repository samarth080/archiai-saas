BUILDING_TYPES: dict[str, dict] = {
    "studio_apartment": {
        "keywords": ("studio apartment", "studio flat", "studio", "bedsit", "bachelor pad"),
        "floors": 1,
    },
    "apartment": {
        "keywords": ("apartment", "flat", "condo", "unit", "1bhk", "2bhk", "3bhk", "4bhk"),
        "floors": 1,
    },
    "family_home": {
        "keywords": ("family home", "family house", "house", "home", "bungalow", "cottage"),
        "floors": 1,
    },
    "two_storey_home": {
        "keywords": ("two storey", "two story", "2 storey", "2 story", "two floor house", "2 floor house"),
        "floors": 2,
    },
    "townhouse": {
        "keywords": ("townhouse", "town house", "terraced house", "row house"),
        "floors": 2,
    },
    "villa": {
        "keywords": ("villa", "mansion", "estate", "luxury home"),
        "floors": 2,
    },
    "office": {
        "keywords": ("office", "workspace", "coworking", "co working", "commercial"),
        "floors": 1,
    },
    "retail": {
        "keywords": ("shop", "store", "retail", "boutique", "showroom"),
        "floors": 1,
    },
    "restaurant": {
        "keywords": ("restaurant", "cafe", "coffee shop", "bistro", "eatery", "diner"),
        "floors": 1,
    },
    "school": {
        "keywords": ("school", "classroom", "educational", "college", "university"),
        "floors": 2,
    },
    "clinic": {
        "keywords": ("clinic", "medical", "doctor", "dental", "healthcare"),
        "floors": 1,
    },
    "hotel": {
        "keywords": ("hotel", "motel", "inn", "bed and breakfast", "guesthouse"),
        "floors": 3,
    },
    "warehouse": {
        "keywords": ("warehouse", "industrial", "factory", "storage facility"),
        "floors": 1,
    },
}


BUILDING_TEMPLATES: dict[str, list[tuple[str, int, str]]] = {
    "studio_apartment": [
        ("open_plan_living", 1, "large"),
        ("bathroom", 1, "small"),
    ],
    "apartment": [
        ("living_room", 1, "medium"),
        ("kitchen", 1, "medium"),
        ("bedroom", 2, "medium"),
        ("bathroom", 1, "small"),
    ],
    "family_home": [
        ("living_room", 1, "large"),
        ("kitchen", 1, "medium"),
        ("dining_room", 1, "medium"),
        ("master_bedroom", 1, "large"),
        ("bedroom", 2, "medium"),
        ("bathroom", 2, "small"),
        ("foyer", 1, "small"),
    ],
    "two_storey_home": [
        ("living_room", 1, "large"),
        ("kitchen", 1, "large"),
        ("dining_room", 1, "medium"),
        ("foyer", 1, "small"),
        ("bathroom", 1, "small"),
        ("master_bedroom", 1, "large"),
        ("bedroom", 2, "medium"),
        ("bathroom", 1, "medium"),
    ],
    "office": [
        ("reception", 1, "medium"),
        ("workspace", 1, "xlarge"),
        ("meeting_room", 2, "medium"),
        ("office", 1, "small"),
        ("kitchen", 1, "small"),
        ("bathroom", 2, "small"),
    ],
    "restaurant": [
        ("dining_room", 1, "xlarge"),
        ("kitchen", 1, "large"),
        ("bar", 1, "medium"),
        ("bathroom", 2, "small"),
        ("storage", 1, "small"),
    ],
    "retail": [
        ("retail_display", 1, "xlarge"),
        ("storage", 1, "medium"),
        ("changing_room", 2, "small"),
        ("office", 1, "small"),
        ("bathroom", 1, "small"),
    ],
}


STYLE_HINTS: dict[str, dict] = {
    "minimalist": {"open_plan_bias": True, "room_count_modifier": -1, "ceiling_height": "high"},
    "modern": {"open_plan_bias": True, "room_count_modifier": 0, "ceiling_height": "standard"},
    "traditional": {"open_plan_bias": False, "room_count_modifier": 0, "ceiling_height": "standard"},
    "luxury": {"open_plan_bias": False, "room_count_modifier": 1, "size_upgrade": True},
    "compact": {"open_plan_bias": True, "room_count_modifier": -1, "size_downgrade": True},
    "spacious": {"open_plan_bias": True, "room_count_modifier": 0, "size_upgrade": True},
    "cozy": {"open_plan_bias": False, "room_count_modifier": -1, "size_downgrade": True},
    "studio": {"open_plan_bias": True, "room_count_modifier": -2},
    "open_plan_living": {"open_plan_bias": True},
}

