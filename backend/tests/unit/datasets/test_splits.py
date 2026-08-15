import pytest

from app.datasets.schema import EssayRecord, GenerationConfig
from app.datasets.splits import assign_splits

CFG = GenerationConfig(temperature=0.7, top_p=0.9, top_k=50, max_tokens=800, seed=1)


def human(eid, wc=300, source="src-a"):
    return EssayRecord(
        essay_id=eid,
        text=f"human {eid} " * wc,
        label="human",
        split="",
        source=source,
        license="CC-BY-4.0",
        collection_date="2026-01-01",
        topic="adversity",
        length_words=wc,
    )


def ai(eid, wc=300, model="gpt2-medium"):
    return EssayRecord(
        essay_id=eid,
        text=f"ai {eid} " * wc,
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


def polished(eid, original_id, wc=300):
    return EssayRecord(
        essay_id=eid,
        text=f"pol {eid} " * wc,
        label="ai_polished",
        split="",
        original_essay_id=original_id,
        model="gpt2-medium",
        model_revision="rev",
        polish_prompt="Polish this: {essay}",
        generation_config=CFG,
        generation_date="2026-01-01",
        topic="adversity",
        length_words=wc,
    )


def test_all_records_assigned_once():
    records = [human(f"h{i}") for i in range(10)] + [ai(f"a{i}") for i in range(10)]
    splits = assign_splits(records, seed=42)
    assert len(splits) == 20
    assert set(splits.values()) <= {"train", "val", "test"}


def test_rough_proportions():
    records = [human(f"h{i}") for i in range(100)]
    splits = assign_splits(records, seed=42)
    n = {k: sum(1 for v in splits.values() if v == k) for k in ("train", "val", "test")}
    assert n["train"] == pytest.approx(70, abs=4)
    assert n["val"] == pytest.approx(15, abs=4)
    assert n["test"] == pytest.approx(15, abs=4)


def test_deterministic_across_input_order():
    records = [human(f"h{i}", wc=100 + i) for i in range(30)]
    permuted = list(reversed(records))
    a = assign_splits(records, seed=7)
    b = assign_splits(permuted, seed=7)
    assert a == b


def test_different_seed_differs():
    records = [human(f"h{i}", wc=100 + i) for i in range(30)]
    a = assign_splits(records, seed=1)
    b = assign_splits(records, seed=2)
    assert a != b


def test_holdout_models_to_cross_model():
    records = [ai(f"a{i}", model="gpt2-medium") for i in range(5)] + [
        ai(f"l{i}", model="llama-3-8b") for i in range(5)
    ]
    splits = assign_splits(records, seed=1, holdout_models=("llama-3-8b",))
    for i in range(5):
        assert splits[f"l{i}"] == "test_cross_model"
    for i in range(5):
        assert splits[f"a{i}"] != "test_cross_model"


def test_polished_to_secondary_and_original_paired():
    records = [human("h1"), polished("p1", "h1")]
    splits = assign_splits(records, seed=1)
    assert splits["p1"] == "test_secondary"
    assert splits["h1"] == "test_secondary"  # leak group stays together


def test_human_records_never_cross_model():
    records = [human("h1"), ai("a1", model="llama-3-8b")]
    splits = assign_splits(records, seed=1, holdout_models=("llama-3-8b",))
    assert splits["a1"] == "test_cross_model"
    assert splits["h1"] in {"train", "val", "test"}
