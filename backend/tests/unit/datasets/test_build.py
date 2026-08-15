import json

import pytest

from app.datasets.build import build_dataset_version


def _make_viorra(tmp_path):
    path = tmp_path / "raw" / "viorra-admissions-essays" / "viorra_combined_dataset.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "Essay": "Faith's essay about speaking up.",
            "Feedback_cleaned": "ok",
            "Score": 95,
            "Source": "Johns Hopkins Admissions Blog",
            "Feedback_Source": "Official_AdmissionStaff",
        },
        {
            "Essay": "Nancy's essay about sticky notes.",
            "Feedback_cleaned": "ok",
            "Score": 95,
            "Source": "CollegeVine Common App Essay Examples",
            "Feedback_Source": "Editorial_Consultant",
        },
    ]
    path.write_text(json.dumps(rows), encoding="utf-8")


def _make_leaf(tmp_path):
    path = tmp_path / "raw" / "LEAF" / "leaf.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        {
            "source_url": "https://essayforum.com/writing/abc/",
            "split": "train",
            "essay_title": "IELTS task 2: city life",
            "essay_text": "The trend of mass immigration to metropolises continues.",
            "human_feedback_text": "f",
            "AI-augmented_feedback_text": "a",
        },
        {
            "source_url": "https://essayforum.com/writing/def/",
            "split": "test",
            "essay_title": "IELTS task 2: environment",
            "essay_text": "Environmental problems require global cooperation.",
            "human_feedback_text": "f",
            "AI-augmented_feedback_text": "a",
        },
    ]
    path.write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")


def _make_ghostbuster(tmp_path):
    base = tmp_path / "raw" / "ghostbuster-data" / "essay"
    (base / "human").mkdir(parents=True)
    (base / "prompts").mkdir(parents=True)
    (base / "human" / "1.txt").write_text("A human essay about the film.", encoding="utf-8")
    (base / "prompts" / "1.txt").write_text("Analyze themes in the film.", encoding="utf-8")


def _make_raw(tmp_path):
    _make_viorra(tmp_path)
    _make_leaf(tmp_path)
    _make_ghostbuster(tmp_path)
    return tmp_path / "raw"


def test_build_dataset_version_ingests_all_sources(tmp_path):
    raw = _make_raw(tmp_path)
    out = build_dataset_version("v0.1.0", raw, tmp_path / "out", seed=42)
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "v0.1.0"
    assert manifest["total_records"] == 5
    assert manifest["label_counts"] == {"human": 5}
    assert sum(manifest["split_counts"].values()) == 5
    assert set(manifest["split_counts"]) <= {"train", "val", "test"}


def test_build_dataset_version_records_have_provenance(tmp_path):
    raw = _make_raw(tmp_path)
    out = build_dataset_version("v0.1.0", raw, tmp_path / "out", seed=1)
    text = (out / "records.jsonl").read_text(encoding="utf-8").strip()
    records = [json.loads(line) for line in text.splitlines()]
    assert {r["source"] for r in records} == {
        "Johns Hopkins Admissions Blog",
        "CollegeVine Common App Essay Examples",
        "LEAF (EssayForum)",
        "Ghostbuster (vivek3141/ghostbuster-data)",
    }
    assert all(r["license"] in {"CC-BY-NC-4.0", "CC-BY-3.0"} for r in records)
    assert all(r["split"] in {"train", "val", "test"} for r in records)


def test_build_dataset_version_missing_raw_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_dataset_version("v0.1.0", tmp_path / "does-not-exist", tmp_path / "out")
