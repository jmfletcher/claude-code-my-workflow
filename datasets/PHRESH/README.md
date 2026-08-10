# PHRESH — Authorship Monopoly Analysis

**Dataset:** Pittsburgh Hill/Homewood Research on Neighborhood Change and Health (PHRESH)
**Source:** PubMed title/abstract name search + NIH grant numbers (tiab-filtered)
**Funding:** NCI / NHLBI / NIA (NIH) — confirmed
**Status:** Complete (2026-08-10)

---

## Source & method

PHRESH (Pitt SPH / RAND) has no scrapable exhaustive bibliography. Papers were
acquired via a PubMed search combining distinctive study-name phrases with core
NIH grant numbers, with title/abstract filters on grant hits to exclude unrelated
co-citations. Includes Think PHRESH and PHRESH Zzz extensions of the same cohort
infrastructure.

Query (see `config.yaml` `source.entrez_query`): Pittsburgh Hill/Homewood /
Think PHRESH / PHRESH Zzz / PHRESH+Pittsburgh terms, plus grants CA149105,
CA164137, HL122460, HL131531, AG072652 intersected with PHRESH/Pittsburgh/
Homewood/Dubowitz/Hill District/food desert tiab terms.

| Field | Value |
|-------|-------|
| PMIDs retrieved | 56 |
| Papers parsed | 56 |
| Unique authors (after auto-alias) | 80 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 56 |
| HHI | 2.50 |
| Top-1 share | 100% (Dubowitz T) |
| Top-3 share | 100% |
| Top-10 share | 100% |

**Top authors:** Dubowitz T (56), Troxel WM (29), Hunter GP (25), Beckman R (24),
Collins RL (22). Extremely concentrated: Tamara Dubowitz co-authors every paper in
this PubMed set — typical of a community-partnered, PI-led single-site cohort with
a stable RAND/Pitt core team.

## Coverage note

Acquired via PubMed name + grant search (source = search), so the coverage ratio
is 1.0 by construction. Grant-only hits without Pittsburgh/PHRESH tiab markers
were excluded to reduce false positives from shared-grant co-citations.

Domain (TF-IDF) analysis was skipped in this run (`tm` R package not installed).

## Reproduce

```bash
scripts/run_pubmed_dataset.sh PHRESH
```
