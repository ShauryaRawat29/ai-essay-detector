# Skill: stylometric-analysis

## Purpose
Extracting statistical and stylometric features from text: lexical diversity, syntactic patterns, readability, repetition, sentence rhythm, punctuation patterns, and POS distributions.

## When to Use
- Implementing stylometric feature extractors
- Adding new stylometric measures
- Validating feature determinism and measurability
- Defining feature schemas

## Core Rules
1. **Every feature has a documented formula**: Reference or mathematical definition required
2. **Deterministic**: Same input → identical output
3. **Sentence and passage level**: All features computable at both granularities
4. **No LLM involvement**: Pure statistical/computational linguistics
5. **Versioned**: Feature extractor version tracked with every run
6. **Robust to noise**: Handle short sentences, unusual punctuation, encoding issues

## Prohibited Behavior
- ❌ Features without documented definitions
- ❌ Non-deterministic extraction (random seeds, non-fixed tokenization)
- ❌ Using LLM to compute or explain features
- ❌ Sentence-only features (must support passage aggregation)
- ❌ Inventing features not tied to measurable text properties

## Feature Families

### Lexical Diversity
- Type-Token Ratio (TTR)
- Moving-Average TTR (MATTR)
- Measure of Textual Lexical Diversity (MTLD)
- HD-D (Hypergeometric Distribution Diversity)
- Rare word rate (frequency bands)
- Word length statistics

### Syntactic / POS
- POS tag distributions (universal tags)
- POS n-gram frequencies
- Dependency tree depth (if parser available)
- Clause density (subordinate/main)
- Average dependency distance

### Readability
- Flesch-Kincaid Grade Level
- Flesch Reading Ease
- Automated Readability Index (ARI)
- Coleman-Liau Index
- Gunning Fog Index
- SMOG Index
- Custom: syllable-per-word, character-per-word

### Repetition
- n-gram repetition rate (character and word)
- Self-similarity (sentence embedding cosine)
- Lexical repetition (word recurrence)
- Structural repetition (sentence pattern similarity)

### Sentence Rhythm / Structure
- Sentence length statistics (mean, std, skew, kurtosis)
- Sentence length regularity (coefficient of variation)
- Punctuation density and patterns
- Clause-per-sentence
- Paragraph structure (if applicable)

### Contextual
- Cross-sentence coherence (embedding similarity)
- Topic consistency (if topic model available)
- Discourse marker frequency

## Implementation Stack
- spaCy for tokenization, POS, sentence splitting, dependency parsing
- textstat for readability formulas
- Custom implementations for MTLD, HD-D, MATTR
- NumPy/SciPy for statistics

## Relevant Project Files
- `backend/app/features/stylometric.py` - feature extractors
- `backend/app/features/registry.py` - feature registry with versions
- `docs/METHODOLOGY.md` - feature definitions and formulas
- `docs/EXPERIMENTS.md` - feature version tracking