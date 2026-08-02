"""Deterministic spatial-planning primitives (ProgramGraph + validation).

Building-type-agnostic, no ML. See program_graph.py for the model and the
lossless RoomSpec bridge, and validation.py for explainable warnings.
"""
from app.services.planning.program_graph import (
    Edge,
    EngineProgram,
    Node,
    ProgramGraph,
    from_building_template,
    from_parser_output,
    from_requirements,
    from_room_specs,
    from_user_objects,
    merge,
    to_engine_program,
    to_room_specs,
)
from app.services.planning.graph_scoring import (
    ConstraintCheck,
    GraphSatisfaction,
    graph_satisfaction_dict,
    score_graph_satisfaction,
)
from app.services.planning.validation import Warning, validate
from app.services.planning.program_validation import (
    build_program_metadata,
    validate_program,
)

__all__ = [
    "Node",
    "Edge",
    "ProgramGraph",
    "EngineProgram",
    "from_parser_output",
    "from_building_template",
    "from_requirements",
    "from_user_objects",
    "from_room_specs",
    "merge",
    "to_engine_program",
    "to_room_specs",
    "validate",
    "Warning",
    "ConstraintCheck",
    "GraphSatisfaction",
    "score_graph_satisfaction",
    "graph_satisfaction_dict",
    "build_program_metadata",
    "validate_program",
]
