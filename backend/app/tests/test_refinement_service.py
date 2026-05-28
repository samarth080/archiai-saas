from app.services.refinement_service import AddOp, parse_refinement


def test_parse_add_single_bedroom():
    assert parse_refinement("add a bedroom") == [AddOp(room_type="bedroom", count=1)]


def test_parse_add_numeric_count():
    assert parse_refinement("add 3 bathrooms") == [AddOp(room_type="bathroom", count=3)]


def test_parse_add_word_count():
    assert parse_refinement("add three bedrooms") == [AddOp(room_type="bedroom", count=3)]


def test_parse_add_another():
    assert parse_refinement("another bedroom please") == [AddOp(room_type="bedroom", count=1)]
