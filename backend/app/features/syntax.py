"""Sentence-level syntactic features (POS distribution, POS entropy,
dependency depth, clause density) computed from the spaCy dependency parse.

These measure machine-like regularity in grammar: unnaturally even POS mixes,
and repetitive clause structures. Values are deterministic.
"""

from __future__ import annotations

import math

from app.features.splitter import _get_nlp

UNIVERSAL_POS: tuple[str, ...] = (
    "ADJ",
    "ADP",
    "ADV",
    "AUX",
    "CCONJ",
    "DET",
    "INTJ",
    "NOUN",
    "NUM",
    "PART",
    "PRON",
    "PROPN",
    "PUNCT",
    "SCONJ",
    "SYM",
    "VERB",
    "X",
)

CLAUSE_DEPS = frozenset({"ROOT", "conj", "ccomp", "xcomp", "advcl", "relcl", "acl"})

FEATURE_NAMES: tuple[str, ...] = (
    tuple(f"pos_{tag}" for tag in UNIVERSAL_POS)
    + ("pos_entropy", "dep_depth_mean", "clause_density")
)


class SyntaxExtractor:
    name = "syntax"
    version = "0.1.0"
    feature_names: tuple[str, ...] = FEATURE_NAMES

    def extract_sentence(self, text: str) -> dict[str, float]:
        doc = _get_nlp()(text)
        tokens = list(doc)
        total = len(tokens)
        pos_counts: dict[str, int] = {tag: 0 for tag in UNIVERSAL_POS}
        for tok in tokens:
            tag = tok.pos_ if tok.pos_ in UNIVERSAL_POS else "X"
            pos_counts[tag] += 1

        feats: dict[str, float] = {}
        for tag in UNIVERSAL_POS:
            feats[f"pos_{tag}"] = pos_counts[tag] / total if total else 0.0

        entropy = 0.0
        for tag in UNIVERSAL_POS:
            p = feats[f"pos_{tag}"]
            if p > 0:
                entropy -= p * math.log2(p)
        feats["pos_entropy"] = entropy

        feats["dep_depth_mean"] = _mean_dep_depth(doc) if total else 0.0
        feats["clause_density"] = (
            float(sum(1 for tok in tokens if tok.dep_ in CLAUSE_DEPS)) if total else 0.0
        )
        return feats


def _mean_dep_depth(doc) -> float:
    """Mean token distance from the ROOT in the dependency tree."""
    depths: dict[int, int] = {}

    def depth(tok) -> int:
        if tok.i in depths:
            return depths[tok.i]
        if tok.dep_ == "ROOT":
            depths[tok.i] = 0
            return 0
        d = 1 + depth(tok.head)
        depths[tok.i] = d
        return d

    values = [depth(tok) for tok in doc]
    return float(sum(values) / len(values)) if values else 0.0
