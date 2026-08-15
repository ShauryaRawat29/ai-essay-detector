# DATASET.md

## Source Registry

### Human Essays
| Source | License | Access | Count | Topics | Length Range | Status |
|--------|---------|--------|-------|--------|--------------|--------|
| `qsardor/viorra-admissions-essays` (HF) | **CC BY-NC 4.0** (HF page; corrected from earlier MIT snippet) | `data/raw/viorra-admissions-essays/viorra_combined_dataset.json` | 128 essays | Admissions personal statements (JHU 59, CollegeVine 41, Shemmassian 13, Emory 7, CollegeEssayGuy 6, others 2) | 276–2,372 words (median 645) | **Downloaded**; admissions-specific; survivorship + source-diversity caveats; README claims 615 but JSON holds 128 — recorded as-is |
| `EducationalTestingService/LEAF` | CC-BY-NC-4.0 (LICENSE.md on disk) | `data/raw/LEAF/leaf.jsonl` | 4,918 (train 4018 / test 500 / dev 400) | Academic essays from essayforum.com (IELTS Task 2 etc.) incl. ESL/learner writing | variable | **Downloaded**; non-admissions; good ESL coverage; carries source `split` labels — re-evaluate against our document-level strategy |
| Ghostbuster `vivek3141/ghostbuster-data` | CC-BY-3.0 (LICENSE on disk) | `data/raw/ghostbuster-data/essay/human/` | 1,000 human essays | Essay prompts (e.g., film analysis), paired by number with `prompts/*.txt` | variable | **Downloaded**; human + AI pairs with prompts; not admissions-specific |

### AI-Generated Essays
| Model | Prompt Strategy | Config | Count | Topics | Status |
|-------|-----------------|--------|-------|--------|--------|
| gpt2-medium (rev `6dcaa7a…`) | Self-generated, admissions prompt templates v1 (see below) | standard/creative/focused/adversarial | 0 generated so far | Admissions prompts | **Self-generated** — `backend/app/datasets/generator.py` built + unit-tested; generation batch not yet run |
| llama-3-8b-instruct (open weights) | Self-generated, same templates | same table | 0 | Admissions prompts | **Self-generated** — holdout family for `test_cross_model`; licensing = Llama 3 Community License |
| Ghostbuster generated set | From Ghostbuster paper prompts (gpt, gpt_prompt1/2, gpt_semantic, gpt_writing, claude) | fixed in source | 7,000 AI essays (1,000 per generator) | Essay prompts (e.g., film analysis), paired with `prompts/*.txt` | **Downloaded** (`data/raw/ghostbuster-data/essay/`); CC-BY-3.0; cross-model value |
| `bmbgsj/AIGC-text-bank` | 12 LLMs incl. GPT-4o, DeepSeek-R1, Llama-3.3-70B; domains incl. Essay (native + non-native) | research-only stated intent | 699k ai_native | 10 domains | Candidate but **license restriction risk** — research-only clause may conflict with open-source product; requires review |

### AI-Polished Human Essays
| Base Source | Model | Polish Prompt | Count | Status |
|-------------|-------|---------------|-------|--------|
| Self-generated from our human records (e.g., LEAF / Ghostbuster human sets) | llama-3-8b-instruct | Polish Prompt v1 (below) | 0 | **Self-generated** — paired with originals as leak group → `test_secondary` |
| `bmbgsj/AIGC-text-bank` ai_polish subset | 12 LLMs | source-specific | 732k | Candidate — same research-only license concern as above |

### Research Notes (Phase 5, honest findings)
1. **Large academic admissions-essay corpora cannot supply raw text.** The well-known
   UC 60k-applicant corpus and related replication data (Harvard Dataverse) release
   only derived LIWC features — raw essays are withheld for applicant privacy
   (recorded as "Not usable", removed from the candidate table).
2. **The VIORRA HF dataset is CC BY-NC 4.0, NOT MIT.** The earlier search snippet
   claiming MIT was stale/wrong; the live HF page and the citation block say
   CC BY-NC 4.0. The on-disk JSON holds 128 essays (README claims 615 — recorded
   as-is, no fabrication). Its JHU subset is the strongest admissions-specific
   material, but it also aggregates other consultants' published examples.
3. **LEAF (EssayForum) is the best non-admissions human complement**, especially for
   the mandatory bias audit (ESL / language-learner writers), under CC-BY-NC-4.0
   (verified on disk). NOTE: non-commercial license — the hackathon deliverable is
   non-commercial, but verify before any future productization.
4. **Ghostbuster (CC-BY-3.0, verified on disk) provides 1,000 human + 7,000 AI essay
   files with paired prompts** (paper: Ghostbuster, arXiv:2305.15047). Useful for
   cross-model evaluation and prompt-faithful AI records.
5. **AI data is most reliably self-generated** with our own pipeline (gpt2-medium +
   a holdout family such as llama-3-8b-instruct), which gives us exact provenance
   (AGENTS.md rule #5) and control over the split strategy. Large third-party AIGC
   banks (e.g., AIGC-text-bank) are attractive for cross-model breadth but their
   "academic research only" intent must be cleared with the Architect before use in
   an open-source artifact.
6. **Downloaded raw data is gitignored** (`backend/data/raw/`) and is NOT a dataset
   version. Integration (convert to `EssayRecord`, run through the builder) is
   **complete for human sources** as dataset **v0.1.0**; AI sources are the next
   phase. Provenance rows above record what is actually on disk.

## Target Dataset Range (NOT Existing Data)
**Target**: 1,000–3,000 total essays across all categories. This is a **target range**, not an existing dataset. As of v0.1.0 the built dataset contains **6,039 human records** (all downloaded sources ingested and split document-level). AI and AI-polished categories are still 0 and will be added in later versions. Target floor for human essays (≥200 from ≥2 sources) is already exceeded by v0.1.0.

## Minimum Viable Dataset Strategy (PROVISIONAL TARGETS)
The following floors are **provisional minimum targets to be validated by the Dataset Engineer**, not scientifically established requirements:
- **Human essays**: ≥200 (from ≥2 distinct sources with verified consent/license)
- **AI-generated essays**: ≥200 (from ≥2 AI model families, varied prompts/configs)
- **AI-polished essays**: ≥50–100 (paired with original human essays)
- **Topic coverage**: ≥3 distinct admissions essay topics
- **Length coverage**: Representation across <200, 200–500, 500–800, >800 words
- **Author background diversity**: Where ethically and legally appropriate, include ESL, formal, edited variants

These minimums will be validated against statistical power requirements during dataset engineering.

## Variability Dimensions (Per Category)
Where possible, vary:
- **Topic**: Common prompts (overcoming adversity, intellectual curiosity, community impact, etc.) + unusual/niche topics
- **Writing quality**: Natural variation in human data; for AI, vary temperature/top-p
- **Essay length**: Short (<200), medium (200–500), standard (500–800), long (>800) words
- **Author background**: ESL, formal academic, heavily edited (where consented)
- **AI model**: At least 2 families (e.g., GPT-2, Llama-3); more for cross-model evaluation
- **Prompting style**: Standard, creative, focused, adversarial ("write like human")
- **Degree of AI editing**: Light polish (grammar/flow), moderate rewrite, heavy restructuring

## Provenance

### Human Data Collection
- **Consent process**: Documented per source (CC-BY, explicit consent form, public domain)
- **Anonymization**: PII removal (names, institutions, specific locations, dates)
- **Preprocessing**: Unicode normalization (NFC), whitespace collapse, encoding validation
- **Collection date**: ISO8601 per source

### AI Data Generation
For each generation batch:
- **Model**: Name, version, revision/commit (e.g., `gpt2-medium`, `llama-3-8b-instruct`)
- **Prompt template**: Exact template with variables
- **Prompt variables**: Topic, word count, style instructions
- **Generation config**: temperature, top_p, top_k, max_tokens, seed
- **Date**: ISO8601
- **Preprocessing**: Same as human (normalization only; no content alteration)

## Generation Methodology

### Prompt Templates
```
# Admissions Essay Prompt v1
Write a college admissions essay on the topic: {topic}
Word count: {word_count} words
Style: Personal, reflective, authentic voice
```

### Generation Configurations
| Config Name | Temperature | Top-p | Top-k | Max Tokens | Use Case |
|-------------|-------------|-------|-------|------------|----------|
| standard | 0.7 | 0.9 | 50 | 800 | Baseline |
| creative | 0.9 | 0.95 | 100 | 800 | High diversity |
| focused | 0.3 | 0.8 | 20 | 800 | Low diversity |
| adversarial | 0.7 | 0.9 | 50 | 800 | "Write like human" added |

### Polish Prompt
```
# Polish Prompt v1
Edit the following essay for clarity, flow, and grammar while preserving the author's voice and story:
{essay}
```

## Metadata Schema (Concrete)

### Human Essay
```yaml
source: str                          # dataset name, URL, submission ID
license: str                         # CC-BY, consent form ID, public domain
collection_date: ISO8601             # e.g., 2026-01-15
preprocessing: List[str]             # e.g., ["nfc_normalize", "whitespace_collapse"]
writer_demographics: Dict | null     # optional, only if consented (e.g., {"esl": true})
essay_id: str                        # unique, stable (UUIDv4 or source-specific)
text: str                            # full essay text
topic: str                           # prompt topic or "free_response"
length_words: int                    # word count after preprocessing
label: "human"
split: "train" | "val" | "test"      # document-level only
```

### AI-Generated Essay
```yaml
model: str                           # e.g., "gpt2-medium", "llama-3-8b-instruct"
model_revision: str                  # commit hash or version tag
prompt_template: str                 # exact template used
prompt_variables: Dict               # {"topic": "...", "word_count": 600}
generation_config:
  temperature: float
  top_p: float
  top_k: int
  max_tokens: int
  seed: int
generation_date: ISO8601
preprocessing: List[str]             # same as human
essay_id: str
text: str
label: "ai_generated"
split: "train" | "val" | "test" | "test_cross_model"  # document-level
```

### AI-Polished Human Essay
```yaml
original_essay_id: str               # reference to human essay (leak group key)
model: str
model_revision: str
polish_prompt: str                   # exact template
generation_config: Dict              # temperature, top_p, top_k, max_tokens, seed
generation_date: ISO8601
preprocessing: List[str]             # same as human
essay_id: str
text: str
label: "ai_polished"
split: "test_secondary" | "test"     # document-level; default test_secondary
```

## Train/Validation/Test Strategy

### Splits
- **Train**: 70% (stratified by source, length bucket, topic cluster)
- **Validation**: 15%
- **Test (in-distribution)**: 15%
- **Test (cross-model)**: AI essays from model families **held out from training** (separate split)
- **Test (out-of-domain, optional)**: Human essays from sources not in training
- **Test (secondary / polished)**: AI-polished essays (paired with originals); default `test_secondary`
- **Split level**: Document (essay) ONLY — never sentence-level
- **Random seed**: Fixed per dataset version (recorded in version history)

### Stratification
- Source (dataset origin)
- Length bucket: short (<300), medium (300–700), long (>700)
- Topic cluster: k-means on embeddings (k=10) or prompt category

### Leakage Prevention (Strict)
1. **Exact duplicate removal**: SHA256 hash of normalized text
2. **Near-duplicate detection**: MinHash Jaccard > 0.8 → remove from smaller split
3. **Shared AI prompts across splits**: Prohibited — each prompt template+variables used in only one split
4. **Writer ID overlap**: Checked if metadata available; enforce disjoint across splits
5. **Embedding similarity**: Cosine > 0.95 across splits → flag for review
6. **AI-polished leak group**: Original human essay and its AI-polished derivative form a **leak group** — both MUST go to the SAME split (or polished held to `test_secondary`). Never train on original and test on polished (or vice versa).

## Known Coverage Gaps
- [x] Source research completed + 3 sources downloaded (Phase 5)
- [x] Integration: downloaded raw converted to `EssayRecord`s and built into **dataset v0.1.0** (6,039 human records; `backend/data/datasets/v0.1.0/`)
- [x] AI generation pipeline built + unit-tested (`app/datasets/generator.py`); batch not yet run
- [ ] AI essays: 0 in dataset so far (generation batch pending; Ghostbuster AI excluded pending provenance-gap decision)
- [ ] AI-polished essays: 0 in dataset so far (pipeline planned)
- [ ] Limited ESL writer representation — mitigatable via LEAF (CC-BY-NC-4.0)
- [ ] Limited unusual topic coverage — mitigatable via self-generated AI data
- [ ] Limited very short essays (< 150 words) — human sources skew to 650-word prompts
- [ ] Limited heavily edited/professional essays — depends on consent-based collection
- [ ] AI models: only gpt2-medium + llama-3-8b planned; third-party banks blocked on license review
- [ ] Prompt diversity: only Templates v1 defined
- [ ] AI-polished degree of editing: only light polish planned (Polish Prompt v1)
- [ ] Raw-text availability: UC/Stanford corpora unusable (privacy) — plan A is JHU collection + LEAF + self-generation

## Version History
| Version | Date | Changes | Split Seed |
|---------|------|---------|------------|
| v0.1.0 | 2026-08-15 | **Initial build** — human sources only (VIORRA 128 + LEAF 4,917 + Ghostbuster-human 994 = 6,039). Preprocessing: strip, newline_normalize, collapse_hspace, nfc_normalize. Dedup: SHA-256 exact (0 removed). Splits: document-level, stratified by (source, length_bucket), 70/15/15 → train 4,230 / val 905 / test 904. Held-out: `holdout_models=[]`, `ai_polished` and AI sets absent (none exist yet). | 42 |

### v0.1.0 Build Notes (provenance, honest reporting)
- **Scope**: human `EssayRecord`s only. AI-generated and AI-polished categories are intentionally absent — the AI generation batch has not been run, and Ghostbuster's 7,000 AI essays are **excluded pending a provenance-gap decision**: the schema requires `generation_config` (model, config, date) for `ai_generated`, which the Ghostbuster files do not provide. See "Ghostbuster AI provenance decision" TODO.
- **VIORRA (128)**: license recorded as CC BY-NC 4.0; `topic` set to `"personal_statement"` (sources do not expose per-essay prompts); `source` = each essay's `Source` field (JHU 59, CollegeVine 41 split across consultant pages, Shemmassian 13, Emory 7, CollegeEssayGuy 6, IvyCollegeEssay.com 1, unspecified 1).
- **LEAF (4,917 of 4,918)**: 1 row had blank `essay_text` and was skipped. `topic` = `essay_title`; source `split` labels (train/test/dev) are recorded in `writer_demographics["source_split"]` but NOT used — our own document-level splits govern. `source` = `"LEAF (EssayForum)"`.
- **Ghostbuster-human (994 of 1,000)**: 6 files are blank and were skipped. `topic` = paired `prompts/{n}.txt` text; essays without a readable prompt get `topic="unspecified_prompt"`. `source` = `"Ghostbuster (vivek3141/ghostbuster-data)"`, license CC-BY-3.0.
- **`collection_date` caveat**: recorded as the ACQUISITION date `2026-08-15`, not the original authorship date (sources do not expose it). Treat as provenance of acquisition only.
- **Subject caveat**: LEAF is IELTS/essayforum academic writing (not admissions) and Ghostbuster prompts are film-analysis (not admissions). Only VIORRA is admissions-specific. Bias-audit sets must account for this domain gap.
- **Distribution skew**: LEAF dominates (4,917/6,039 ≈ 81%). Stratified splits preserve source ratios per split; model training should consider per-source weighting.
- **Artifacts**: `backend/data/datasets/v0.1.0/records.jsonl` + `manifest.json`. Raw sources remain gitignored at `backend/data/raw/`; the versioned dataset is intended for Git versioning.