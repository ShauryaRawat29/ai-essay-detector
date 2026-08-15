import pytest

from app.features.stylometric import StylometricExtractor

EXTRACT = StylometricExtractor().extract_sentence


def test_ttr():
    assert EXTRACT("the the cat cat")["ttr"] == pytest.approx(0.5)


def test_ttr_no_words_is_zero():
    assert EXTRACT("!!!")["ttr"] == 0.0


def test_word_length_mean():
    assert EXTRACT("cat dog elephant")["word_length_mean"] == pytest.approx(14 / 3)


def test_lexical_recurrence():
    assert EXTRACT("the the cat")["lexical_recurrence"] == pytest.approx(1 / 3)


def test_ngram_rep_char_3():
    assert EXTRACT("aaaa")["ngram_rep_char_3"] == pytest.approx(0.5)
    assert EXTRACT("ababab")["ngram_rep_char_3"] == pytest.approx(0.5)
    assert EXTRACT("abcde")["ngram_rep_char_3"] == 0.0


def test_ngram_rep_word_2():
    assert EXTRACT("the the the")["ngram_rep_word_2"] == pytest.approx(0.5)
    assert EXTRACT("the cat sat")["ngram_rep_word_2"] == 0.0


def test_punct_density():
    assert EXTRACT("Hello, world!")["punct_density"] == pytest.approx(2 / 12)


def test_sent_len():
    assert EXTRACT("one two three")["sent_len"] == 3


def test_readability_features_pinned_from_textstat():
    # Expected values pinned from textstat 0.7.13 for this exact input
    # (regression pin of a known-good output, not re-derived here).
    text = (
        "The quiet student carefully reviewed the lengthy essay before "
        "submitting it to the university admissions office on Tuesday."
    )
    feats = EXTRACT(text)
    assert feats["flesch_reading_ease"] == pytest.approx(19.365, abs=1e-6)
    assert feats["flesch_kincaid_grade"] == pytest.approx(15.03, abs=1e-6)
    assert feats["ari"] == pytest.approx(15.3066667, abs=1e-6)
    assert feats["coleman_liau"] == pytest.approx(16.3888889, abs=1e-6)
    assert feats["gunning_fog"] == pytest.approx(16.0888889, abs=1e-6)


def test_determinism():
    text = "Repeat this exactly. Twice."
    assert EXTRACT(text) == EXTRACT(text)
