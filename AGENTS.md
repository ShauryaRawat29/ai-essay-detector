# AI Essay Detector

## Project Mission

Build a real AI-writing analysis application for college admissions essays that provides evidence-based, sentence-level detection with honest evaluation and documented limitations. This is Project 2 of the 2026 i12 HR Drive Hackathon by Callus.

## Non-Negotiable Detector Principles

### 1. Evidence Over Verdicts
Never present AI authorship as proven fact. Use language such as:
- "machine-like writing signals"
- "higher evidence of AI-like patterns"
- "lower evidence"
- "uncertain"

### 2. No Opaque LLM Judgement
**Forbidden architecture:**
```
Essay -> GPT/Claude -> "AI" -> UI
```

**Allowed architecture:**
```
Essay
-> feature extraction
-> language-model measurements
-> statistical/stylometric measurements
-> detection model
-> sentence/passage scores
-> evidence
-> UI
```

The language model must NOT make the final judgement. It may only provide measurable signals (token probabilities, perplexity, entropy) that our own software consumes.

### 3. Sentence and Passage Level Analysis Required
An overall essay score alone is insufficient. Every flag must have evidence at the sentence/passage level.

### 4. Every Flag Must Have Evidence
The UI must explain signals such as:
- unusually low/high perplexity
- token entropy patterns
- sentence-length regularity
- lexical diversity
- repetition
- punctuation/style patterns
- POS distributions
- readability
- contextual similarity
- other validated features

Do not invent explanations not supported by actual feature values.

### 5. Dataset Provenance Is Mandatory
Every dataset source must be documented. Generated AI data must record:
- model
- prompt
- generation configuration
- date
- source
- preprocessing

### 6. Prevent Data Leakage
Never split sentences from the same essay across train and test. Splits must occur at essay/document level.

### 7. Honest Evaluation Is Mandatory
Report:
- precision, recall, F1
- accuracy where appropriate
- confusion matrix
- calibration where appropriate
- test-set composition
- limitations
- three confidently incorrect examples

### 8. Bias Investigation Is Mandatory
Explicitly investigate whether the detector produces excessive false positives for:
- second-language English writers
- unusually formal human writers
- heavily edited essays
- short essays
- unusual topics

### 9. Reproducibility Matters
Experiments must record:
- dataset version
- feature version
- model version
- random seed where applicable
- configuration
- evaluation split

### 10. Agents Must Not Silently Change Architectural Decisions
If an agent disagrees with an existing architectural decision:
- explain the disagreement
- create/update a decision proposal
- request review
- do not silently rewrite architecture

### 11. Documentation Is Part of the Product
A reviewer should be able to understand:
- what was built
- why it was built
- how it works
- what data was used
- how it was evaluated
- where it fails
- what remains uncertain

## Repository Structure

```
.ai-essay-detector/
├── AGENTS.md                          # This file - root control layer
├── .agents/
│   ├── agents/                        # Agent role definitions
│   │   ├── architect.md
│   │   ├── research.md
│   │   ├── dataset-engineer.md
│   │   ├── nlp-engineer.md
│   │   ├── ml-engineer.md
│   │   ├── backend-engineer.md
│   │   ├── frontend-engineer.md
│   │   ├── ui-ux-engineer.md
│   │   ├── qa-engineer.md
│   │   └── red-team-reviewer.md
│   ├── skills/                        # Project-specific skills
│   │   ├── essay-detector-core/
│   │   │   └── SKILL.md
│   │   ├── language-model-analysis/
│   │   │   └── SKILL.md
│   │   ├── stylometric-analysis/
│   │   │   └── SKILL.md
│   │   ├── dataset-engineering/
│   │   │   └── SKILL.md
│   │   ├── ml-evaluation/
│   │   │   └── SKILL.md
│   │   ├── explainable-ai/
│   │   │   └── SKILL.md
│   │   ├── bias-analysis/
│   │   │   └── SKILL.md
│   │   ├── ml-experimentation/
│   │   │   └── SKILL.md
│   │   ├── api-contracts/
│   │   │   └── SKILL.md
│   │   ├── evidence-first-ui/
│   │   │   └── SKILL.md
│   │   ├── software-engineering-quality/
│   │   │   └── SKILL.md
│   │   └── test-driven-development/
│   │       └── SKILL.md
│   └── workflows/                     # Workflow definitions
│       ├── research.md
│       ├── architecture-review.md
│       ├── dataset-workflow.md
│       ├── ml-experiment.md
│       ├── feature-implementation.md
│       ├── api-implementation.md
│       ├── frontend-implementation.md
│       ├── testing.md
│       ├── red-team-review.md
│       └── release-review.md
├── docs/                              # Project documentation
│   ├── PROJECT.md
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── RESEARCH.md
│   ├── METHODOLOGY.md
│   ├── DATASET.md
│   ├── EXPERIMENTS.md
│   ├── EVALUATION.md
│   ├── FAILURE-CASES.md
│   ├── LIMITATIONS.md
│   ├── SKILLS.md
│   └── QUALITY-STANDARDS.md
├── frontend/                          # Next.js application
│   ├── AGENTS.md                      # Frontend-specific rules
│   ├── src/
│   └── ...
├── backend/                           # FastAPI application
│   ├── AGENTS.md                      # Backend/ML-specific rules
│   └── .venv/
└── README.md
```

## Architecture Authority

The **Architect** agent owns:
- System architecture and boundaries
- Technical decisions (recorded in `docs/DECISIONS.md`)
- API contracts between frontend/backend
- Detection pipeline design
- Data flow specifications

No agent may change architectural decisions without Architect review and a recorded ADR.

## Documentation Rules

1. All documentation lives in `docs/` or alongside code as `AGENTS.md` files
2. Use `TODO:` or `PLACEHOLDER:` for uncompleted work - never fabricate results
3. Every experiment, dataset, and decision must be traceable
4. `docs/DECISIONS.md` uses ADR format (decision, context, options, chosen, trade-offs, date, status)
5. `docs/EXPERIMENTS.md` records: ID, hypothesis, config, dataset version, result, conclusion
6. `docs/EVALUATION.md` records metrics, test set composition, calibration, failure analysis

## Dataset Rules

1. **Provenance first**: Document source before collecting
2. **No leakage**: Split at document level, never sentence level
3. **AI-generated metadata**: Record model, prompt, config, date, preprocessing
4. **Human data consent**: Verify licensing and consent for all human essays
5. **Version datasets**: Tag dataset versions; reference in experiments
6. **Balance**: Target diverse topics, lengths, writers; document coverage gaps

## Evaluation Rules

1. **Primary metrics**: Precision, Recall, F1 per class; macro-averaged
2. **Calibration**: Report reliability diagrams / Brier score where applicable
3. **Confusion matrix**: Required for every evaluation
4. **Cross-model evaluation**: Test on outputs from models not seen during training
5. **Failure analysis**: Document 3+ confidently incorrect predictions with analysis
6. **Bias audit**: Explicit test sets for ESL, formal, edited, short, unusual topics
7. **No cherry-picking**: Report all test sets, not just best-performing

## Testing Rules

1. **Unit tests** for: feature extractors, classifiers, API endpoints, UI components
2. **Integration tests** for: full detection pipeline, API contracts
3. **ML pipeline tests**: feature determinism, model loading, inference consistency
4. **Regression tests**: Pin known-known-good outputs for fixed inputs
5. **Edge cases**: Empty text, very short, very long, non-English, adversarial
6. **Frontend**: Accessibility, responsive, sentence highlighting accuracy

## Software Engineering Quality (Mandatory)

1. All code, configuration, and ML/data pipeline work MUST follow the
   `software-engineering-quality` skill and satisfy the quality gate in
   `docs/QUALITY-STANDARDS.md` before it is considered complete.
2. All implementation MUST follow `test-driven-development`: tests are written
   first and observed to fail before implementation code exists.
3. Mandatory for: architect, nlp-engineer, ml-engineer, backend-engineer,
   frontend-engineer, ui-ux-engineer, qa-engineer, red-team-reviewer. The
   research and dataset agents apply it whenever they create executable code or
   data-processing pipelines.
4. No change is complete until tests, lint, type checks, self-review, security
   review, and documentation are all green (see the quality gate in the skill).
5. Never claim a check (test, lint, typecheck) passed without actually running it.

## Security Rules

1. No secrets in code or config - use environment variables
2. No API keys committed; `.env` files in `.gitignore`
3. Input validation on all API endpoints (length, encoding, content-type)
4. Rate limiting on inference endpoints
5. No user data persisted without consent
6. Sanitize all outputs to prevent XSS in frontend

## Git Rules

**Do not commit:**
- `node_modules/`
- `.next/`
- `backend/.venv/`
- Model caches (`~/.cache/huggingface/`, `*.bin`, `*.safetensors`)
- Secrets, API keys, `.env` files
- Generated large datasets (unless explicitly intended for versioning)
- Temporary files, `*.log`, `*.tmp`

**Check and improve `.gitignore` files** in root, frontend/, backend/

**Commit messages**: Conventional format (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)

**Do NOT make Git commits in this phase** unless explicitly requested.

## Agent Collaboration Rules

1. **Repository is shared memory**: Read relevant `AGENTS.md`, `docs/`, decision records, skills before major changes
2. **No hidden conversational memory**: All context must be in files
3. **Never fabricate another agent's work**: If you need something, request it or create a TODO
4. **Never claim an experiment happened if it did not**: Use `TODO:` placeholders
5. **Never claim a dataset was evaluated if it was not**
6. **Load relevant skills** using the skill tool when tasks match skill descriptions

## Prohibited Shortcuts

- ❌ Sending essay to LLM and asking "Is this AI-generated?"
- ❌ Using LLM as final classifier
- ❌ Overall essay score without sentence-level evidence
- ❌ Flags without measurable feature support
- ❌ Training/test splits at sentence level
- ❌ Reporting only accuracy without precision/recall/F1
- ❌ Evaluating only on training-data-like test sets
- ❌ Undocumented datasets or generated data
- ❌ Silent architecture changes
- ❌ Committing secrets, model weights, or large generated data
- ❌ Implementing features before architecture review
- ❌ Coding before research phase completes