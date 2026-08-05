"""Phase 1 — SpaceCatalog. Acceptance per the workflow doc: every legacy
RoomType enum value round-trips through the catalog losslessly, and the
clinic fixture's vocabulary (a non-residential seed already in the repo)
resolves untouched."""
import json
from pathlib import Path

import pytest

from app.config.mvp_defaults import ROOM_SIZING
from app.schemas.requirements import RequirementsSpec, RoomRequest, RoomType
from app.services.catalog import (
    CATALOG,
    SpaceType,
    UnknownSpaceType,
    get,
    min_dimensions,
    register,
    resolve_alias,
    spaces_from_rooms,
)

FIXTURES = Path(__file__).parent / "fixtures" / "requirements"


@pytest.mark.parametrize("room_type", list(RoomType))
def test_every_legacy_enum_value_resolves(room_type):
    space = get(room_type.value)
    assert isinstance(space, SpaceType)
    assert space.min_w > 0
    assert space.min_d > 0
    assert space.preferred_area_m2 > 0


def test_bedroom_keeps_its_real_minimum_dimensions():
    # The one case ROOM_SIZING and BASE_SIZES already agreed on (12.0 m2) —
    # proves the merge doesn't silently overwrite an existing-agreement case.
    space = get("bedroom")
    assert space.min_w == 3.0
    assert space.min_d == 3.0
    assert space.preferred_area_m2 == 12.0


def test_conflicting_area_resolves_to_base_sizes_not_room_sizing():
    # bathroom: ROOM_SIZING says 4.0 m2, BASE_SIZES says 6.0 m2 — the
    # documented resolution rule picks BASE_SIZES for area, ROOM_SIZING for
    # the real min dimensions it already has.
    space = get("bathroom")
    assert space.preferred_area_m2 == 6.0
    assert (space.min_w, space.min_d) == (1.5, 2.1)


# ── min_dimensions (PlanRoom.type migration, engine generalization workflow
# migration-order item 4) — lenient, never-raises sizing lookup used by
# hard_constraints.validate and engine.rebuild_derived_geometry. ───────────


@pytest.mark.parametrize("room_type", list(RoomType))
def test_min_dimensions_matches_room_sizing_exactly_for_every_residential_type(room_type):
    # Byte-identical parity is what makes the PlanRoom.type migration a
    # zero-behavior-change swap for every existing residential validation
    # path — not just "close enough".
    sizing = ROOM_SIZING[room_type]
    assert min_dimensions(room_type.value) == (sizing.min_w, sizing.min_d)


def test_min_dimensions_covers_non_residential_catalog_types_too():
    assert min_dimensions("consultation_room") == (get("consultation_room").min_w, get("consultation_room").min_d)


def test_min_dimensions_falls_back_to_the_default_for_a_truly_unknown_type():
    assert min_dimensions("zzz_totally_unknown") == (1.2, 1.2)
    assert min_dimensions("zzz_totally_unknown", default=(2.0, 3.0)) == (2.0, 3.0)


@pytest.mark.parametrize(
    "enum_key,canonical_key",
    [("dining", "dining_room"), ("entry", "foyer"), ("utility", "laundry"), ("parking", "garage")],
)
def test_enum_only_names_alias_to_their_free_string_key(enum_key, canonical_key):
    assert resolve_alias(enum_key) == canonical_key
    assert get(enum_key).key == canonical_key


def test_get_is_case_and_separator_insensitive():
    assert get("Master Bedroom").key == "master_bedroom"
    assert get("MASTER-BEDROOM").key == "master_bedroom"


def test_unknown_type_raises_with_no_invented_guess():
    with pytest.raises(UnknownSpaceType) as exc_info:
        get("recording_studio")
    assert exc_info.value.key == "recording_studio"


def test_close_typo_gets_a_real_suggestion_not_silent_acceptance():
    with pytest.raises(UnknownSpaceType) as exc_info:
        get("bedrom")
    assert exc_info.value.suggestion == "bedroom"


def test_register_extends_the_catalog_for_the_session():
    register(
        SpaceType(
            key="recording_studio",
            label="Recording Studio",
            node_type="space",
            zone="private",
            min_w=3.0,
            min_d=3.0,
            preferred_area_m2=15.0,
        )
    )
    try:
        assert get("recording_studio").preferred_area_m2 == 15.0
    finally:
        CATALOG.pop("recording_studio", None)


def test_derived_minimums_for_base_sizes_only_types_respect_the_absolute_floor():
    for space in CATALOG.values():
        assert space.min_w >= 1.2
        assert space.min_d >= 1.2


@pytest.mark.parametrize("name", ["1bhk", "2bhk", "3bhk_adjacencies", "4bhk", "clinic"])
def test_existing_requirement_fixtures_round_trip_through_the_catalog_untouched(name):
    raw = json.loads((FIXTURES / f"{name}.json").read_text())
    for room in raw.get("rooms", []):
        space = get(room["type"])
        assert isinstance(space, SpaceType)


# ── Phase 1.2 migration order item 1: rooms -> spaces normalizer ────────────


def test_spaces_from_rooms_is_lossless_on_count():
    rooms = [RoomRequest(type=RoomType.bedroom, count=2), RoomRequest(type=RoomType.bathroom, count=1)]
    spaces = spaces_from_rooms(rooms)
    assert [(s.space_type, s.count) for s in spaces] == [("bedroom", 2), ("bathroom", 1)]


@pytest.mark.parametrize(
    "enum_type,canonical_key",
    [
        (RoomType.dining, "dining_room"),
        (RoomType.entry, "foyer"),
        (RoomType.utility, "laundry"),
        (RoomType.parking, "garage"),
    ],
)
def test_spaces_from_rooms_maps_enum_only_names_to_their_catalog_key(enum_type, canonical_key):
    spaces = spaces_from_rooms([RoomRequest(type=enum_type, count=1)])
    assert spaces[0].space_type == canonical_key


def test_every_room_type_enum_value_survives_the_normalizer():
    # All 12 RoomType values are catalog keys (via alias resolution) — the
    # migration is claimed lossless; prove it for every value, not a sample.
    rooms = [RoomRequest(type=room_type, count=1) for room_type in RoomType]
    spaces = spaces_from_rooms(rooms)
    assert len(spaces) == len(rooms)
    for space in spaces:
        assert get(space.space_type) is not None


def test_requirements_spec_spaces_field_is_additive_and_backward_compatible():
    rooms = [RoomRequest(type=RoomType.bedroom, count=2)]
    spec_without_spaces = RequirementsSpec(rooms=rooms)
    assert spec_without_spaces.spaces == []

    spec_with_spaces = RequirementsSpec(rooms=rooms, spaces=spaces_from_rooms(rooms))
    assert spec_with_spaces.spaces[0].space_type == "bedroom"
    assert spec_with_spaces.spaces[0].count == 2
    # rooms untouched by populating spaces alongside it.
    assert spec_with_spaces.rooms == rooms


@pytest.mark.parametrize("name", ["1bhk", "2bhk", "3bhk_adjacencies", "4bhk", "clinic"])
def test_existing_fixtures_normalize_to_spaces_losslessly(name):
    raw = json.loads((FIXTURES / f"{name}.json").read_text())
    spec = RequirementsSpec.model_validate(raw)
    spaces = spaces_from_rooms(spec.rooms)
    assert sum(s.count for s in spaces) == sum(r.count for r in spec.rooms)
    assert len(spaces) == len(spec.rooms)
