# CLAUDE.MD -- Wisconsin Mortality Project

**Project:** Wisconsin Black-White Life Expectancy Gap Analysis
**PI:** Jason Fletcher
**Institution:** University of Wisconsin
**Branch:** main

---

## Core Principles

- **Plan first** -- enter plan mode before non-trivial tasks; save plans to `quality_reports/plans/`
- **Verify after** -- run scripts and confirm output at the end of every task
- **Replicate first** -- match Roberts et al. (2019) results before extending
- **Publication-ready** -- all figures must be polished, print-quality, and self-contained
- **Quality gates** -- nothing ships below 80/100
- **[LEARN] tags** -- when corrected, save `[LEARN:category] wrong → right` to MEMORY.md

---

## Project Summary

Partially replicate Roberts et al. (2019) "Contributors to Wisconsin's persistent black-white gap in life expectancy" (BMC Public Health) -- specifically the life expectancy trends (Figures 1-2) -- then extend with geographic decomposition:

1. **Statewide Wisconsin** -- replicate the original life expectancy analysis
2. **Milwaukee County** (FIPS 55079) -- urban core with large Black population
3. **Dane County** (FIPS 55025) -- Madison metro area
4. **Rest of Wisconsin** -- state minus Milwaukee and Dane Counties

Key outputs: race- and sex-specific life tables, Black-White life expectancy gap trends, and publication-ready figures comparing gaps across geographies. No cause-of-death decomposition.

---

## Folder Structure

```
wisconsin-mortality/
├── CLAUDE.md                    # This file
├── .claude/                     # Rules, skills, agents, hooks
├── Data/
│   ├── mortality/wi59_17.csv    # WI death records 1959–2017 (individual-level)
│   ├── population/              # CDC bridged-race population estimates 1969–2023
│   └── shp/                     # County shapefiles (cb_2018_us_county_500k)
├── Papers/                      # Reference papers (Roberts 2019, Roesch 2023)
├── scripts/python/              # All Python analysis scripts
├── Figures/                     # Publication-ready output figures
├── output/                      # Tables, pickle/parquet files, intermediate results
├── quality_reports/             # Plans, session logs, replication reports
├── explorations/                # Research sandbox
├── templates/                   # Session log, quality report templates
└── Bibliography_base.bib        # Project bibliography
```

---

## Data Codebook

### Mortality: `Data/mortality/wi59_17.csv`
| Column | Meaning | Key Values |
|--------|---------|------------|
| `deathyear` | Year of death | 1959–2017 |
| `race` | Race | 1=White, 2=Black |
| `sex` | Sex | 1=Male, 2=Female |
| `age` | Age at death | 0–100+ |
| `countyrs` | County FIPS | 55079=Milwaukee, 55025=Dane |
| `hispanic` | Hispanic origin | Filter to non-Hispanic |

### Population: `Data/population/wi.1969_2023.singleages.through89.90plus.txt`
Fixed-width CDC bridged-race format:
| Position | Field | Values |
|----------|-------|--------|
| 1–4 | Year | 1969–2023 |
| 5–6 | State | WI |
| 7–11 | County FIPS | 55001–55141 |
| Col 14 | Race | 1=White, 2=Black, 3=AIAN, 4=API |
| Col 15 | Hispanic origin | 0=Non-Hisp, 1=Hispanic, 9=NA |
| Col 16 | Sex | 1=Male, 2=Female |
| Col 17–18 | Age | 00–89, 90=90+ |
| Col 19–26 | Population | Zero-padded count |

### Key FIPS Codes
- **55079** = Milwaukee County
- **55025** = Dane County (Madison)
- All 55xxx = Wisconsin counties

---

## Commands

```bash
# Run Python analysis script
python3 scripts/python/script_name.py

# Quality score
python3 scripts/quality_score.py scripts/python/script_name.py
```

---

## Quality Thresholds

| Score | Gate | Meaning |
|-------|------|---------|
| 80 | Commit | Good enough to save |
| 90 | PR | Ready for deployment |
| 95 | Excellence | Aspirational |

---

## Skills Quick Reference (Most Relevant)

| Command | What It Does |
|---------|-------------|
| `/data-analysis [dataset]` | End-to-end Python analysis |
| `/review-python [file]` | Python code quality review |
| `/commit [msg]` | Stage, commit, PR, merge |
| `/lit-review [topic]` | Literature search + synthesis |
| `/research-ideation [topic]` | Research questions + strategies |
| `/review-paper [file]` | Manuscript review |
| `/deep-audit` | Repository-wide consistency audit |
| `/context-status` | Show session health + context usage |
| `/learn [skill-name]` | Extract discovery into persistent skill |

---

## Replication Targets: Roberts et al. (2019)

Study period: 3-year averages (1999–2001, 2007–2009, 2014–2016)
Focus: Non-Hispanic Black vs. Non-Hispanic White, Wisconsin statewide

| Target | Period | Males | Females | Source |
|--------|--------|-------|---------|--------|
| B-W LE gap | 2014–16 | 7.34 yr | 5.61 yr | Fig 1, Fig 2 |
| White LE | 2014–16 | 77.75 yr | 82.15 yr | Fig 1, Fig 2 |
| Black LE | 2014–16 | 70.41 yr | 76.54 yr | Fig 1, Fig 2 |
| B-W gap (2000) | 1999–01 | 7.40 yr | 5.73 yr | Fig 1, Fig 2 |

---

## Current Analysis State

| Component | Status | Script | Key Output |
|-----------|--------|--------|------------|
| Data cleaning & parsing | **Done** | `scripts/python/analysis.py` (Phase 1) | `output/pooled_data.parquet` |
| Life tables (statewide) | **Done** | Phase 2 | `output/life_expectancy_results.parquet` |
| Replication check (Roberts) | **Done** | Phase 2 | Within 0.1–0.4 yr of published values |
| Milwaukee County life tables | **Done** | Phase 3 | B-W gap: 9.2 yr (M), 6.1 yr (F) in 2015-17 |
| Dane County life tables | **Done** | Phase 3 | B-W gap: 8.5 yr (M), 5.4 yr (F) in 2015-17 |
| Rest-of-WI life tables | **Done** | Phase 3 | B-W gap: 3.8 yr (M), 4.3 yr (F) in 2015-17 |
| Figs 1-2: LE trends (statewide) | **Done** | Phase 4 | `Figures/fig1_*.pdf`, `fig2_*.pdf` |
| Figs 3-4: B-W gap by geography | **Done** | Phase 4 | `Figures/fig3_*.pdf`, `fig4_*.pdf` |
| Fig 5: LE bar chart by race×geo | **Done** | Phase 4 | `Figures/fig5_*.pdf` |
| Fig 6: Wisconsin county map | **Done** | Phase 5 | `Figures/fig6_wisconsin_map_bw_gap.pdf` |
| Publication tables (3 tables) | **Done** | Phase 6 | `output/tables/table1–3_*.csv` |
