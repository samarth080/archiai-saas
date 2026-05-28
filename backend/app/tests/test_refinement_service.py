from app.services.refinement_service import AddOp, RemoveOp, ResizeOp, parse_refinement


def test_parse_add_single_bedroom():
    assert parse_refinement("add a bedroom") == [AddOp(room_type="bedroom", count=1)]


def test_parse_add_numeric_count():
    assert parse_refinement("add 3 bathrooms") == [AddOp(room_type="bathroom", count=3)]


def test_parse_add_word_count():
    assert parse_refinement("add three bedrooms") == [AddOp(room_type="bedroom", count=3)]


def test_parse_add_another():
    assert parse_refinement("another bedroom please") == [AddOp(room_type="bedroom", count=1)]


def test_parse_remove_single():
    assert parse_refinement("remove the office") == [RemoveOp(room_type="office", count=1)]


def test_parse_remove_all():
    assert parse_refinement("remove all bathrooms") == [RemoveOp(room_type="bathroom", count=None)]


def test_parse_remove_no_more():
    assert parse_refinement("no more bathrooms") == [RemoveOp(room_type="bathroom", count=None)]


def test_parse_resize_bigger():
    assert parse_refinement("make the kitchen bigger") == [ResizeOp(room_type="kitchen", factor=1.4)]


def test_parse_resize_smaller():
    assert parse_refinement("shrink the living room") == [
        ResizeOp(room_type="living_room", factor=0.7)
    ]


def test_parse_combined_add_remove():
    assert parse_refinement("add a bedroom and remove the office") == [
        AddOp(room_type="bedroom", count=1),
        RemoveOp(room_type="office", count=1),
    ]


def test_parse_returns_empty_for_unrecognised():
    assert parse_refinement("just chilling here") == []
