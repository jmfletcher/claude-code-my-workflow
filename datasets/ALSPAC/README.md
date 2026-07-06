# ALSPAC — Authorship Monopoly Analysis

**Source:** [ALSPAC publications index](https://www.bristol.ac.uk/alspac/researchers/publications/) (University of Bristol)

## Pipeline

```bash
# Full pipeline (scrape + enrich + metrics + figures)
Rscript datasets/ALSPAC/scripts/run_pipeline.R

# Scrape only (with et al enrichment via Crossref/PubMed)
.venv-ffcws/bin/python scripts/alspac/ingest_publications.py
```

## Author enrichment

Listings that use "et al." are enriched automatically:

1. Crossref lookup by DOI
2. PubMed lookup by DOI
3. PubMed title (+ year) search
4. Crossref bibliographic search

Partial listings are kept only when all enrichment steps fail.

## Outputs

- `raw/publications.json` — scraped records with full author lists
- `raw/enrichment_cache.json` — Crossref/PubMed cache for reruns
- `processed/papers_authors.csv` — one row per author per paper
- `output/monopoly_metrics.csv` — HHI and top-x shares
