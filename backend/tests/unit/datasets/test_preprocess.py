import pytest

from app.datasets.preprocess import preprocess


def test_nfc_normalization():
    text, steps = preprocess("cafe\u0301")  # e + combining acute
    assert text == "caf\u00e9"  # single precomposed codepoint
    assert "nfc_normalize" in steps


def test_crlf_normalized_and_paragraph_breaks_preserved():
    text, _ = preprocess("first\r\n\r\nsecond")
    assert text == "first\n\nsecond"


def test_horizontal_whitespace_collapsed():
    text, steps = preprocess("a\t\t b    c")
    assert text == "a b c"
    assert "collapse_hspace" in steps


def test_single_newlines_preserved():
    text, _ = preprocess("line one\nline two")
    assert text == "line one\nline two"


def test_strip_whitespace():
    text, steps = preprocess("   padded text   ")
    assert text == "padded text"
    assert "strip" in steps


def test_null_byte_rejected():
    with pytest.raises(ValueError):
        preprocess("bad\x00text")


def test_surrogate_rejected():
    with pytest.raises(ValueError):
        preprocess("bad\ud800text")


def test_three_plus_newlines_collapsed_to_paragraph_break():
    text, _ = preprocess("a\n\n\n\nb")
    assert text == "a\n\nb"


def test_ascii_unchanged():
    text, steps = preprocess("Simple ASCII essay.")
    assert text == "Simple ASCII essay."
    assert len(steps) == 4
