# WHI — Authorship Monopoly Analysis

**Dataset:** Women's Health Initiative
**Source:** PubMed title/abstract name search (study site behind bot protection)
**Funding:** NHLBI (NIH) — confirmed
**Status:** Phase 2 — complete (2026-07-06)

---

## Source & method

The WHI publications database at whi.org returns HTTP 403 to automated clients, so it
could not be scraped. Papers were acquired via a PubMed title/abstract search for the
study name and run through the standard XML pipeline.

Query: `"Women's Health Initiative"[tiab]`

| Field | Value |
|-------|-------|
| PMIDs retrieved | 3,493 |
| Papers parsed | 3,467 |
| Unique authors (after auto-alias) | 6,919 |

## Metrics

| Metric | Value |
|--------|-------|
| Papers | 3,467 |
| HHI | 0.145 |
| Top-1 share | 17.7% (Manson JE) |
| Top-3 share | 27.8% |
| Top-10 share | 44.0% |

**Top authors:** Manson JE (614), Stefanick ML (311), Wactawski-Wende J (301),
Chlebowski RT (295), Shadyab AH (279). JoAnn Manson (WHI PI) anchors the network, but
concentration is only moderate for a very large multi-center trial.

## Coverage note

Because the study's own list was inaccessible, the PubMed name search **is** the source
list here, so the coverage ratio is 1.0 by construction. The real caveat is query
recall: papers that don't put "Women's Health Initiative" in the title/abstract are
missed. This is a name-search floor rather than a curated-vs-search comparison.

## Reproduce

```bash
scripts/run_pubmed_dataset.sh WHI
```
