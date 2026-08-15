"""Deterministic sentence splitting using spaCy (en_core_web_sm).

The spaCy pipeline is loaded lazily once per process and cached, so importing
this module never triggers a model load. Splitting is deterministic: identical
input text always produces identical sentence spans.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

SPACY_MODEL = "en_core_web_sm"

_lock = threading.Lock()
_nlp: object | None = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        with _lock:
            if _nlp is None:
                import spacy

                _nlp = spacy.load(SPACY_MODEL)
    return _nlp


@dataclass(frozen=True)
class SentenceSpan:
    text: str
    start: int  # char offset of the sentence's first token in the original text
    end: int


def _paragraph_break_before(text: str, start: int) -> bool:
    """True if the whitespace run immediately before ``start`` contains 2+ newlines."""
    run_start = start
    while run_start > 0 and text[run_start - 1].isspace():
        run_start -= 1
    return text[run_start:start].count("\n") >= 2


class SentenceSplitter:
    version = "0.1.0"

    def split_spans(self, text: str) -> tuple[SentenceSpan, ...]:
        doc = _get_nlp()(text)
        spans = []
        for sent in doc.sents:
            span_text = sent.text.strip()
            if not span_text:
                continue
            start = sent[0].idx
            end = sent[-1].idx + len(sent[-1].text)
            spans.append(SentenceSpan(text=span_text, start=start, end=end))
        return tuple(spans)

    def split(self, text: str) -> tuple[str, ...]:
        """Return stripped, non-empty sentences of ``text``."""
        return tuple(span.text for span in self.split_spans(text))

    def paragraph_break_indices(self, text: str) -> frozenset:
        """Indices of sentences that begin a ``\\n\\n``-separated paragraph.

        Sentence 0 always begins the first paragraph.
        """
        breaks = set()
        for i, span in enumerate(self.split_spans(text)):
            if i == 0 or _paragraph_break_before(text, span.start):
                breaks.add(i)
        return frozenset(breaks)
