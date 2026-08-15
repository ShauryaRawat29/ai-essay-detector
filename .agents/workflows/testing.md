# Workflow: Testing

## Trigger
- Pre-merge (CI)
- Pre-release
- Post-model-update
- Post-dataset-update
- Regression investigation

## Process

### Quality Gate Chain (mandatory, no skips)
Quality Skill → Implementation → Tests → Static checks → Review → Documentation

### 0. Mandatory Skills
- Load `software-engineering-quality` and `test-driven-development`
- Tests must be written first and observed to fail (TDD); testing workflow
  validates that discipline in addition to running suites

### 1. Unit Tests (Per Component)
Run all unit test suites:
- `backend/app/features/` — feature extractors
- `backend/app/models/` — model loading, inference
- `backend/app/pipeline/` — orchestration
- `backend/app/api/` — validators, formatters
- `frontend/src/components/` — React components
- `frontend/src/lib/` — utilities, API client

### 2. Integration Tests
- Full pipeline: essay → features → model → evidence
- API contracts: request/response schemas
- Frontend-backend: mocked E2E flow
- Model loading: versioned artifacts

### 3. ML Pipeline Tests
- Feature determinism: same input → identical features (3 runs)
- Model loading: correct version, metadata
- Inference consistency: same input → same scores (±tolerance)
- Calibration verification: reliability matches training

### 4. Regression Tests
- Golden inputs → golden outputs (features, scores, evidence)
- Model version regression: new version passes baseline
- Dataset version regression: same split → same metrics

### 5. Edge Case Tests
- Empty string, whitespace
- Very short (< 50 chars), very long (> 10k)
- Non-English, mixed language
- Adversarial: prompt injection, unicode tricks, repetition
- Malformed: invalid UTF-8, null bytes

### 6. Frontend Specific
- Accessibility: axe-core automated + manual
- Visual regression: sentence highlight pixel accuracy
- Responsive: 375px, 768px, 1440px viewports
- Evidence tooltip: correct feature values displayed

### 7. Report
- Aggregate results
- Failures block merge/release
- Flaky tests: investigate or quarantine
- Coverage report (target: >80% unit, >60% integration)

## Agents Involved
- **QA Engineer** (lead): Owns test infrastructure, runs suites
- **All Engineers**: Provide testable code, fix failures
- **Red Team Reviewer**: Contributes adversarial cases

## Gates
- **No merge without passing unit + integration**
- **No merge without quality gate: TDD discipline verified, lint clean, type check clean, docs updated**
- **No release without full suite + regression**
- **No model deploy without ML pipeline tests**
- **No frontend deploy without accessibility pass**

## Prohibited
- ❌ Skipping tests for speed
- ❌ Flaky tests unaddressed
- ❌ No regression tests for model updates
- ❌ Testing only happy paths
- ❌ Using production data in tests