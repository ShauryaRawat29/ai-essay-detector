import json

from app.datasets.builder import DatasetBuilder
from app.datasets.schema import EssayRecord, GenerationConfig, PreprocessStep

CFG = GenerationConfig(temperature=0.7, top_p=0.9, top_k=50, max_tokens=800, seed=1)


def human(eid, text=None, wc=7, source="src-a"):
    if text is None:
        text = f"The student {eid} worked hard on the essay."
    return EssayRecord(
        essay_id=eid,
        text=text,
        label="human",
        split="",
        source=source,
        license="CC-BY-4.0",
        collection_date="2026-01-01",
        topic="adversity",
        length_words=wc,
    )


def ai(eid, text=None, wc=7, model="gpt2-medium"):
    if text is None:
        text = f"An AI generated essay about {eid} and curiosity."
    return EssayRecord(
        essay_id=eid,
        text=text,
        label="ai_generated",
        split="",
        model=model,
        model_revision="rev",
        prompt_template="Write on {topic}",
        prompt_variables={"topic": "curiosity"},
        generation_config=CFG,
        generation_date="2026-01-01",
        topic="curiosity",
        length_words=wc,
    )


def test_build_creates_jsonl_and_manifest(tmp_path):
    builder = DatasetBuilder(version="v0.1.0", seed=42)
    builder.add_records([human("h1"), ai("a1")])
    out = builder.build(tmp_path)

    assert (out / "records.jsonl").exists()
    assert (out / "manifest.json").exists()

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "v0.1.0"
    assert manifest["seed"] == 42
    assert manifest["total_records"] == 2


def test_build_assigns_splits_and_writes_records(tmp_path):
    builder = DatasetBuilder(version="v0.1.0", seed=42)
    builder.add_records([human("h1"), ai("a1")])
    out = builder.build(tmp_path)

    lines = (out / "records.jsonl").read_text(encoding="utf-8").strip().splitlines()
    records = [json.loads(line) for line in lines]
    assert {r["essay_id"] for r in records} == {"h1", "a1"}
    assert {r["split"] for r in records} <= {"train", "val", "test"}
    assert all(r["label"] in {"human", "ai_generated"} for r in records)


def test_builder_applies_preprocessing(tmp_path):
    builder = DatasetBuilder(version="v0.1.0", seed=42)
    builder.add_records([human("h1", text="cafe\u0301    essay", wc=2)])
    out = builder.build(tmp_path)
    line = (out / "records.jsonl").read_text(encoding="utf-8").strip().splitlines()[0]
    rec = json.loads(line)
    assert rec["text"] == "caf\u00e9 essay"
    assert PreprocessStep.NFC_NORMALIZE.value in rec["preprocessing"]


def test_builder_dedupes_exact_duplicates(tmp_path):
    builder = DatasetBuilder(version="v0.1.0", seed=42)
    builder.add_records([human("h1", text="Same text."), human("h2", text="Same text.")])
    out = builder.build(tmp_path)
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["total_records"] == 1
    assert manifest["removed_duplicates"] == 1


def test_builder_manifest_counts_per_split(tmp_path):
    records = [human(f"h{i}") for i in range(20)] + [ai(f"a{i}") for i in range(20)]
    builder = DatasetBuilder(version="v0.1.0", seed=1)
    builder.add_records(records)
    out = builder.build(tmp_path)
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert sum(manifest["split_counts"].values()) == 40
    assert set(manifest["split_counts"]) <= {"train", "val", "test"}


def test_build_deterministic(tmp_path):
    records = [human(f"h{i}") for i in range(20)] + [ai(f"a{i}") for i in range(20)]
    out1 = DatasetBuilder(version="v0.1.0", seed=1).add_records(records).build(tmp_path / "a")
    out2 = DatasetBuilder(version="v0.1.0", seed=1).add_records(records).build(tmp_path / "b")
    f1 = (out1 / "records.jsonl").read_text(encoding="utf-8")
    f2 = (out2 / "records.jsonl").read_text(encoding="utf-8")
    assert f1 == f2
