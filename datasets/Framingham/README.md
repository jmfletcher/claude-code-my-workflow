# Framingham Heart Study — Authorship Monopoly Analysis

**Dataset:** Framingham Heart Study
**Source:** [FHS bibliography](https://www.framinghamheartstudy.org/fhs-bibliography/) (by-year pages)
**Funding:** NHLBI (NIH) — contract 75N92019D00031, confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The FHS bibliography is spread across decade and per-year pages; entries carry a PubMed
link and/or `PubMed PMID/number:` text. `fetch_framingham_pmids.R` crawls all
bibliography pages (1950s–2025) and harvests PMIDs, which then feed the PubMed XML
pipeline for authoritative author data.

| Field | Value |
|-------|-------|
| PMIDs harvested | 4,535 |
| PubMed records fetched | 4,535 (100%) |
| Papers parsed | 4,523 |
| Papers with abstract | 4,201 |
| Unique authors (after auto-alias) | 16,127 |
| Year range | 1951–2026 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 4,523 |
| HHI | 0.365 |
| Top-1 share | 19.4% (Vasan RS) |
| Top-3 share | 35.4% |
| Top-10 share | 67.4% |

**Top authors:** Vasan RS (878), Levy D (762), Benjamin EJ (586), Larson MG (525),
Kannel WB (475). Multi-generational succession is visible in career spans: Kannel
(1969–2014) and Wilson (1980–2025) overlap with the current-era leaders Vasan
(1995–2026) and Seshadri (1997–2026). Moderate concentration for a very large,
70-year cohort.

**Domain (k=8):** the genetics/GWAS cluster (1,190 papers) is most concentrated
(HHI 1.95); the large core CVD cluster (3,174 papers) is broad (HHI 0.25).

## Coverage estimate

| Quantity | Count |
|----------|------:|
| Curated list (PMID) | 4,535 |
| Broad PubMed query hits | 4,609 |
| Overlap | 2,864 |
| On list, missed by query | 1,671 |
| In literature, not on list | 1,745 |
| PMID union | 6,280 |
| **Curated list covers** | **~72% of the union** |

Query: `"Framingham Heart Study"[tiab] OR "Framingham Study"[tiab] OR "Framingham
Offspring"[tiab]`. The by-year bibliography and the name-based search are close in size
but only partially overlap: 1,671 curated papers don't name Framingham in the
title/abstract, and 1,745 papers mention Framingham without being on the curated list
(often consortium/GWAS meta-analyses). Metrics use the curated bibliography.

## Reproduce

```bash
Rscript scripts/R/fetch_framingham_pmids.R Framingham
Rscript scripts/R/fetch_pubmed_collection.R Framingham
Rscript scripts/R/parse_pubmed_xml.R Framingham
Rscript scripts/R/extract_paper_metadata.R Framingham
Rscript scripts/R/apply_author_aliases.R Framingham
Rscript scripts/R/compute_monopoly_metrics.R Framingham
Rscript scripts/R/plot_monopoly_figures.R Framingham
Rscript scripts/R/analyze_temporal_concentration.R Framingham
Rscript scripts/R/analyze_domain_concentration.R Framingham
Rscript scripts/R/plot_extended_analysis.R Framingham
Rscript scripts/R/estimate_coverage.R Framingham
```
