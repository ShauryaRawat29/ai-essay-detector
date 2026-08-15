"""Text preprocessing for dataset records (provenance step recording).

Applied steps are recorded on each record. Paragraph breaks are PRESERVED
(single ``\\n`` and double ``\\n``) because the passage pipeline (ADR-003) uses
``\\n\\n`` as a hard window boundary — collapsing all whitespace would destroy
that signal.
"""

from __future__ import annotations

import re
import unicodedata

from app.datasets.schema import PreprocessStep

_NEWLINE_RE = re.compile(r"\r\n|\r")
_TRIPLE_NEWLINE_RE = re.compile(r"\n{3,}")
_HSPACE_RE = re.compile(r"[ \t]+")


def preprocess(text: str) -> tuple[str, tuple[str, ...]]:
    """Normalize text and return ``(processed_text, applied_steps)``."""
    _validate_encoding(text)
    steps: list[str] = []

    text = unicodedata.normalize("NFC", text)
    steps.append(PreprocessStep.NFC_NORMALIZE.value)

    text = _NEWLINE_RE.sub("\n", text)
    text = _TRIPLE_NEWLINE_RE.sub("\n\n", text)
    steps.append(PreprocessStep.NEWLINE_NORMALIZE.value)

    text = _HSPACE_RE.sub(" ", text)
    steps.append(PreprocessStep.COLLAPSE_HSPACE.value)

    text = text.strip()
    steps.append(PreprocessStep.STRIP.value)

    return text, tuple(steps)


def _validate_encoding(text: str) -> None:
    if "\x00" in text:
        raise ValueError("null byte in text")
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in text):
        raise ValueError("surrogate code point in text")
