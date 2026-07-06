# Dataset Template

Copy this folder to `datasets/{name}/` when onboarding a new dataset.

## Structure

```
datasets/{name}/
├── README.md              # Dataset description, source, known limitations
├── config.yaml            # Source URL, metadata, top-x values
├── raw/                   # Downloaded records (gitignored if large)
├── processed/
│   ├── papers_authors.csv # Long format: one row per paper-author pair
│   └── author_aliases.csv # Manual dedup table (SSOT for merges)
├── output/
│   ├── monopoly_metrics.csv
│   ├── author_rankings.csv
│   └── figures/
└── scripts/
    └── run_pipeline.R     # Orchestrates full pipeline
```

## Setup Checklist

```
[ ] Copy this folder to datasets/{name}/
[ ] Fill config.yaml with source details
[ ] Write README.md with dataset description
[ ] Create empty author_aliases.csv with header row
[ ] Implement or adapt run_pipeline.R
[ ] First fetch + count reconciliation
[ ] Update CLAUDE.md project state table
```

## author_aliases.csv Header

```csv
author_raw,author_id,notes,merged_by,merged_date
```

## See Also

- `.claude/rules/dataset-pipeline-protocol.md` — file schemas
- `.claude/rules/authorship-monopoly-metrics.md` — metric definitions
- `.claude/rules/pubmed-collection-protocol.md` — PubMed download (if applicable)
