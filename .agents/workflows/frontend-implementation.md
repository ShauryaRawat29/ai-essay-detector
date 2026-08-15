# Workflow: Frontend Implementation

## Trigger
- New UI component needed (UX spec approved)
- Evidence display enhancement
- Bug fix in results visualization
- Accessibility improvement

## Process

### Quality Gate Chain (mandatory, no skips)
Quality Skill → Implementation → Tests → Static checks → Review → Documentation

### 1. Read Frontend Rules
- Load `frontend/AGENTS.md`
- Load `evidence-first-ui` skill
- Load `software-engineering-quality` and `test-driven-development` (mandatory — quality gate + TDD apply)
- Review UX specs from UI/UX Engineer

### 2. Define UX (if not provided)
- Wireframe/component spec
- Evidence display requirements
- Accessibility requirements
- Responsive breakpoints

### 3. Implement
- TypeScript + React (Next.js App Router)
- Component in `frontend/src/components/`
- Tailwind CSS for styling
- Evidence-first: no verdict language
- Feature transparency: tooltips link to values

### 4. Test
- Unit: component rendering, props, utilities
- Integration: analysis flow, evidence display
- Accessibility: axe-core, keyboard, screen reader
- Visual regression: highlight accuracy
- Edge cases: empty, long, special chars

### 5. Accessibility Checklist
- [ ] Semantic HTML
- [ ] Focus visible
- [ ] Keyboard navigable
- [ ] Screen reader labels
- [ ] Color contrast 4.5:1
- [ ] Reduced motion support
- [ ] High contrast mode

### 6. Review
- UI/UX Engineer reviews evidence clarity
- Red Team Reviewer audits for misleading presentations
- QA Engineer validates test coverage

## Agents Involved
- **Frontend Engineer** (lead): Implements
- **UI/UX Engineer**: Provides specs, reviews
- **Backend Engineer**: Coordinates API
- **QA Engineer**: Validates tests
- **Red Team Reviewer**: Audits evidence presentation

## Gates
- **No component without passing the quality gate: TDD (tests fail first), lint, type check, self-review, docs**
- **No evidence display without feature value tooltips**
- **No verdict language (AI/Human, probability %)**
- **No color-only signaling (red/green)**
- **Accessibility tests must pass**
- **Visual regression: highlights match sentence boundaries**

## Prohibited
- ❌ "AI Probability: XX%" displays
- ❌ Binary AI/Human badges
- ❌ Hidden uncertainty
- ❌ Invented explanations
- ❌ Skipping accessibility