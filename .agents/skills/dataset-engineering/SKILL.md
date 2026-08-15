# Skill: dataset-engineering

## Purpose
Dataset collection, provenance tracking, cleaning, metadata management, AI sample generation, train/validation/test splitting with leakage prevention, and versioning.

## When to Use
- Collecting new data sources
- Generating AI-written or AI-polished essays
- Creating/updating dataset splits
- Auditing for leakage
- Documenting dataset provenance

## Core Rules
1. **Provenance first**: No data without documented source, license, collection date
2. **AI metadata mandatory**: Model, prompt, config, date, preprocessing for every generated sample
3. **Human consent verified**: License or explicit consent for every human essay
4. **Document-level splits only**: Never split sentences from same essay across splits
5. **Leakage prevention**: Verify no duplicates, near-duplicates, shared prompts, or writer overlap across splits
6. **Version everything**: Dataset version, split version, generation config version

## Prohibited Behavior
- ❌ Using data without provenance documentation
- ❌ AI-generated data without full generation metadata
- ❌ Human data without consent/license verification
- ❌ Sentence-level train/test splits
- ❌ Skipping leakage checks
- ❌ Unversioned dataset releases

## Required Metadata Schema

### Human Essay
```yaml
source: str  # dataset name, URL, submission ID
license: str  # CC-BY, consent form ID, public domain
collection_date: ISO8601
preprocessing: List[str]  # normalization steps applied
writer_demographics: Dict  # optional, if consented
essay_id: str  # unique, stable
text: str
topic: str  # if available
length_words: int
```

### AI-Generated Essay
```yaml
model: str  # e.g., "gpt-2", "llama-3-8b-instruct"
model_revision: str  # commit hash or version
prompt_template: str  # exact template used
prompt_variables: Dict  # topic, length, style instructions
generation_config:
  temperature: float
  top_p: float
  top_k: int
  max_tokens: int
  seed: int
generation_date: ISO8601
preprocessing: List[str]
essay_id: str
text: str
```

### AI-Polished Human Essay
```yaml
original_essay_id: str  # reference to human essay
model: str
model_revision: str
polish_prompt: str
generation_config: Dict
generation_date: ISO8601
preprocessing: List[str]
essay_id: str
text: str
```

## Splitting Strategy
- Stratify by: source, length bucket (short/medium/long), topic cluster
- Target ratios: 70/15/15 or 80/10/10 train/val/test
- Random seed recorded and fixed per dataset version
- Split version = dataset_version + "_split_" + seed

## Leakage Checks
1. Exact duplicate detection (hash)
2. Near-duplicate (MinHash Jaccard > 0.8)
3. Shared prompt/template across splits (for AI data)
4. Writer ID overlap (if metadata available)
5. Embedding similarity (cosine > 0.95) across splits

## Relevant Project Files
- `backend/data/` - dataset scripts and metadata
- `docs/DATASET.md` - source registry and methodology
- `docs/EXPERIMENTS.md` - dataset version references