"""Phase 4 close-out benchmark.

Committed fixtures + a candidate-by-candidate comparison of the four placement
engines (tile / bsp / row-packer `graph` / slicing-tree `gtree`) across five
building programs, each with at least one MUST adjacency so the graph engines
are generated. For every *final, post-processed* candidate (walls + doors +
partition markers already added) it records:

  - hard invariant failures (overlaps + rooms outside the footprint)
  - MUST adjacency satisfaction
  - daylight / exterior-wall satisfaction
  - reachability after doors are generated
  - minimum-dimension compliance
  - final quality score
  - winning placement engine + key warnings

The test asserts the hard safety invariants for *every* candidate (no overlaps,
inside footprint) and that the winner is deterministic; the full metric table is
printed (run with -s) for the close-out record.
"""
from app.services.layout_quality_service import (
    _floor_unreachable_rooms,
    _outside_footprint,
    _rooms_overlap,
)
from app.services.layout_service import generate_layout
from app.services.planning import from_parser_output, score_graph_satisfaction
from app.services.prompt_service import detect_building_type, parse_prompt, parsed_to_room_specs

_MIN_DIM = 1.5

# Committed benchmark fixtures — each carries at least one "next to" MUST.
FIXTURES = [
    ("office",
     "office where the workspace is next to the reception, with 3 meeting rooms, "
     "2 offices, a kitchen and 2 bathrooms"),
    ("clinic",
     "clinic where the reception is next to the waiting room and a consultation room "
     "next to the bathroom, with 3 consultation rooms and storage"),
    ("house",
     "3 bedroom house where the kitchen is next to the dining room, with a living "
     "room, 2 bathrooms and a study"),
    ("restaurant",
     "restaurant where the kitchen is next to the storage, with a dining area, a bar "
     "and 2 bathrooms"),
    ("warehouse-office",
     "warehouse with a storage area, an office next to the reception, and 2 bathrooms"),
]


def _candidate_metrics(candidate, graph):
    rooms = [r for r in candidate["rooms"] if r.get("objectType") == "room"]
    overlap_checked = [r for r in candidate["rooms"] if r.get("objectType") in ("room", "stair")]
    footprints = {f.get("level"): f.get("footprint", {}) for f in candidate.get("floors", [])}

    overlaps = sum(
        1
        for i, a in enumerate(overlap_checked)
        for b in overlap_checked[i + 1:]
        if _rooms_overlap(a, b)
    )
    outside = sum(
        1 for r in overlap_checked
        if r.get("floorLevel") in footprints and _outside_footprint(r, footprints[r["floorLevel"]])
    )
    min_dim_violations = sum(1 for r in rooms if r["size"]["w"] < _MIN_DIM - 0.01 or r["size"]["d"] < _MIN_DIM - 0.01)
    unreachable = _floor_unreachable_rooms(candidate["rooms"])
    sat = score_graph_satisfaction(graph, candidate)

    return {
        "engine": candidate["metadata"].get("placementEngine"),
        "hard_failures": overlaps + outside,
        "overlaps": overlaps,
        "outside_footprint": outside,
        "min_dim_violations": min_dim_violations,
        "must": (sat.must_satisfied, sat.must_total),
        "daylight": (sat.daylight_satisfied, sat.daylight_total),
        "unreachable_after_doors": len(unreachable),
        "score": candidate["insights"]["score"],
        "warnings": candidate["insights"]["warnings"][:3],
    }


def _run_fixture(prompt: str):
    parsed = parse_prompt(prompt)
    building_type = detect_building_type(prompt)
    specs = parsed_to_room_specs(parsed)
    graph = from_parser_output(parsed, specs)
    winner, candidates = generate_layout(
        specs,
        prompt=prompt,
        building_type=building_type,
        total_floors=parsed.total_floors,
        adjacency_constraints=parsed.adjacency_constraints,
        zone_assignments=parsed.zone_assignments,
        return_all_candidates=True,
    )
    return building_type, winner, candidates, graph


def test_phase4_benchmark_records_and_asserts_invariants(capsys):
    print("\n\n===== PHASE 4 BENCHMARK (final post-processed candidates) =====")
    for name, prompt in FIXTURES:
        building_type, winner, candidates, graph = _run_fixture(prompt)
        win_engine = winner["metadata"].get("placementEngine")
        print(f"\n[{name}] building_type={building_type} winner={win_engine} "
              f"candidates={winner['metadata'].get('candidateCount')}")
        print(f"  {'engine':10} {'hardFail':8} {'MUST':6} {'daylight':9} {'unreach':7} {'minDim':6} {'score':5}")
        for cand in candidates:
            m = _candidate_metrics(cand, graph)
            marker = " *WIN" if m["engine"] == win_engine else ""
            print(f"  {m['engine']:10} {m['hard_failures']:8} "
                  f"{m['must'][0]}/{m['must'][1]:<4} {m['daylight'][0]}/{m['daylight'][1]:<6} "
                  f"{m['unreachable_after_doors']:7} {m['min_dim_violations']:6} {m['score']:5}{marker}")
            for w in m["warnings"]:
                print(f"        - {w}")
            # Hard safety invariants must hold for EVERY candidate of EVERY engine.
            assert m["overlaps"] == 0, f"{name}/{m['engine']}: {m['overlaps']} overlaps"
            assert m["outside_footprint"] == 0, f"{name}/{m['engine']}: {m['outside_footprint']} outside footprint"

    # Emit the captured table even on success.
    out = capsys.readouterr().out
    print(out)


def test_phase4_benchmark_is_deterministic():
    for _name, prompt in FIXTURES:
        _, w1, _, _ = _run_fixture(prompt)
        _, w2, _, _ = _run_fixture(prompt)
        # Winning engine + score are stable across runs (ids differ; structure doesn't).
        assert w1["metadata"]["placementEngine"] == w2["metadata"]["placementEngine"]
        assert w1["insights"]["score"] == w2["insights"]["score"]
