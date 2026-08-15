"""Shared types and helpers for the feature extraction pipeline (Phase 2).

The detection pipeline consumes a :class:`FeatureMatrix`: per-sentence feature
vectors plus per-passage feature vectors aligned to sentence-index windows.
All features must be deterministic (same input, same output) and versioned via
the feature registry (``f0.2.0``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

WORD_RE = re.compile(r"[A-Za-z0-9']+")


def tokenize(text: str) -> list[str]:
    """Deterministic word tokenization: lowercase alphanumerics + apostrophes."""
    return WORD_RE.findall(text.lower())


def ttr(tokens: list[str]) -> float:
    """Type-token ratio over a token list (0.0 for an empty list)."""
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


@dataclass(frozen=True)
class FeatureMatrix:
    """Feature output of the Phase 2 pipeline.

    ``sentence_features[i]`` is the feature vector for sentence ``i``.
    ``passage_features[j]`` is the vector for passage ``j``, whose sentences are
    ``passage_sentence_indices[j]`` (a window of sentence indices).
    """

    feature_version: str
    sentence_features: tuple[dict[str, float], ...]
    passage_features: tuple[dict[str, float], ...]
    passage_sentence_indices: tuple[tuple[int, ...], ...]
    metadata: dict[str, str] = field(default_factory=dict)
