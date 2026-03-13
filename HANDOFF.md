# Handoff for New Agent/Session

**Date:** 2026-03-10  
**Project:** Free Prescription Drugs and Mortality: Evidence from Poland (UW–Madison)  
**Work directory:** `claude-code-my-workflow` (this folder)  
**Canonical source folder:** `Poland Prescription Drugs Pedro` (Cursor Projects). This repo tracks the Pedro folder only — not the archived `Poland Prescription Drugs` in Completed Projects.

---

## Project in One Paragraph

Three empirical strategies (within-Poland DiD, cross-country DiD, synthetic control) use HMD data to estimate the effect of Poland’s free prescription drug policies (Drugs 75+ from Sep 2016; Drugs 65+ from Sep 2023). Pipeline: `00_data_loading.py` → `01_descriptive.py` → `02_within_poland_did.py` → `03_cross_country_did.py` → `04_synthetic_control.py`. Outputs go to `Data/processed`, `Figures`, `Paper/tables`. Paper draft is `Paper/main.md`; PDF is built with `scripts/md_to_pdf.py`. A pre-COVID run uses `OUTPUT_SUBDIR=results_pre2020` and `END_YEAR=2019`; all outputs for that run live under `results_pre2020/`.

---

## What This Session Did

1. **Synthetic control post-2016 bug (Figure 11)**  
   The synthetic Poland series stopped at 2016 because the series was built as `donors.values @ weights`; any donor with a missing value in a year made that year NaN.  
   **Fix (in `scripts/python/04_synthetic_control.py`):** The synthetic series is now built year-by-year: for each year, only donors with non-missing data are used, and their weights are renormalized to sum to 1. A zero-weight sum is handled (no divide-by-zero).

2. **Reran synthetic control and rebuilt outputs**  
   - Main run: `python3 scripts/python/04_synthetic_control.py` → updated `Figures/fig11_*`, `Figures/fig12_*` (PNG + PDF) and `Paper/tables/table5_synthetic_control.csv`.  
   - Pre-2020 run: `OUTPUT_SUBDIR=results_pre2020 END_YEAR=2019 python3 scripts/python/04_synthetic_control.py` → same under `results_pre2020/Figures/` and `results_pre2020/Paper/tables/`.

3. **Rebuilt both PDFs**  
   - Main: `env -i HOME="$HOME" PATH="$PATH" python3 scripts/md_to_pdf.py` → `Paper/main.pdf`.  
   - Pre-2020: `OUTPUT_SUBDIR=results_pre2020 python3 scripts/md_to_pdf.py` → `results_pre2020/Paper/main.pdf`.

---

## Current State

| Item | Status |
|------|--------|
| Phases 0–4 (data, descriptives, within-Poland DiD, cross-country DiD, SCM) | Implemented and run |
| Figure 11 / synthetic control | Fixed; synthetic and actual Poland plot through full post period |
| Figure 12 (placebo) | Updated with same SCM logic |
| Main paper PDF | `Paper/main.pdf` up to date |
| Pre-2020 paper PDF | `results_pre2020/Paper/main.pdf` up to date |
| Phase 5 (paper) | Draft in `Paper/main.md`; tables/figures wired into PDF |

---

## Paths and Config

- **Config:** `scripts/config.py` — uses env `OUTPUT_SUBDIR` and `END_YEAR`.  
- **Main outputs:** `Figures/`, `Paper/tables/`, `Data/processed/`, `Paper/main.pdf`.  
- **Pre-2020 outputs:** `results_pre2020/Figures/`, `results_pre2020/Paper/tables/`, `results_pre2020/Data/processed/`, `results_pre2020/Paper/main.pdf`.  
- **PDF builder:** `scripts/md_to_pdf.py` — reads `Paper/main.md` (or `results_pre2020/Paper/main.md` when `OUTPUT_SUBDIR=results_pre2020`), pulls tables from the corresponding `Paper/tables/` and figures from the corresponding `Figures/`.

---

## Commands to Remember

```bash
# From project root: claude-code-my-workflow/

# Full pipeline (main)
python3 scripts/python/00_data_loading.py
python3 scripts/python/01_descriptive.py
python3 scripts/python/02_within_poland_did.py
python3 scripts/python/03_cross_country_did.py
python3 scripts/python/04_synthetic_control.py

# Full pipeline (pre-2020)
OUTPUT_SUBDIR=results_pre2020 END_YEAR=2019 python3 scripts/python/00_data_loading.py
# ... then 01, 02, 03, 04 with same env

# Build PDFs
python3 scripts/md_to_pdf.py                                    # -> Paper/main.pdf
OUTPUT_SUBDIR=results_pre2020 python3 scripts/md_to_pdf.py      # -> results_pre2020/Paper/main.pdf
```

---

## Gotchas for Next Agent

1. **Sandbox vs Arrow:** `04_synthetic_control.py` (and any script that reads parquet) can hit Arrow/pyarrow sysctl errors in the sandbox. Run with full permissions (`required_permissions: ["all"]`) if the script exits with code 134 or IOError from Arrow.

2. **Main vs pre-2020 PDF:** The first time you run `md_to_pdf.py`, ensure no stray `OUTPUT_SUBDIR` is set when building the main paper, or use `env -i HOME="$HOME" PATH="$PATH" python3 scripts/md_to_pdf.py` so the main PDF uses `Figures/` and `Paper/tables/` at project root.

3. **SCM logic:** Synthetic series is now computed per year using only donors with non-missing data for that year; weights are renormalized for that year. Pre-treatment fit and placebo tests are unchanged.

---

## Where to Look for More

- **Project overview and commands:** `CLAUDE.md`  
- **Pre-2020 run:** `scripts/run_pre2020.sh`, `results_pre2020/README.md`  
- **Paper text:** `Paper/main.md`, `results_pre2020/Paper/main.md`
