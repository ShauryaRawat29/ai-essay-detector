"""Raw-source ingestion: convert downloaded sources into EssayRecords.

Each function reads one source format from ``backend/data/raw`` and returns
provenance-complete ``EssayRecord``\\ s (label ``human``, split ``""`` to be
assigned later by the :class:`DatasetBuilder`). Whitespace-only essays are
skipped. The recorded ``collection_date`` is the ACQUISITION date — not the
original authorship date, which the sources do not expose (a documented
provenance limitation; see docs/DATASET.md).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from app.datasets.schema import EssayRecord

ACQUISITION_DATE = "2026-08-15"

LEAF_LICENSE = "CC-BY-NC-4.0"
VIORRA_LICENSE = "CC-BY-NC-4.0"
GHOSTBUSTER_LICENSE = "CC-BY-3.0"

LEAF_SOURCE = "LEAF (EssayForum)"
GHOSTBUSTER_SOURCE = "Ghostbuster (vivek3141/ghostbuster-data)"
UNSPECIFIED_PROMPT = "unspecified_prompt"


def _is_blank(text: str) -> bool:
    return not text or not text.strip()


def ingest_viorra(path: Path) -> list[EssayRecord]:
    """VIORRA admissions essays (128 on disk; JSON list of {Essay, Source, ...})."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"VIORRA source not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    records: list[EssayRecord] = []
    for idx, row in enumerate(data):
        essay = row.get("Essay") or ""
        if _is_blank(essay):
            continue
        records.append(
            EssayRecord(
                essay_id=f"viorra-{idx + 1:04d}",
                text=essay,
                label="human",
                split="",
                length_words=len(essay.split()),
                topic="personal_statement",
                source=str(row.get("Source") or "unknown"),
                license=VIORRA_LICENSE,
                collection_date=ACQUISITION_DATE,
            )
        )
    return records


def ingest_leaf(path: Path) -> list[EssayRecord]:
    """LEAF essays (4,918 rows; JSONL of {essay_text, essay_title, ...})."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"LEAF source not found: {path}")

    records: list[EssayRecord] = []
    with path.open(encoding="utf-8") as fh:
        for idx, line in enumerate(fh):
            if not line.strip():
                continue
            row = json.loads(line)
            essay = row.get("essay_text") or ""
            if _is_blank(essay):
                continue
            records.append(
                EssayRecord(
                    essay_id=f"leaf-{idx + 1:05d}",
                    text=essay,
                    label="human",
                    split="",
                    length_words=len(essay.split()),
                    topic=row.get("essay_title") or "unspecified_topic",
                    source=LEAF_SOURCE,
                    license=LEAF_LICENSE,
                    collection_date=ACQUISITION_DATE,
                    writer_demographics={
                        "source_url": row.get("source_url") or "",
                        "source_split": row.get("split") or "",
                    },
                )
            )
    return records


def ingest_ghostbuster_human(root: Path) -> list[EssayRecord]:
    """Ghostbuster human essays (1,000; essay/human/N.txt paired with prompts/N.txt)."""
    root = Path(root)
    human_dir = root / "essay" / "human"
    prompts_dir = root / "essay" / "prompts"
    if not human_dir.is_dir():
        raise FileNotFoundError(f"Ghostbuster human dir not found: {human_dir}")

    def _ordered_text_files(directory: Path) -> list[tuple[int, Path]]:
        out = []
        for path in directory.iterdir():
            if path.suffix != ".txt":
                continue
            try:
                number = int(path.stem)
            except ValueError:
                continue
            out.append((number, path))
        return sorted(out)

    records: list[EssayRecord] = []
    for number, path in _ordered_text_files(human_dir):
        essay = path.read_text(encoding="utf-8")
        if _is_blank(essay):
            continue
        prompt_path = prompts_dir / f"{number}.txt"
        topic = UNSPECIFIED_PROMPT
        if prompt_path.exists():
            topic = prompt_path.read_text(encoding="utf-8").strip() or UNSPECIFIED_PROMPT
        records.append(
            EssayRecord(
                essay_id=f"gb-human-{number:04d}",
                text=essay,
                label="human",
                split="",
                length_words=len(essay.split()),
                topic=topic,
                source=GHOSTBUSTER_SOURCE,
                license=GHOSTBUSTER_LICENSE,
                collection_date=ACQUISITION_DATE,
            )
        )
    return records


def ingest_all_human(raw_root: Path) -> Iterable[EssayRecord]:
    """Ingest every downloaded human source under ``raw_root``."""
    raw_root = Path(raw_root)
    viorra = ingest_viorra(raw_root / "viorra-admissions-essays" / "viorra_combined_dataset.json")
    leaf = ingest_leaf(raw_root / "LEAF" / "leaf.jsonl")
    ghostbuster = ingest_ghostbuster_human(raw_root / "ghostbuster-data")
    yield from (viorra + leaf + ghostbuster)
