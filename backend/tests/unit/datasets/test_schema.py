import pytest

from app.datasets.schema import EssayRecord, GenerationConfig

VALID_CONFIG = GenerationConfig(temperature=0.7, top_p=0.9, top_k=50, max_tokens=800, seed=7)


def human(**overrides):
    params = dict(
        essay_id="h1",
        text="A human essay.",
        label="human",
        split="",
        source="test-source",
        license="CC-BY-4.0",
        collection_date="2026-01-01",
        topic="adversity",
        length_words=3,
    )
    params.update(overrides)
    return EssayRecord(**params)


def ai(**overrides):
    params = dict(
        essay_id="a1",
        text="An AI essay.",
        label="ai_generated",
        split="",
        model="gpt2-medium",
        model_revision="6dcaa7a952f72f9298047fd5137cd6e4f05f41da",
        prompt_template="Write on {topic}",
        prompt_variables={"topic": "curiosity"},
        generation_config=VALID_CONFIG,
        generation_date="2026-01-01",
        topic="curiosity",
        length_words=3,
    )
    params.update(overrides)
    return EssayRecord(**params)


def polished(**overrides):
    params = dict(
        essay_id="p1",
        text="A polished essay.",
        label="ai_polished",
        split="",
        original_essay_id="h1",
        model="gpt2-medium",
        model_revision="6dcaa7a952f72f9298047fd5137cd6e4f05f41da",
        polish_prompt="Polish this: {essay}",
        generation_config=VALID_CONFIG,
        generation_date="2026-01-01",
        topic="adversity",
        length_words=3,
    )
    params.update(overrides)
    return EssayRecord(**params)


def test_generation_config_valid_ranges():
    assert VALID_CONFIG.temperature == 0.7


@pytest.mark.parametrize(
    "kw",
    [
        dict(temperature=0.0),
        dict(temperature=3.0),
        dict(top_p=0.0),
        dict(top_p=1.5),
        dict(top_k=0),
        dict(max_tokens=0),
        dict(max_tokens=5000),
    ],
)
def test_generation_config_invalid_ranges_raise(kw):
    with pytest.raises(ValueError):
        GenerationConfig(
            temperature=kw.get("temperature", 0.7),
            top_p=kw.get("top_p", 0.9),
            top_k=kw.get("top_k", 50),
            max_tokens=kw.get("max_tokens", 800),
            seed=7,
        )


def test_human_requires_provenance():
    with pytest.raises(ValueError):
        human(source=None, license=None, collection_date=None)


def test_ai_requires_generation_provenance():
    with pytest.raises(ValueError):
        ai(model=None, generation_config=None)


def test_ai_requires_model_revision_and_prompt():
    with pytest.raises(ValueError):
        ai(model_revision=None)
    with pytest.raises(ValueError):
        ai(prompt_template=None)


def test_polished_requires_original_id():
    with pytest.raises(ValueError):
        polished(original_essay_id=None)


def test_invalid_label_raises():
    with pytest.raises(ValueError):
        human(label="robot")


def test_invalid_split_raises():
    with pytest.raises(ValueError):
        human(split="nowhere")


def test_invalid_preprocessing_steps_raises():
    with pytest.raises(ValueError):
        human(preprocessing=("nfc_normalize", "not-a-step"))


def test_empty_text_raises():
    with pytest.raises(ValueError):
        human(text="   ")


def test_roundtrip_to_dict():
    rec = ai()
    back = EssayRecord.from_dict(rec.to_dict())
    assert back == rec
    assert back.generation_config == VALID_CONFIG
