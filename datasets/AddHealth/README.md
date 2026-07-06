# Add Health — Authorship Monopoly Analysis

**Dataset:** National Longitudinal Study of Adolescent to Adult Health (Add Health)
**Source:** PubMed title/abstract name search (study site JS-rendered)
**Funding:** NICHD / NIA (NIH) — P01HD31921, confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The Add Health publications page loads results through a client-side ajax search widget
with no server-rendered listing to scrape. Papers were acquired via a PubMed
title/abstract name search and run through the standard XML pipeline.

Query: `"Add Health"[tiab] OR "National Longitudinal Study of Adolescent Health"[tiab] OR
"National Longitudinal Study of Adolescent to Adult Health"[tiab]`

| Field | Value |
|-------|-------|
| PMIDs retrieved | 2,668 |
| Papers parsed | 2,664 |
| Unique authors (after auto-alias) | 4,012 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 2,664 |
| HHI | 0.013 |
| Top-1 share | 4.2% (Harris KM) |
| Top-3 share | 9.9% |
| Top-10 share | 16.8% |

**Top authors:** Harris KM (112), Halpern CT (104), Beaver KM (69), Gordon-Larsen P (56),
Kim J (49). Add Health is the **least concentrated** dataset measured — a public-use
social-science resource with an extremely broad author base. Kathleen Mullan Harris
(PI) leads but co-authors only ~4% of papers.

## Coverage note

The curated site could not be scraped, so the PubMed name search is the source list and
the coverage ratio is 1.0 by construction. The caveat is query recall: "Add Health" is a
common short phrase, so the query balances specificity (full study names) against recall.

## Reproduce

```bash
scripts/run_pubmed_dataset.sh AddHealth
```
