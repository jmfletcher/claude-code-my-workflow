# MIDUS — Authorship Monopoly Analysis (Test Run)

**Dataset:** Midlife in the United States (MIDUS)
**Source:** [MIDUS Publication Database](https://midus.wisc.edu/pubdatabase.php?search=%20&field=Author&date=&to=&pagesize=30&order=Date&cf=0&page=1)
**Expected papers:** 2,409 (database count)
**Fetched / parsed:** 2,304 fetched · 2,294 with authors
**Status:** Test run complete (June 2026)

---

## Source Details

| Field | Value |
|-------|-------|
| Source type | MIDUS web publication database |
| URL | https://midus.wisc.edu/pubdatabase.php |
| Database count | 2,409 (June 2026) |
| Fetched | 2,304 (96%) |
| With parsed authors | 2,294 |
| Author format | APA citations scraped from HTML |

Unlike REGARDS (PubMed XML), MIDUS citations are parsed from HTML bibliography strings. Author strings use `{LastName} {Initials}` after APA normalization.

**Known gaps:** ~105 entries not captured (likely missing DOI blocks or pagination edge cases); 10 entries with author-parse failures. Review `processed/alias_suggestions.csv` for name merges (e.g. Almeida D → Almeida D M).

---

## Pipeline

```bash
Rscript datasets/MIDUS/scripts/run_pipeline.R
```

Rebuild authors only (after parser fixes, no re-fetch):

```bash
Rscript scripts/R/rebuild_midus_authors.R MIDUS
```

---

## Metrics (after initial-rule alias merge)

| Metric | Before merge | After merge (333 aliases) |
|--------|--------------|---------------------------|
| Papers | 2,294 | 2,294 |
| Unique authors | 3,854 | 3,521 |
| HHI | 0.024 | 0.029 |
| Top-1 share | 7.5% | **8.3%** (Almeida D M) |
| Top-3 share | 16.6% | **18.6%** |
| Top-10 share | 22.6% | **25.1%** |

**Top authors (merged):** Almeida D M (191), Ryff C D (155), Lachman M E (96), Sutin A R (61), Terracciano A (60).

**Alias rule:** Same last name + same first initial merged automatically (e.g., `Almeida D` → `Almeida D M`). See `processed/author_aliases.csv` (333 entries).

Figures: `output/figures/` (rank-frequency, top-x shares, HHI by year, temporal trends, domain comparisons).
