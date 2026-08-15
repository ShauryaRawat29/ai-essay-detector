"""Passage windowing (ADR-003) and passage-level aggregation (Phase 2).

Passages are fixed overlapping windows of sentences (default window=3,
stride=1) that respect explicit ``\\n\\n`` paragraph boundaries when provided
(paragraph fallback). Passage feature vectors are generic aggregates of the
sentence-level features plus passage-only measures (MATTR, MTLD).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from app.features.base import tokenize, ttr

MTLD_FACTOR = 0.72
MATTR_WINDOW = 50
PERCENTILES = (5.0, 25.0, 50.0, 75.0, 95.0)


@dataclass(frozen=True)
class Passage:
    sentence_indices: tuple[int, ...]


def build_passages(
    n_sentences: int,
    *,
    window: int = 3,
    stride: int = 1,
    paragraph_breaks: frozenset[int] | None = None,
) -> tuple[Passage, ...]:
    """Build overlapping sentence windows that never cross paragraph boundaries.

    ``paragraph_breaks`` is a set of sentence indices that begin a paragraph
    (the first segment always starts at 0). A window must be fully contained in
    one paragraph segment.
    """
    if n_sentences < 0:
        raise ValueError("n_sentences must be >= 0")
    if window < 1:
        raise ValueError("window must be >= 1")
    if stride < 1:
        raise ValueError("stride must be >= 1")
    if n_sentences == 0:
        return ()

    if paragraph_breaks:
        ordered = sorted(paragraph_breaks)
        segments = [
            (ordered[i], ordered[i + 1] if i + 1 < len(ordered) else n_sentences)
            for i in range(len(ordered))
        ]
    else:
        segments = [(0, n_sentences)]

    passages: list[Passage] = []
    for seg_start, seg_stop in segments:
        start = seg_start
        while start + window <= seg_stop:
            passages.append(Passage(tuple(range(start, start + window))))
            start += stride
    return tuple(passages)


def aggregate(
    vectors: list[dict[str, float]], names: tuple[str, ...]
) -> dict[str, float]:
    """Aggregate sentence feature vectors into passage-level statistics.

    For every feature in ``names`` emits ``<name>_mean/_std/_cv/_min/_max`` and
    ``<name>_p5/_p25/_p50/_p75/_p95``. Uses population std; ``_cv`` is NaN when
    the mean is 0.
    """
    out: dict[str, float] = {}
    for name in names:
        values = np.array([v[name] for v in vectors if name in v], dtype=float)
        if values.size == 0:
            continue
        mean = float(values.mean())
        std = float(values.std())
        cv = float(std / mean) if mean != 0 else math.nan
        out[f"{name}_mean"] = mean
        out[f"{name}_std"] = std
        out[f"{name}_cv"] = cv
        out[f"{name}_min"] = float(values.min())
        out[f"{name}_max"] = float(values.max())
        for p in PERCENTILES:
            out[f"{name}_p{int(p)}"] = float(np.percentile(values, p))
    return out


class PassageExtractor:
    """Passage-only measures computed over a passage's concatenated text."""

    name = "passage"
    version = "0.1.0"
    feature_names: tuple[str, ...] = ("mattr", "mtld")

    def extract(self, passage_text: str) -> dict[str, float]:
        return {"mattr": self.mattr(passage_text), "mtld": self.mtld(passage_text)}

    def mattr(self, text: str) -> float:
        """Moving-average TTR over sliding 50-token windows.

        Falls back to plain TTR when the passage has fewer than 50 tokens so the
        feature is always defined. Returns 0.0 for a token-less passage.
        """
        tokens = tokenize(text)
        n = len(tokens)
        if n == 0:
            return 0.0
        if n < MATTR_WINDOW:
            return ttr(tokens)
        windows = [ttr(tokens[i : i + MATTR_WINDOW]) for i in range(n - MATTR_WINDOW + 1)]
        return float(sum(windows) / len(windows))

    def mtld(self, text: str) -> float:
        """Mean segmental type-token ratio (McCarthy & Jarvis, factor 0.72).

        Average of the forward and backward segment scores; trailing partial
        segments contribute ``(segment TTR) / factor``.
        """
        tokens = tokenize(text)
        if not tokens:
            return 0.0
        forward = self._mtld_direction(tokens)
        backward = self._mtld_direction(list(reversed(tokens)))
        return (forward + backward) / 2.0

    @staticmethod
    def _mtld_direction(tokens: list[str]) -> float:
        n = len(tokens)
        pos = 0
        count = 0.0
        while pos < n:
            seen = set()
            seg_len = 0
            while pos < n:
                seen.add(tokens[pos])
                seg_len += 1
                pos += 1
                if len(seen) / seg_len <= MTLD_FACTOR:
                    count += 1
                    break
            else:
                return count + (len(seen) / seg_len) / MTLD_FACTOR
        return count
