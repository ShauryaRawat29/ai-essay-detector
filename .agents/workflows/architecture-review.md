# Workflow: Architecture Review

## Trigger
- New major component proposed
- Cross-cutting change (data flow, API, pipeline stages)
- Agent disagrees with existing decision
- Pre-implementation for any significant feature

## Process

### 1. Request Review
- Agent creates Architecture Decision Record (ADR) draft in `docs/DECISIONS.md`
- Uses ADR template (see below)
- Notifies Architect

### 2. Architect Review
- Reads ADR and relevant context
- Consults affected agents (async or sync)
- Evaluates against:
  - Non-Negotiable Principles (root AGENTS.md)
  - Existing decisions (docs/DECISIONS.md)
  - System boundaries (docs/ARCHITECTURE.md)
  - Scalability, maintainability, testability

### 3. Decision Meeting (if needed)
- Sync discussion for complex trade-offs
- All affected agents invited
- Record dissenting views

### 4. Record Decision
- Architect finalizes ADR in `docs/DECISIONS.md`
- Status: `Proposed` → `Accepted` | `Rejected` | `Deferred`
- Updates `docs/ARCHITECTURE.md` if needed
- Notifies all agents

### 5. Implementation Gate
- No implementation begins until ADR is `Accepted`
- Implementation follows Feature Implementation workflow

## ADR Template
```markdown
## ADR-XXX: [Title]

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Rejected | Deferred | Superseded
**Author**: [Agent]
**Reviewers**: [List]

### Context
[What problem are we solving? What constraints exist?]

### Options Considered
1. **Option A**: [Description, pros, cons]
2. **Option B**: [Description, pros, cons]
3. **Option C**: [Description, pros, cons]

### Decision
[Chosen option and rationale]

### Trade-offs
- **Accepted**: [What we gain]
- **Accepted**: [What we lose/accept]
- **Mitigations**: [How we address downsides]

### Consequences
- **Architecture**: [Changes to docs/ARCHITECTURE.md]
- **API**: [Contract changes]
- **Data**: [Schema/migration changes]
- **Testing**: [New test requirements]

### Related ADRs
- ADR-XXX: [Related decision]
```

## Agents Involved
- **Architect** (lead): Owns process, final decision
- **Requesting Agent**: Proposes, provides context
- **Affected Agents**: Review, provide input
- **Red Team Reviewer**: Challenges assumptions

## Gates
- **No silent architecture changes**: All changes via ADR
- **No implementation before Accepted ADR**
- **Deferred decisions**: Explicit timeline for revisit

## Escalation
If agent disagrees with Accepted ADR:
1. Write new ADR proposing change (not silent rewrite)
2. Reference original ADR
3. Request Architect review