# Panel Conditioning and Mortality in UK Birth Cohort Studies

**Replication package** · Jason Fletcher · University of Wisconsin–Madison

> Do people born in weeks selected for major UK panel studies have different
> mortality than people born in adjacent non-selected weeks?

---

## Overview

Three major UK birth cohort studies — the NSHD (1946), NCDS (1958), and BCS70 (1970) —
each enrolled all births occurring within a single target week. This design creates a
natural comparison group: births in adjacent weeks share the same calendar-time environment
but were never recruited. Using administrative vital statistics from England and Wales
(1970–2013), we compare mortality trajectories for selected ("treated") birth weeks against
eight adjacent control weeks within each cluster.

The pooled treatment estimate is positive but fragile: it attenuates to statistical
insignificance under narrow control windows, and an exact permutation test yields
$p = 0.222$. The NCDS — the cohort most comparable to the experimental WLS design —
shows a null effect, consistent with prior evidence from Warren et al. (2022).

**Manuscript:** `manuscript/main.qmd` (rendered to `manuscript/main.pdf`)

---

## Repository structure

```
.
├── analysis/               # Python analysis pipeline (scripts 00–08)
├── Data/                   # Raw data (NOT tracked; see DATA.md for access)
│   └── HMD/                # Human Mortality Database (NOT tracked; see DATA.md)
├── manuscript/             # Quarto source (.qmd) and rendered PDF
├── output/
│   ├── figures/            # All figures (PDF + PNG); tracked
│   └── tables/             # All tables (CSV + LaTeX + JSON); tracked
├── quality_reports/        # Analysis plans and session logs
├── Bibliography_base.bib   # BibTeX bibliography
├── requirements.txt        # Python dependencies (pinned)
├── DATA.md                 # Data access instructions
└── CLAUDE.md               # AI-assistant configuration (project rules)
```

---

## Reproducing the results

### 1. Requirements

Python ≥ 3.10. Install dependencies:

```bash
pip install -r requirements.txt
```

Quarto ≥ 1.5 is required to render the manuscript:

```bash
# macOS (Homebrew)
brew install quarto
# or download from https://quarto.org/docs/get-started/
```

### 2. Data

Raw data files are **not tracked** in this repository (large ONS `.xls` files and
licensed HMD data). See [`DATA.md`](DATA.md) for download instructions and placement.

Pre-computed output tables and figures **are** tracked in `output/`, so you can
read the manuscript and inspect all results without re-running the pipeline.

### 3. Running the pipeline

Run from the repository root, in order:

```bash
python3 analysis/00_data_overview.py   # inspect raw files
python3 analysis/01_load_and_clean.py  # build tidy panel → output/tables/01_*.csv
python3 analysis/02_replicate_stata.py # legacy replication check
python3 analysis/03_figures.py         # mortality trajectory figures
python3 analysis/04_main_tables.py     # pooled + by-cohort coefficient tables
python3 analysis/05_cause_of_death.py  # cause-specific decomposition
python3 analysis/06_robustness.py      # robustness checks + permutation test
python3 analysis/07_life_expectancy.py # back-of-envelope life-expectancy exercise
python3 analysis/08_descriptive_stats.py # descriptive table + HMD validation
```

Each script prints a summary and writes outputs to `output/figures/` and `output/tables/`.
Scripts 03–08 depend on `output/tables/01_age_aggregated.csv` produced by script 01.

### 4. Rendering the manuscript

```bash
cd manuscript
quarto render main.qmd --to pdf
```

The manuscript embeds all tables and figures dynamically from `output/`. Rendering
requires the full Python environment (the `.qmd` executes Python code blocks).

---

## Analysis overview

| Script | Output | Description |
|--------|--------|-------------|
| `00_data_overview.py` | (console) | Inspect raw ONS files |
| `01_load_and_clean.py` | `01_*.csv` | Tidy long panel; impute denominators |
| `02_replicate_stata.py` | `02_*.csv` | Port Stata regressions; verify parity |
| `03_figures.py` | `fig02_*.png`, `fig03_*.png` | Mortality trajectory plots |
| `04_main_tables.py` | `04_*.csv/json/tex` | Pooled + age-interval + by-cohort tables |
| `05_cause_of_death.py` | `05_*.csv` | Cause-specific coefficients |
| `06_robustness.py` | `06_*.csv/json`, `fig06_*.png` | Window, log, LOO, permutation test |
| `07_life_expectancy.py` | `07_*.csv/json`, `fig07_*.png` | Life-table translation (appendix) |
| `08_descriptive_stats.py` | `08_*.csv/tex` | Descriptive table; HMD validation |

---

## Key findings

- **Pooled ITT:** $\hat\beta = 0.060$ (SE = 0.027, $p = 0.024$), but sensitive to
  control window width and not significant under exact permutation inference ($p = 0.222$).
- **NCDS (closest parallel to WLS):** $\hat\beta = -0.021$ ($p = 0.36$) — null.
- **Narrow window (4 nearest controls):** $\hat\beta = 0.039$ ($p = 0.105$) — insignificant.
- Cause-of-death decomposition is exploratory; multiple-testing concern applies.
- Ages 0–9 estimate is mechanically implausible as a panel conditioning effect.

---

## Data sources

| Source | Description | Access |
|--------|-------------|--------|
| ONS deaths by week of birth | Death counts by year, week of birth, cause; E&W 1970–2013 | See `DATA.md` |
| Human Mortality Database (GBRTENW) | Period death rates for England and Wales | See `DATA.md` |

---

## Citation

Fletcher, Jason (2026). "Panel Conditioning and Mortality in UK Birth Cohort Studies:
Evidence from Administrative Vital Statistics." Working paper, University of
Wisconsin–Madison.

---

## License

Code: MIT. See `LICENSE`.
Data: see `DATA.md` for terms of the underlying sources.
