# Strong Heart Study — Authorship Monopoly Analysis

**Dataset:** Strong Heart Study
**Source:** PubMed title/abstract name search
**Funding:** NHLBI (NIH) — confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The Strong Heart Study site has no readily scrapable publication list. Papers were
acquired via a PubMed title/abstract name search (a distinctive phrase) and run through
the standard XML pipeline.

Query: `"Strong Heart Study"[tiab]`

| Field | Value |
|-------|-------|
| PMIDs retrieved | 373 |
| Papers parsed | 371 |
| Unique authors (after auto-alias) | 780 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 371 |
| HHI | 1.30 |
| Top-1 share | 58.8% (Howard BV) |
| Top-3 share | 67.7% |
| Top-10 share | 90.0% |

**Top authors:** Howard BV (218), Lee ET (172), Devereux RB (134). One of the most
concentrated cohorts measured: Barbara Howard co-authors nearly 60% of Strong Heart
papers, typical of a single-site cohort with a small, stable leadership team.

## Coverage note

Acquired via PubMed name search (source = search), so the coverage ratio is 1.0 by
construction. "Strong Heart Study" is distinctive, so recall is expected to be high.

## Reproduce

```bash
scripts/run_pubmed_dataset.sh StrongHeart
```
