# WLS — Authorship Concentration Analysis

**Dataset:** Wisconsin Longitudinal Study (WLS)
**Source:** [Zotero group library](https://www.zotero.org/groups/5400572/wisconsinlongitudinalstudy/items/7DFUY4LF/library)
**Parsed publications:** 1,006
**Status:** Initial pipeline run (June 2026)

---

## About WLS

The Wisconsin Longitudinal Study follows Wisconsin high school graduates (1957 cohort) and siblings across social, economic, and health domains. This analysis measures authorship concentration among publications catalogued in the WLS Zotero group library maintained by the study team.

---

## Source Details

| Field | Value |
|-------|-------|
| Source type | Zotero group API (public library) |
| Group ID | 5400572 |
| Collection URL | https://www.zotero.org/groups/5400572/wisconsinlongitudinalstudy/items/7DFUY4LF/library |
| Expected count | 1,006 items (June 2026) |
| Parsed publications | 1,006 |
| Year range | 1958–2026 |
| Last fetched | 2026-06-24 |

**Item types:** journalArticle (702), thesis (107), preprint (97), bookSection (60), book (15), presentation (14), report (9), manuscript (2).

Authors are extracted from Zotero `creators` metadata and normalized to `{LastName} {Initials}`. The full group library is fetched (not a subcollection).

---

## Pipeline

```bash
Rscript datasets/WLS/scripts/run_pipeline.R
```

Re-fetch after Zotero library updates:

```bash
Rscript scripts/R/fetch_wls_publications.R WLS
```

---

## Metrics (after initial-rule alias merge)

| Metric | Value |
|--------|-------|
| Papers | 1,006 |
| Unique authors | 1,650 (128 auto-aliases) |
| HHI | 0.046 |
| Top-1 share | **13.2%** (Hauser R M) |
| Top-3 share | **21.1%** |
| Top-5 share | 28.4% |
| Top-10 share | 35.5% |
| Top-20 share | 45.5% |

**Top authors:** Hauser R M (133), Sewell W H (59), Herd P (44), Carr D (42), Stephan Y (38).

**Comparison:** WLS is among the least concentrated datasets — top-1 (13%) and top-3 (21%) are above MIDUS (8%/19%) but well below MESA (17%/30%), NIH-AARP (43%/55%), REGARDS (39%/75%), and PROSPER (63%/80%). Expected for a long-running social science cohort with broad external use beyond a single PI team.

Figures: `output/figures/` (rank-frequency, top-x shares, HHI by year, papers by year, temporal trends, career spans).
