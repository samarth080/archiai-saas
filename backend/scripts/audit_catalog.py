"""Phase 1.1 step 1 — diff the three sizing/vocab tables that disagree today.

Prints every type that exists in more than one source and whether their
areas agree, plus every type that's residential-enum-only or free-string-only.
Real output, not a guess — this is what `space_catalog.py`'s seed data
resolves, and the resolution rule is stated once, here, not silently decided.

Usage: ..\\.venv311\\Scripts\\python.exe backend\\scripts\\audit_catalog.py
"""
from __future__ import annotations

from app.config.mvp_defaults import ROOM_SIZING
from app.services.parser.data.size_rules import BASE_SIZES

# RoomType enum values use "dining"/"study" etc.; BASE_SIZES uses the parser's
# free-string vocabulary ("dining_room", "study"). Where the MVP enum's own
# name isn't a BASE_SIZES key, its nearest free-string equivalent is named
# here so the diff is apples-to-apples instead of reporting false "missing".
_ENUM_TO_FREE_STRING = {
    "dining": "dining_room",
    "entry": "foyer",
    "utility": "laundry",
    "parking": "garage",
}


def main() -> None:
    room_sizing_area = {
        room_type.value: sizing.preferred_area_m2
        for room_type, sizing in ROOM_SIZING.items()
    }

    print("# Catalog audit - Phase 1.1 step 1\n")
    print(f"ROOM_SIZING (mvp_defaults.py): {len(room_sizing_area)} residential enum types")
    print(f"BASE_SIZES (parser/data/size_rules.py): {len(BASE_SIZES)} free-string types\n")

    print("## Overlapping types - area (m2) conflicts\n")
    print("| enum key | free-string key | ROOM_SIZING area | BASE_SIZES area | agree? |")
    print("|---|---|---|---|---|")
    matched_free_strings: set[str] = set()
    for enum_key, area in sorted(room_sizing_area.items()):
        free_key = _ENUM_TO_FREE_STRING.get(enum_key, enum_key)
        base_area = BASE_SIZES.get(free_key)
        if base_area is None:
            print(f"| {enum_key} | {free_key} | {area} | - (no match) | n/a |")
            continue
        matched_free_strings.add(free_key)
        agree = "yes" if abs(area - base_area) < 0.01 else "**CONFLICT**"
        print(f"| {enum_key} | {free_key} | {area} | {base_area} | {agree} |")

    only_base = sorted(set(BASE_SIZES) - matched_free_strings)
    print(f"\n## BASE_SIZES-only types (no residential-enum equivalent): {len(only_base)}\n")
    print(", ".join(only_base))

    print(
        "\n## Resolution rule applied in space_catalog.py\n"
        "BASE_SIZES is authoritative for `preferred_area_m2` (broader vocabulary, "
        "covers non-residential, actively maintained by the pattern-data pipeline). "
        "ROOM_SIZING is authoritative for `min_w`/`min_d` (BASE_SIZES has no "
        "dimension data at all). For BASE_SIZES-only types with no ROOM_SIZING "
        "minimum, min_w/min_d are derived from area assuming the catalog's "
        "default max_aspect (2.5), clamped to a 1.2 m absolute floor."
    )


if __name__ == "__main__":
    main()
