---
paths:
  - "datasets/**/*"
  - "scripts/R/**/*"
---

# Dataset Pipeline Protocol

**Each dataset under `datasets/{name}/` follows this canonical structure and file schema.**

For slide/paper SSOT, see `single-source-of-truth.md` (scoped to `Slides/`, `Quarto/`).

---

## Folder Structure

```
datasets/{name}/
├── README.md
├── config.yaml
├── raw/
│   ├── pubmed_manifest.csv      # PMID list + fetch metadata
│   └── pubmed_records.xml       # Full PubMed XML (gitignored if large)
├── processed/
│   ├── papers_authors.csv       # Long format: one row per paper-author pair
│   └── author_aliases.csv       # Manual dedup table (SSOT for merges)
├── output/
│   ├── monopoly_metrics.csv     # HHI, top-x, summary stats
│   ├── author_rankings.csv      # Author paper counts (post-merge)
│   └── figures/                 # Publication-ready PDF + PNG
└── scripts/
    └── run_pipeline.R           # Orchestrates full pipeline for this dataset
```

---

## config.yaml Schema

```yaml
dataset:
  name: REGARDS
  full_name: "REasons for Geographic And Racial Differences in Stroke"
  description: "Longitudinal cohort study of stroke disparities"

source:
  type: pubmed_collection
  collection_id: "46426411"
  collection_url: "https://www.ncbi.nlm.nih.gov/myncbi/browse/collection/46426411/"
  expected_paper_count: 911        # Update after first fetch
  last_fetched: null               # ISO date, set by pipeline

metrics:
  top_x_values: [1, 3, 5, 10]
  compute_by_year: true            # If publication year available

paths:
  raw_dir: raw
  processed_dir: processed
  output_dir: output
```

---

## processed/papers_authors.csv Schema

| Column | Type | Description |
|--------|------|-------------|
| `pmid` | string | PubMed ID |
| `title` | string | Paper title |
| `pub_year` | integer | Publication year (nullable) |
| `author_raw` | string | Author as returned by PubMed (LastName Initials) |
| `author_id` | string | Canonical author ID after alias merge |
| `author_position` | integer | 1 = first author, etc. |
| `affiliation` | string | Primary affiliation if available (nullable) |

**Constraints:**
- One row per paper-author pair
- `author_id` must exist in author rankings after alias merge
- Paper count = distinct `pmid` values

---

## processed/author_aliases.csv Schema

| Column | Type | Description |
|--------|------|-------------|
| `author_raw` | string | PubMed author string to merge |
| `author_id` | string | Canonical ID (typically most common variant) |
| `notes` | string | **Required.** Rationale for merge (e.g., "Same person, different initial") |
| `merged_by` | string | Who approved merge (e.g., "jmfletcher", "auto-suggested") |
| `merged_date` | date | ISO date of merge decision |

**Constraints:**
- Every merge must have non-empty `notes`
- `author_id` values must be consistent (transitive merges)
- Flag auto-suggested merges for human review before metrics computation

---

## output/monopoly_metrics.csv Schema

| Column | Type | Description |
|--------|------|-------------|
| `dataset` | string | Dataset name |
| `metric` | string | "hhi", "top_x_share", "n_papers", "n_authors" |
| `value` | numeric | Metric value |
| `top_x` | integer | Only for top_x_share metric (nullable otherwise) |
| `year` | integer | Only if computed by year (nullable otherwise) |
| `computed_date` | date | ISO date of computation |

---

## Pipeline Execution Order

```
1. Read config.yaml
2. Fetch PubMed records → raw/
3. Parse authors → processed/papers_authors.csv
4. Apply author_aliases.csv merges
5. Compute metrics → output/monopoly_metrics.csv
6. Generate figures → output/figures/
7. QC: reconcile counts (see authorship-monopoly-metrics.md)
```

**Never skip steps or edit downstream files without rerunning from the affected step.**

---

## Graduation from Explorations

When promoting from `explorations/` to `datasets/{name}/`:

1. Copy structure from `datasets/_template/`
2. Quality score >= 80 on all scripts
3. Count reconciliation passes
4. README documents approach and known limitations
5. Move exploration to `explorations/ARCHIVE/completed_{name}/`

---

## New Dataset Checklist

```
[ ] Copy datasets/_template/ to datasets/{name}/
[ ] Fill config.yaml with source details
[ ] Write README.md with dataset description
[ ] Implement or adapt run_pipeline.R
[ ] First fetch + count reconciliation
[ ] Seed author_aliases.csv (even if empty)
[ ] Update CLAUDE.md project state table
```
