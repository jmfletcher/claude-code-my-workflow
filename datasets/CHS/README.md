# CHS — Authorship Monopoly Analysis

**Dataset:** Cardiovascular Health Study
**Source:** [CHS bibliography](https://chs-nhlbi.org/CurrentBibliography) (docx, n=2,315)
**Funding:** NHLBI (NIH) — confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The CHS coordinating center posts a Word-format bibliography where most entries end
with `PM:{PMID}`. We extract those PMIDs (`fetch_chs_pmids.R`) and reuse the PubMed
XML pipeline for authoritative author data.

| Field | Value |
|-------|-------|
| Bibliography entries | 2,315 |
| PMIDs extracted | 1,866 (81%) |
| PubMed records fetched | 1,866 (100%) |
| Papers with abstract | 1,839 |
| Unique authors (after auto-alias) | 10,052 |

~449 entries lacked a `PM:` tag (older/preprint/errata) and are excluded.

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 1,866 |
| HHI | 0.762 |
| Top-1 share | 35.6% (Psaty BM) |
| Top-3 share | 58.2% |
| Top-10 share | 71.2% |

**Top authors:** Psaty BM (665), Siscovick DS (361), Newman AB (304), Rotter JI (294),
Tracy RP (232). Bruce Psaty co-authors over a third of all CHS papers — a strongly
concentrated coordinating-center cohort.

**Domain (k=8):** dementia/cognition (HHI 1.74) and sleep (1.38) are most concentrated;
the large CVD/stroke/mortality cluster (1,119 papers) is broader (HHI 0.41).

## Coverage estimate

| Quantity | Count |
|----------|------:|
| Curated list (PMID) | 1,866 |
| Broad PubMed query hits | 2,018 |
| Overlap | 1,064 |
| On list, missed by query | 802 |
| In literature, not on list | 954 |
| PMID union | 2,820 |
| **Curated list covers** | **~66% of the union** |

Query: `"Cardiovascular Health Study"[tiab]`. Many CHS papers don't put the study name
in title/abstract (802 curated papers missed by the query), and consortium/GWAS papers
that mention CHS aren't on the curated list (954). The curated docx remains the best
single-source list; metrics are computed on it.

## Reproduce

```bash
Rscript scripts/R/fetch_chs_pmids.R CHS
Rscript scripts/R/fetch_pubmed_collection.R CHS
Rscript scripts/R/parse_pubmed_xml.R CHS
Rscript scripts/R/extract_paper_metadata.R CHS
Rscript scripts/R/apply_author_aliases.R CHS
Rscript scripts/R/compute_monopoly_metrics.R CHS
Rscript scripts/R/plot_monopoly_figures.R CHS
Rscript scripts/R/analyze_temporal_concentration.R CHS
Rscript scripts/R/analyze_domain_concentration.R CHS
Rscript scripts/R/plot_extended_analysis.R CHS
Rscript scripts/R/estimate_coverage.R CHS
```
