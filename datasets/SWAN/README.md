# SWAN — Authorship Monopoly Analysis

**Dataset:** Study of Women's Health Across the Nation (SWAN)
**Source:** PubMed title/abstract name search (study site not scrapable)
**Funding:** NIA / NINR / ORWH (NIH) — confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The SWAN publications page did not return a scrapable listing (server errors / JS). Papers
were acquired via a PubMed title/abstract name search and run through the standard XML
pipeline.

Query: `"Study of Women's Health Across the Nation"[tiab]`

| Field | Value |
|-------|-------|
| PMIDs retrieved | 709 |
| Papers parsed | 707 |
| Unique authors (after auto-alias) | 943 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 707 |
| HHI | 0.409 |
| Top-1 share | 22.9% (Matthews KA) |
| Top-3 share | 52.8% |
| Top-10 share | 75.5% |

**Top authors:** Matthews KA (162), Greendale GA (139), Harlow SD (129). A tightly-knit
multi-site cohort where the founding investigators co-author a majority of papers — high
concentration comparable to JHS.

## Coverage note

The site could not be scraped, so the PubMed name search is the source list and the
coverage ratio is 1.0 by construction. The full study name is distinctive, so query
recall is expected to be high.

## Reproduce

```bash
scripts/run_pubmed_dataset.sh SWAN
```
