# EdShare — Authorship Monopoly Analysis

**Source:** [EdSHARe Bibliography](https://edshareproject.org/research-and-publications/bibliography)

## Notes

- Drupal bibliography with full semicolon-separated author lists (no et al truncation).
- Covers research using harmonized NLS:72 and HS&B:80 data via EdSHARe.
- Full corpus ~989 entries; split analyses:
  - **Pre-2015** (`EdShare_pre2015/`): pub_year ≤ 2014
  - **Post-2015** (`EdShare_post2015/`): pub_year ≥ 2015

```bash
# Full corpus (ingest + metrics)
Rscript datasets/EdShare/scripts/run_pipeline.R

# Period splits (reuse EdShare/raw/publications.json)
Rscript datasets/EdShare_pre2015/scripts/run_pipeline.R
Rscript datasets/EdShare_post2015/scripts/run_pipeline.R
```

## Outputs

- `raw/publications.json` — scraped bibliography records
- `processed/papers_authors.csv` — one row per author per paper
- `output/monopoly_metrics.csv` — HHI and top-x shares
