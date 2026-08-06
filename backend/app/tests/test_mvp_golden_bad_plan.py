"""Phase 9 golden regression for the reported landlocked-bath layout."""

from app.schemas.layout_plan import Door, LayoutPlan, PlanPlot, PlanRoom, Wall
from app.schemas.requirements import RequirementsSpec
from app.services.layout_engine.engine import generate_plan
from app.services.quality.hard_constraints import _door_adjacency, validate
from app.services.quality.scorer import score


def _landlocked_bath_plan() -> LayoutPlan:
    """Entry -> Bedroom -> Bathroom, with the bathroom in the plot centre."""

    return LayoutPlan(
        plot=PlanPlot(width_m=9, depth_m=9, facing="east"),
        rooms=[
            PlanRoom(id="entry", type="entry", label="Entry", x=0, y=0, w=3, h=3),
            PlanRoom(id="bed", type="bedroom", label="Bedroom", x=3, y=0, w=3, h=3),
            PlanRoom(id="bath", type="bathroom", label="Landlocked Bathroom", x=3, y=3, w=3, h=3),
        ],
        walls=[
            Wall(id="entry-bed", x1=3, y1=0, x2=3, y2=3),
            Wall(id="bed-bath", x1=3, y1=3, x2=6, y2=3),
        ],
        doors=[
            Door(id="door-entry-bed", wall_ref="entry-bed", offset=1),
            Door(id="door-bed-bath", wall_ref="bed-bath", offset=1),
        ],
    )


def _requirements() -> RequirementsSpec:
    return RequirementsSpec.model_validate({
        "building_type": "apartment",
        "spaces": [
            {"space_type": "entry", "count": 1},
            {"space_type": "bedroom", "count": 1},
            {"space_type": "bathroom", "count": 1},
        ],
        "plot": {"width_m": 9, "depth_m": 9},
        "facing": "east",
    })


def test_landlocked_bath_reproduces_the_three_human_diagnostics():
    plan = _landlocked_bath_plan()
    requirements = _requirements()

    hard_codes = {violation.code for violation in validate(plan, requirements)}
    warning_codes = {
        warning.code
        for warning in score(plan, requirements, include_vastu=True).warnings
    }

    assert "through_room_access" in hard_codes
    assert "generic.wet_room_exterior" in warning_codes
    assert "vastu.brahmasthan_occupied" in warning_codes


def test_explicit_ensuite_attachment_is_still_allowed():
    plan = _landlocked_bath_plan()
    payload = _requirements().model_dump(mode="json")
    payload["adjacency"] = [
        {"room_a": "bedroom", "room_b": "bathroom", "strength": "must"}
    ]
    requirements = RequirementsSpec.model_validate(payload)

    assert "through_room_access" not in {
        violation.code for violation in validate(plan, requirements)
    }


def test_three_bhk_bathrooms_open_directly_to_circulation():
    requirements = RequirementsSpec.model_validate({
        "building_type": "house",
        "spaces": [
            {"space_type": "bedroom", "count": 3},
            {"space_type": "bathroom", "count": 2},
            {"space_type": "living_room", "count": 1},
            {"space_type": "kitchen", "count": 1},
        ],
        "plot": {"width_m": 12, "depth_m": 15},
        "facing": "east",
    })

    plan = generate_plan(requirements)
    adjacency = _door_adjacency(plan)
    types = {room.id: room.type for room in plan.rooms}
    circulation = {"corridor", "hallway", "passage", "passageway"}

    assert validate(plan, requirements) == []
    for bathroom in (room for room in plan.rooms if room.type == "bathroom"):
        assert any(types[neighbour] in circulation for neighbour in adjacency[bathroom.id])
