# EdShare Post-2017 — Authorship Monopoly Analysis

**Source:** [EdSHARe Bibliography](https://edshareproject.org/research-and-publications/bibliography) — filtered journal-article listing (July 2026).

## Scope

- **54 journal articles** with publication year ≥ 2017
- Curated from the bibliography search results (HS&B / EdSHARe midlife cohort literature)
- Excludes 2016 entries and non-journal items (e.g. Hanushek et al. 2022 working paper)

Prior full-corpus analyses are archived at
`datasets/_archive/EdShare_phase1_2026-07-06/` (989-paper full set plus pre/post-2015 splits).

```bash
Rscript datasets/EdShare_post2017/scripts/run_pipeline.R
```

## Outputs

- `raw/bibliography_citations.txt` — source citation list
- `processed/papers_authors.csv` — one row per author per paper
- `output/monopoly_metrics.csv` — HHI and top-x shares
