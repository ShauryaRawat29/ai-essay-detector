"""Versioned dataset builder: preprocess -> validate -> dedupe -> assign splits
-> write ``records.jsonl`` + ``manifest.json`` under ``data/datasets/vX.Y.Z/``.

Manifest records the version, fixed split seed, holdout models, counts per
split and label, applied preprocessing, and duplicate removals — the
reproducibility record for every dataset version (AGENTS.md rule #9).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path

from app.datasets.dedup import content_hash
from app.datasets.preprocess import preprocess
from app.datasets.schema import EssayRecord
from app.datasets.splits import assign_splits

RECORDS_FILENAME = "records.jsonl"
MANIFEST_FILENAME = "manifest.json"


@dataclass
class DatasetBuilder:
    version: str
    seed: int = 42
    holdout_models: tuple[str, ...] = ()
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    _records: list[EssayRecord] = field(default_factory=list)

    def add_records(self, records: Iterable[EssayRecord]) -> DatasetBuilder:
        self._records.extend(records)
        return self

    def build(self, out_dir: Path) -> Path:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        processed = self._preprocess_and_validate(self._records)
        kept, removed_duplicates = self._dedupe(processed)
        split_map = assign_splits(
            kept,
            seed=self.seed,
            train_ratio=self.train_ratio,
            val_ratio=self.val_ratio,
            holdout_models=self.holdout_models,
        )
        records_out = [replace(record, split=split_map[record.essay_id]) for record in kept]
        records_out.sort(key=lambda r: r.essay_id)

        self._write_records(out_dir, records_out)
        self._write_manifest(out_dir, records_out, removed_duplicates)
        return out_dir

    @staticmethod
    def _preprocess_and_validate(records: Iterable[EssayRecord]) -> list[EssayRecord]:
        out: list[EssayRecord] = []
        for record in records:
            text, steps = preprocess(record.text)
            out.append(
                replace(
                    record,
                    text=text,
                    preprocessing=steps,
                    length_words=len(text.split()),
                )
            )
        return out

    @staticmethod
    def _dedupe(records: list[EssayRecord]) -> tuple[list[EssayRecord], int]:
        seen = set()
        kept: list[EssayRecord] = []
        removed = 0
        for record in records:
            digest = content_hash(record.text)
            if digest in seen:
                removed += 1
            else:
                seen.add(digest)
                kept.append(record)
        return kept, removed

    @staticmethod
    def _write_records(out_dir: Path, records: list[EssayRecord]) -> None:
        lines = [json.dumps(record.to_dict(), ensure_ascii=False) for record in records]
        (out_dir / RECORDS_FILENAME).write_text(
            "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
        )

    def _write_manifest(
        self, out_dir: Path, records: list[EssayRecord], removed_duplicates: int
    ) -> None:
        split_counts: dict[str, int] = {}
        label_counts: dict[str, int] = {}
        preprocessing_used: set[str] = set()
        for record in records:
            split_counts[record.split] = split_counts.get(record.split, 0) + 1
            label_counts[record.label] = label_counts.get(record.label, 0) + 1
            preprocessing_used.update(record.preprocessing)

        manifest = {
            "version": self.version,
            "created_at": datetime.now(UTC).isoformat(),
            "seed": self.seed,
            "train_ratio": self.train_ratio,
            "val_ratio": self.val_ratio,
            "holdout_models": list(self.holdout_models),
            "total_records": len(records),
            "input_records": len(self._records),
            "removed_duplicates": removed_duplicates,
            "split_counts": split_counts,
            "label_counts": label_counts,
            "preprocessing": sorted(preprocessing_used),
            "files": [RECORDS_FILENAME, MANIFEST_FILENAME],
        }
        (out_dir / MANIFEST_FILENAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
