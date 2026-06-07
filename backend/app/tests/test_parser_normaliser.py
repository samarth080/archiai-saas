from app.services.parser.normaliser import normalise, tokenize


def test_normalise_replaces_multi_word_room_synonyms_first():
    assert normalise("Large master bedroom with attached bathroom") == "large master_bedroom with ensuite"


def test_normalise_expands_number_words():
    assert normalise("three bedrooms and a washroom") == "3 bedrooms and 1 bathroom"


def test_normalise_handles_open_plan_and_hyphen_variants():
    assert normalise("open-plan kitchen dining") == "open_plan_living kitchen dining"


def test_tokenize_preserves_canonical_room_tokens():
    assert tokenize("Two lounge rooms") == ["2", "living_room", "rooms"]
