import pytest

from app.datasets import generator
from app.datasets.generator import (
    MAX_GENERATED_WORDS,
    MIN_GENERATED_WORDS,
    GenerationQualityError,
    build_prompt,
    config_for,
    generate_ai_record,
)
from app.datasets.schema import EssayRecord, GenerationConfig


@pytest.fixture
def fake_generate(monkeypatch):
    captured = {}

    def fake(model_name, revision, prompt, cfg):
        captured["config"] = cfg
        captured["prompt"] = prompt
        return (
            "The quiet student reviewed the essay once more. She checked every detail "
            "carefully before submitting her application to the university. The story "
            "began in a small town where curiosity led to discovery. Her teachers "
            "always said that patience and practice mattered more than talent alone. "
            "Over the years she learned to embrace mistakes as opportunities to grow. "
            "The final draft reflected all the lessons she had gathered along the way."
        )

    monkeypatch.setattr(generator, "_generate_text", fake)
    return captured


def test_config_for_seeded_standard():
    cfg = config_for("standard", seed=7)
    assert cfg == GenerationConfig(temperature=0.7, top_p=0.9, top_k=50, max_tokens=800, seed=7)


def test_config_for_adversarial_matches_standard_params():
    std = config_for("standard", seed=1)
    adv = config_for("adversarial", seed=1)
    assert adv.temperature == std.temperature
    assert adv.top_p == std.top_p
    assert adv.top_k == std.top_k
    assert adv.max_tokens == std.max_tokens


@pytest.mark.parametrize("name", ["creative", "focused"])
def test_config_for_other_variants(name):
    cfg = config_for(name, seed=3)
    assert cfg.seed == 3
    assert 0 < cfg.temperature <= 2.0
    assert cfg.max_tokens > 0


def test_unknown_config_raises():
    with pytest.raises(ValueError):
        config_for("nope", seed=1)


def test_build_prompt_substitutes_variables():
    prompt = build_prompt("curiosity", word_count=600)
    assert "curiosity" in prompt
    assert "600" in prompt


def test_build_prompt_adversarial_adds_human_instruction():
    prompt = build_prompt("curiosity", word_count=600, variant="adversarial")
    assert "human" in prompt.lower()
    assert "natural" in prompt.lower()


def test_generate_ai_record_provenance(fake_generate):
    record = generate_ai_record(
        essay_id="gen-0001",
        topic="overcoming adversity",
        config_name="standard",
        seed=11,
        model_name="gpt2-medium",
        revision="abc123",
    )
    assert isinstance(record, EssayRecord)
    assert record.label == "ai_generated"
    assert record.model == "gpt2-medium"
    assert record.model_revision == "abc123"
    assert record.prompt_template is not None
    assert record.prompt_variables == {"topic": "overcoming adversity", "word_count": 600}
    assert record.generation_config.seed == 11
    assert record.generation_config.temperature == 0.7
    assert record.generation_date
    assert record.split == ""
    assert record.length_words > 0


def test_generate_ai_record_uses_adversarial_prompt(fake_generate):
    generate_ai_record("g1", "topic", config_name="adversarial", seed=1)
    assert "human" in fake_generate["prompt"].lower()


def test_generate_ai_record_passes_seeded_config_to_model(fake_generate):
    generate_ai_record("g1", "topic", config_name="creative", seed=42)
    assert fake_generate["config"].seed == 42
    assert fake_generate["config"].temperature == 0.9


def test_short_output_rejected(monkeypatch):
    monkeypatch.setattr(generator, "_generate_text", lambda *a, **k: "Hi.")
    with pytest.raises(GenerationQualityError):
        generate_ai_record("g1", "topic", config_name="standard", seed=1)


def test_runaway_output_rejected(monkeypatch):
    long_text = ("word " * (MAX_GENERATED_WORDS + 100)).strip()
    monkeypatch.setattr(generator, "_generate_text", lambda *a, **k: long_text)
    with pytest.raises(GenerationQualityError):
        generate_ai_record("g1", "topic", config_name="standard", seed=1)


def test_empty_output_rejected(monkeypatch):
    monkeypatch.setattr(generator, "_generate_text", lambda *a, **k: "   ")
    with pytest.raises(GenerationQualityError):
        generate_ai_record("g1", "topic", config_name="standard", seed=1)


def test_same_seed_deterministic(fake_generate):
    a = generate_ai_record("g1", "topic", config_name="standard", seed=5)
    b = generate_ai_record("g2", "topic", config_name="standard", seed=5)
    assert a.text == b.text
    assert a.generation_config.seed == b.generation_config.seed


def test_min_and_max_guards_exist():
    assert MIN_GENERATED_WORDS >= 50
    assert MAX_GENERATED_WORDS <= 700
