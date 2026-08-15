"""Sentence-level language-model signal features (Phase 3).

Consumes :class:`LMInstrument` output (measurable per-token signals) and
aggregates them per sentence. The LM is an instrument only — it never makes a
judgement. Sentences are scored with full essay context (one causal forward
pass), so a sentence's LM features reflect both its own text and what precedes
it.
"""

from __future__ import annotations

import math
import statistics

from app.models.lm_instrument import LMInstrument

FEATURE_NAMES: tuple[str, ...] = (
    "perplexity",
    "token_entropy_mean",
    "token_entropy_std",
    "log_prob_mean",
    "log_prob_std",
    "rank_mean",
    "rank_std",
    "prob_curvature",
)


class LMSignalExtractor:
    name = "lm_signal"
    version = "0.1.0"
    feature_names: tuple[str, ...] = FEATURE_NAMES

    def __init__(self, instrument=None) -> None:
        self._instrument = instrument if instrument is not None else LMInstrument()

    @property
    def instrument(self):
        return self._instrument

    def extract_essay(self, text: str, sentence_spans) -> tuple[dict[str, float], ...]:
        """Return one LM feature vector per sentence span, scored with context."""
        scored = self._instrument.score(text, sentence_spans)
        by_sentence: dict[int, list] = {}
        for sig in scored.signals:
            by_sentence.setdefault(sig.sentence_index, []).append(sig)

        result = []
        for si in range(len(sentence_spans)):
            signals = by_sentence.get(si, [])
            result.append(_aggregate_sentence(signals))
        return tuple(result)


def _aggregate_sentence(signals) -> dict[str, float]:
    if not signals:
        return {name: 0.0 for name in FEATURE_NAMES}
    log_probs = [s.log_prob for s in signals]
    entropies = [s.entropy for s in signals]
    ranks = [s.rank for s in signals]
    top1s = [s.top1_prob for s in signals]
    mean_lp = statistics.fmean(log_probs)
    return {
        "perplexity": math.exp(-mean_lp),
        "token_entropy_mean": statistics.fmean(entropies),
        "token_entropy_std": statistics.pstdev(entropies),
        "log_prob_mean": mean_lp,
        "log_prob_std": statistics.pstdev(log_probs),
        "rank_mean": statistics.fmean(ranks),
        "rank_std": statistics.pstdev(ranks),
        "prob_curvature": statistics.fmean(top1s),
    }
