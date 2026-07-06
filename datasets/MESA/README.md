# MESA — Authorship Concentration Analysis (Top-x Focus)

**Dataset:** Multi-Ethnic Study of Atherosclerosis (MESA)
**Source:** [MESA Published Papers (chronological docx, 2026-05-06)](https://tools.mesa-nhlbi.org/MESA_Files/publications/MESA_Published_Papers_Chronological_5-6-2026.docx)
**Parsed papers:** 1,877 (1 citation failed author parse; 1 truncated at file end)
**Status:** Initial pipeline run (June 2026)

---

## Source Details

| Field | Value |
|-------|-------|
| Source type | MESA NHLBI publication list (Word docx) |
| Author format | Vancouver-style citations (`LastName AB`) |
| Year range | 2002–2026 |
| HHI computed | No (top-x focus) |

Unlike REGARDS (PubMed XML) or MIDUS (HTML database), MESA citations are parsed from the NHLBI chronological Word export. Author strings use `{LastName} {Initials}` after Vancouver normalization. Entries with `et al.` contribute only the listed first author.

---

## Pipeline

```bash
Rscript datasets/MESA/scripts/run_pipeline.R
```

Re-parse after docx update (no re-download if file cached in `raw/`):

```bash
Rscript scripts/R/fetch_mesa_publications.R MESA
```

---

## Metrics (after initial-rule alias merge)

| Metric | Before merge | After merge (1,181 aliases) |
|--------|--------------|----------------------------|
| Papers | 1,877 | 1,877 |
| Unique authors | 8,415 | 7,234 |
| Top-1 share | 12.2% | **16.7%** (Lima JA) |
| Top-3 share | 29.3% | **29.5%** |
| Top-10 share | 53.9% | **59.6%** |
| Top-20 share | 70.6% | **76.1%** |

**Top authors (merged):** Lima JA (313), Budoff MJ (252), Bluemke DA (238), Rotter JI (218), Barr RG (185).

**Alias rule:** Authors with the same last name and first initial are merged automatically (e.g., `Lima J` → `Lima JA`). See `processed/author_aliases.csv` (1,181 entries, `merged_by = auto_initial_rule`).

Figures: `output/figures/` (rank-frequency, top-x shares, top-x by year, papers by year, temporal trends, career spans).
