"""Document-level split assignment (DATASET.md strategy; AGENTS.md rule #6).

Rules, all document-level only:
- AI-polished essays always go to ``test_secondary``; their paired original
  human essay (the leak group) is moved there too.
- AI essays from held-out model families go to ``test_cross_model``.
- Everything else is split train/val/test stratified by (origin, length bucket)
  with a fixed seed (deterministic; permutation-independent).
"""

from __future__ import annotations

import random
from collections.abc import Iterable

from app.datasets.schema import EssayRecord
from app.evaluation.baselines import length_bucket


def assign_splits(
    records: Iterable[EssayRecord],
    *,
    seed: int,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    holdout_models: Iterable[str] = (),
) -> dict[str, str]:
    """Map every essay_id to its split. ``split`` field of records is ignored."""
    records = list(records)
    assignments: dict[str, str] = {}

    polished = [r for r in records if r.label == "ai_polished"]
    leak_ids = {r.original_essay_id for r in polished if r.original_essay_id}
    for r in polished:
        assignments[r.essay_id] = "test_secondary"
    for r in records:
        if r.essay_id in leak_ids and r.essay_id not in assignments:
            assignments[r.essay_id] = "test_secondary"

    holdout = set(holdout_models)
    for r in records:
        if r.essay_id in assignments:
            continue
        if r.label != "human" and r.model in holdout:
            assignments[r.essay_id] = "test_cross_model"

    pool = [r for r in records if r.essay_id not in assignments]
    assignments.update(_stratified_split(pool, seed, train_ratio, val_ratio))
    return assignments


def _stratified_split(
    pool: list[EssayRecord], seed: int, train_ratio: float, val_ratio: float
) -> dict[str, str]:
    rng = random.Random(seed)
    strata: dict[tuple[str, str], list[EssayRecord]] = {}
    for record in pool:
        origin = record.source or record.model or "unknown"
        strata.setdefault((origin, length_bucket(record.length_words)), []).append(record)

    assignments: dict[str, str] = {}
    for key in sorted(strata):
        members = sorted(strata[key], key=lambda r: r.essay_id)
        rng.shuffle(members)
        n = len(members)
        n_train = int(round(n * train_ratio))
        n_val = int(round(n * val_ratio))
        for record in members[:n_train]:
            assignments[record.essay_id] = "train"
        for record in members[n_train : n_train + n_val]:
            assignments[record.essay_id] = "val"
        for record in members[n_train + n_val :]:
            assignments[record.essay_id] = "test"
    return assignments
