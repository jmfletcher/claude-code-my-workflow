# Session log — 2026-04-02 (pipeline execution)

## Goal

Continue from interrupted session: run analysis pipeline, verify outputs, render manuscript and slides.

## Decisions

- `matplotlib.use("Agg")` added to all figure scripts (required for headless/sandbox rendering).
- **Quarto dependencies installed**: nbformat, nbclient, ipykernel, jupyter-core (added to requirements.txt).
- **Slides canonical path**: `Slides/` (capital S) — macOS merged writes to `slides/` into existing `Slides/` template folder.

## Key findings from data

| Finding | Detail |
|---------|--------|
| Denominator | `rate ≈ total / 15.3` → fixed cohort birth count N ≈ 15,300 per week; **not** a surviving population |
| Missing rates | 37.4% of age-resolved rows — expected (young cohorts can't yet have old-age deaths) |
| `week_in_year` | Cluster-relative (1–9), not ISO week number |

## Results (first estimates)

| Spec | Cohort coef | SE | p | N |
|------|------------|-----|---|---|
| Pooled (spec 1) | **0.061** | 0.029 | 0.036 | 5,913 |
| Age 0–9 | 0.070 | 0.028 | 0.014 | 423 |
| Age 30–39 | −0.042 | 0.048 | 0.384 | 1,350 |
| Age 60–69 | **0.497** | 0.177 | 0.005 | 360 |

Pattern: elevated treated-week mortality at young ages and old ages; near-null in middle ages.

## Artifacts created

| File | Status |
|------|--------|
| `analysis/00_data_overview.py` | Updated (xlrd-resilient) |
| `analysis/02_replicate_stata.py` | Running ✅ |
| `analysis/03_figures.py` | Running ✅ |
| `output/figures/fig01_age_interval_coefs.{pdf,png}` | ✅ |
| `output/figures/fig02_mortality_trajectories.{pdf,png}` | ✅ |
| `output/figures/fig03_cohort_age_profiles.{pdf,png}` | ✅ |
| `output/tables/02_age_intervals_cohort_coef.csv` | ✅ |
| `manuscript/main.html` | Renders ✅ |
| `Slides/main.html` | Renders ✅ |

## Open questions / next session

1. **Denominator rigor**: Install xlrd locally (`pip install xlrd seaborn`) and run `00_data_overview.py` on ONS XLS files to verify birth counts and confirm denominator.
2. **`01_load_and_clean.py`**: Read ONS XLS → clean analytical CSV with explicit N columns.
3. **By-cohort analysis**: Replicate estimates separately for NSHD/NCDS/BCS70 — heterogeneity check.
4. **Age-60–69 large estimate**: 0.497 effect on only 360 cells needs scrutiny — small-sample artifact or real late-life divergence?
5. **`03_figures.py` polish**: Label treated cohort name on fig02; improve color accessibility.

## Quality score

Pipeline session. Scripts run cleanly; manuscript and slides render. Score: **82/100** (results preliminary; denominator not yet confirmed from primary ONS source; analysis on legacy CSV only).


---
**Context compaction (auto) at 12:09**
Check git log and quality_reports/plans/ for current state.


---
**Context compaction (auto) at 15:40**
Check git log and quality_reports/plans/ for current state.


---
**Context compaction (auto) at 19:48**
Check git log and quality_reports/plans/ for current state.
