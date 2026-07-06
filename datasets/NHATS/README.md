# NHATS — Authorship Monopoly Analysis

**Dataset:** National Health and Aging Trends Study
**Source:** [NHATS publications](https://www.nhats.org/publications/search) (paginated cards)
**Funding:** NIA (NIH) — U01AG032947, confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The NHATS site lists publications as cards exposing author list, title, year, and DOI.
`fetch_nhats_publications.R` paginates the search (100/page), parses Vancouver-style
authors, and records DOIs. No PubMed IDs are exposed, so metrics use the citation list.

| Field | Value |
|-------|-------|
| Publications parsed | 1,162 |
| Author rows | 5,245 |
| Unique authors (after auto-alias) | 2,006 |
| Year range | 2011–2025 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 1,162 |
| HHI | 0.039 |
| Top-1 share | 6.3% (Wolff JL) |
| Top-3 share | 15.2% |
| Top-10 share | 25.7% |

**Top authors:** Wolff JL (73), Freedman VA (72), Ornstein KA (54), Kasper JD (49),
Ehrlich JR (40). NHATS is a **low-concentration** cohort — a public-use aging dataset
with a broad, dispersed author base, in sharp contrast to intramural cohorts like the
Sister Study. Freedman and Kasper are the NHATS PIs but co-author well under 10% each.

## Coverage estimate

| Quantity | Count |
|----------|------:|
| Curated list (citations) | 1,162 |
| Broad PubMed query hits | 1,002 |

Query: `"National Health and Aging Trends Study"[tiab] OR "NHATS"[tiab]`. The curated list
is citation-only (no PMIDs), so PMID overlap can't be computed; the curated list
(1,162) is larger than the name-based PubMed query (1,002), indicating it is at least
as comprehensive as a title/abstract search.

## Reproduce

```bash
Rscript scripts/R/fetch_nhats_publications.R NHATS
Rscript scripts/R/apply_author_aliases.R NHATS
Rscript scripts/R/compute_monopoly_metrics.R NHATS
Rscript scripts/R/plot_monopoly_figures.R NHATS
Rscript scripts/R/analyze_temporal_concentration.R NHATS
Rscript scripts/R/analyze_domain_concentration.R NHATS
Rscript scripts/R/plot_extended_analysis.R NHATS
Rscript scripts/R/estimate_coverage.R NHATS
```
