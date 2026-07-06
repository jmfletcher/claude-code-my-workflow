# HCHS/SOL — Authorship Monopoly Analysis

**Dataset:** Hispanic Community Health Study / Study of Latinos
**Source:** [HCHS/SOL publications](https://sites9.cscc.unc.edu/hchs/res-publications)
**Funding:** NHLBI + NIMHD (NIH) — confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The study website lists each manuscript with a PubMed ID. We scrape all PMIDs
(`fetch_hchs_sol_pmids.R`), then reuse the PubMed XML pipeline
(`fetch_pubmed_collection.R` → `parse_pubmed_xml.R`) for authoritative author data.
This avoids fragile citation-string parsing.

| Field | Value |
|-------|-------|
| Curated PMIDs scraped | 642 |
| PubMed records fetched | 642 (100%) |
| Papers with abstract | 637 |
| Unique authors (after auto-alias) | 2,494 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 642 |
| HHI (author paper-share) | 1.374 |
| Top-1 share | 56.4% (Daviglus ML) |
| Top-3 share | 79.0% |
| Top-5 share | 85.2% |
| Top-10 share | 91.0% |

HHI > 1 reflects author-level paper-shares on heavily multi-authored papers (a
handful of core investigators appear on most manuscripts). Top-x share stays in [0,1].

**Top authors:** Daviglus ML (362), Gallo LC (249), Kaplan RC (212), Isasi CR (204),
Sotres-Alvarez D (197). HCHS/SOL is highly concentrated — the coordinating-center
investigators co-author the large majority of papers.

## Coverage estimate

| Quantity | Count |
|----------|------:|
| Curated list (PMID) | 642 |
| Broad PubMed query hits | 738 |
| Overlap | 570 |
| On list, missed by query | 72 |
| In literature, not on list | 168 |
| PMID union | 810 |
| **Curated list covers** | **~79% of the union** |

Query: `"Hispanic Community Health Study"[tiab] OR "Study of Latinos"[tiab]`. The
curated list is fairly complete but misses ~168 externally-indexed papers; ~72 curated
papers don't match the text query (title/abstract phrasing differs). Concentration
metrics here are computed on the curated list.

## Reproduce

```bash
Rscript scripts/R/fetch_hchs_sol_pmids.R HCHS_SOL
Rscript scripts/R/fetch_pubmed_collection.R HCHS_SOL
Rscript scripts/R/parse_pubmed_xml.R HCHS_SOL
Rscript scripts/R/extract_paper_metadata.R HCHS_SOL
Rscript scripts/R/apply_author_aliases.R HCHS_SOL
Rscript scripts/R/compute_monopoly_metrics.R HCHS_SOL
Rscript scripts/R/plot_monopoly_figures.R HCHS_SOL
Rscript scripts/R/analyze_temporal_concentration.R HCHS_SOL
Rscript scripts/R/analyze_domain_concentration.R HCHS_SOL
Rscript scripts/R/plot_extended_analysis.R HCHS_SOL
Rscript scripts/R/estimate_coverage.R HCHS_SOL
```
