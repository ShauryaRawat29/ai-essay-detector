"""Versioned feature registry and essay-level extraction entry point.

The registry catalogues every feature (implemented or planned), groups them by
family (lexical / repetition / readability / rhythm / syntax / lm / contextual),
and tracks status. ``extract_essay`` wires the deterministic pipeline:

    text -> sentence splitter -> sentence features (stylometric + syntax
    + LM signals scored with full-context) -> passage windows
    -> passage aggregates + MATTR/MTLD -> FeatureMatrix

LM features (Phase 3) come from the :class:`LMInstrument` (gpt2-medium) as a
document-level extractor: it scores the whole essay in one causal pass and
returns one vector per sentence, so every sentence is conditioned on the text
that precedes it.
"""

from __future__ import annotations

from app.features.base import FeatureMatrix
from app.features.lm_signals import LMSignalExtractor
from app.features.passages import PassageExtractor, aggregate, build_passages
from app.features.splitter import SentenceSplitter
from app.features.stylometric import StylometricExtractor
from app.features.syntax import UNIVERSAL_POS, SyntaxExtractor

FEATURE_REGISTRY_VERSION = "f0.3.0"

_LEXICAL_IMPL = ("ttr", "word_length_mean", "sent_len", "mattr", "mtld")
_REPETITION_IMPL = ("ngram_rep_char_3", "ngram_rep_word_2", "lexical_recurrence")
_READABILITY_IMPL = (
    "flesch_reading_ease",
    "flesch_kincaid_grade",
    "ari",
    "coleman_liau",
    "gunning_fog",
)
_RHYTHM_IMPL = (
    "punct_density",
    "sent_len_mean",
    "sent_len_std",
    "sent_len_cv",
    "clause_density_mean",
)
_SYNTAX_IMPL = ("pos_entropy", "dep_depth_mean", "clause_density") + tuple(
    f"pos_{tag}" for tag in UNIVERSAL_POS
)
_LM_IMPL = (
    "perplexity",
    "token_entropy_mean",
    "token_entropy_std",
    "log_prob_mean",
    "log_prob_std",
    "rank_mean",
    "rank_std",
    "prob_curvature",
)
_CONTEXTUAL_EXPERIMENTAL = ("coherence_prev", "coherence_next", "topic_consistency")
_LEXICAL_PLANNED = ("hdd", "rare_word_rate")
_REPETITION_EXPERIMENTAL = ("self_similarity",)


def _catalog() -> dict[str, tuple[str, str]]:
    cat: dict[str, tuple[str, str]] = {}

    def add(family: str, status: str, names) -> None:
        for name in names:
            cat[name] = (family, status)

    add("lexical", "implemented", _LEXICAL_IMPL)
    add("lexical", "planned", _LEXICAL_PLANNED)
    add("repetition", "implemented", _REPETITION_IMPL)
    add("repetition", "experimental", _REPETITION_EXPERIMENTAL)
    add("readability", "implemented", _READABILITY_IMPL)
    add("rhythm", "implemented", _RHYTHM_IMPL)
    add("syntax", "implemented", _SYNTAX_IMPL)
    add("lm", "implemented", _LM_IMPL)
    add("contextual", "experimental", _CONTEXTUAL_EXPERIMENTAL)
    return cat


_CATALOG = _catalog()


class FeatureRegistry:
    """Owns the versioned feature catalog and the extraction pipeline."""

    def __init__(
        self,
        sentence_extractors=None,
        document_extractors=None,
    ) -> None:
        self.splitter = SentenceSplitter()
        if sentence_extractors is None:
            sentence_extractors = (StylometricExtractor(), SyntaxExtractor())
        if document_extractors is None:
            document_extractors = (LMSignalExtractor(),)
        self.sentence_extractors = tuple(sentence_extractors)
        self.document_extractors = tuple(document_extractors)
        self.passage_extractor = PassageExtractor()

    @property
    def version(self) -> str:
        return FEATURE_REGISTRY_VERSION

    @property
    def feature_names(self) -> tuple[str, ...]:
        names: set[str] = set()
        for ex in self.sentence_extractors:
            names.update(ex.feature_names)
        for ex in self.document_extractors:
            names.update(ex.feature_names)
        names.update(self.passage_extractor.feature_names)
        return tuple(sorted(names))

    def status(self, name: str) -> str:
        if name not in _CATALOG:
            raise KeyError(name)
        return _CATALOG[name][1]

    def family(self, name: str) -> str:
        if name not in _CATALOG:
            raise KeyError(name)
        return _CATALOG[name][0]

    def extract_essay(
        self,
        text: str,
        *,
        passage_window: int = 3,
        passage_stride: int = 1,
        paragraph_fallback: bool = True,
    ) -> FeatureMatrix:
        spans = self.splitter.split_spans(text)
        sentences = tuple(span.text for span in spans)
        paragraph_breaks: frozenset[int] | None = None
        if paragraph_fallback:
            paragraph_breaks = self.splitter.paragraph_break_indices(text)
        return self.extract(
            text,
            spans,
            sentences,
            paragraph_breaks=paragraph_breaks,
            passage_window=passage_window,
            passage_stride=passage_stride,
        )

    def extract(
        self,
        text: str,
        sentence_spans,
        sentences: tuple[str, ...],
        *,
        paragraph_breaks: frozenset[int] | None = None,
        passage_window: int = 3,
        passage_stride: int = 1,
    ) -> FeatureMatrix:
        sentence_features: list[dict[str, float]] = []
        for sent in sentences:
            vec: dict[str, float] = {}
            for ex in self.sentence_extractors:
                vec.update(ex.extract_sentence(sent))
            sentence_features.append(vec)

        for ex in self.document_extractors:
            per_sentence = ex.extract_essay(text, sentence_spans)
            for i, vec in enumerate(per_sentence):
                sentence_features[i].update(vec)

        passages = build_passages(
            len(sentences),
            window=passage_window,
            stride=passage_stride,
            paragraph_breaks=paragraph_breaks,
        )

        passage_features: list[dict[str, float]] = []
        index_windows: list[tuple[int, ...]] = []
        for passage in passages:
            members = [sentence_features[i] for i in passage.sentence_indices]
            keys = tuple(members[0].keys())
            vec = aggregate(members, keys)
            passage_text = " ".join(sentences[i] for i in passage.sentence_indices)
            vec.update(self.passage_extractor.extract(passage_text))
            passage_features.append(vec)
            index_windows.append(passage.sentence_indices)

        lm = self.document_extractors[0].instrument
        return FeatureMatrix(
            feature_version=self.version,
            sentence_features=tuple(sentence_features),
            passage_features=tuple(passage_features),
            passage_sentence_indices=tuple(index_windows),
            metadata={
                "pipeline": "phase3-deterministic",
                "splitter": self.splitter.version,
                "extractors": ",".join(
                    [ex.name for ex in self.sentence_extractors]
                    + [ex.name for ex in self.document_extractors]
                    + [self.passage_extractor.name]
                ),
                "lm_instrument": f"{lm.model_name}@{lm.revision}",
                "lm_revision": lm.revision,
                "lm_device": lm.device,
            },
        )


_REGISTRY = FeatureRegistry()


def extract_essay(
    text: str,
    *,
    passage_window: int = 3,
    passage_stride: int = 1,
    paragraph_fallback: bool = True,
) -> FeatureMatrix:
    """Convenience entry point using the shared registry instance."""
    return _REGISTRY.extract_essay(
        text,
        passage_window=passage_window,
        passage_stride=passage_stride,
        paragraph_fallback=paragraph_fallback,
    )
