# Skill: software-engineering-quality

## Purpose
Mandatory engineering quality bar for ALL code, configuration, and ML/data
pipelines in this repository. Every implementation artifact must pass the
quality gate defined in `docs/QUALITY-STANDARDS.md` before it is considered
complete.

## When to Use
- ANY code implementation (backend, frontend, scripts, pipelines)
- ANY configuration change (env, CI, build, runtime)
- ANY ML/data pipeline or experiment script
- ANY code review (QA, Red Team, release review)

## Mandatory Audience
architect, nlp-engineer, ml-engineer, backend-engineer, frontend-engineer,
ui-ux-engineer, qa-engineer, red-team-reviewer. The research and dataset agents
also apply it whenever they create executable code or data-processing pipelines.

## Non-Negotiable Principles
1. **Evidence over verdicts** — never present AI authorship as proven fact
   (see `essay-detector-core`).
2. **No opaque LLM judgement** — the language model provides measurable signals
   only; it never makes the final call.
3. **Evidence at sentence/passage level** — overall scores alone are never
   acceptable.
4. **Honesty** — no fabricated results, no cherry-picked metrics, no claimed
   experiments that did not run.

## Code Design
- **Single Responsibility Principle**: each module/function has one reason to change.
- **Separation of concerns**: distinct layers (API, service, ML, data) do not bleed into each other.
- **High cohesion, low coupling**: related behavior lives together; modules depend on stable contracts, not internals.
- **DRY** where duplication represents the same responsibility (do not force abstraction for incidental similarity).
- **Avoid premature abstraction**: introduce abstractions when a second real case exists, not speculatively.
- Prefer simple, readable code over clever one-liners.
- Small, focused functions that do one thing.
- Intention-revealing names; no abbreviations beyond convention.
- No unnecessary cleverness, magic, or tricks.
- Do not add features beyond the task (YAGNI). Implement the requirement, not a speculative future.
- No dead code, commented-out blocks, or debug prints left behind.

## Type Safety
- Backend: type annotations on all public functions and dataclasses/Pydantic
  models. `py.typed` style typing for any exported package.
- Frontend: strict TypeScript — avoid `any` unless explicitly justified; prefer
  explicit interfaces/types; avoid unsafe type assertions (e.g. `as` casts that
  hide real mismatches).
- Validate external data everywhere: do not trust API responses, uploaded text,
  dataset metadata, or model output blindly. Validate at the boundary.
- ML: typed feature/configuration dataclasses; no magic dict access.
- Never type APIs as `Any` at boundaries; define explicit request/response
  schemas.
- Python: use explicit return types where useful; avoid unnecessary `Any`.

## Architecture
- Respect the documented boundaries: frontend (Next.js), backend (FastAPI),
  ML pipeline, datasets. See `docs/ARCHITECTURE.md`.
- No silent architecture changes: propose via ADR in `docs/DECISIONS.md` and
  get Architect review (AGENTS.md rule 10).
- Keep route handlers thin; logic belongs in services/pipeline modules.
- Everything the frontend needs passes through typed API contracts
  (`api-contracts` skill).
- No state leakage between requests (FastAPI), and no client-side state that
  should live server-side.

## Code Quality
- Lint clean (backend: ruff; frontend: ESLint/next lint — exact commands in
  `docs/QUALITY-STANDARDS.md`).
- Formatting consistent with the repository (ruff format / Prettier).
- No warnings introduced; existing warnings fixed where feasible.
- Descriptive names; no abbreviations beyond convention.
- Configuration must be centralized where appropriate (env/config module), not
  scattered as hardcoded values.

## Error Handling
- Validate all inputs at boundaries (length, encoding, content-type, range).
- Fail loudly and explicitly with meaningful error messages; never swallow
  exceptions.
- Prefer explicit error responses over silent fallbacks in API code.
- Handle resource cleanup (files, connections, model caches) deterministically.

## Security
- No secrets in code or config; use environment variables only.
- Never commit `.env`, keys, or tokens (AGENTS.md Security Rules).
- Rate limiting on inference endpoints; input validation on all endpoints.
- Sanitize all outputs to prevent XSS in the frontend.
- No user data persisted without consent.
- Review every change against the Security Rules in AGENTS.md.

## Testing
- Follow `test-driven-development`: tests exist and fail before implementation
  code (skill: `test-driven-development`).
- Unit tests for feature extractors, classifiers, API endpoints, UI components.
- Integration tests for the full detection pipeline and API contracts.
- ML pipeline tests: feature determinism, model loading, inference consistency.
- Regression tests pinning known-good outputs for fixed inputs.
- Edge cases: empty, very short, very long, non-English, adversarial inputs.
- Every discovered bug that can recur must receive a regression test.
- Do not write tests merely to increase coverage; tests must verify behavior.

## ML Quality
- Document-level splits only; never split sentences from one essay across
  train/test (AGENTS.md rule 6).
- Report precision, recall, F1 (macro), confusion matrix, calibration,
  test-set composition, limitations, and three confidently incorrect examples
  (AGENTS.md rule 7).
- Investigate bias: ESL, formal, edited, short, unusual-topic writers
  (AGENTS.md rule 8).
- Reproducibility: dataset version, feature version, model version, seed,
  configuration, split (AGENTS.md rule 9).
- Dataset provenance is mandatory: model, prompt, config, date, source,
  preprocessing (AGENTS.md rule 5).

## Documentation
- Every behavior change must be reflected in `docs/` (DECISIONS, EXPERIMENTS,
  EVALUATION, DATASET, FAILURE-CASES, LIMITATIONS) as applicable.
- Use `TODO:`/`PLACEHOLDER:` for uncompleted work; never fabricate results.
- No undocumented datasets, experiments, or decisions.

## AI-Generated Code Standard
Code produced by an AI assistant must meet the SAME bar as human code:
- Tests written and observed to fail before implementation (TDD).
- No "test-shaped" code that exists only to make CI green.
- The assistant must not silently change architecture; if it disagrees with an
  architectural decision it must explain, propose an ADR, and request review.
- Do not invent explanations or results not supported by actual feature values.
- Verify by running the actual test/lint commands; never claim a check passed
  without running it.

## Quality Gate
A change is NOT complete until ALL of the following pass. Full details and
commands in `docs/QUALITY-STANDARDS.md`.

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

Gate steps (an implementation phase is complete ONLY when):
1. Tests run and pass (written first and watched to fail per TDD).
2. Type checking runs clean.
3. Linting runs clean.
4. Formatting checks run clean.
5. Git diff inspected (only intended files, no secrets/weights/data).
6. Dead/unused code removed.
7. Dependencies checked (no unnecessary additions).
8. Secrets checked (none committed).
9. Architecture compliance verified (no silent deviations).
10. Documentation updated.
11. Failures reported honestly (never claim a check passed without running it).

A phase is NOT complete simply because the application starts.

## Verification
- Run the actual commands from `docs/QUALITY-STANDARDS.md`. Do not claim a
  check passed without running it.
- If a command is unavailable in the environment, say so explicitly and record
  it as a TODO, rather than skipping silently.

## Relevant Project Files
- `docs/QUALITY-STANDARDS.md` — authoritative standards, commands, checklist
- `docs/SKILLS.md` — skill provenance and governance
- `.agents/skills/test-driven-development/SKILL.md` — test-first rules
- `.agents/workflows/*.md` — process gates that invoke this skill
- `AGENTS.md` — repository principles this skill enforces