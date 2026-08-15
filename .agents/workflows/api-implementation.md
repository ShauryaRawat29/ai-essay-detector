# Workflow: API Implementation

## Trigger
- New endpoint needed (Architecture Review approved)
- Schema change required
- Backward-compatible enhancement
- Bug fix in API layer

## Process

### Quality Gate Chain (mandatory, no skips)
Quality Skill → Implementation → Tests → Static checks → Review → Documentation

### 1. Define Contract
- Load `api-contracts` skill
- Load `software-engineering-quality` and `test-driven-development` (mandatory — quality gate + TDD apply)
- Write/update Pydantic schemas in `backend/app/schemas.py`
- Define request/response/error examples
- Version in URL: `/api/v1/`

### 2. Implement
- FastAPI route with dependency injection
- Input validation (length, encoding, content-type)
- Rate limiting dependency
- Service layer call (orchestration)
- Structured error handling

### 3. Test
- Unit: validators, formatters, error mapping
- Integration: full request → response with test client
- Contract: schema validation on responses
- Edge cases: empty, oversized, malformed, rate limit
- Error format consistency

### 4. Document
- Update `docs/ARCHITECTURE.md` API section
- Update OpenAPI spec (auto-generated)
- Notify Frontend Engineer of changes

### 5. Version
- Patch: backward-compatible additions
- Minor: new endpoints, optional fields
- Major: breaking changes (requires Architecture Review)

## Agents Involved
- **Backend Engineer** (lead): Implements
- **Architect**: Reviews contract compliance
- **Frontend Engineer**: Coordinates integration
- **QA Engineer**: Validates contract tests

## Gates
- **No endpoint without Pydantic schemas**
- **No endpoint without passing the quality gate: TDD (tests fail first), lint, type check, self-review, docs**
- **No endpoint without input validation**
- **No endpoint without rate limiting**
- **No schema change without version bump**
- **All errors use standard error format**

## Prohibited
- ❌ Raw dict responses (must use Pydantic)
- ❌ Missing input validation
- ❌ Stack traces in error responses
- ❌ Breaking changes in patch/minor versions
- ❌ Undocumented endpoints