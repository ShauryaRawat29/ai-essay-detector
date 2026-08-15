"""Dataset version build runner: ingest raw -> dedupe -> split -> v0.1.0.

Run with ``python -m app.datasets.build`` from ``backend/``. Produces
``backend/data/datasets/vX.Y.Z/`` (records.jsonl + manifest.json). Human
sources are ingested from the downloaded ``data/raw``; AI self-generation is
a separate later step. Source-provenance decisions are documented in
docs/DATASET.md.
"""

from __future__ import annotations

from pathlib import Path

from app.config import BASE_DIR
from app.datasets.builder import DatasetBuilder
from app.datasets.ingest import ingest_all_human

DEFAULT_RAW_ROOT = BASE_DIR / "data" / "raw"
DEFAULT_OUTPUT_ROOT = BASE_DIR / "data" / "datasets"


def build_dataset_version(
    version: str,
    raw_root: Path,
    out_dir: Path,
    seed: int = 42,
) -> Path:
    """Ingest human sources and build a versioned dataset; returns out_dir."""
    raw_root = Path(raw_root)
    if not raw_root.is_dir():
        raise FileNotFoundError(f"raw data root not found: {raw_root}")

    builder = DatasetBuilder(version=version, seed=seed)
    builder.add_records(ingest_all_human(raw_root))
    return builder.build(out_dir)


def main() -> None:
    version = "v0.1.0"
    out_dir = DEFAULT_OUTPUT_ROOT / version
    result = build_dataset_version(version, DEFAULT_RAW_ROOT, out_dir)
    manifest = result / "manifest.json"
    print(f"built dataset v0.1.0 -> {result}")
    print(f"manifest -> {manifest}")


if __name__ == "__main__":
    main()
