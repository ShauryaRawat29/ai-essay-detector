# Backend/ML-Specific Rules

## Software Engineering Quality (Mandatory)

All backend, ML, and data-pipeline work MUST follow the
`software-engineering-quality` skill and the quality gate in
`docs/QUALITY-STANDARDS.md`, and MUST follow `test-driven-development` (tests
written and observed to fail first). See `../AGENTS.md`. Run the actual
test/lint/typecheck commands before claiming a check passed.

## Technology Stack
- Python 3.11+
- FastAPI
- Pydantic v2
- spaCy, textstat, transformers, torch
- scikit-learn, XGBoost
- SQLite (initial)
- pytest

## Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # /api/v1/analyze endpoint
│   │   └── dependencies.py     # Rate limiting, auth (future)
│   ├── schemas.py              # Pydantic request/response models
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestration.py    # DetectionPipeline class
│   │   └── evidence.py         # Evidence generation
│   ├── features/
│   │   ├── __init__.py
│   │   ├── registry.py         # FeatureExtractorRegistry
│   │   ├── stylometric.py      # StylometricFeatureExtractor
│   │   └── lm_signals.py       # LMSignalExtractor
│   ├── models/
│   │   ├── __init__.py
│   │   ├── loader.py           # ModelLoader (versioned)
│   │   ├── classifier.py       # Classifier wrapper
│   │   └── lm_instrument.py    # Local LM wrapper
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics.py          # Precision, recall, F1, calibration
│   │   ├── bias_audit.py       # Bias evaluation
│   │   └── failure_analysis.py # Failure case analysis
│   └── experiments/
│       ├── __init__.py
│       └── run_experiment.py   # Experiment runner
├── data/                       # Dataset scripts (not committed)
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── ml_pipeline/
│   └── fixtures/
├── models/                     # Model artifacts (not committed)
├── requirements.txt
├── pyproject.toml
├── .env.example
└── .gitignore
```

## Non-Negotiable Backend Principles

### 1. No Opaque LLM Judgement
- The backend NEVER sends essay to external LLM for classification
- Local LM used ONLY for measurable signals (logprobs, perplexity, entropy)
- Classifier is our own scikit-learn/XGBoost model

### 2. Evidence-First API
- Response MUST include sentence-level evidence
- Response MUST include feature values and baselines
- Response MUST include limitations array
- NEVER return "probability", "confidence", "is_ai" verdict

### 3. Deterministic Inference
- Same input + same model/feature versions = same output
- No randomness in inference path
- Temperature=0 for LM instrument (if applicable)

### 4. Version Pinning
- Every response includes `feature_version` and `model_version`
- Model artifacts loaded by explicit version
- Feature extractors registered with versions

## API Requirements

### Input Validation
- Max text length: 10,000 characters
- UTF-8 encoding required
- Content-Type: application/json
- Reject empty/whitespace-only

### Rate Limiting
- 60 requests/minute per IP (configurable)
- Return 429 with `Retry-After` header
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### Error Handling
- Standard error format (see `api-contracts` skill)
- No stack traces in responses
- Structured logging for debugging

### Security
- No secrets in code (use `.env`, loaded via `python-dotenv`)
- `.env` in `.gitignore`
- Input sanitization (length, encoding)
- No user data persisted without consent

## ML Pipeline Rules

### Feature Extraction
- All extractors inherit base class with `extract(sentences) -> FeatureMatrix`
- Deterministic: fixed tokenization, no random seeds
- Versioned: `FeatureExtractorRegistry.get_version()`
- Tested: unit tests with golden outputs

### Model Training
- Document-level splits only (enforced by Dataset Engineer)
- Cross-validation with GroupKFold (groups = essay IDs)
- Calibration on held-out validation set
- Artifacts: `model.pkl`, `config.json`, `metadata.json`

### Model Serving
- `ModelLoader.load(version)` - explicit version
- Warm-up on startup
- Health check endpoint includes model version
- Graceful degradation if model unavailable

### Evaluation (Mandatory Per Release)
- Precision, Recall, F1 per class + macro
- Confusion matrix
- Calibration: Brier score, reliability diagram
- Cross-model: test on unseen model families
- Bias audit: 5+ subgroups
- Failure analysis: 3+ confident failures

## Testing

### Unit Tests (pytest)
- `tests/unit/features/` - feature extractors with golden outputs
- `tests/unit/models/` - model loading, prediction consistency
- `tests/unit/pipeline/` - orchestration, evidence generation
- `tests/unit/api/` - validators, formatters, rate limiter

### Integration Tests
- `tests/integration/test_pipeline.py` - full essay → evidence
- `tests/integration/test_api.py` - request/response contracts

### ML Pipeline Tests
- `tests/ml_pipeline/test_determinism.py` - 3 runs identical
- `tests/ml_pipeline/test_model_loading.py` - versioned artifacts
- `tests/ml_pipeline/test_calibration.py` - reliability check

### Regression Tests
- `tests/regression/golden_inputs.json` - fixed inputs
- `tests/regression/golden_outputs.json` - expected outputs
- Run on every model/feature version bump

## Environment Variables
```
# .env (not committed)
API_HOST=0.0.0.0
API_PORT=8000
MODEL_VERSION=1.0.0
FEATURE_VERSION=1.0.0
RATE_LIMIT_PER_MINUTE=60
LM_MODEL_PATH=/path/to/local/model
DATABASE_URL=sqlite:///./app.db
```

## Git Ignore (Backend)
- `.venv/`
- `__pycache__/`
- `*.pyc`
- `.env`
- `models/` (model artifacts)
- `data/raw/`, `data/processed/` (large datasets)
- `*.log`
- `.pytest_cache/`
- `.coverage`
- `*.sqlite`
- `*.bin`, `*.safetensors` (model weights)