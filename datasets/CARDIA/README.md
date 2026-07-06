# CARDIA — Authorship Monopoly Analysis

**Source:** [CARDIA Zenodo community](https://zenodo.org/communities/cardia-cc/records) (`cardia-cc`)

## Pipeline

```bash
Rscript datasets/CARDIA/scripts/run_pipeline.R
```

## Notes

- Zenodo REST API provides structured metadata with **full author lists** (no et al truncation).
- Community is curated by the CARDIA Coordinating Center ([UAB CARDIA site](https://sites.uab.edu/cardia/)).
- ~1,366 records as of 2026 (mostly journal articles, 1987–2025).

## Outputs

- `raw/publications.json` — Zenodo API dump
- `processed/papers_authors.csv` — one row per author per paper
- `output/monopoly_metrics.csv` — HHI and top-x shares
