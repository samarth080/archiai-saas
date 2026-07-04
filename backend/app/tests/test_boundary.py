"""Phase 4 Stage 2 — boundary model."""
from app.services.planning.boundary import (
    ALL_EDGES,
    Rect,
    build_boundary,
    compute_footprint,
    split_contact,
)


def test_compute_footprint_from_area():
    fp = compute_footprint(100.0)
    assert fp.w > 0 and fp.d > 0
    # width follows sqrt(area*1.6) clamped to [7, 22]
    assert 7.0 <= fp.w <= 22.0
    # depth carries the area budget (incl. circulation overhead)
    assert fp.area >= 100.0


def test_compute_footprint_plot_width_override_and_clamp():
    assert compute_footprint(100.0, plot_width_m=12.0).w == 12.0
    assert compute_footprint(100.0, plot_width_m=100.0).w == 40.0  # clamped to _PLOT_WIDTH_MAX
    assert compute_footprint(100.0, plot_width_m=1.0).w == 4.0     # clamped to _PLOT_WIDTH_MIN


def test_compute_footprint_zero_area():
    fp = compute_footprint(0.0)
    assert fp == Rect(0.0, 0.0, 0.0, 0.0)


def test_build_boundary_orientation_sets_front_edge():
    fp = Rect(0.0, 0.0, 10.0, 8.0)
    assert build_boundary(fp, "S").front == "S"
    assert build_boundary(fp, "N").front == "N"
    assert build_boundary(fp, "e").front == "E"
    assert build_boundary(fp, None).front == "S"  # default


def test_front_door_centered_on_front_edge():
    fp = Rect(0.0, 0.0, 10.0, 8.0)
    # South front edge is at z=0, centred at x=5
    assert build_boundary(fp, "S").front_door_center == (5.0, 0.0)
    # West front edge is at x=0, centred at z=4
    assert build_boundary(fp, "W").front_door_center == (0.0, 4.0)


def test_split_contact_vertical_cut():
    left, right = split_contact(ALL_EDGES, "vertical")
    # both keep N/S; left keeps W, right keeps E; neither keeps the other's side
    assert left == frozenset({"N", "S", "W"})
    assert right == frozenset({"N", "S", "E"})


def test_split_contact_horizontal_cut():
    front, back = split_contact(ALL_EDGES, "horizontal")
    assert front == frozenset({"E", "W", "S"})
    assert back == frozenset({"E", "W", "N"})


def test_split_contact_propagates_partial_contact():
    # An interior rect that only touches the North edge: a horizontal cut gives
    # the back child N, the front child nothing.
    front, back = split_contact(frozenset({"N"}), "horizontal")
    assert front == frozenset()
    assert back == frozenset({"N"})
