# HPFS — Authorship Monopoly Analysis

**Dataset:** Health Professionals Follow-up Study
**Source:** PubMed title/abstract name search (study site lists selected papers only)
**Funding:** NCI (NIH) — U01CA167552, confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

Like its sister cohort NHS, the HPFS site posts only selected publications. Papers were
acquired via a PubMed title/abstract name search and run through the standard XML pipeline.

Query: `"Health Professionals Follow-up Study"[tiab] OR "Health Professionals Follow up Study"[tiab]`

| Field | Value |
|-------|-------|
| PMIDs retrieved | 1,385 |
| Papers parsed | 1,384 |
| Unique authors (after auto-alias) | 1,933 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 1,384 |
| HHI | 0.621 |
| Top-1 share | 41.6% (Giovannucci EL) |
| Top-3 share | 68.9% |
| Top-10 share | 77.7% |

**Top authors:** Giovannucci EL (576), Willett WC (438), Rimm EB (326). HPFS is
**highly concentrated** — the same Harvard nutrition group that runs NHS co-authors the
large majority of HPFS papers, with Giovannucci alone on ~42%.

## Coverage note

The study site is a curated subset, so the PubMed name search is the source and the
coverage ratio is 1.0 by construction. Query recall is the caveat.

## Reproduce

```bash
scripts/run_pubmed_dataset.sh HPFS
```
