from app.features.splitter import SentenceSplitter


def test_empty_text_returns_no_sentences():
    splitter = SentenceSplitter()
    assert splitter.split("") == ()
    assert splitter.split("   \n\t ") == ()


def test_single_sentence_without_final_punctuation():
    assert SentenceSplitter().split("This is a single sentence") == (
        "This is a single sentence",
    )


def test_multiple_sentences_split():
    text = "This is a test. And another one here!"
    assert SentenceSplitter().split(text) == (
        "This is a test.",
        "And another one here!",
    )


def test_surrounding_whitespace_stripped():
    text = "  First sentence.   Second sentence.  "
    assert SentenceSplitter().split(text) == (
        "First sentence.",
        "Second sentence.",
    )


def test_single_newlines_do_not_force_splits():
    text = "One line\nsecond line\nthird"
    assert SentenceSplitter().split(text) == ("One line\nsecond line\nthird",)


def test_deterministic_across_calls():
    splitter = SentenceSplitter()
    text = "Determinism matters here. It must be stable across calls."
    assert splitter.split(text) == splitter.split(text)


def test_paragraph_break_indices():
    splitter = SentenceSplitter()
    text = "First para.\n\nSecond para.\n\nThird para."
    assert splitter.paragraph_break_indices(text) == frozenset({0, 1, 2})


def test_no_paragraph_breaks_single_block():
    splitter = SentenceSplitter()
    text = "First sentence. Second sentence. Third sentence."
    assert splitter.paragraph_break_indices(text) == frozenset({0})
