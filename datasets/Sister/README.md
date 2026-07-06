# Sister Study — Authorship Monopoly Analysis

**Dataset:** Sister Study (NIEHS)
**Source:** [Sister Study articles](https://sisterstudy.niehs.nih.gov/English/articles.htm)
**Funding:** NIEHS (NIH) — intramural, confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The NIEHS articles page lists Vancouver-style citations inside `<li>` elements; only a
handful carry PubMed links. `fetch_sister_publications.R` extracts each citation and
parses authors directly. Author lists truncated with an ellipsis on the page lose their
middle authors (a small number of entries), which slightly understates co-authorship
breadth but not the dominant core authors.

| Field | Value |
|-------|-------|
| Citations parsed | 393 |
| Author rows | 5,328 |
| Unique authors (after auto-alias) | 1,553 |
| Year range | 2007–2026 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 393 |
| HHI | 1.43 (raw sum of squared shares; exceeds 1 because papers are multi-authored and shares are per-author, not partitioned) |
| Top-1 share | 88.8% (Sandler DP) |
| Top-3 share | 93.4% |
| Top-10 share | 97.2% |

**Top authors:** Sandler DP (349), O'Brien KM (140), Weinberg CR (130), Taylor JA (101),
White AJ (74). The Sister Study is the **most concentrated** cohort measured so far:
PI Dale Sandler co-authors ~89% of all listed papers, reflecting a tightly controlled
NIEHS intramural cohort with centralized data access.

## Coverage estimate

| Quantity | Count |
|----------|------:|
| Curated list (citations) | 393 |
| Broad PubMed query hits | 199 |

Query: `"Sister Study"[tiab] AND (breast OR cancer OR environ*)`. The curated list is
citation-only (no PMIDs), so PMID overlap can't be computed. The curated list (393) is
substantially larger than the name-based PubMed query (199) — many Sister Study papers
do not put the study name in the title/abstract — so the study's own list is the more
comprehensive source and is used for metrics.

## Reproduce

```bash
Rscript scripts/R/fetch_sister_publications.R Sister
Rscript scripts/R/apply_author_aliases.R Sister
Rscript scripts/R/compute_monopoly_metrics.R Sister
Rscript scripts/R/plot_monopoly_figures.R Sister
Rscript scripts/R/analyze_temporal_concentration.R Sister
Rscript scripts/R/analyze_domain_concentration.R Sister
Rscript scripts/R/plot_extended_analysis.R Sister
Rscript scripts/R/estimate_coverage.R Sister
```
