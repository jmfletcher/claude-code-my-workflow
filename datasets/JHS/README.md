# Jackson Heart Study — Authorship Monopoly Analysis

**Dataset:** Jackson Heart Study (JHS)
**Source:** PubMed title/abstract name search (study site JS-rendered)
**Funding:** NHLBI / NIMHD (NIH) — confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The JHS website is JS-rendered with no scrapable publication listing. Papers were
acquired via a PubMed title/abstract name search — very specific for this study — and
run through the standard XML pipeline.

Query: `"Jackson Heart Study"[tiab]`

| Field | Value |
|-------|-------|
| PMIDs retrieved | 662 |
| Papers parsed | 657 |
| Unique authors (after auto-alias) | 2,663 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 657 |
| HHI | 0.342 |
| Top-1 share | 27.2% (Sims M) |
| Top-3 share | 57.1% |
| Top-10 share | 72.6% |

**Top authors:** Sims M (179), Correa A (134), Taylor HA (115). A single-site cohort
with a small core team (Sims, Correa, Taylor — all JHS leadership) driving a majority of
papers: high concentration, similar in shape to other single-center cohorts (CHS, HCHS/SOL).

## Coverage note

The site could not be scraped, so the PubMed name search is the source list and the
coverage ratio is 1.0 by construction. "Jackson Heart Study" is a distinctive phrase, so
query recall is expected to be high.

## Reproduce

```bash
scripts/run_pubmed_dataset.sh JHS
```
