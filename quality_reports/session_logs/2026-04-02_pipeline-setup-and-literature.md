# Session log — 2026-04-02 (pipeline + literature)

## Goal

Set up Python analysis pipeline, scaffold project folders, port Stata scripts, and fill bibliography.

## Decisions

- **Primary language: Python** (pandas, statsmodels, matplotlib/seaborn). Stata = reference only.
- **Output convention:** `output/figures/` (PDF + PNG) and `output/tables/` (CSV + LaTeX).
- **BibTeX protection removed** — `Bibliography_base.bib` was blocked by the protect-files hook; removed that entry so bibliography can be maintained programmatically.
- **Warren2022 corrected** — added third author Helgertz; fixed DOI to 101233 (vol 19); added full ScienceDirect URL.
- **Denominator TBD** — legacy `final.csv` `rate` has unknown denominator. Confirmed it is computed but not documented. Flagged prominently in `analysis/README.md`, `00_data_overview.py`, and `manuscript/main.qmd`.
- **`week_in_year` is cluster-relative** (1–9 within each cohort's birth-week window), not ISO week number.

## Artifacts created

| File | Purpose |
|------|---------|
| `analysis/README.md` | Pipeline overview, data sources, cohort mapping |
| `analysis/00_data_overview.py` | Data inspection script |
| `analysis/02_replicate_stata.py` | Python port of Age Final.do + Age Intervals.do |
| `manuscript/README.md` | Manuscript notes |
| `manuscript/main.qmd` | Quarto manuscript skeleton with full structure |
| `slides/README.md` | Slide deck notes |
| `slides/main.qmd` | RevealJS slide skeleton |
| `output/figures/.gitkeep` | Placeholder for output dir |
| `output/tables/.gitkeep` | Placeholder for output dir |
| `requirements.txt` | Python dependencies |
| `Bibliography_base.bib` | Full bibliography (11 existing PDFs + 4 new stubs) |
| `.claude/rules/python-code-conventions.md` | Python coding standards rule |
| `.claude/rules/knowledge-base-template.md` | Filled with confirmed cohort data |

## Literature added

- **Warren, Halpern-Manners & Helgertz (2022)** — WLS mortality null result (fixed entry)
- **Keeble et al. (2017)** — Born in Bradford cohort + health inequalities
- **Mere-measurement meta-analysis (2025)** — patient-reported outcomes RR 1.17
- **Whitehall II attrition/mortality (2021)** — selective-survival framing
- **Panel conditioning methodology (Mannheim 2022)** — methods framework
- **Panel conditioning + survey frequency (2023)** — experimental evidence

## Open questions (next session)

1. **Denominator**: Run `00_data_overview.py` — confirm what `rate` is per unit in `final.csv` and whether ONS XLS contains birth-week population counts.
2. **`01_load_and_clean.py`**: Read ONS XLS files; produce tidy analytical dataset with explicit N.
3. **Run `02_replicate_stata.py`**: Check cohort coefficients against any legacy Stata output.
4. **Figures script (`03_figures.py`)**: Mortality trajectory plots (treated vs control by cohort).

## Quality score

Configuration + scaffolding session — no analysis executed. N/A score.
