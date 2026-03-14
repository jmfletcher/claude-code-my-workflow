# CLAUDE.md — Wisconsin Infant Mortality Project (Attempt 2)

**Project:** Wisconsin Infant Mortality: Evidence, Disparities, and Intervention Plausibility
**Author:** Jason Fletcher, University of Wisconsin
**Language:** Python (pandas, matplotlib/seaborn, pdfplumber)
**Output:** Quarto (.qmd) → PDF report
**Work directory:** This folder (Attempt 2)

---

## Core Principles

- **Plan first** — For non-trivial tasks, draft plan → save to `quality_reports/plans/` → present → wait for approval
- **Verify after** — Run scripts and confirm outputs at the end of every task
- **Single source of truth** — Python scripts are authoritative for data and figures; the Quarto report derives from their outputs and the literature
- **Quality gates** — Nothing ships below 80/100
- **[LEARN] tags** — When corrected, save `[LEARN:category] wrong → right` to MEMORY.md
- **Publication quality** — All figures must be polished and publication-ready (300 DPI, consistent palette)

---

## Research Aims

1. **Describe** infant mortality by race (Black, White) and geography (State, Milwaukee, Dane, Rest of Wisconsin) with appropriate uncertainty (95% CIs).
2. **Assess plausibility** of demonstrating intervention success in reducing Black–White disparities — given small Black birth/death counts outside Milwaukee, confidence intervals often exceed typical intervention effect sizes.
3. **Survey literature** on interventions that reduce infant mortality (effect sizes, lives saved per dollar where available).
4. **Tie evidence to policy** — Wisconsin Birth Equity Act (Rep. Shelia Stubbs, AB 1082–1088); argue why **targeting Milwaukee** is more reasonable for evaluation.

**Key constraint:** Outside Milwaukee, numbers of Black infants are small; Milwaukee is the only geography with enough Black infant deaths (~55/year) to support interpretable evaluation.

---

## Folder Structure

```
Attempt 2/
├── CLAUDE.md                           # This file
├── MEMORY.md                           # [LEARN] entries and persistent corrections
├── Bibliography_base.bib               # Project references
├── .claude/                            # Workflow framework (agents, rules, hooks)
├── data/
│   ├── input/                          # WISH PDFs (7 files, read-only)
│   └── processed/                      # Generated CSVs (from Attempt 1 or regenerated)
├── scripts/
│   └── python/
│       ├── config.py                    # Config: paths, palette, constants
│       ├── 01_load_and_clean.py        # Read CSVs, validate, prepare tidy data
│       ├── 02_figures.py               # 4 rate-by-race figures (matplotlib)
│       ├── 03_tables.py                # Summary tables (Tables 1, 2, 3)
│       └── 04_detectability.py         # Power calculations, minimum detectable effects
├── Figures/                            # Python-generated figures (300 DPI PNG)
├── Quarto/
│   ├── report.qmd                      # Main report → PDF
│   └── emory-clean.scss                # Theme
├── literature/                         # Literature reviews (from Attempt 1)
├── reference/                          # Attempt 1 outputs for comparison
│   ├── report_attempt1.md
│   └── figures_attempt1/
├── quality_reports/
│   ├── plans/
│   ├── specs/
│   ├── session_logs/
│   └── merges/
├── templates/
└── explorations/                       # Experimental analyses
```

---

## Commands

```bash
# From project root (Attempt 2/)

# 1) Run all analysis scripts
python3 scripts/python/01_load_and_clean.py
python3 scripts/python/02_figures.py
python3 scripts/python/03_tables.py
python3 scripts/python/04_detectability.py

# 2) Render Quarto report to PDF
quarto render Quarto/report.qmd --to pdf

# 3) Full pipeline
python3 scripts/python/01_load_and_clean.py && \
python3 scripts/python/02_figures.py && \
python3 scripts/python/03_tables.py && \
python3 scripts/python/04_detectability.py && \
quarto render Quarto/report.qmd --to pdf
```

---

## Dependencies

```
pandas
matplotlib
seaborn
pdfplumber
```

---

## Quality Thresholds

| Score | Gate       | Meaning                          |
|-------|-----------|----------------------------------|
| 80    | Commit    | Good enough to save              |
| 90    | PR/Share  | Ready for external use            |
| 95    | Excellence| Aspirational                     |

---

## Key Policy and Data Context

| Item | Notes |
|------|--------|
| Birth Equity Act | Rep. Shelia Stubbs; seven bills AB 1082–1088 (Cap Times, March 2026) |
| WISH | Wisconsin Interactive Statistics on Health — births and infant deaths by race |
| Suppression | "X" in WISH = suppressed (often 1–4); use Total − White and document |
| Milwaukee | ~55 Black infant deaths/year; largest concentration for evaluation |

---

## Figure Palette (Publication-Ready)

**Do not change without reason.**

| Element | Value | Notes |
|---------|-------|-------|
| White (race) | `#2171b5` (blue) | ColorBrewer-inspired, accessible |
| Black (race) | `#b2182b` (dark red) | ColorBrewer-inspired, accessible |
| Resolution | 300 DPI | Publication standard |
| Title suffix | "(95% CI, Poisson-based)" | CIs explicit in figure |
| CI method | Poisson: rate ± 1.96 × (1000√D)/B | Consistent across all figures |

---

## Current Project State

| Phase | Status | Key Output |
|-------|--------|------------|
| Data (CSVs from Attempt 1) | Done | 5 CSVs in data/processed/ |
| Literature review | Done | 3 files in literature/ |
| Reference report | Done | reference/report_attempt1.md |
| Workflow config | Done | CLAUDE.md, .claude/, MEMORY.md |
| Python analysis scripts | Done | config.py, 01–04 in scripts/python/ |
| Figures | Done | 4 PNGs in Figures/ (300 DPI) |
| Tables + detectability | Done | 3 CSVs + summary in output/ |
| Quarto report (PDF) | Done | Quarto/report.qmd → report.pdf |

---

## Migration from Attempt 1

This project is a redo of Attempt 1 (`../Attempt 1/`) using the Claude Code academic workflow. Key changes:

- **Python stays Python** — analysis scripts remain in Python (pandas, matplotlib) rather than R
- **Quarto replaces ReportLab** — report rendered via Quarto → PDF instead of markdown → ReportLab
- **Workflow framework** — full agent-based review, quality gates, session logging
- **Processed CSVs as input** — no need to re-extract PDFs; CSVs copied from Attempt 1
- **DO NOT modify Attempt 1** — that folder is read-only reference
