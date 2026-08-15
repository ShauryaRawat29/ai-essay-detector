"""Sentence-level stylometric features (lexical diversity, repetition,
readability, punctuation rhythm). All values are deterministic and derived from
measurable surface properties of the sentence only.
"""

from __future__ import annotations

import re

import textstat

from app.features.base import tokenize

WHITESPACE_RE = re.compile(r"\s+")
PUNCT_CHARS = frozenset(".,!?;:\"'()[]{}<>-")

FEATURE_NAMES: tuple[str, ...] = (
    "ttr",
    "word_length_mean",
    "sent_len",
    "lexical_recurrence",
    "ngram_rep_char_3",
    "ngram_rep_word_2",
    "punct_density",
    "flesch_reading_ease",
    "flesch_kincaid_grade",
    "ari",
    "coleman_liau",
    "gunning_fog",
)


class StylometricExtractor:
    name = "stylometric"
    version = "0.1.0"
    feature_names: tuple[str, ...] = FEATURE_NAMES

    def extract_sentence(self, text: str) -> dict[str, float]:
        tokens = tokenize(text)
        total = len(tokens)
        unique = len(set(tokens))
        feats: dict[str, float] = {}
        feats["ttr"] = unique / total if total else 0.0
        feats["word_length_mean"] = sum(len(t) for t in tokens) / total if total else 0.0
        feats["sent_len"] = float(total)
        feats["lexical_recurrence"] = (total - unique) / total if total else 0.0
        feats["ngram_rep_char_3"] = _char_ngram_repetition(text, 3)
        feats["ngram_rep_word_2"] = _word_ngram_repetition(tokens, 2)
        feats["punct_density"] = _punct_density(text)
        feats["flesch_reading_ease"] = float(textstat.flesch_reading_ease(text))
        feats["flesch_kincaid_grade"] = float(textstat.flesch_kincaid_grade(text))
        feats["ari"] = float(textstat.automated_readability_index(text))
        feats["coleman_liau"] = float(textstat.coleman_liau_index(text))
        feats["gunning_fog"] = float(textstat.gunning_fog(text))
        return feats


def _char_ngram_repetition(text: str, n: int) -> float:
    """Share of duplicate character n-grams in the compacted (whitespace-removed) text."""
    compact = WHITESPACE_RE.sub("", text)
    if len(compact) < n:
        return 0.0
    grams = [compact[i : i + n] for i in range(len(compact) - n + 1)]
    return 1.0 - len(set(grams)) / len(grams)


def _word_ngram_repetition(tokens: list[str], n: int) -> float:
    """Share of duplicate word n-grams over the tokenized sentence."""
    if len(tokens) < n:
        return 0.0
    grams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    return 1.0 - len(set(grams)) / len(grams)


def _punct_density(text: str) -> float:
    """Punctuation share over non-whitespace characters (0.0 for no characters)."""
    non_ws = [c for c in text if not c.isspace()]
    if not non_ws:
        return 0.0
    punct = sum(1 for c in non_ws if c in PUNCT_CHARS)
    return punct / len(non_ws)
