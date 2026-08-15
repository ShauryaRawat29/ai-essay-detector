"""Exact-duplicate removal (DATASET.md leakage prevention #1).

Uses the SHA-256 hash of the preprocessed text; the first occurrence in input
order is kept. Case is significant (only exact post-preprocessing duplicates
are removed).
"""

from __future__ import annotations

import hashlib


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dedupe(
    records: list[str],
    existing_hashes: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Return ``(kept, removed)`` preserving input order; keeps first occurrence."""
    seen: set[str] = set(existing_hashes or ())
    kept: list[str] = []
    removed: list[str] = []
    for record in records:
        digest = content_hash(record)
        if digest in seen:
            removed.append(record)
        else:
            seen.add(digest)
            kept.append(record)
    return kept, removed
