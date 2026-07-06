# FFCWS — Authorship Concentration Analysis

**Dataset:** Future of Families and Child Wellbeing Study (Fragile Families)
**Source:** [FFCWS publications catalog](https://ffcws.princeton.edu/publications)
**Parsed publications:** 1,710 (from 1,723 scraped records)
**Status:** Pipeline complete (June 2026)

---

## About FFCWS

The Future of Families and Child Wellbeing Study (formerly Fragile Families & Child Wellbeing Study) follows a birth cohort of ~5,000 children born in large U.S. cities (1998–2000) and their parents. This analysis measures authorship concentration among publications catalogued on the study website.

---

## Source Details

| Field | Value |
|-------|-------|
| Source type | Drupal bibcite HTML (sitemap + per-record pages) |
| Ingest script | `scripts/ffcws/ingest_publications.py` (curl_cffi + Cloudflare bypass) |
| Parse script | `scripts/R/fetch_ffcws_publications.R` |
| Scraped records | 1,723 |
| Parsed for metrics | 1,710 (13 duplicate titles removed) |
| Year range | 1998–2026 |
| Last fetched | 2026-06-24 |

---

## Pipeline

```bash
# Full pipeline (parse raw JSON → metrics → figures)
Rscript datasets/FFCWS/scripts/run_pipeline.R
```

Re-scrape from website (~15 min):

```bash
python scripts/ffcws/ingest_publications.py
Rscript datasets/FFCWS/scripts/run_pipeline.R
```

---

## Metrics (after initial-rule alias merge)

| Metric | Value |
|--------|-------|
| Papers | 1,710 |
| Unique authors | 1,771 (39 auto-aliases) |
| HHI | 0.024 |
| Top-1 share | **7.2%** (McLanahan S) |
| Top-3 share | **13.2%** |
| Top-5 share | 17.8% |
| Top-10 share | 26.3% |
| Top-20 share | 34.3% |

**Top authors:** McLanahan S (123), Brooks-Gunn J (83), Reichman N (67), CRCFW (61), Garfinkel I (53).

**Note:** `CRCFW` is an institutional author string from the study center — appears on 61 records and ranks 4th on top-1; consider a manual alias merge if center authorship should be distributed.

**Comparison:** FFCWS is the least concentrated dataset in the project — top-1 (7%) below MIDUS (8%) and WLS (13%), and far below REGARDS (39%) or PROSPER (63%). Broad external use of a major social-policy cohort.

Figures: `output/figures/`.

---

## Raw Files

| File | Description |
|------|-------------|
| `raw/publications.json` | Full structured records from ingest |
| `raw/publications.csv` | Flat export |
| `raw/ffcws_publications.csv` | Parsed pipeline input |
| `raw/summary.json` | Scrape metadata |
