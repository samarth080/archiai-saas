"""Phase 9 property gates for arbitrary catalog programs and archetypes."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.schemas.requirements import Facing, RequirementsSpec
from app.services.catalog.space_catalog import CIRCULATION_WIDTHS
from app.services.layout_engine.archetypes import ARCHETYPES
from app.services.layout_engine.geometry import EPS, Rect
from app.services.layout_engine.search import generate_candidates
from app.services.quality.hard_constraints import validate


CATALOG_PROGRAM_TYPES = (
    "living_room",
    "kitchen",
    "dining_room",
    "bedroom",
    "bathroom",
    "office",
    "workspace",
    "meeting_room",
    "reception",
    "waiting_room",
    "consultation_room",
    "classroom",
    "retail_display",
    "changing_room",
    "storage",
    "bar",
)


@st.composite
def catalog_decisions(draw):
    kinds = draw(
        st.lists(
            st.sampled_from(CATALOG_PROGRAM_TYPES),
            min_size=3,
            max_size=7,
            unique=True,
        )
    )
    spaces = [
        {
            "space_type": kind,
            "count": draw(st.integers(min_value=1, max_value=2)),
        }
        for kind in kinds
    ]
    return spaces, draw(st.sampled_from(tuple(Facing))), draw(st.integers(0, 10_000))


@pytest.mark.parametrize("layout_style", tuple(ARCHETYPES))
@settings(max_examples=20, deadline=None, derandomize=True)
@given(catalog_decisions())
def test_catalog_programs_preserve_geometry_access_and_determinism(
    layout_style: str,
    decisions: tuple[list[dict], Facing, int],
):
    spaces, facing, seed = decisions
    spec = RequirementsSpec.model_validate({
        "building_type": "other",
        "spaces": spaces,
        "plot": {"width_m": 45.0, "depth_m": 55.0},
        "facing": facing.value,
        "layout_style": layout_style,
    })

    first = generate_candidates(spec, n=6, seed=seed)
    repeated = generate_candidates(spec, n=6, seed=seed)

    assert first
    assert first == repeated
    plot = Rect(0, 0, spec.plot.width_m, spec.plot.depth_m)
    for candidate in first:
        plan = candidate.plan
        assert validate(plan, spec) == []

        for index, room in enumerate(plan.rooms):
            room_rect = Rect(room.x, room.y, room.w, room.h)
            assert plot.contains(room_rect)
            assert all(
                not room_rect.overlaps(Rect(other.x, other.y, other.w, other.h))
                for other in plan.rooms[index + 1:]
                if room.floor == other.floor
            )

        for corridor in (
            room for room in plan.rooms
            if room.type in {"corridor", "hallway", "passage", "passageway"}
        ):
            assert min(corridor.w, corridor.h) >= (
                CIRCULATION_WIDTHS["residential"] - EPS
            )
