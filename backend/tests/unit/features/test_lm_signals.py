import pytest

from app.features import extract_essay

ESSAY = (
    "The quiet student carefully reviewed the lengthy essay before submitting it. "
    "She checked every paragraph twice. "
    "Finally, she pressed send."
)

# Golden LM features pinned from the real instrument (gpt2-medium @
# 6dcaa7a952f72f9298047fd5137cd6e4f05f41da, CUDA, 2026-08-15). These are
# known-good regression pins (like the textstat pins): if the instrument,
# revision, or scoring logic changes, the values must be re-pinned. Tolerances
# account for device-level float variation (CPU vs CUDA).
GOLDEN = [
    {
        "perplexity": 249.262908928,
        "token_entropy_mean": 5.036283775,
        "token_entropy_std": 2.125781419,
        "log_prob_mean": -5.518508199,
        "log_prob_std": 3.609674513,
        "rank_mean": 864.454545455,
        "rank_std": 1715.671687370,
        "prob_curvature": 0.201216526,
    },
    {
        "perplexity": 54.527502548,
        "token_entropy_mean": 3.637981494,
        "token_entropy_std": 0.867765098,
        "log_prob_mean": -3.998705208,
        "log_prob_std": 1.609039934,
        "rank_mean": 19.0,
        "rank_std": 21.969676071,
        "prob_curvature": 0.209408811,
    },
    {
        "perplexity": 10.095577459,
        "token_entropy_mean": 2.702358623,
        "token_entropy_std": 1.554551798,
        "log_prob_mean": -2.312097453,
        "log_prob_std": 2.264133423,
        "rank_mean": 17.666666667,
        "rank_std": 35.122009560,
        "prob_curvature": 0.468946528,
    },
]


def test_lm_sentence_features_pinned():
    matrix = extract_essay(ESSAY)
    for si, expected in enumerate(GOLDEN):
        for key, value in expected.items():
            assert matrix.sentence_features[si][key] == pytest.approx(
                value, rel=1e-2, abs=1e-3
            )


def test_lm_feature_names_present():
    matrix = extract_essay(ESSAY)
    keys = set(matrix.sentence_features[0])
    assert {
        "perplexity",
        "token_entropy_mean",
        "token_entropy_std",
        "log_prob_mean",
        "log_prob_std",
        "rank_mean",
        "rank_std",
        "prob_curvature",
    } <= keys


def test_passage_lm_aggregates_present():
    matrix = extract_essay(ESSAY)
    pk = set(matrix.passage_features[0])
    # sentence-level feature ``perplexity`` aggregates to ``perplexity_mean``;
    # sentence-level ``log_prob_mean`` (mean of token log-probs) aggregates to
    # ``log_prob_mean_mean``.
    assert "perplexity_mean" in pk
    assert "perplexity_std" in pk
    assert "log_prob_mean_mean" in pk
    assert "rank_mean_mean" in pk
    assert "prob_curvature_mean" in pk


def test_metadata_includes_instrument_provenance():
    matrix = extract_essay(ESSAY)
    assert "gpt2-medium" in matrix.metadata["lm_instrument"]
    assert matrix.metadata["lm_revision"].startswith("6dcaa7a")


def test_lm_features_deterministic():
    a = extract_essay(ESSAY)
    b = extract_essay(ESSAY)
    assert a.sentence_features == b.sentence_features
    assert a.passage_features == b.passage_features
