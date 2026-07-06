# BLSA — Authorship Monopoly Analysis

**Dataset:** Baltimore Longitudinal Study of Aging
**Source:** PubMed title/abstract name search
**Funding:** NIA (NIH, intramural) — confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The BLSA (blsa.nih.gov) has no scrapable bibliography. Papers were acquired via a PubMed
title/abstract name search (a distinctive phrase) and run through the standard XML pipeline.

Query: `"Baltimore Longitudinal Study of Aging"[tiab]`

| Field | Value |
|-------|-------|
| PMIDs retrieved | 822 |
| Papers parsed | 821 |
| Unique authors (after auto-alias) | 1,578 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 821 |
| HHI | 0.513 |
| Top-1 share | 47.6% (Ferrucci L) |
| Top-3 share | 65.8% |
| Top-10 share | 77.5% |

**Top authors:** Ferrucci L (391), Resnick SM (241), Simonsick EM (173). As an NIA
intramural study, BLSA is **highly concentrated** — Luigi Ferrucci (NIA scientific
director) is on ~48% of papers, reflecting centralized intramural leadership.

## Coverage note

Acquired via PubMed name search (source = search), so the coverage ratio is 1.0 by
construction. The full study name is distinctive, so recall is expected to be high.

## Reproduce

```bash
scripts/run_pubmed_dataset.sh BLSA
```
