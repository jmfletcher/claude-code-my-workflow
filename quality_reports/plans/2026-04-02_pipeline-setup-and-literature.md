# Plan: Analysis pipeline setup + literature review
**Status:** COMPLETED  
**Date:** 2026-04-02  
**Triggered by:** User instruction to add literature, work in Python with Stata duplication, and move forward.

---

## Scope

1. **Python as primary analysis language.** Port the two legacy Stata scripts to Python (pandas + statsmodels). Update config rules accordingly.
2. **Literature bibliography.** Register all existing `Papers/` PDFs in `Bibliography_base.bib` plus add BibTeX stubs for new high-relevance papers identified in web search.
3. **Project scaffold.** Create `analysis/`, `manuscript/`, `slides/` folder structures with README/driver stubs.
4. **Knowledge base.** Fill in cohort names, treated weeks, and control design from what we know.

---

## What we know from legacy code + data

### Three cohorts (treated weeks)
| Cohort | Treated week | Birth years in data | Group code in `final.csv` |
|--------|-------------|---------------------|--------------------------|
| NSHD 1946 | 3–9 March 1946 | 1944–1948 (±2 yr) | `cohort = 1`, `group = 1` |
| NCDS 1958 | 3–9 March 1958 | 1956–1960 (±2 yr) | `cohort = 1`, `group = 2` |
| BCS70 1970 | 5–11 April 1970 | 1968–1972 (±2 yr) | `cohort = 1`, `group = 3` |

### Data structure (legacy `final.csv`)
- Unit: (birth week) × (death calendar year), with constructed mortality rate (per 10,000 or similar)
- 9 weeks per cohort-year (1 treated + 8 control), 3 cohort groups
- Variables: `week`, `year`, `cohort` (treated=1), `total` (deaths), `week_in_year`, `time`, `rate`, `log_rate`, `group`

### Legacy Stata regressions (to port)
**Age Final.do:** `reg rate cohort i.age_needed b0.year b0.week_in_year, cluster(week)` (pooled + base-week variant)

**Age Intervals.do:** same model by 10-year age decile (0–9, 10–19, …, 60–69), clustering by week

---

## File output convention
**Single convention:** `output/figures/` for all figure outputs; `output/tables/` for tables.  
(Use `analysis/` for scripts, `output/` for all generated artifacts.)

---

## Python environment
- `pandas`, `statsmodels`, `matplotlib`, `seaborn`, `numpy`
- No fixed R requirement for this project; Python first.
- `pyproject.toml` or `requirements.txt` for dependencies.

---

## Approach per task

### 1. Config update (Python)
- Update `r-code-conventions.md` paths to also scope `**/*.py`
- Add a `python-code-conventions.md` rule
- Add `Bash(python3 *)` already in `settings.json` (OK)

### 2. BibTeX
- Add existing Papers/ files as entries in `Bibliography_base.bib`
- Add stubs for new papers found in search

### 3. Scaffold
```
analysis/
  00_data_overview.py        # inspect raw data files, print shapes/columns
  01_load_and_clean.py       # read ONS XLS → tidy CSV
  02_replicate_stata.py      # port Age Final.do + Age Intervals.do
  README.md

manuscript/
  main.qmd                   # Quarto manuscript skeleton
  README.md

slides/
  main.qmd                   # Quarto slides skeleton (revealjs)
  README.md

output/
  figures/  (gitignored until we decide on tracking)
  tables/
```

### 4. Port Stata → Python
- `02_replicate_stata.py`: replicate the two `.do` files using `statsmodels.OLS` + `cluster` kwarg
- Spot-check: pooled `cohort` coefficient vs legacy CSV values

### 5. Knowledge base
- Fill cohort dates and treated-week mapping table

---

## Verification
- [ ] `python3 analysis/00_data_overview.py` runs without error
- [ ] `python3 analysis/02_replicate_stata.py` produces estimates roughly matching legacy Stata regression
- [ ] `quarto render manuscript/main.qmd` compiles to PDF or HTML skeleton
- [ ] `quarto render slides/main.qmd` compiles
- [ ] BibTeX parses without error

---

## Open questions (not blockers)
- Exact denominator: `final.csv` reports `rate` but not `N`. The larger ONS XLS may have birth counts. Confirm in `00_data_overview.py`.
- `mortality age final.csv` has `age_needed` column (0–70) — confirm this is the age-at-death from the death event, not birth age.
- Cause-of-death file (`tcm77-419405.xls`) included in `Data/` — use in extension analysis later.
