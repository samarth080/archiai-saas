"""Explainable validation for a ProgramGraph.

Returns human-readable warnings (never raises) so the UI can surface *why* a
program may not lay out well — e.g. "Operating theatre requires an external wall
for daylight but the footprint offers limited perimeter." These are advisory;
generation still proceeds.
"""
from dataclasses import dataclass

from app.services.planning.program_graph import ProgramGraph


@dataclass
class Warning:
    code: str
    message: str
    severity: str = "info"  # info | warning
    node_id: str | None = None


# Warning codes (the documented families):
CODE_MISSING_ADJACENCY_NODE = "adjacency.missing_node"
CODE_PUBLIC_PRIVATE_DIRECT = "separation.public_private_direct"
CODE_EXTERNAL_WALL_PRESSURE = "daylight.external_wall_pressure"
CODE_NO_CIRCULATION = "circulation.missing"
CODE_WET_ROOM_ISOLATED = "service.wet_room_isolated"
CODE_UNDERSIZED = "accessibility.undersized"

# Rough perimeter budget: a simple rectangle offers ~4 external wall segments;
# beyond that, not every daylight-needing space can sit on the perimeter.
_EXTERNAL_WALL_BUDGET = 4
_MIN_REASONABLE_DIM_M = 1.5


def validate(graph: ProgramGraph) -> list[Warning]:
    warnings: list[Warning] = []
    node_ids = {n.id for n in graph.nodes}

    # 1. Edges that reference a node not in the graph.
    for edge in graph.edges:
        for ref in (edge.node_a, edge.node_b):
            if ref not in node_ids:
                warnings.append(
                    Warning(
                        code=CODE_MISSING_ADJACENCY_NODE,
                        message=f"Relationship references a missing space '{ref}'.",
                        severity="warning",
                    )
                )

    # 2. A MUST-adjacency directly linking a public and a private space is a
    #    privacy smell.
    by_id = {n.id: n for n in graph.nodes}
    for edge in graph.edges:
        a = by_id.get(edge.node_a)
        b = by_id.get(edge.node_b)
        if not a or not b:
            continue
        zones = {a.zone, b.zone}
        if edge.strength == "MUST" and "public" in zones and "private" in zones:
            warnings.append(
                Warning(
                    code=CODE_PUBLIC_PRIVATE_DIRECT,
                    message=(
                        f"'{a.label or a.space_type}' and '{b.label or b.space_type}' are "
                        "required adjacent but span public↔private zones; consider a buffer."
                    ),
                    severity="info",
                    node_id=a.id,
                )
            )

    # 3. More daylight-needing spaces than a simple footprint's perimeter can host.
    external = [n for n in graph.nodes if n.requires_external_wall]
    if len(external) > _EXTERNAL_WALL_BUDGET:
        names = ", ".join(sorted({n.label or n.space_type for n in external}))
        warnings.append(
            Warning(
                code=CODE_EXTERNAL_WALL_PRESSURE,
                message=(
                    f"{len(external)} spaces want an external wall for daylight "
                    f"({names}); a simple footprint may not give them all one."
                ),
                severity="info",
            )
        )

    # 4. Multiple private spaces but no circulation node to reach them.
    private_count = sum(1 for n in graph.nodes if n.zone == "private")
    has_circulation = any(n.type == "circulation" for n in graph.nodes)
    if private_count >= 2 and not has_circulation:
        warnings.append(
            Warning(
                code=CODE_NO_CIRCULATION,
                message=(
                    f"{private_count} private spaces but no corridor/hallway — they may "
                    "only be reachable through each other. Consider adding circulation."
                ),
                severity="warning",
            )
        )

    # 5. Undersized spaces (accessibility / minimum clearance).
    for node in graph.buildable_nodes():
        for dim in (node.width, node.depth):
            if dim is not None and dim < _MIN_REASONABLE_DIM_M:
                warnings.append(
                    Warning(
                        code=CODE_UNDERSIZED,
                        message=(
                            f"'{node.label or node.space_type}' is only {dim:g} m on one side; "
                            "below a usable/accessible minimum."
                        ),
                        severity="info",
                        node_id=node.id,
                    )
                )
                break

    return warnings
