# Workflow: Dataset Workflow

## Trigger
- New data source identified
- Need for AI-generated samples
- New dataset version required
- Leakage audit scheduled

## Process

### Quality Gate Chain (mandatory, no skips)
Quality Skill → Implementation → Tests → Static checks → Review → Documentation

### 0. Mandatory Skills
- Load `software-engineering-quality` and `test-driven-development`
- All data-processing pipelines/scripts must satisfy the quality gate and be test-first

### 1. Define Sources
- Document in `docs/DATASET.md` Source Registry
- For each source: name, URL, license, access method, contact
- Verify license/consent before collection

### 2. Collect Human Essays
- Download/import with provenance metadata
- Apply preprocessing (documented)
- Assign stable essay IDs
- Store raw + preprocessed versions

### 3. Generate AI Essays
- Define prompt templates (documented in `docs/DATASET.md`)
- Choose models, configurations, seeds
- Generate with full metadata capture
- Apply same preprocessing as human

### 4. Generate AI-Polished Essays
- Select human essays for polishing
- Define polish prompts
- Generate with full metadata
- Link to original essay IDs

### 5. Validate & Clean
- Deduplicate (exact + near-duplicate)
- Length filtering (min/max documented)
- Encoding validation (UTF-8)
- Quality checks (non-empty, mostly English)

### 6. Split (Document Level Only)
- Stratify: source, length bucket, topic
- Fixed random seed per dataset version
- Verify no leakage (see Leakage Checks)
- Export split indices + metadata

### 7. Version & Document
- Dataset version: `vX.Y.Z` (major.minor.patch)
- Update `docs/DATASET.md` with:
  - Source registry
  - Generation methodology
  - Split strategy and seed
  - Leakage check results
  - Known coverage gaps

## Leakage Checks (Mandatory)
1. Exact duplicate hashes across splits
2. MinHash Jaccard > 0.8 across splits
3. Shared AI prompts/templates across splits
4. Writer ID overlap (if metadata exists)
5. Embedding cosine > 0.95 across splits

## Agents Involved
- **Dataset Engineer** (lead): Executes workflow
- **Architect**: Approves split strategy
- **NLP Engineer**: Defines preprocessing requirements
- **ML Engineer**: Receives splits for training
- **Red Team Reviewer**: Audits for leakage

## Gates
- **No pipeline/script without passing the quality gate: TDD, lint, type check, provenance documented**
- **No training without documented splits**
- **No AI data without full generation metadata**
- **No human data without consent verification**
- **Leakage check pass required before ML Experimentation**

## Output
- `data/raw/`, `data/processed/`, `data/splits/`
- `docs/DATASET.md` updated
- Split indices files (versioned)