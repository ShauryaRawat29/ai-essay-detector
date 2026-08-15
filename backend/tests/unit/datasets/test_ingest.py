import json

import pytest

from app.datasets.ingest import ingest_ghostbuster_human, ingest_leaf, ingest_viorra
from app.datasets.schema import EssayRecord


def _make_viorra(tmp_path, records):
    path = tmp_path / "raw" / "viorra_combined_dataset.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def _make_leaf(tmp_path, records):
    path = tmp_path / "raw" / "LEAF" / "leaf.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    return path


def _make_ghostbuster(tmp_path, pairs):
    base = tmp_path / "raw" / "ghostbuster-data" / "essay"
    (base / "human").mkdir(parents=True, exist_ok=True)
    (base / "prompts").mkdir(parents=True, exist_ok=True)
    for essay_id, essay, prompt in pairs:
        (base / "human" / f"{essay_id}.txt").write_text(essay, encoding="utf-8")
        if prompt is not None:
            (base / "prompts" / f"{essay_id}.txt").write_text(prompt, encoding="utf-8")
    return tmp_path / "raw" / "ghostbuster-data"


def test_ingest_viorra_builds_human_records(tmp_path):
    path = _make_viorra(
        tmp_path,
        [
            {
                "Essay": "Faith's essay about speaking up in front of the microphone.",
                "Feedback_cleaned": "ok",
                "Score": 95,
                "Source": "Johns Hopkins Admissions Blog",
                "Feedback_Source": "Official_AdmissionStaff",
            },
            {
                "Essay": "Nancy's essay about sticky notes on the bedroom door.",
                "Feedback_cleaned": "ok",
                "Score": 95,
                "Source": "CollegeVine Common App Essay Examples",
                "Feedback_Source": "Editorial_Consultant",
            },
        ],
    )
    records = ingest_viorra(path)
    assert len(records) == 2
    r = records[0]
    assert isinstance(r, EssayRecord)
    assert r.label == "human"
    assert r.split == ""
    assert r.source == "Johns Hopkins Admissions Blog"
    assert r.license == "CC-BY-NC-4.0"
    assert r.collection_date
    assert r.essay_id.startswith("viorra-")
    assert r.text.startswith("Faith")
    assert r.length_words > 0


def test_ingest_viorra_skips_empty_essays(tmp_path):
    path = _make_viorra(
        tmp_path,
        [
            {
                "Essay": "   ",
                "Feedback_cleaned": "ok",
                "Score": 95,
                "Source": "A",
                "Feedback_Source": "B",
            },
            {
                "Essay": "A real essay about music and memory.",
                "Feedback_cleaned": "ok",
                "Score": 95,
                "Source": "A",
                "Feedback_Source": "B",
            },
        ],
    )
    records = ingest_viorra(path)
    assert len(records) == 1


def test_ingest_viorra_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ingest_viorra(tmp_path / "nope.json")


def test_ingest_leaf_builds_human_records(tmp_path):
    path = _make_leaf(
        tmp_path,
        [
            {
                "source_url": "https://essayforum.com/writing/abc/",
                "split": "train",
                "essay_title": "IELTS Academic task 2: city life",
                "essay_text": "The trend of mass immigration to metropolises continues.",
                "human_feedback_text": "fb",
                "AI-augmented_feedback_text": "aifb",
            },
        ],
    )
    records = ingest_leaf(path)
    assert len(records) == 1
    r = records[0]
    assert r.label == "human"
    assert r.source == "LEAF (EssayForum)"
    assert r.license == "CC-BY-NC-4.0"
    assert r.topic == "IELTS Academic task 2: city life"
    assert r.essay_id.startswith("leaf-")
    assert r.text == "The trend of mass immigration to metropolises continues."
    assert r.writer_demographics["source_url"].startswith("https://essayforum.com")
    assert r.writer_demographics["source_split"] == "train"


def test_ingest_leaf_skips_empty_essays(tmp_path):
    path = _make_leaf(
        tmp_path,
        [
            {
                "source_url": "u",
                "split": "train",
                "essay_title": "t",
                "essay_text": "",
                "human_feedback_text": "f",
                "AI-augmented_feedback_text": "a",
            },
        ],
    )
    assert ingest_leaf(path) == []


def test_ingest_ghostbuster_human_pairs_prompts(tmp_path):
    base = _make_ghostbuster(
        tmp_path, [(7, "A human essay about the film.", "Analyze themes in the film.")]
    )
    records = ingest_ghostbuster_human(base)
    assert len(records) == 1
    r = records[0]
    assert r.label == "human"
    assert r.essay_id == "gb-human-0007"
    assert r.topic == "Analyze themes in the film."
    assert r.license == "CC-BY-3.0"
    assert r.text == "A human essay about the film."


def test_ingest_ghostbuster_human_missing_prompt_placeholder(tmp_path):
    base = _make_ghostbuster(tmp_path, [(3, "Essay text here.", None)])
    records = ingest_ghostbuster_human(base)
    assert len(records) == 1
    assert records[0].essay_id == "gb-human-0003"
    assert records[0].topic == "unspecified_prompt"
