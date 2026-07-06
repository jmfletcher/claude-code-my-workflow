# Nurses' Health Study — Authorship Monopoly Analysis

**Dataset:** Nurses' Health Study (NHS/NHSII)
**Source:** PubMed title/abstract name search (study site lists selected papers only)
**Funding:** NCI / NHLBI (NIH) — UM1CA186107, confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The NHS website posts only a selected/highlighted subset of publications, so a curated
scrape would understate the literature. Papers were acquired via a PubMed
title/abstract name search and run through the standard XML pipeline.

Query: `"Nurses' Health Study"[tiab]`

| Field | Value |
|-------|-------|
| PMIDs retrieved | 3,453 |
| Papers parsed | 3,450 |
| Unique authors (after auto-alias) | 4,102 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 3,450 |
| HHI | 0.291 |
| Top-1 share | 24.7% (Willett WC) |
| Top-3 share | 41.9% |
| Top-10 share | 64.2% |

**Top authors:** Willett WC (851), Hu FB (572), Giovannucci EL (475). The Harvard
nutritional-epidemiology group (Willett and successors) anchors a quarter of all NHS
papers — high concentration for a cohort of this size, driven by a centralized
investigator team rather than the cohort's scale.

## Coverage note

The study site is a curated subset, so the PubMed name search is used as the source and
the coverage ratio is 1.0 by construction. Query recall is the caveat.

## Reproduce

```bash
scripts/run_pubmed_dataset.sh NHS
```
