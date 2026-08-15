# SKILLS.md — skills.sh Research and Installation Record

**Status:** Decided
**Date:** 2026-08-15
**Scope:** Evaluation of external skills from skills.sh against the project's
10 authoritative project skills, the mandatory `software-engineering-quality`
skill, and repository rules.

## Purpose

The project uses its own curated skills under `.agents/skills/`:

| Skill | Authority |
|-------|-----------|
| `essay-detector-core` | Detector principles (evidence-first, no LLM verdict) |
| `language-model-analysis` | Token probabilities, perplexity, entropy |
| `stylometric-analysis` | Sentence length, lexical diversity, POS, readability |
| `dataset-engineering` | Provenance, document-level splits, leakage prevention |
| `ml-evaluation` | Precision/recall/F1, calibration, confusion matrix, bias |
| `explainable-ai` | Sentence/passage-level evidence, no opaque LLM judgement |
| `bias-analysis` | ESL, formal, edited, short, unusual-topic audits |
| `ml-experimentation` | Versioned experiments, reproducibility, seeds |
| `api-contracts` | Backend/frontend contract discipline |
| `evidence-first-ui` | Neutral evidence UI, no verdict-like red/green |
| `software-engineering-quality` | Mandatory quality gate (this phase) |
| `test-driven-development` | Installed from skills.sh (this phase) |

Decision rule: **install external skills only when they materially improve the
project AND do not overlap, conflict with, or duplicate the skills above.**

## Evaluation Criteria

For every candidate skill, skills.sh research recorded:
1. What it actually provides.
2. Whether it overlaps with existing project skills or rules.
3. Whether it conflicts with any project principle.
4. Whether its content is stable and cleanly installable without adding
   dependencies (the skills.sh CLI itself is a dependency and was NOT run).
5. Whether it adds material value to this specific project.

## Decision Summary

- **Installed: 1** — `test-driven-development` (obra/superpowers), adapted.
- **Rejected: 20** — candidates that duplicate project skills, are deprecated,
  conflict with project rules, are not cleanly installable, or add no material
  value.

## Evaluated Candidates

### A. General Software Engineering

| Skill | Source | Purpose | Installed | Reason | Potential overlap | Conflict |
|-------|--------|---------|-----------|--------|-------------------|----------|
| `test-driven-development` | obra/superpowers | Red-green-refactor TDD discipline; prevents tests that reverse-engineer passing code | **Yes** | Materially improves test integrity for AI-generated code; no project skill covers test-first discipline; content fetched and adapted | `testing.md` workflow, `qa-engineer` | None |
| `verification-before-completion` | obra/superpowers | Verify work is actually complete | No | Redundant with the mandatory quality gate in `software-engineering-quality` and `release-review.md` | Quality gate | None |
| `webapp-testing` | anthropics/skills | Generic web-app test patterns (unit/integration/e2e) | No | Overlaps `testing.md` and `frontend/AGENTS.md` testing rules; QA engineer owns testing; patterns are generic, not project-specific | `testing.md`, QA agent | None |

### B. Next.js / Frontend

| Skill | Source | Purpose | Installed | Reason | Potential overlap | Conflict |
|-------|--------|---------|-----------|--------|-------------------|----------|
| `next-best-practices` | vercel-labs/next-skills | Next.js best practices | No | **Deprecated** — knowledge now ships as bundled docs in Next.js 16.3+ (`frontend/node_modules/next/dist/docs/`), already present; `frontend/AGENTS.md` already points agents at it | Bundled Next docs | None |
| `vercel-react-best-practices` | vercel-labs/agent-skills | React/Next performance rules | No | Not material for this small, non-perf-critical app; `evidence-first-ui` is authoritative for UI | `evidence-first-ui` | None |
| `frontend-design` | anthropics/skills | Aesthetic design guidance | No | Conflicts with `evidence-first-ui`: evidence-first mandates a neutral, low-signal palette and forbids verdict-like color coding | `evidence-first-ui` | **Yes** — contradicts mandated neutral evidence UI |

### C. Python / Backend (FastAPI)

| Skill | Source | Purpose | Installed | Reason | Potential overlap | Conflict |
|-------|--------|---------|-----------|--------|-------------------|----------|
| `fastapi` | fastapi/fastapi (official) | Keep agents current with FastAPI API | No | Content not cleanly installable without the skills.sh CLI (a dependency); project backend rules + `software-engineering-quality` already mandate thin handlers, Pydantic boundaries, validation | `api-contracts`, backend rules | None |
| `production-fastapi` | vstorm-co/production-stack-skills | Opinionated production FastAPI patterns | No | Overlaps `backend/AGENTS.md`; opinionated patterns conflict with the project's intentionally simple dev-first backend | backend rules | None |
| `fastapi-python` | mindrally/skills | Generic FastAPI style guidance | No | Redundant with backend rules | backend rules | None |
| `fastapi-code-review` | existential-birds/beagle | FastAPI code-review checklist | No | Subsumed by `software-engineering-quality` review requirements and `docs/QUALITY-STANDARDS.md` | Quality skill | None |

### D. Machine Learning

| Skill | Source | Purpose | Installed | Reason | Potential overlap | Conflict |
|-------|--------|---------|-----------|--------|-------------------|----------|
| `scikit-learn` | k-dense-ai/scientific-agent-skills | Scikit-learn library usage reference | No | Library-usage reference; project `ml-evaluation` + `ml-experimentation` are authoritative for methodology; low marginal value | `ml-evaluation`, `ml-experimentation` | None |
| `scikit-learn-best-practices` | mindrally/skills | sklearn best practices | No | Redundant with the above rejection | `ml-evaluation` | None |
| `ml-experiment-standards` | muend/geoai-skills | Experiment tracking standards | No | Near-total overlap with `ml-experimentation` project skill | `ml-experimentation` | None |

### E. NLP

| Skill | Source | Purpose | Installed | Reason | Potential overlap | Conflict |
|-------|--------|---------|-----------|--------|-------------------|----------|
| — | — | — | No | No suitable NLP/transformers/stylometry skills found in the skills.sh registry; `language-model-analysis` and `stylometric-analysis` are authoritative | Project skills | — |

### F. Data Engineering

| Skill | Source | Purpose | Installed | Reason | Potential overlap | Conflict |
|-------|--------|---------|-----------|--------|-------------------|----------|
| — | — | — | No | No suitable dataset-engineering/leakage-prevention skills found; `dataset-engineering` is comprehensive and authoritative | `dataset-engineering` | — |

### G. Security

| Skill | Source | Purpose | Installed | Reason | Potential overlap | Conflict |
|-------|--------|---------|-----------|--------|-------------------|----------|
| `security-review` | affaan-m/everything-claude-code | 10-domain security review checklist | No | Overlaps AGENTS.md Security Rules + `software-engineering-quality` security section; essentials integrated into `docs/QUALITY-STANDARDS.md` | AGENTS.md Security, quality skill | None |
| `api-security-best-practices` | sickn33/antigravity-awesome-skills | API security patterns | No | Redundant with the above | AGENTS.md Security | None |
| `production-security` | vstorm-co/production-stack-skills | Production security patterns | No | Overlaps; opinionated scope not material yet | AGENTS.md Security | None |

### H. Documentation / ADR

| Skill | Source | Purpose | Installed | Reason | Potential overlap | Conflict |
|-------|--------|---------|-----------|--------|-------------------|----------|
| `documentation-and-adrs` | addyosmani/agent-skills | Documentation + ADR discipline | No | Project already has a canonical ADR template in `docs/DECISIONS.md` and ADR requirements in `architecture-review.md` | `DECISIONS.md`, `architecture-review.md` | None |
| `architecture-decision-records` | wshobson/agents | ADR practices | No | Same as above | Same | None |
| `create-architectural-decision-record` | github/awesome-copilot | ADR creation | No | Tool-specific; conflicts with the project's exact ADR format | Same | None |

## Supplemental Evaluation (round 2, categories A–H deep-dive)

Candidates surfaced by targeted skills.sh searches for every category in the
task spec. Same decision rule: install only when material, non-overlapping,
non-conflicting.

| Skill | Source | Purpose | Installed | Reason | Potential overlap | Conflict |
|-------|--------|---------|-----------|--------|-------------------|----------|
| `code-review` | paulrberg/agent-skills | Evidence-based diff review | No | QA Engineer + quality gate already own review; adds no project-specific value | `qa-engineer`, quality skill | None |
| `code-reviewer` | jeffallan/claude-skills | Senior code-review checklist | No | Same as above | Same | None |
| `code-review` | ahgraber/skills | Structured code review | No | Same as above | Same | None |
| `review-and-simplify-changes` | dimillian/skills | Review/simplify with Codex subagents | No | Tool-specific (Codex subagents); overlaps quality gate step 6 | Quality gate | None |
| `autofix` | lgbarn/skills | Review + safe auto-fix | No | Overlaps quality gate; tool-specific gate discipline | Quality gate | None |
| `clean-code` | sickn33/antigravity-awesome-skills | Uncle Bob principles | No | Subsumed by `software-engineering-quality` Code Design section | Quality skill | None |
| `typescript-clean-code` | bmad-labs/skills | Clean Code adapted for TS | No | Frontend is small; principles subsumed; references-driven skill is heavyweight | Quality skill | None |
| `typescript-refactor` | pproenca/dot-skills | 47 TS/TSX refactoring rules | No | Current to TS 6.0/React 19 but not material for current small app; revisit if TS surface grows | Quality skill | None |
| `typescript-expert` | sickn33/antigravity-awesome-skills | Advanced type-level programming | No | Overkill for this codebase; strict-mode rules already mandated | Quality skill | None |
| `typescript-best-practices` | jwynia/agent-skills | TS coding standards | No | Redundant with `frontend/AGENTS.md` + `api-contracts` typing | Frontend rules | None |
| `senior-frontend` | borghei/claude-skills (and sickn33 variant) | Scaffolding, React patterns, bundle analysis | No | Next 14+ oriented scaffolding; overlaps frontend rules; `evidence-first-ui` is authoritative | Frontend rules | None |
| `frontend-engineering` | schalkneethling/create-project-calavera | Semantic HTML/CSS guidance | No | Overlaps frontend accessibility rules; not material for 6 components | Frontend rules | None |
| `front-end-developer` | mindrally/skills | Senior frontend persona prompt | No | Persona only; no material guidance | — | None |
| `frontend-a11y` | affaan-m/ecc | React/Next a11y patterns | No | `frontend/AGENTS.md` already mandates WCAG AA, axe-core, keyboard/focus rules | Frontend rules | None |
| `fastapi-rest-api-design` | open-edge-platform/anomalib | REST design + FastAPI quality | No | Overlaps `api-contracts` + `backend/AGENTS.md` + quality skill | `api-contracts` | None |
| `fastapi-patterns` | affaan-m/everything-claude-code | Production FastAPI layout/DI/tests | No | Overlaps backend rules; we already established the layout in Phase 1 | Backend rules | None |
| `fastapi-expert` | jeffallan/claude-skills | Async/Pydantic v2/JWT | No | Overlaps backend rules; JWT/auth out of scope for now | Backend rules | None |
| `fastapi` | jezweb/claude-skills | FastAPI + SQLAlchemy + JWT patterns | No | Pins FastAPI 0.128 (we use 0.141); SQLAlchemy not in stack; content would drift | Backend rules | None |
| `python-backend-expert` | hieutrtr/ai1-skills | FastAPI + SQLAlchemy/Alembic | No | SQLAlchemy/Alembic not in stack; overlaps backend rules | Backend rules | None |
| `binary-classification` | brojonat/llmsrules | XGBoost binary classification | No | `ml-evaluation`/`ml-experimentation` are authoritative for methodology | ML skills | None |
| `multiclass-classification` | brojonat/llmsrules | XGBoost multiclass | No | Not applicable (binary detection task) | ML skills | None |
| `xgboost-lightgbm` | tondevrel/scientific-agent-skills | GB library reference | No | Library reference; project ML skills authoritative | ML skills | None |
| `data-validation` | anthropics/knowledge-work-plugins | Pre-delivery QA checklist | No | Overlaps `ml-evaluation` + quality standards | ML skills | None |
| `data-validation` | cosmix/claude-loom | Validation/sanitization libraries | No | Overlaps AGENTS Security Rules + quality skill; no Pydantic-specific value | Security rules | None |
| `data-testing` | dtsong/data-engineering-skills | SQL/dbt pipeline testing | No | dbt/SQL not in stack | — | None |
| `data-science-agent-skills` (leakage-adversary, experiment-provenance-ledger, etc.) | Emily2040/data-science-agent-skills | 25-skill DS portfolio incl. leakage + provenance | No | `dataset-engineering` + `ml-experimentation` already cover leakage prevention and provenance as authoritative project skills | `dataset-engineering`, `ml-experimentation` | None |
| `api-security-review` | bobmatnyc/claude-mpm-skills | API security checklist | No | Overlaps AGENTS Security Rules + `api-security-best-practices` | Security rules | None |
| `secure-code-review` | aiming-lab/metaclaw | Security review checklist | No | Overlaps AGENTS Security Rules; essentials in QUALITY-STANDARDS | Security rules | None |
| `input-validation-and-sanitization` | aiming-lab/metaclaw | Boundary validation patterns | No | Overlaps AGENTS Security Rules + quality skill Error Handling/Security sections | Security rules | None |

Supplemental result: 0 installed, 26 rejected. Combined total: **1 installed,
46 rejected**.

## Installed Skill — `test-driven-development`

- **Origin:** `obra/superpowers` via skills.sh, adapted for this repository.
- **Location:** `.agents/skills/test-driven-development/SKILL.md`
- **Why installed:** It is the single strongest, non-conflicting, material
  improvement found. It directly addresses the "AI-generated code standard"
  risk: AI assistants naturally write tests *after* implementation, and such
  tests reverse-engineer passing code and prove nothing. The skill enforces
  test-first, watch-it-fail, minimal-green, refactor discipline.
- **How it integrates:** Required for all implementation work alongside
  `software-engineering-quality`; referenced by `testing.md`, implementation
  workflows, and QA agent rules.
- **No dependencies were installed.** The skill is a markdown file in the repo;
  the `npx skills` CLI was not used.

## Governance (How to Avoid Duplication)

- **Where rules live:**
  - Repository principles and non-negotiables → root `AGENTS.md`.
  - Project-specific domain knowledge → project skills in `.agents/skills/`.
  - Generic engineering quality → `software-engineering-quality` skill +
    `docs/QUALITY-STANDARDS.md`.
  - Test-first discipline → `test-driven-development` skill.
  - Process / order of operations → workflows in `.agents/workflows/`.
  - Canonical records (ADR, experiments, datasets) → `docs/` files only.
- Before proposing a new skill, check this file and the project skills first.
- External skill adoption requires: (1) material value, (2) no overlap,
  (3) no conflict, (4) stable installable content, (5) record here.