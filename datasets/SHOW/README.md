# SHOW — Authorship Concentration Analysis

**Dataset:** Survey of the Health of Wisconsin (SHOW)
**Source:** [REACH research publications](https://reach.med.wisc.edu/research/#publications) (curated CSV with complete author lists)
**Parsed publications:** 123
**Status:** Pipeline complete (June 2026)

---

## About SHOW

SHOW is a statewide population health examination survey linking clinical, physical, and survey data for Wisconsin residents, housed at UW-Madison REACH. This analysis measures authorship concentration among publications listed on the REACH publications page, using a manually curated CSV with verified author metadata.

---

## Source Details

| Field | Value |
|-------|-------|
| Source type | Curated CSV (`reach_publications_complete_authors.csv`) |
| Collection URL | https://reach.med.wisc.edu/research/#publications |
| CSV rows | 131 (8 flagged duplicates excluded) |
| Parsed publications | 123 |
| With complete author lists | 120 (+ 1 corporate author) |
| Year range | 2010–2026 |
| Last fetched | 2026-06-24 |

Author strings in the CSV use full names (`F Javier Nieto`); the pipeline normalizes to project standard (`Nieto FJ`).

---

## Pipeline

```bash
Rscript datasets/SHOW/scripts/run_pipeline.R
```

To refresh after updating the CSV in `raw/`:

```bash
Rscript scripts/R/fetch_show_publications.R SHOW
Rscript datasets/SHOW/scripts/run_pipeline.R
```

---

## Metrics (after initial-rule alias merge)

| Metric | Value |
|--------|-------|
| Papers | 123 |
| Unique authors | 339 (36 auto-aliases) |
| HHI | 0.796 |
| Top-1 share | **66.7%** (Malecki K) |
| Top-3 share | **74.0%** |
| Top-5 share | 78.1% |
| Top-10 share | 81.3% |
| Top-20 share | 85.4% |

**Top authors:** Malecki K (82), Schultz A A (35), Peppard P E (30), Nieto F J (24), Walsh M C (18).

**Comparison:** SHOW is the **most concentrated** dataset in the project on top-1 share (67%) — above PROSPER (63%) and REGARDS (39%). Malecki K appears on two-thirds of all SHOW papers, reflecting central infrastructure/PI role for a state survey platform with a smaller publication corpus than national cohorts.

Figures: `output/figures/`.

---

## Raw Files

| File | Description |
|------|-------------|
| `raw/reach_publications_complete_authors.csv` | Source CSV with full author lists |
| `raw/show_publications.csv` | Parsed pipeline input |
| `raw/pubmed_manifest.csv` | Paper manifest |
