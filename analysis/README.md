# Analysis Pipeline

Python scripts for the Panel Conditioning (UK cohorts) project.
Run from the **repository root**, in order.

---

## Full pipeline

| Script | Inputs | Key outputs | Description |
|--------|--------|-------------|-------------|
| `00_data_overview.py` | Raw ONS `.xls` | (console) | Inspect raw files; print shapes, columns, sample rows |
| `01_load_and_clean.py` | Raw ONS `.xls` | `01_clean_long.csv`, `01_age_aggregated.csv` | Read ONS XLS → tidy long-format panel; impute denominators; document cohort mapping |
| `02_replicate_stata.py` | `01_age_aggregated.csv`, legacy CSVs | `02_*.csv` | Port legacy Stata regressions to Python; verify parity with original results |
| `03_figures.py` | `01_age_aggregated.csv` | `fig02_*.png`, `fig03_*.png` | Publication-ready mortality trajectory and age-profile plots |
| `04_main_tables.py` | `01_age_aggregated.csv` | `04_results_summary.json`, `04_table*.csv/tex` | Pooled treatment estimate, age-interval table, by-cohort table |
| `05_cause_of_death.py` | Raw ONS cause XLS | `05_cause_coef_*.csv` | Cause-specific treatment coefficients (cancer, CVD, respiratory, external, other) |
| `06_robustness.py` | `01_age_aggregated.csv` | `06_robustness_coef.csv`, `06_permutation_*.csv/json`, `fig06_*.png` | Six alternative specifications (narrow windows, log, leave-one-out) + exact permutation test |
| `07_life_expectancy.py` | `01_age_aggregated.csv`, `04_table2_age_intervals.csv` | `07_le_summary.json`, `07_lifetable_comparison.csv`, `fig07_*.png` | Back-of-envelope life-table translation of age-interval estimates (Appendix A) |
| `08_descriptive_stats.py` | `01_age_aggregated.csv`, `Data/HMD/Mx_1x1.txt` | `08_descriptive_stats.csv/tex`, `08_hmd_comparison.csv/tex` | Descriptive mortality table by cohort × age interval; HMD validation (Appendix C) |

---

## Running

```bash
# Install dependencies first
pip install -r requirements.txt

# Run pipeline in order
python3 analysis/00_data_overview.py
python3 analysis/01_load_and_clean.py
python3 analysis/02_replicate_stata.py
python3 analysis/03_figures.py
python3 analysis/04_main_tables.py
python3 analysis/05_cause_of_death.py
python3 analysis/06_robustness.py
python3 analysis/07_life_expectancy.py
python3 analysis/08_descriptive_stats.py
```

Scripts 02–08 all depend on `output/tables/01_age_aggregated.csv` from script 01.
Script 05 additionally reads the raw ONS cause-of-death XLS.
Script 08 additionally reads `Data/HMD/Mx_1x1.txt`.

See [`DATA.md`](../DATA.md) for data access instructions.

---

## Output convention

- Figures → `output/figures/` (PDF + PNG at 300 dpi)
- Tables → `output/tables/` (CSV + LaTeX `.tex` + JSON where applicable)
- All outputs are tracked in the repository so results are readable without re-running.

---

## Regression specification

The baseline model estimated by scripts 04–08 is:

```
rate_{b,y,a} = α + β·treated_{b,y} + γ_a + δ_y + η_w + ε_{b,y,a}
```

- `rate`: mortality rate (deaths per 1,000 per year) for birth week `b`, birth year `y`, age `a`
- `treated`: 1 for the cohort-selected birth week in the target birth year, 0 otherwise
- `γ_a`: age fixed effects (`C(age_str)`)
- `δ_y`: birth-year fixed effects (`C(birth_year_str)`)
- `η_w`: within-cluster week-position fixed effects (`C(wiy_str)`, positions 1–9)
- Standard errors clustered by birth-week string (~135 clusters; 3 treated, 120 control)

---

## Cohort / treated-week mapping

| Cohort | Study | Treated birth week | `group` | `birth_year` |
|--------|-------|--------------------|---------|--------------|
| NSHD 1946 | MRC National Survey of Health & Development | 3–9 March 1946 | 1 | 1946 |
| NCDS 1958 | National Child Development Study | 3–9 March 1958 | 2 | 1958 |
| BCS70 1970 | 1970 British Cohort Study | 5–11 April 1970 | 3 | 1970 |

Each group contains five birth years centred on the target year (e.g., 1944–1948 for NSHD).
The `cohort` variable equals 1 only for the target birth-year × treated-position cell.
