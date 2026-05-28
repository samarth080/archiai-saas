from app.services.refinement_service import AddOp, RemoveOp, parse_refinement


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
