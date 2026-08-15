# QUALITY-STANDARDS.md — Software Engineering Quality Standards

**Status:** Adopted (2026-08-15)
**Enforcing skill:** `.agents/skills/software-engineering-quality/SKILL.md`
**Authoritative for:** all code, configuration, and ML/data pipeline work.

## Purpose

Define the minimum quality bar every change must meet before it is considered
complete, and name who is accountable for each aspect. Every agent that writes
code MUST satisfy this document and the `software-engineering-quality` skill
(mandatory) and `test-driven-development` (tests written first and observed to
fail).

## Mandatory Skills

| Skill | Applies to |
|-------|-----------|
| `software-engineering-quality` | All implementation work (this document's companion) |
| `test-driven-development` | All implementation work; tests first, observed to fail |

---

# Code Quality

- Single Responsibility Principle; separation of concerns; high cohesion, low coupling.
- DRY where duplication is the same responsibility; no premature abstraction.
- Small, focused, intention-revealing functions; simple over clever.
- Never introduce: dead code, unused imports/variables, magic numbers,
  hardcoded environment-specific paths, hardcoded secrets, commented-out
  abandoned code, unnecessary dependencies or abstractions, giant functions or
  giant unrelated files.
- Configuration centralized where appropriate (env/config module).
- Lint clean and format-consistent (commands below).

# Architecture

- Respect boundaries in `docs/ARCHITECTURE.md`; no silent changes (ADR +
  Architect review, AGENTS.md principle 10).
- Frontend: components hold no ML/business logic; API via defined contracts;
  reusable components have clear responsibilities.
- Backend: thin route handlers; logic in services; ML logic in ML/domain
  modules; schemas in defined contract modules; no duplicated feature
  calculations.
- ML: deterministic feature extraction; versioned feature definitions;
  training and inference use compatible feature schemas; isolated model
  loading; preprocessing must not leak test information.

# Type Safety

- TypeScript: avoid `any` unless justified; explicit interfaces/types;
  validate external data (don't trust API responses blindly); avoid unsafe
  type assertions.
- Python: type public interfaces; Pydantic for API boundaries; explicit
  return types where useful; avoid unnecessary `Any`; validate external input.

# Testing

- TDD Iron Law: no production code without a failing test first.
- Required where applicable: unit, integration, API, regression, ML-pipeline,
  and frontend tests.
- Every discovered bug that can recur gets a regression test.
- No tests merely to inflate coverage; tests must verify behavior.
- No flaky tests; no happy-path-only suites; no production data in tests.

# Security

- Never commit: API keys, passwords, tokens, private credentials, model
  credentials, personal data.
- Validate all external input; trust nothing: frontend input, uploaded text,
  API responses, dataset metadata, model output.
- Environment variables for secrets/configuration; rate limiting on inference
  endpoints; sanitize outputs (XSS); no user data persisted without consent.
- Review each change against AGENTS.md Security Rules.

# ML Reproducibility

- Never fabricate metrics, datasets, or experiment results.
- Never train on test data; no document variants across splits; never tune
  against the final test set.
- Never silently change feature definitions or model versions.
- Every experiment records: hypothesis, dataset, feature version, model
  version, configuration, metrics, conclusion.

# Dataset Quality

- Provenance first: source, license/consent, model/prompt/config/date for AI
  data, preprocessing for every sample.
- Document-level splits only; stratified; seeded; versioned.
- Leakage checks mandatory (exact dup, near-dup, shared prompts, writer
  overlap, embedding similarity).

# API Quality

- Thin FastAPI routes; Pydantic schemas at boundaries; typed contracts shared
  with frontend (`api-contracts` skill).
- Input validation (length, encoding, content-type); standard error format;
  no stack traces in responses.
- Versioned API (`/api/v1/`); rate limiting with 429 + `Retry-After`.

# Frontend Quality

- Strict TypeScript; evidence-first UI (no verdicts, no red/green).
- Components by defined contracts (`frontend/AGENTS.md`); feature values and
  baselines shown; uncertainty first-class.

# Accessibility

- WCAG AA minimum: semantic HTML, focus visible, keyboard navigation, screen
  reader announcements, contrast ≥ 4.5:1, reduced motion, high contrast mode.
- axe-core in CI; sentence-highlight accuracy verified.

# Documentation

- Document non-obvious decisions, architecture boundaries, public APIs,
  feature definitions, model assumptions, known limitations.
- Do not document obvious code line-by-line; documentation describes what the
  code ACTUALLY does.
- Use `TODO:`/`PLACEHOLDER:` for unfinished work; never fabricate results.

# AI-Assisted Development

AI-generated code is NOT automatically accepted. Every AI-generated change
must be:
1. Understood by the implementing agent.
2. Reviewed against architecture.
3. Tested.
4. Checked for unnecessary complexity.
5. Checked for duplicated logic.
6. Checked for security issues.
7. Documented where necessary.

Never blindly paste generated code. Never claim a check passed without running it.

# Release Quality Gate

A phase is complete ONLY when all steps pass. A phase is NOT complete simply
because the application starts.

```
Quality Skill
      ↓
Implementation
      ↓
Tests            run and green
      ↓
Static checks    type checking, linting, formatting
      ↓
Review           self-review + security review + agent review
      ↓
Documentation    docs/ updated, git diff inspected
      ↓
DONE
```

1. Run tests.
2. Run type checking.
3. Run linting.
4. Run formatting/checks.
5. Inspect the git diff.
6. Check for dead/unused code.
7. Check dependencies.
8. Check secrets.
9. Check architecture compliance.
10. Check documentation.
11. Report failures honestly.

## Commands (Run, Do Not Assume)

### Backend (from `backend/`)
| Check | Command | Status |
|-------|---------|--------|
| Tests | `.venv/Scripts/python -m pytest` | ✅ Installed (pytest 9.1.1); 153 tests green |
| Lint | `.venv/Scripts/ruff check app tests` | ✅ Installed (ruff 0.16.3); green (Phase 5 tooling) |
| Types | `.venv/Scripts/mypy app` | ✅ Installed (mypy 2.3.1); green (Phase 5 tooling) |
| Format | `ruff format --check app tests` | ⏳ `TODO:` format enforcement not yet enabled — only `ruff check` is in the gate |

### Frontend (from `frontend/`)
| Check | Command | Status |
|-------|---------|--------|
| Lint | `npm run lint` (eslint) | ✅ Installed; green in Phase 1 |
| Build + types | `npm run build` (Next.js runs TS type check) | ✅ Installed; green in Phase 1 |
| Tests | `npm test` | ⏳ `TODO:` no test runner configured yet — set up per `frontend/AGENTS.md` |

Until `TODO:` items land, the gate step they cover is **not** green and must be
called out explicitly rather than silently skipped.

## Roles and Responsibilities (Quality Ownership)

| Aspect | Owner | Supporting |
|--------|-------|------------|
| Architecture / ADRs | Architect | All agents propose |
| Feature correctness + determinism | NLP Engineer | QA Engineer |
| Model quality / evaluation | ML Engineer | QA, Red Team |
| API contracts / schemas | Backend Engineer | Architect |
| UI evidence correctness | Frontend Engineer | UI/UX Engineer |
| UX evidence clarity (no verdicts) | UI/UX Engineer | Red Team |
| Test strategy + suite health | QA Engineer | All engineers |
| Adversarial/bias/failure audit | Red Team Reviewer | QA Engineer |
| Dataset provenance + leakage | Dataset Engineer | Red Team |
| Research integrity | Research | Red Team |
| Quality gate enforcement | Every agent on its own work | QA blocks merges; Architect/Red Team block releases |

**Boundaries (no silent dual ownership):** feature extraction is NLP Engineer's;
classifiers are ML Engineer's; API/endpoints are Backend Engineer's; UI is
Frontend Engineer's; UX design is UI/UX Engineer's. Collaboration happens via
workflows and reviews — an agent does not silently take over another's
deliverable. Tests are written by the implementing agent (TDD) and audited by
QA Engineer.

## Final Checklist

Before any change is declared done:

- [ ] Tests pass
- [ ] Type checking passes
- [ ] Lint passes
- [ ] Formatting passes
- [ ] No unused dependencies
- [ ] No secrets
- [ ] No dead code
- [ ] No unexplained architectural deviation
- [ ] Documentation updated
- [ ] ML experiment reproducible
- [ ] Dataset leakage checked
- [ ] Error handling verified
- [ ] Security reviewed
- [ ] Git diff reviewed

## Exceptions

- None for production code. Explicit human-partner sign-off is required to
  waive TDD for a specific deliverable, and the waiver must be recorded.

## Governance

- Standards live HERE, not duplicated in agent files or skills. If a rule
  changes, update this document + the `software-engineering-quality` skill
  together, and record the change in `docs/DECISIONS.md`.
- External skill proposals are governed by `docs/SKILLS.md`.