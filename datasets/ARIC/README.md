# ARIC — Authorship Monopoly Analysis

**Source:** [ARIC Published Manuscripts](https://aric.cscc.unc.edu/aric9/publications/published_manuscripts)

## Pipeline

```bash
Rscript datasets/ARIC/scripts/run_pipeline.R
```

## Author enrichment

The ARIC table lists only the first two authors per paper. Full author lists are fetched from **PubMed** using the PMID included in each row (~3,400 papers).

## Outputs

- `raw/publications.json` — scraped rows with PubMed-enriched authors
- `raw/pubmed_cache.json` — cached PubMed metadata for reruns
- `processed/papers_authors.csv` — one row per author per paper
- `output/monopoly_metrics.csv` — HHI and top-x shares
