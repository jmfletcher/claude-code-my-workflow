# HRS — Authorship Monopoly Analysis

**Dataset:** Health and Retirement Study
**Source:** PubMed title/abstract name search (study bibliography behind Cloudflare)
**Funding:** NIA (NIH) — U01AG009740, confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The HRS bibliography at hrs.isr.umich.edu returns HTTP 403 (Cloudflare challenge) to
automated clients. Papers were acquired via a PubMed title/abstract name search and run
through the standard XML pipeline.

Query: `"Health and Retirement Study"[tiab]`

| Field | Value |
|-------|-------|
| PMIDs retrieved | 4,659 |
| Papers parsed | 4,652 |
| Unique authors (after auto-alias) | 6,916 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 4,652 |
| HHI | 0.015 |
| Top-1 share | 4.1% (Langa KM) |
| Top-3 share | 9.0% |
| Top-10 share | 14.7% |

**Top authors:** Langa KM (193), Glymour MM (117), Crimmins EM (114). HRS is a
public-use aging panel with very low authorship concentration — like Add Health and
NHATS, its broad research community means no single team dominates.

## Coverage note

The curated bibliography was inaccessible, so the PubMed name search is the source list
and the coverage ratio is 1.0 by construction. The caveat is query recall (papers not
naming HRS in the title/abstract are missed).

## Reproduce

```bash
scripts/run_pubmed_dataset.sh HRS
```
