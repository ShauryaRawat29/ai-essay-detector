import math

import pytest

from app.features.syntax import UNIVERSAL_POS, SyntaxExtractor

EXTRACT = SyntaxExtractor().extract_sentence


def test_pos_distribution():
    feats = EXTRACT("I run.")
    assert feats["pos_PRON"] == pytest.approx(1 / 3)
    assert feats["pos_VERB"] == pytest.approx(1 / 3)
    assert feats["pos_PUNCT"] == pytest.approx(1 / 3)
    assert feats["pos_NOUN"] == 0.0


def test_pos_entropy_uniform_three():
    feats = EXTRACT("I run.")
    assert feats["pos_entropy"] == pytest.approx(math.log2(3), abs=1e-9)


def test_pos_entropy_two_tags():
    # "Wow!" -> INTJ + PUNCT, each 0.5 -> entropy log2(2) == 1.0
    feats = EXTRACT("Wow!")
    assert feats["pos_entropy"] == pytest.approx(1.0, abs=1e-9)


def test_dep_depth_mean():
    feats = EXTRACT("I run.")
    # run is ROOT (depth 0); I and '.' depend on it (depth 1) -> mean 2/3
    assert feats["dep_depth_mean"] == pytest.approx(2 / 3, abs=1e-9)


def test_clause_density():
    assert EXTRACT("I run.")["clause_density"] == 1.0
    assert EXTRACT("I run and jump.")["clause_density"] == 2.0


def test_all_17_pos_keys_present():
    feats = EXTRACT("I run.")
    for tag in UNIVERSAL_POS:
        assert f"pos_{tag}" in feats


def test_determinism():
    text = "A quick brown fox jumps over the lazy dog."
    assert EXTRACT(text) == EXTRACT(text)
