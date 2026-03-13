# CLAUDE.MD -- Polish Prescription Drug Policy & Mortality

**Project:** Free Prescription Drugs and Mortality: Evidence from Poland
**Institution:** University of Wisconsin-Madison
**Branch:** main

---

## Core Principles

- **Plan first** -- enter plan mode before non-trivial tasks; save plans to `quality_reports/plans/`
- **Verify after** -- run scripts and confirm output at the end of every task
- **Single source of truth** -- Python scripts are authoritative; paper derives from their output
- **Quality gates** -- nothing ships below 80/100
- **[LEARN] tags** -- when corrected, save `[LEARN:category] wrong → right` to MEMORY.md
- **Publication quality** -- all figures must be polished and publication-ready

---

## Research Design

**Policy:** Poland's "Drugs 75+" program (Sep 2016: free drugs for >=75; Sep 2023: expanded to >=65)

**Three empirical strategies:**
1. Within-Poland age-based DiD (treatment: >=75 vs control: 60-74)
2. Cross-country DiD (Poland vs Visegrad + broader CEE)
3. Synthetic control (cohort perspective, 36 donor countries)

**Data:** Human Mortality Database (HMD) -- death rates, deaths, exposures, life tables, cause-of-death

---

## Folder Structure

```
project-root/
├── CLAUDE.MD                    # This file
├── .claude/                     # Rules, skills, agents, hooks
├── Bibliography_base.bib        # Centralized bibliography
├── Data/HMD/                    # Human Mortality Database
│   ├── POL/                     # Poland-specific (STATS, Cause, InputDB)
│   ├── hmd_statistics_20251211/ # Cross-country (37 countries)
│   ├── lt_both/                 # Life tables (both sexes)
│   ├── lt_female/               # Life tables (female)
│   └── lt_male/                 # Life tables (male)
├── Paper/                       # Paper (Markdown then LaTeX)
│   ├── main.md                  # Main paper draft
│   ├── sections/                # Individual sections
│   ├── tables/                  # Generated tables
│   └── figures/                 # Publication figures (symlink)
├── Figures/                     # Output figures
├── scripts/
│   ├── python/                  # Analysis scripts (numbered pipeline)
│   └── config.py                # Paths and constants
├── quality_reports/             # Plans, session logs
├── explorations/                # Research sandbox
├── templates/                   # Templates
└── master_supporting_docs/      # Key papers
```

---

## Commands

```bash
# Run analysis pipeline
python3 scripts/python/00_data_loading.py
python3 scripts/python/01_descriptive.py
python3 scripts/python/02_within_poland_did.py
python3 scripts/python/03_cross_country_did.py
python3 scripts/python/04_synthetic_control.py

# Build PDF from paper draft (Paper/main.md -> Paper/main.pdf)
python3 scripts/md_to_pdf.py

# Pre-2020 run (data through 2019, exclude COVID-19): all outputs in results_pre2020/
export OUTPUT_SUBDIR=results_pre2020 END_YEAR=2019
python3 scripts/python/00_data_loading.py
python3 scripts/python/01_descriptive.py
python3 scripts/python/02_within_poland_did.py
python3 scripts/python/03_cross_country_did.py
python3 scripts/python/04_synthetic_control.py
OUTPUT_SUBDIR=results_pre2020 python3 scripts/md_to_pdf.py
# Or: bash scripts/run_pre2020.sh
```

---

## Quality Thresholds

| Score | Gate | Meaning |
|-------|------|---------|
| 80 | Commit | Good enough to save |
| 90 | PR | Ready for deployment |
| 95 | Excellence | Aspirational |

---

## Key Policy Dates

| Date | Event |
|------|-------|
| Sep 2016 | Drugs 75+ introduced (subset of drugs, age >=75) |
| 2017 | Drug list expanded |
| May 2018 | Major expansion (cancer drugs, antibiotics, etc.) |
| Mar 2021 | Further expansion |
| Sep 2023 | Drugs 65+ (nearly all drugs, age >=65) |

---

## Comparator Country Sets

| Set | Countries | Rationale |
|-----|-----------|-----------|
| Visegrad | CZE, SVK, HUN | Post-communist, similar health systems |
| CEE-broad | + EST, LTU, LVA, HRV, SVN, BGR | Broader Eastern Europe |
| EU-mixed | + AUT, DEU, ESP, ITA | Western European benchmark |

---

## Skills Quick Reference

| Command | What It Does |
|---------|-------------|
| `/commit [msg]` | Stage, commit, PR, merge |
| `/lit-review [topic]` | Literature search + synthesis |
| `/research-ideation [topic]` | Research questions + strategies |
| `/interview-me [topic]` | Interactive research interview |
| `/review-paper [file]` | Manuscript review |
| `/data-analysis [dataset]` | End-to-end analysis |
| `/learn [skill-name]` | Extract discovery into persistent skill |
| `/context-status` | Show session health + context usage |
| `/deep-audit` | Repository-wide consistency audit |
| `/proofread [file]` | Grammar/typo/overflow review |

---

## Current Project State

| Phase | Status | Key Output |
|-------|--------|------------|
| 0: Setup | Complete | Config, folders, data |
| 1: Data & Descriptives | Complete | Processed datasets, descriptives, baseline figures, Table 1 |
| 2: Within-Poland DiD | Complete | DiD & TWFE estimates, event study, robustness, Table 3 |
| 3: Cross-Country DiD | Complete | Cross-country DiD & triple-diff, event studies, Table 4 |
| 4: Synthetic Control | Complete | SCM estimates, placebo tests, Table 5 |
| 5: Paper Draft | In progress | Pre-print manuscript outline, tables ready |
