# Workflow: Feature Implementation

## Trigger
- New feature approved in Architecture Review
- Bug fix in feature extraction
- Feature version bump required
- Performance optimization

## Process

### Quality Gate Chain (mandatory, no skips)
Quality Skill → Implementation → Tests → Static checks → Review → Documentation

### 1. Read Architecture
- Review `docs/ARCHITECTURE.md` for pipeline interfaces
- Check `docs/DECISIONS.md` for relevant ADRs
- Understand data flow: input → feature → output schema

### 2. Identify Relevant Skill
- Load skills via skill tool:
  - `software-engineering-quality` (mandatory — quality gate applies)
  - `test-driven-development` (mandatory — tests fail before implementation)
  - `stylometric-analysis` for stylometric features
  - `language-model-analysis` for LM signals
  - `essay-detector-core` for pipeline integration

### 3. Implement Narrowly
- Single feature or feature family per PR
- Follow skill's core rules
- Deterministic implementation
- Type hints and docstrings

### 4. Test
- Unit tests: fixed inputs → expected outputs (golden files)
- Determinism test: run 3x, assert identical
- Edge cases: empty, short, long, unicode, malformed
- Passage-level aggregation test

### 5. Document
- Update feature registry with version
- Document formula/definition in `docs/METHODOLOGY.md`
- Record feature version in `docs/EXPERIMENTS.md` for next experiment

### 6. Register
- Add to feature extractor registry
- Version bump: `feature_version` in pipeline config
- Ensure backward compatibility or document breaking change

## Agents Involved
- **NLP Engineer** (lead): Implements
- **Architect**: Reviews interface compliance
- **QA Engineer**: Validates tests
- **ML Engineer**: Consumes in next experiment

## Gates
- **No feature without unit tests + golden outputs**
- **No feature without passing the quality gate: TDD (tests fail first), lint, type check, self-review, docs**
- **No feature without documented definition**
- **No pipeline integration without feature version bump**
- **Determinism test must pass**

## Prohibited
- ❌ Non-deterministic features
- ❌ Features without passage-level support
- ❌ Skipping unit tests
- ❌ Inventing features not in methodology
- ❌ Silent version bumps