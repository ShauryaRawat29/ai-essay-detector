# Skill: api-contracts

## Purpose
Defining and maintaining API contracts between frontend and backend: request/response schemas, error formats, versioning, and compatibility rules.

## When to Use
- Designing new API endpoints
- Modifying existing schemas
- Versioning API changes
- Validating frontend/backend integration
- Documenting contracts for consumers

## Core Rules
1. **Contracts are explicit**: Pydantic schemas for every request/response
2. **Versioned**: API version in URL (`/api/v1/`) and response headers
3. **Backward compatible within major version**: No breaking changes without major version bump
4. **Evidence-first responses**: Never return verdict-only; always include sentence-level evidence
5. **Error format standardized**: Consistent error schema across all endpoints
6. **Rate limits documented**: In headers and docs

## Prohibited Behavior
- ❌ Changing schemas without version bump
- ❌ Returning "AI: true/false" or "probability: 0.87" without evidence
- ❌ Inconsistent error formats
- ❌ Undocumented endpoints
- ❌ Breaking changes in patch/minor versions

## Core Contract: `/api/v1/analyze`

### Request
```json
{
  "text": "string (required, 1-10000 chars, UTF-8)",
  "options": {
    "passage_window": "integer (default: 3, 1-10)",
    "include_features": "boolean (default: false)"
  }
}
```

### Response (Success)
```json
{
  "analysis_id": "uuid",
  "timestamp": "ISO8601",
  "feature_version": "string",
  "model_version": "string",
  "sentences": [
    {
      "index": 0,
      "text": "string",
      "signals": {
        "perplexity": {"value": 42.3, "baseline_mean": 120.5, "baseline_std": 35.2, "evidence": "low"},
        "token_entropy": {"value": 2.1, "baseline_mean": 3.8, "baseline_std": 0.9, "evidence": "low"},
        "sentence_length_cv": {"value": 0.15, "baseline_mean": 0.35, "baseline_std": 0.12, "evidence": "high"}
      },
      "evidence_strength": "medium",
      "evidence_summary": "Low perplexity and entropy suggest predictable token choices; regular sentence length"
    }
  ],
  "passages": [
    {
      "sentence_indices": [0, 1, 2],
      "aggregated_signals": {...},
      "evidence_summary": "..."
    }
  ],
  "limitations": [
    "Short essay (180 words) — limited statistical power",
    "Detector trained on GPT-2/Llama-3; may not generalize to all models"
  ]
}
```

### Response (Error)
```json
{
  "error": {
    "code": "VALIDATION_ERROR|RATE_LIMITED|INTERNAL_ERROR|MODEL_UNAVAILABLE",
    "message": "Human-readable description",
    "details": {}  // optional, e.g., field errors
  }
}
```

### Headers
- `X-API-Version`: "1.0"
- `X-RateLimit-Limit`: "60"
- `X-RateLimit-Remaining`: "59"
- `X-RateLimit-Reset`: "unix timestamp"

## Relevant Project Files
- `backend/app/schemas.py` - Pydantic models
- `backend/app/api/routes.py` - FastAPI routes
- `docs/ARCHITECTURE.md` - API contract section
- `frontend/src/lib/api.ts` - TypeScript client types