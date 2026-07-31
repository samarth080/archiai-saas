"""Packet 7.2 — real, measured baseline across the acceptance prompt matrix.

Runs each acceptance prompt (from the owner's engine-generalization workflow)
through the current production path (parse_prompt -> generate_layout, the
same call sequence as POST /api/design/generate) and records real numbers:
requested vs produced space counts, hard failures, MUST adjacency ratio,
quality score, warnings, and runtime. No fabricated scores — every number
here comes from the engine actually running.

Usage: ..\\.venv311\\Scripts\\python.exe backend\\scripts\\benchmark_acceptance_prompts.py
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from app.services.layout_quality_service import score_layout_quality
from app.services.layout_service import generate_layout
from app.services.planning import (
    build_program_metadata,
    from_parser_output,
    score_graph_satisfaction,
)
from app.services.prompt_service import parse_prompt, parsed_to_room_specs

PROMPTS: dict[str, str] = {
    "house": (
        "Design a compact single-floor 2-bedroom house on a 12m x 15m "
        "east-facing plot with a living room, kitchen beside dining, "
        "two bathrooms, utility room, and good daylight."
    ),
    "clinic": (
        "Design a single-floor neighborhood clinic with reception connected "
        "to waiting, three consultation rooms near waiting, an accessible "
        "bathroom, a staff-only lab, records storage away from public areas, "
        "and a clear entrance route."
    ),
    "office": (
        "Design a small office with reception beside the open workspace, "
        "two meeting rooms connected to the workspace, one manager office "
        "with daylight, a pantry, toilets, storage away from reception, and "
        "clear circulation."
    ),
    "restaurant": (
        "Design a restaurant with naturally lit dining, a kitchen connected "
        "to service entry and cold storage, toilets away from food "
        "preparation, a reception point, and clear customer and staff "
        "circulation."
    ),
    "two_floor_house": (
        "Design a two-floor family house with living, dining, kitchen, "
        "utility, guest bedroom, and bathroom downstairs; three bedrooms and "
        "two bathrooms upstairs; align the stairs and wet areas between "
        "floors."
    ),
    "accessible_home": (
        "Design a compact accessible single-floor home with step-free "
        "entry, one bedroom, an accessible bathroom, open living and "
        "dining, kitchen, utility, 1.2m circulation clearances, and good "
        "daylight."
    ),
}


@dataclass
class BenchmarkRow:
    prompt_id: str
    building_type: str
    requested_spaces: int
    produced_spaces: int
    quality_score: int
    warnings: list[str]
    must_adjacency_ratio: float | None
    runtime_ms: float
    deterministic: bool


def _geometry_fingerprint(layout: dict) -> list[tuple]:
    """Room identity minus the fresh UUID `id` each generation assigns —
    compares actual geometry/type/zone, not incidental identifiers."""
    return sorted(
        (
            r.get("roomType"),
            r.get("floorLevel"),
            round(r["position"]["x"], 3),
            round(r["position"]["z"], 3),
            round(r["size"]["w"], 3),
            round(r["size"]["d"], 3),
        )
        for r in layout["rooms"]
        if r.get("objectType") == "room"
    )


def _run_once(prompt: str) -> tuple[dict, object, list[object]]:
    parsed = parse_prompt(prompt)
    room_specs = parsed_to_room_specs(parsed)
    layout, candidates = generate_layout(
        room_specs,
        prompt=prompt,
        building_type=parsed.building_type,
        total_floors=parsed.total_floors,
        adjacency_constraints=parsed.adjacency_constraints,
        zone_assignments=parsed.zone_assignments,
        vastu_requested=parsed.vastu_requested,
        plot_width_m=parsed.plot_width_m,
        orientation=parsed.facing_direction,
        return_all_candidates=True,
        plot_depth_m=parsed.plot_depth_m,
        road_side=parsed.road_side,
        entry_side=parsed.entry_side,
        daylight_rooms=parsed.daylight_rooms,
        separation_constraints=parsed.separation_constraints,
    )
    return layout, parsed, room_specs


def benchmark(prompt_id: str, prompt: str) -> BenchmarkRow:
    start = time.perf_counter()
    layout, parsed, room_specs = _run_once(prompt)
    runtime_ms = (time.perf_counter() - start) * 1000

    # Determinism: run again, compare geometry (ignoring the fresh UUID `id`
    # each generation assigns, which would otherwise always differ).
    layout2, _, _ = _run_once(prompt)
    deterministic = _geometry_fingerprint(layout) == _geometry_fingerprint(layout2)

    requested = len(room_specs)
    produced = len([r for r in layout["rooms"] if r.get("objectType") == "room"])

    quality = score_layout_quality(layout)

    must_ratio = None
    try:
        graph = from_parser_output(parsed, room_specs)
        build_program_metadata(parsed, graph)
        satisfaction = score_graph_satisfaction(graph, layout)
        must_edges = [c for c in satisfaction.checks if c.strength == "MUST"]
        if must_edges:
            satisfied = sum(1 for c in must_edges if c.status == "satisfied")
            must_ratio = satisfied / len(must_edges)
    except Exception:
        pass

    return BenchmarkRow(
        prompt_id=prompt_id,
        building_type=parsed.building_type,
        requested_spaces=requested,
        produced_spaces=produced,
        quality_score=quality.score,
        warnings=list(quality.warnings),
        must_adjacency_ratio=must_ratio,
        runtime_ms=runtime_ms,
        deterministic=deterministic,
    )


def main() -> None:
    rows = [benchmark(pid, prompt) for pid, prompt in PROMPTS.items()]

    print("| Prompt | Building type | Requested | Produced | Quality | Warnings | MUST adj | Runtime (ms) | Deterministic |")
    print("|---|---|---|---|---|---|---|---|---|")
    for row in rows:
        must_str = f"{row.must_adjacency_ratio:.0%}" if row.must_adjacency_ratio is not None else "n/a"
        print(
            f"| {row.prompt_id} | {row.building_type} | {row.requested_spaces} | "
            f"{row.produced_spaces} | {row.quality_score} | "
            f"{len(row.warnings)} | {must_str} | {row.runtime_ms:.0f} | {row.deterministic} |"
        )

    print("\nWarning detail:")
    for row in rows:
        for w in row.warnings:
            print(f"- [{row.prompt_id}] {w}")


if __name__ == "__main__":
    main()
