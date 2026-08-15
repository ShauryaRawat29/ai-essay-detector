# ARCHITECTURE.md

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │     │    Backend       │     │  ML/NLP Stack   │
│  (Next.js 16)   │────▶│   (FastAPI)      │────▶│  (Python)       │
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
         │ Sentence   │ │ Feature    │ │  LM        │
         │ Splitter   │ │ Extraction │ │ Instrument │
         └────────────┘ └────────────┘ └────────────┘
                              │               │
                       ┌──────┴──────┐  ┌──────┴──────┐
                       ▼             ▼  ▼             ▼
                ┌───────────┐ ┌──────────┐ ┌──────────┐
                │ Stylometric│ │ Syntax   │ │ LM Signals│
                │ Features   │ │ Features │ │(GPT-2 Med)│
                └───────────┘ └──────────┘ └──────────┘
                              │               │
                       ┌──────┴───────────────┴──────┐
                       ▼                             ▼
                ┌─────────────────┐         ┌─────────────────┐
                │ Baselines       │         │ Evidence        │
                │ (ADR-004)       │         │ Scoring         │
                └─────────────────┘         └─────────────────┘
                       │                             │
                       ▼                             ▼
                ┌──────────────────────────────────────────────┐
                │ AnalysisResult: sentences, passages,         │
                │ limitations, feature_version, model_version  │
                └──────────────────────────────────────────────┘
```

## Data Flow

1. **Input**: User pastes essay text (UTF-8, max 10k chars) via frontend
2. **Validation**: Length, encoding, content-type checks; 60 req/min/IP rate limit
3. **Sentence Splitting**: spaCy deterministic sentence segmentation (`SentenceSplitter`)
4. **Feature Extraction** (parallel, deterministic, versioned `f0.3.0`):
   - **Stylometric**: TTR, word length, sentence length, MATTR, MTLD, n-gram repetition, lexical recurrence, readability (Flesch, FK, ARI, Coleman-Liau, Gunning Fog), rhythm (punctuation density, sentence length stats, clause density)
   - **Syntax**: POS entropy, dependency depth, clause density, 17 universal POS tag frequencies
   - **LM Signals** (GPT-2 Medium, full-context causal pass): perplexity, token entropy mean/std, log-prob mean/std, rank mean/std, probability curvature (8 features per sentence)
   - **Passage aggregates**: Overlapping windows (k=3, stride=1, paragraph fallback), aggregates of sentence features + MATTR/MTLD/ngram-rep
5. **Baseline Lookup**: Essay length → bucket (short/standard/long/xlong); per-feature human baseline statistics (mean, std, p5-p95) from train split only
6. **Evidence Scoring**: Per-sentence & per-passage z-score vs baseline; evidence strength (high/medium/low/uncertain) from z-score magnitude
7. **Response**: `AnalysisResult` JSON with sentence/passage evidence, summary counts, limitations — never a probability or verdict

## Frontend/Backend Boundary

**API Contract**: `POST /api/v1/analyze` → `AnalysisResult` (see `api-contracts` skill)

### Backend Responsibilities
- Input validation, rate limiting (in-memory sliding window, 60 req/min/IP)
- Pipeline orchestration (`DetectionPipeline` with shared LM instrument)
- Model serving (lazy load, versioned)
- Evidence formatting (honest language, no verdicts)

### Frontend Responsibilities
- Essay input UI (textarea, word/char count, max 10k chars)
- Evidence visualization (sentence highlighting, expandable signal tables)
- Uncertainty/limitations display (prominent)
- Accessibility (WCAG AA: semantic HTML, focus visible, keyboard nav, color contrast ≥4.5:1)

## Detection Pipeline Stages

| Stage | Input | Output | Versioned |
|-------|-------|--------|-----------|
| Split | Raw text | Sentence list + spans | No (deterministic) |
| Stylometric Features | Sentences | Feature matrix | Yes (feature_version `f0.3.0`) |
| Syntax Features | Sentences | Feature matrix | Yes (feature_version) |
| LM Signals | Sentences + full text | Signal matrix | Yes (feature_version + model_version) |
| Passage Aggregation | Sentence features + windows | Passage feature matrix | Yes (feature_version) |
| Baseline Lookup | Essay word count | Bucket name + per-feature stats | Yes (baselines_version `1.0`) |
| Evidence Scoring | Features + baselines | Per-sentence/passage signals | Yes (feature_version + baselines_version) |

## Resolved Decisions (ADR-001 through ADR-009)

| ADR | Title | Status | Summary |
|-----|-------|--------|---------|
| ADR-001 | Local LM Instrument Selection | **Accepted** | GPT-2 Medium (355M) as measurement instrument; pinned rev `6dcaa7a`; EXP-001 validated |
| ADR-002 | Classifier Algorithm | **Accepted** | Evidence pipeline (no classifier yet); baselines + z-scores as signal detector |
| ADR-003 | Passage Definition | **Accepted** | Fixed window k=3 stride=1 + paragraph fallback; semantic deferred |
| ADR-004 | Baseline Computation | **Accepted** | Training-human only, length-bucketed, versioned with features |
| ADR-005 | Calibration Method | **Accepted (Provisional)** | Platt primary; Isotonic if N≥1000 & non-sigmoid reliability (future classifier) |
| ADR-006 | API Rate Limiting | **Accepted** | In-memory 60 req/min/IP; Redis for prod |
| ADR-007 | Frontend State Management | **Accepted** | React hooks for client state; no global store needed |
| ADR-008 | Detection Label Definition | **Accepted** | No labels in v0.1; evidence-only output (future: binary primary + polished secondary) |
| ADR-009 | Evidence Generation | **Accepted** | Template-based from features + baselines; no LLM explanations; no false precision |

## Versioning Strategy

- **Dataset**: `vX.Y.Z` (major=source change, minor=split change, patch=metadata) — **v0.1.0 deployed**
- **Features**: `fX.Y.Z` (major=breaking, minor=new family, patch=bugfix) — **f0.3.0 deployed**
- **Model**: `mX.Y.Z` (major=architecture, minor=retrain, patch=calibration) — **0.1.0 (evidence pipeline)**
- **API**: `/api/vN/` (major only for breaking changes) — **v1**
- **Baselines**: `baselines_f{feature_version}.json` — **baselines_f0.3.0.json**

## Implementation Status (ALL IMPLEMENTED ✅)

| Component | Status | Notes |
|-----------|--------|-------|
| `GET /api/v1/health` | **IMPLEMENTED** | Reports API/app/python version, feature version (`f0.3.0`), model status, CUDA + GPU name. Never triggers model load. |
| Model registry service | **IMPLEMENTED** | `backend/app/models/loader.py` — versioned spec registration + load-state tracking. GPT-2 Medium registered as `lm_instrument`. |
| Device detection | **IMPLEMENTED** | `backend/app/models/device.py` — cached CUDA detection (`cuda:0`). |
| Rate limiting | **IMPLEMENTED** | In-memory sliding window, 60 req/min/IP (ADR-006). |
| CORS | **IMPLEMENTED** | Dev defaults to `localhost:3000`; overridable via `ALLOWED_ORIGINS`. |
| Frontend proxy | **IMPLEMENTED** | `next.config.ts` rewrites `/api/*` → backend (same-origin, no CORS). |
| `POST /api/v1/analyze` | **IMPLEMENTED** | Evidence-shaped response (`AnalysisResult`); 422 on validation/context-window; 503 if baselines missing. |
| Sentence splitting + feature extraction | **IMPLEMENTED** | Deterministic spaCy splitter, stylometric + syntax extractors, passage windows (ADR-003), MATTR/MTLD. Registry `f0.3.0`. |
| LM signals (perplexity, entropy, log-prob, rank) | **IMPLEMENTED** | `LMInstrument` (gpt2-medium @ pinned rev, CUDA; full-context causal; 1024-token cap with `LongDocumentError`); `LMSignalExtractor` (8 sentence-level features). |
| Baseline computation | **IMPLEMENTED** | ADR-004 pipeline: length buckets, min-N=30 merge fallback, mean/std/p5-p95, `baselines_f0.3.0.json` with full provenance. |
| Evidence scoring pipeline | **IMPLEMENTED** | `score_essay` pure function (z-scores vs baselines) + `DetectionPipeline` orchestration; per-sentence/passage evidence strength (high/medium/low/uncertain). |
| Frontend evidence UI | **IMPLEMENTED** | Next.js 16, evidence-first: summary card, sentence highlights (neutral colors), expandable signal tables, limitations panel. |
| Dataset v0.1.0 | **IMPLEMENTED** | 6,039 human essays (VIORRA 128, LEAF 4,917, Ghostbuster-human 994), stratified doc-level splits (seed 42), SHA-256 dedup (0 removed). |
| AI generation pipeline | **IMPLEMENTED** | `generator.py` + `generate_batch.py` (checkpointed, resumable); configs standard/creative/focused/adversarial; provenance-complete records. |
| Quality gate (ruff + mypy) | **IMPLEMENTED** | ruff 0.16.3 + mypy 2.3.1; both green on 38 source files. |
| Tests | **IMPLEMENTED** | 200+ tests (unit + integration + pipeline); TDD throughout. |

## Key Files

```
backend/
├── app/
│   ├── api/routes.py              # /api/v1/health, /api/v1/analyze
│   ├── config.py                  # Settings, env-driven
│   ├── features/
│   │   ├── registry.py            # FeatureRegistry (f0.3.0), extract_essay()
│   │   ├── stylometric.py         # StylometricExtractor
│   │   ├── syntax.py              # SyntaxExtractor
│   │   ├── lm_signals.py          # LMSignalExtractor
│   │   ├── passages.py            # PassageExtractor, aggregates
│   │   └── splitter.py            # SentenceSplitter
│   ├── models/
│   │   ├── lm_instrument.py       # LMInstrument (gpt2-medium)
│   │   └── loader.py              # ModelRegistry
│   ├── evaluation/baselines.py    # BaselineArtifact, compute/load
│   ├── pipeline/
│   │   ├── evidence.py            # build_signal_evidence (z-score → evidence)
│   │   ├── analysis.py            # score_essay (pure scoring function)
│   │   └── orchestration.py       # DetectionPipeline (orchestrates all)
│   └── schemas.py                 # AnalyzeRequest, AnalysisResult, etc.
├── data/
│   ├── datasets/v0.1.0/           # records.jsonl, manifest.json
│   └── baselines/v0.1.0/          # baselines_f0.3.0.json, report.json
└── tests/                         # 200+ tests (unit/integration)

frontend/
├── src/app/page.tsx               # Evidence-first analyzer UI
├── src/lib/api.ts                 # analyzeEssay(), fetchHealth()
├── src/lib/types.ts               # TypeScript mirrors of API schemas
└── src/app/globals.css            # Tailwind v4 + evidence colors
```

## Running the Stack

```bash
# Terminal 1: Backend
cd backend
.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Open http://localhost:3000
```

## Test Commands

```bash
# Backend
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\ruff.exe check app tests
.\.venv\Scripts\mypy.exe app

# Frontend
cd frontend
npm run lint
npm run build
```