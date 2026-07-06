# ADNI — Authorship Monopoly Analysis

**Dataset:** Alzheimer's Disease Neuroimaging Initiative
**Source:** [ADNI publications table](https://adni.loni.usc.edu/news-publications/publications/)
**Funding:** NIA (NIH) — U19AG024904, confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The ADNI publications page is a server-side paginated table (10 rows/page, ~642 pages)
listing Year, Title, Author, Journal. `fetch_adni_publications.R` scrapes all pages;
`rebuild_adni_authors.R` parses the two author formats the site mixes: initials-first
semicolon lists (`D. J. Terstege; Y. Ren; ...`) and last-first comma lists with full or
abbreviated given names (`Chen, Q, Abrigo, J and Chu, WCW`). Consortium "authors"
(e.g. "Alzheimer's Disease Neuroimaging Initiative") are dropped.

| Field | Value |
|-------|-------|
| Publications scraped | 5,415 |
| Papers with parsed authors | 5,332 (98%) |
| Author rows | 42,436 |
| Unique authors (after auto-alias) | 13,596 |
| Year range | 2005–2025 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 5,332 |
| HHI | 0.023 |
| Top-1 share | 2.7% (Saykin AJ) |
| Top-3 share | 6.7% |
| Top-10 share | 15.3% |

**Top authors:** Saykin AJ (145), Weiner MW (142), Wang Y (134), Thompson PM (121),
Jack CR (93). ADNI is a **low-concentration** open neuroimaging consortium: its core
leadership (Weiner is the ADNI PI; Saykin, Jack, Thompson are site/core leads) each
appear on well under 3% of papers, and thousands of secondary-analysis groups use the
public data. (Note: single-initial surnames like "Wang Y" over-merge distinct authors,
a general limitation of initial-based disambiguation.)

## Coverage estimate

| Quantity | Count |
|----------|------:|
| Curated list (scraped) | 5,332 |
| Broad PubMed query hits | 5,365 |

Query: `"Alzheimer's Disease Neuroimaging Initiative"[tiab] OR "ADNI"[tiab]`. The scraped
list is citation-only (no PMIDs), so PMID overlap can't be computed, but the curated
table (5,332) and the name-based PubMed search (5,365) are almost identical in size —
strong evidence the ADNI table is comprehensive.

## Reproduce

```bash
Rscript scripts/R/fetch_adni_publications.R ADNI
Rscript scripts/R/rebuild_adni_authors.R
Rscript scripts/R/apply_author_aliases.R ADNI
Rscript scripts/R/compute_monopoly_metrics.R ADNI
Rscript scripts/R/plot_monopoly_figures.R ADNI
Rscript scripts/R/analyze_temporal_concentration.R ADNI
Rscript scripts/R/analyze_domain_concentration.R ADNI
Rscript scripts/R/plot_extended_analysis.R ADNI
Rscript scripts/R/estimate_coverage.R ADNI
```
