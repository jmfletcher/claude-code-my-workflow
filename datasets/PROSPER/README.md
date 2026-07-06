# PROSPER — Authorship Concentration Analysis (Top-x Focus)

**Dataset:** PROSPER (Promoting School-University Partnerships to Enhance Resilience)
**Source:** [PPSI publications search](https://drupal.ppsi.iastate.edu/publications?search=prosper&page=0) + ISU project bibliographies + PSU project pages
**Parsed papers:** 259 (deduplicated full PPSI/PSU corpus)
**Status:** Full corpus pipeline run (June 2026)

---

## Source Details

| Field | Value |
|-------|-------|
| Source type | ISU PPSI Drupal biblio HTML + PSU prevention.psu.edu project pages |
| Primary corpus | PPSI `?search=prosper` index (260 unique entries; 259 after title dedup) |
| Supplemental | Follow-up, Project-Family, AI-Support, G×E, economic analysis, capacity-building (ISU); PROSPER III + rural PA program (PSU) |
| Year range | 1993–2019 |
| HHI computed | No (top-x focus) |

Publications are scraped from PPSI biblio HTML (`views-field-citation` on project pages; `biblio-authors` on the publications index). Author strings are normalized from biblio format (`Last, F. M.`) to project standard (`Last FM`). Downloads require a browser user-agent (automated in `fetch_prosper_publications.R`).

**Dedup:** Title-key normalization merges overlapping entries across sources (756 raw blocks → 259 unique papers). PSU project pages add no unique papers beyond PPSI but are included for completeness.

---

## Pipeline

```bash
Rscript datasets/PROSPER/scripts/run_pipeline.R
```

Re-fetch after source updates:

```bash
Rscript scripts/R/fetch_prosper_publications.R PROSPER
```

Cached HTML: `raw/ppsi_prosper_search.html` plus per-project fetches.

---

## Metrics (after initial-rule alias merge)

| Metric | Value |
|--------|-------|
| Papers | 259 |
| Unique authors | 193 (14 auto-aliases) |
| Top-1 share | **63.3%** (Spoth R) |
| Top-3 share | **80.3%** |
| Top-5 share | 83.8% |
| Top-10 share | 88.0% |
| Top-20 share | 91.9% |

**Top authors:** Spoth R (164), Redmond C (72), Feinberg M E (69), Greenberg M T (52), Shin C (40).

**Comparison:** PROSPER is the most concentrated dataset in the project so far — top-1 (63%) and top-3 (80%) exceed REGARDS (39% top-1, 75% top-3, 90% top-10), MIDUS (19%), and MESA (30%). Expected given a focused prevention-research team (PSU + ISU core investigators) spanning the full program history.

Figures: `output/figures/` (rank-frequency, top-x shares, top-x by year, papers by year, temporal trends, career spans).
