# Skill: test-driven-development

## Purpose
Test-first (red-green-refactor) discipline for all implementation work. Prevents
AI-generated code from shipping tests that reverse-engineer passing code —
a test that never watched its code fail proves nothing.

**Origin:** Adapted from `obra/superpowers` via skills.sh (2026-08-15).
**Required by:** `software-engineering-quality`, `testing.md`, and all
implementation workflows. Mandatory for any code-producing agent.

## When to Use
- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask the human partner):** throwaway prototypes, generated
config/data files, one-off analysis scripts that are explicitly temporary.

## Core Principle
**If you didn't watch the test fail, you don't know if it tests the right thing.**
Violating the letter of the rules is violating the spirit of the rules.

## The Iron Law
```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```
Wrote code before the test? Delete it and start over. No exceptions:
- Do not keep it "as reference".
- Do not "adapt" it while writing tests.
- Do not look at it. Delete means delete.

## Red-Green-Refactor

### RED — Write Failing Test
Write one minimal test showing what should happen.
- One behavior per test. If the name contains "and", split it.
- Clear name that describes the behavior (e.g. `rejects empty email`).
- Test real code, not mocks (mocks only when unavoidable).

### Verify RED — Watch It Fail (MANDATORY)
Run the single test and confirm:
- It fails (not errors).
- The failure message is the expected one.
- It fails because the feature is missing, not a typo.
- Test passes already? You are testing existing behavior. Fix the test.
- Test errors? Fix the error, re-run until it fails correctly.

### GREEN — Minimal Code
Write the simplest code that passes the test. Do not add features, refactor
other code, or "improve" beyond the test.

### Verify GREEN — Watch It Pass (MANDATORY)
Run the test and confirm it passes, no other tests break, and output is
pristine (no warnings/errors). Test fails? Fix the code, not the test.

### REFACTOR — Clean Up (only after green)
Remove duplication, improve names, extract helpers. Keep tests green.
Do not add behavior.

### Repeat
Next failing test for the next feature.

## Common Rationalizations (all rejected)
| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. The test takes 30 seconds. |
| "I'll test after" | Tests-after pass immediately, which proves nothing: they may test the wrong thing, test implementation instead of behavior, or miss the edge case you forgot. |
| "Already manually tested" | Manual testing is ad-hoc and leaves no re-runnable record. |
| "Deleting X hours of code is wasteful" | Sunk cost. Keeping code you cannot trust is the real waste. |
| "Keep as reference" | You will adapt it — that is testing after. Delete means delete. |
| "TDD is dogmatic" | TDD catches bugs before commit, prevents regressions, and makes refactoring safe. "Pragmatic" shortcuts mean debugging in production. |

## Red Flags — STOP and Start Over
- Code before test
- Test after implementation
- Test passes immediately
- Can't explain why the test failed
- Tests added "later"
- Rationalizing "just this once"
- "I already manually tested it"

## Good Tests
| Quality | Good | Bad |
|---------|------|-----|
| **Minimal** | One thing. No "and" in the name. | `test('validates email and domain and whitespace')` |
| **Clear** | Name describes behavior | `test('test1')` |
| **Shows intent** | Demonstrates the desired API | Obscures what the code should do |

## Running Tests in This Repository
- Backend (FastAPI/pytest): `backend/.venv/Scripts/python -m pytest` from `backend/`
- Frontend (Next.js): `npm test` from `frontend/` (when a framework is configured)
- Run only the failing test during RED/GREEN verification, then the full suite
  before completing.

## Verification Checklist
Before marking work complete:
- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for the expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

Can't check all boxes? You skipped TDD. Start over.

## When Stuck
| Problem | Solution |
|---------|----------|
| Don't know how to test | Write the wished-for API. Write the assertion first. Ask your human partner. |
| Test too complicated | Design too complicated. Simplify the interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup huge | Extract helpers. Still complex? Simplify the design. |

## Final Rule
```
Production code -> test exists and failed first
Otherwise -> not TDD
```
No exceptions without the human partner's permission.