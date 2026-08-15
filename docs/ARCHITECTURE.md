# ARCHITECTURE.md

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │     │    Backend       │     │  ML/NLP Stack   │
│  (Next.js)      │────▶│   (FastAPI)      │────▶│  (Python)       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │ Detection Pipeline│
                     │  (Orchestration)  │
                     └──────────────────┘
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
        ┌────────────┐ ┌────────────┐ ┌────────────┐
        │ Sentence   │ │ Feature    │ │  Model     │
        │ Splitter   │ │ Extraction │ │ Inference  │
        └────────────┘ └────────────┘ └────────────┘
                             │               │
                      ┌──────┴──────┐  ┌──────┴──────┐
                      ▼             ▼  ▼             ▼
               ┌───────────┐ ┌──────────┐ ┌──────────┐
               │ Stylometric│ │ LM Signals│ │Classifier│
               │ Features   │ │(GPT-2 Med)│ │(XGBoost/ │
               │            │ │           │ │LogReg)   │
               └───────────┘ └──────────┘ └──────────┘
                             │               │
                      ┌──────┴───────────────┴──────┐
                      ▼                             ▼
               ┌─────────────────┐         ┌─────────────────┐
               │ Evidence        │         │ Label Scheme    │
               │ Generation      │         │ (Binary primary │
               │ (Templates)     │         │ + polished      │
               └─────────────────┘         │ secondary)      │
                                           └─────────────────┘
```

## Data Flow

1. **Input**: User pastes essay text (UTF-8, max 10k chars)
2. **Validation**: Length, encoding, content-type checks
3. **Sentence Splitting**: spaCy sentence segmentation
4. **Feature Extraction** (parallel):
   - Stylometric features per sentence + passage aggregates
   - LM signals per sentence + passage aggregates (GPT-2 Medium, local causal LM)
5. **Model Inference**: Classifier produces per-sentence calibrated scores
6. **Label Resolution**: Binary primary (HUMAN / AI-GENERATED); AI-polished = secondary evaluation set
7. **Evidence Generation**: Scores + features → z-scores vs human baselines → feature contributions → template descriptions → evidence strength categories
8. **Response**: Structured JSON with sentences, passages, limitations, feature_version, model_version

## Frontend/Backend Boundary

**API Contract**: `/api/v1/analyze` (see `api-contracts` skill)

**Backend Responsibilities**:
- Input validation, rate limiting (60 req/min/IP in-memory, dev-only)
- Pipeline orchestration
- Model serving (versioned)
- Evidence formatting

**Frontend Responsibilities**:
- Essay input UI
- Evidence visualization (highlighting, tooltips, panels)
- Uncertainty/limitations display (prominent)
- Accessibility (WCAG AA)

## Detection Pipeline Stages

| Stage | Input | Output | Versioned |
|-------|-------|--------|-----------|
| Split | Raw text | Sentence list | No (deterministic) |
| Stylometric Features | Sentences | Feature matrix | Yes (feature_version) |
| LM Signals | Sentences | Signal matrix | Yes (feature_version + model_version) |
| Classifier | Combined features | Per-sentence calibrated scores | Yes (model_version) |
| Label Resolution | Document label | Binary primary / polished secondary | No (data-defined) |
| Evidence Gen | Scores + features + baselines | Evidence descriptions | Yes (feature_version + model_version) |

## Resolved Decisions (ADR-001 through ADR-009)

| ADR | Title | Status | Summary |
|-----|-------|--------|---------|
| ADR-001 | Local LM Instrument Selection | **Accepted (Provisional)** | GPT-2 Medium (355M) as experimental instrument; EXP-001 validates |
| ADR-002 | Classifier Algorithm | **Accepted** | LogReg baseline + XGBoost primary (calibrated); <3% gain → LogReg |
| ADR-003 | Passage Definition | **Accepted** | Fixed window k=3 stride=1 + paragraph fallback; semantic deferred |
| ADR-004 | Baseline Computation | **Accepted** | Training-human only, length-bucketed, versioned with features |
| ADR-005 | Calibration Method | **Accepted (Provisional)** | Platt primary; Isotonic if N≥1000 & non-sigmoid reliability |
| ADR-006 | API Rate Limiting | **Accepted (Provisional/Dev)** | In-memory 60 req/min/IP; Redis for prod |
| ADR-007 | Frontend State Management | **Accepted** | Zustand for client state; Context for static globals |
| ADR-008 | Detection Label Definition | **Accepted** | Binary primary (HUMAN/AI); polished = secondary test set; sentence scores = weak supervision evidence |
| ADR-009 | Evidence Generation | **Accepted** | Template-based from features + contributions; no LLM explanations; no false precision |

## Versioning Strategy

- **Dataset**: `vX.Y.Z` (major=source change, minor=split change, patch=metadata)
- **Features**: `fX.Y.Z` (major=breaking, minor=new family, patch=bugfix)
- **Model**: `mX.Y.Z` (major=architecture, minor=retrain, patch=calibration)
- **API**: `/api/vN/` (major only for breaking changes)
- **Baselines**: `baselines_f{feature_version}.json`

## Implementation Status

Status of what actually exists in the codebase, updated per implementation phase.
"IMPLEMENTED" means working code + tests; "PLANNED"/"NOT VALIDATED" means not built or not evaluated.

| Component | Status | Notes |
|-----------|--------|-------|
| `GET /api/v1/health` | **IMPLEMENTED** (Phase 1) | Reports API/app/python version, feature version (null until features exist), model status, CUDA + GPU name. Never triggers a model load. |
| Model registry service | **IMPLEMENTED** (Phase 1) | `backend/app/models/loader.py` — versioned spec registration + load-state tracking. GPT-2 Medium registered as `lm_instrument` (spec only, `not_loaded`). Actual loading is a later phase. |
| Device detection | **IMPLEMENTED** (Phase 1) | `backend/app/models/device.py` — cached CUDA detection (`cuda:0` on this dev machine). |
| Rate limiting | **IMPLEMENTED** (Phase 1, dev-only) | In-memory sliding window, 60 req/min/IP (ADR-006). Implemented in-house (`backend/app/api/rate_limit.py`) rather than `fastapi-throttle`; ADR-006's architecture (in-memory sliding window, dev-only, Redis for prod) is unchanged. |
| CORS | **IMPLEMENTED** (Phase 1) | Dev defaults to `localhost:3000` origins; overridable via `ALLOWED_ORIGINS`. |
| Frontend proxy | **IMPLEMENTED** (Phase 1) | `next.config.ts` rewrites `/api/*` → backend (same-origin, no CORS friction). |
| `POST /api/v1/analyze` | **PLANNED** | Phase 9. |
| Sentence splitting + feature extraction | **IMPLEMENTED** (Phase 2) | `backend/app/features/` — deterministic spaCy sentence splitter, stylometric + syntax extractors, passage windows (window=3, stride=1, `\n\n` paragraph fallback, ADR-003), passage aggregates + MATTR/MTLD. Versioned `f0.2.0` (registry catalog). 44 new unit tests with golden outputs. Not yet served over the API. |
| LM signals (perplexity, entropy, log-prob, rank) | **IMPLEMENTED** (Phase 3) | `backend/app/models/lm_instrument.py` (gpt2-medium @ pinned revision `6dcaa7a`, CUDA; full-context causal scoring; 1024-token cap with `LongDocumentError`; never a classifier) + `backend/app/features/lm_signals.py` (8 sentence-level LM features, document-level extractor). Registry `f0.3.0`; 13 new unit tests with golden pins. |
| Baseline computation machinery | **IMPLEMENTED** (Phase 4, machinery only) | `backend/app/evaluation/baselines.py` — ADR-004 pipeline: length buckets (<200/200-500/500-800/>800), min-N=30 with adjacent-bucket merge fallback, mean/std/p5-p95 per feature, `baselines_{feature_version}.json` artifact with schema/feature/dataset versioning + save/load. 13 unit tests on synthetic data. **No real baselines computed yet** — requires the human training split (dataset v0.1.0). Level-of-measurement (sentence-level, min-N=sentences) is provisional pending Architect review. |
| Classifier, evidence generation | **PLANNED** | Phases 6–8. |
| Dataset machinery + source research | **IMPLEMENTED** (Phase 5, machinery + research only) | `backend/app/datasets/` — `schema.py` (EssayRecord + GenerationConfig, label-specific provenance validation), `preprocess.py` (NFC, newline/paragraph preservation, hspace collapse, steps recorded), `dedup.py` (SHA-256 exact dedup), `splits.py` (document-level; train/val/test stratified by (source, length bucket); `test_cross_model` holdout families; `ai_polished` + paired originals → `test_secondary`), `builder.py` (records.jsonl + manifest.json). Source licensing research recorded in `docs/DATASET.md`. **No data collected yet** (target v0.1.0 pending collection). |
| AI essay generation pipeline | **IMPLEMENTED** (Phase 5, machinery only) | `backend/app/datasets/generator.py` — local causal-LM essay generation with exact provenance (model, pinned revision, prompt template + variables, generation config incl. seed, date). Config table standard/creative/focused/adversarial (DATASET.md), `adversarial` adds "write like human" prompt variant; seeded deterministic sampling via transformers `GenerationConfig.seed`; length guards (50–700 words) keep drafts scorable by the 1024-token LM instrument; `GenerationQualityError` on guard failure. 15 unit tests (prompt building, provenance, guards, determinism via monkeypatched `_generate_text`). **No essays generated yet** — real generation is a batch job. |
| Quality gate (ruff + mypy) | **IMPLEMENTED** (Phase 5) | ruff 0.16.3 (`ruff check app tests`) and mypy 2.3.1 (`mypy app`) configured in `backend/pyproject.toml` dev extras; both green. `ruff format` enforcement is a TODO. |
| Dataset, experiments, evaluation, failure cases | **PARTIAL** | `docs/DATASET.md` has source registry + research; actual dataset v0.1.0, `EXPERIMENTS.md`, `EVALUATION.md`, `FAILURE-CASES.md` remain TODO until collection. |