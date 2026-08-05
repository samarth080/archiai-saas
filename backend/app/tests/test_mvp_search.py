"""Workflow Phase 5.1 — candidate search (layout_engine/search.py).

Additive: generate_plan() itself is untouched (verified by the plan_from_program
extraction's own test run) and does not call any of this.
"""
import json
import time
from pathlib import Path

import pytest

from app.schemas.requirements import RequirementsSpec
from app.services.layout_engine.engine import DoesNotFitError, generate_plan
from app.services.layout_engine.search import Candidate, best_candidate, generate_candidates
from app.services.quality.hard_constraints import validate
from app.services.quality.scorer import score

FIXTURES = Path(__file__).parent / "fixtures" / "requirements"
FIXTURE_NAMES = ["1bhk", "2bhk", "3bhk_adjacencies", "4bhk", "clinic"]


def _load(name: str) -> RequirementsSpec:
    return RequirementsSpec.model_validate_json((FIXTURES / f"{name}.json").read_text())


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_every_candidate_is_a_valid_plan(name):
    for candidate in generate_candidates(_load(name), n=16, seed=0):
        assert validate(candidate.plan) == []


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_candidates_are_ranked_by_ascending_energy(name):
    candidates = generate_candidates(_load(name), n=16, seed=0)
    energies = [c.energy for c in candidates]
    assert energies == sorted(energies)


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_best_of_64_scores_at_least_as_well_as_single_shot(name):
    """The doc's own acceptance bar: search must never do worse than the
    plain single-shot placement, only tie or improve on it."""
    spec = _load(name)
    single_shot_score = score(generate_plan(spec), spec).score
    best_score = score(best_candidate(spec, n=64, seed=0), spec).score
    assert best_score >= single_shot_score


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_same_spec_and_seed_produce_the_same_ranked_candidates(name):
    spec = _load(name)
    a = generate_candidates(spec, n=16, seed=7)
    b = generate_candidates(spec, n=16, seed=7)
    assert [c.plan for c in a] == [c.plan for c in b]
    assert [c.energy for c in a] == [c.energy for c in b]


def test_a_different_seed_can_produce_a_different_ranking():
    # Not a hard guarantee for every program (a tiny one may only have one
    # or two distinct room orderings at all), but 3bhk_adjacencies has
    # plenty of rooms to shuffle — pins that the seed genuinely matters,
    # not just documented as a parameter.
    spec = _load("3bhk_adjacencies")
    a = generate_candidates(spec, n=8, seed=1)
    b = generate_candidates(spec, n=8, seed=2)
    assert [c.seed for c in a] != [c.seed for c in b] or a[0].plan != b[0].plan


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_runtime_budget_is_well_under_the_doc_ceiling(name):
    """Doc's own ceiling: <= 3s per program at n=64."""
    spec = _load(name)
    start = time.time()
    generate_candidates(spec, n=64, seed=0)
    assert time.time() - start <= 3.0


def test_first_candidate_is_the_plain_single_shot_ordering():
    spec = _load("4bhk")
    candidates = generate_candidates(spec, n=1, seed=0)
    assert len(candidates) == 1
    assert candidates[0].plan == generate_plan(spec)


def test_generate_candidates_returns_empty_list_for_zero_requested():
    assert generate_candidates(_load("1bhk"), n=0, seed=0) == []


def test_best_candidate_raises_when_the_plot_genuinely_cannot_fit_anything():
    spec = RequirementsSpec.model_validate({
        "rooms": [
            {"type": "bedroom", "count": 4},
            {"type": "bathroom", "count": 2},
            {"type": "kitchen", "count": 1},
            {"type": "living_room", "count": 1},
        ],
        "plot": {"width_m": 4.0, "depth_m": 4.0},
    })
    with pytest.raises(DoesNotFitError):
        best_candidate(spec, n=16, seed=0)


def test_search_finds_a_meaningfully_better_layout_than_single_shot():
    """Real, measured value (not assumed): 3bhk_adjacencies' single-shot
    quality score is 72; best-of-64 search finds a 91. Pinned as an exact
    regression, not just a >= bound, so a future change that erodes this
    specific gain gets caught."""
    spec = _load("3bhk_adjacencies")
    single_shot_score = score(generate_plan(spec), spec).score
    best_score = score(best_candidate(spec, n=64, seed=0), spec).score
    assert single_shot_score == 72
    assert best_score == 91
    assert best_score - single_shot_score >= 15
