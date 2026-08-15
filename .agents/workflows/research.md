# Workflow: Research

## Trigger
- Project start
- New signal family needed
- Architecture requires validation
- Red Team finds unknown weakness

## Process

### 1. Define Research Questions
- Record in `docs/RESEARCH.md`
- Specific, testable questions
- Link to architectural needs

### 2. Literature Survey
- Search: academic papers, arXiv, industry blogs, open-source repos
- Keywords: AI text detection, authorship verification, stylometry, perplexity detection, watermarking
- Document every source with citation

### 3. Evaluate Findings
For each finding:
- **Signal/Method**: What measurable signal or technique?
- **Source**: Full citation
- **Applicability**: Admissions essays? English? Short text?
- **Strengths**: What does it detect well?
- **Weaknesses**: Known failure modes, biases
- **Confidence**: High/Medium/Low
- **Implementation complexity**: Trivial/Moderate/High

### 4. Identify Uncertainties
- Gaps in literature
- Conflicting results
- Assumptions needing validation
- Record in `docs/RESEARCH.md` as "Unresolved Questions"

### 5. Propose Experiments
- For each high-priority uncertainty
- Define hypothesis, method, success criteria
- Hand off to ML Experimentation workflow

## Required Outputs
- Updated `docs/RESEARCH.md` with findings
- List of proposed experiments for `docs/EXPERIMENTS.md`
- Signal candidates for Architect review

## Agents Involved
- **Research** (lead): Executes workflow
- **Architect**: Receives signal candidates, validates architectural fit
- **NLP Engineer**: Validates measurability
- **ML Engineer**: Assesses classification utility
- **Dataset Engineer**: Identifies data needs

## Gates
- **No coding** until research questions resolved or explicitly deferred
- **Architect sign-off** on signal candidates before implementation
- **TODO placeholders** for unresolved questions — never fabricate

## Timeline Guidance
- Initial research: 1-2 weeks
- Ongoing: As needed for new uncertainties