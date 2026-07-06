# NIH-AARP — Authorship Concentration Analysis

**Dataset:** NIH-AARP Diet and Health Study
**Source:** [PubMed collection 62019178](https://pubmed.ncbi.nlm.nih.gov/collections/62019178/?sort=pubdate)
**Parsed papers:** 459
**Status:** Initial pipeline run (June 2026)

---

## About NIH-AARP

The NIH-AARP Diet and Health Study is a prospective cohort of AARP members aged 50–71 examining diet, lifestyle, and cancer/mortality outcomes. This analysis measures authorship concentration among papers in the curated PubMed collection maintained for the study.

---

## Source Details

| Field | Value |
|-------|-------|
| Collection ID | 62019178 |
| Collection URL | https://pubmed.ncbi.nlm.nih.gov/collections/62019178/?sort=pubdate |
| Expected count | 459 papers (June 2026) |
| Fetch method | Automated pagination scrape of public PubMed collection pages |
| Parsed papers | 459 |
| Year range | 1997–2024 |
| Last fetched | 2026-06-24 |

Unlike private My NCBI collections, this public PubMed collection supports automated PMID extraction via paginated HTML (`data-article-id` attributes). PMIDs are cached in `raw/pmid_list.csv`.

---

## Pipeline

```bash
Rscript datasets/NIH_AARP/scripts/run_pipeline.R
```

Re-fetch PMID list (if collection updated):

```bash
rm datasets/NIH_AARP/raw/pmid_list.csv
Rscript scripts/R/fetch_collection_pmids.R NIH_AARP
```

---

## Metrics (after initial-rule alias merge)

| Metric | Value |
|--------|-------|
| Papers | 459 |
| Unique authors | 1,217 (92 auto-aliases) |
| HHI | 0.611 |
| Top-1 share | **42.5%** (Hollenbeck A R) |
| Top-3 share | **54.7%** |
| Top-5 share | 61.7% |
| Top-10 share | 79.7% |
| Top-20 share | 84.3% |

**Top authors:** Hollenbeck A R (195), Park Y (141), Schatzkin A (132), Freedman N D (76), Leitzmann M F (75).

**Comparison:** Moderately concentrated — top-1 (43%) sits between MESA (17%) and REGARDS (39%). Core NCI investigators (Hollenbeck, Park, Schatzkin) dominate but with more co-author breadth than PROSPER (63% top-1).

Figures: `output/figures/` (rank-frequency, top-x shares, HHI by year, papers by year, temporal trends, career spans).
