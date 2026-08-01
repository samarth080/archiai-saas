# Catalog audit - Phase 1.1 step 1

ROOM_SIZING (mvp_defaults.py): 12 residential enum types
BASE_SIZES (parser/data/size_rules.py): 37 free-string types

## Overlapping types - area (m2) conflicts

| enum key | free-string key | ROOM_SIZING area | BASE_SIZES area | agree? |
|---|---|---|---|---|
| balcony | balcony | 4.5 | 8.0 | **CONFLICT** |
| bathroom | bathroom | 4.0 | 6.0 | **CONFLICT** |
| bedroom | bedroom | 12.0 | 12.0 | yes |
| dining | dining_room | 10.0 | 16.0 | **CONFLICT** |
| entry | foyer | 3.0 | 8.0 | **CONFLICT** |
| kitchen | kitchen | 9.0 | 14.0 | **CONFLICT** |
| living_room | living_room | 16.0 | 24.0 | **CONFLICT** |
| master_bedroom | master_bedroom | 15.0 | 20.0 | **CONFLICT** |
| parking | garage | 14.0 | 18.0 | **CONFLICT** |
| pooja_room | pooja_room | 2.5 | 6.0 | **CONFLICT** |
| study | study | 8.0 | 9.0 | **CONFLICT** |
| utility | laundry | 3.5 | 6.0 | **CONFLICT** |

## BASE_SIZES-only types (no residential-enum equivalent): 25

bar, changing_room, checkout, classroom, consultation_room, dining_area, ensuite, gym, hallway, kids_room, kitchen_dining, meditation_room, meeting_room, mudroom, office, open_office, open_plan_living, reception, retail_display, sales_floor, staircase, storage, studio_unit, waiting_room, workspace

## Resolution rule applied in space_catalog.py
BASE_SIZES is authoritative for `preferred_area_m2` (broader vocabulary, covers non-residential, actively maintained by the pattern-data pipeline). ROOM_SIZING is authoritative for `min_w`/`min_d` (BASE_SIZES has no dimension data at all). For BASE_SIZES-only types with no ROOM_SIZING minimum, min_w/min_d are derived from area assuming the catalog's default max_aspect (2.5), clamped to a 1.2 m absolute floor.
