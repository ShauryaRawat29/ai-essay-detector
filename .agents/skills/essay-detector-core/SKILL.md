# Skill: essay-detector-core

## Purpose
Core detection pipeline orchestration: essay ingestion → sentence splitting → feature extraction → model inference → evidence generation → structured output.

## When to Use
- Implementing the main detection pipeline
- Adding new feature extractors to the pipeline
- Modifying inference orchestration
- Defining the core data structures

## Core Rules
1. **Pipeline stages are explicit and testable**: Each stage (split, extract, score, evidence) is a separate function/class with defined input/output
2. **No LLM verdicts**: The pipeline never sends text to an LLM for classification
3. **Sentence-level evidence is mandatory**: Every output includes per-sentence scores and feature values
4. **Feature version pinning**: Pipeline records feature extractor versions used
5. **Model version pinning**: Pipeline records model version used
6. **Deterministic execution**: Same input + same versions = same output

## Prohibited Behavior
- ❌ Calling external LLM APIs for classification
- ❌ Returning only overall score without sentence breakdown
- ❌ Skipping feature extraction for "speed"
- ❌ Using unversioned models or features
- ❌ Inventing evidence not backed by feature values

## Expected Outputs
```python
# Core data structures
class SentenceEvidence:
    index: int
    text: str
    scores: Dict[str, float]  # per-signal scores
    features: Dict[str, float]  # raw feature values
    evidence_strength: str  # "low" | "medium" | "high" | "uncertain"

class PassageEvidence:
    sentence_indices: List[int]
    aggregated_scores: Dict[str, float]
    aggregated_features: Dict[str, float]

class DetectionResult:
    essay_id: str
    sentences: List[SentenceEvidence]
    passages: List[PassageEvidence]
    feature_version: str
    model_version: str
    timestamp: str
    limitations: List[str]
```

## Relevant Project Files
- `backend/app/pipeline/` - pipeline implementation
- `backend/app/schemas.py` - Pydantic schemas matching above
- `backend/app/features/` - feature extractor registry
- `backend/app/models/` - model loading and inference
- `docs/ARCHITECTURE.md` - pipeline design
- `docs/METHODOLOGY.md` - detection methodology