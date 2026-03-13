# Project Setup & Master Research Plan

**Status:** DRAFT
**Date:** 2026-03-10
**Project:** Polish Prescription Drug Policy and Mortality

---

## 1. Project Overview

### Research Question
What is the causal effect of Poland's free prescription drug policy (Drugs 75+) on mortality?

### Background
Poland introduced the "LEKI 75+" (Drugs 75+) program in September 2016, providing free access to a subset of prescription medications for individuals aged 75+. The program was expanded over time (drug list extensions in 2017, May 2018, March 2021) and in September 2023 extended to age 65+ with nearly universal drug coverage.

**Key companion paper:** Majewska & Zaremba (2025) study the *consumption and fiscal cost* effects of this policy. They find 7.5–13% increases in medication consumption and substitution toward costlier drugs. **Our contribution is different:** we study the *mortality* effects, using publicly available demographic data (Human Mortality Database) rather than administrative drug sales data.

**Related US evidence:** Kaestner et al. (2019) find Medicare Part D reduced hospitalizations by ~4% but had no detectable effect on all-cause mortality.

### Data Available
- **Human Mortality Database (HMD):**
  - Poland-specific: `Data/HMD/POL/STATS/` — death rates (Mx), deaths, exposures, life tables, population (1x1, 5x1, 5x5, etc. configurations), years 1958–present
  - Poland cause-of-death: `Data/HMD/POL/Cause/` — cause-specific death rates (cardiovascular, cancer, respiratory, etc.)
  - Cross-country: `Data/HMD/hmd_statistics_20251211/` — 37 countries, all statistics
  - Life tables by sex: `Data/HMD/lt_both/`, `lt_female/`, `lt_male/`
  - **37 countries** including natural comparators: CZE, SVK, HUN (Visegrad), plus DEU, ESP, ITA, AUT, etc.

### Tools
- **Python 3.14.2** with numpy, pandas, matplotlib, scipy, statsmodels, geopandas
- **Missing (need to install):** seaborn, linearmodels, scikit-learn
- **LaTeX:** Not currently installed on system — will write paper in LaTeX, need user to install MacTeX or use alternative (Overleaf export)

---

## 2. Three-Strategy Empirical Design

### Strategy 1: Within-Poland Age-Based DiD
**Idea:** Exploit the age-eligibility threshold (75 in 2016, 65 in 2023) comparing mortality rates across age groups within Poland.

**Treatment group:** Ages ≥75 after Sep 2016; ages ≥65 after Sep 2023
**Control group:** Ages 60–74 before 2023; ages 60–64 after 2023

**Data:** HMD `Mx_1x1.txt` (single-year age × single-year period mortality rates), `Deaths_1x1.txt`, `Exposures_1x1.txt`

**Specification:**
- Event study around the 2016 threshold (and 2023 expansion)
- DiD comparing treated ages (≥75) vs control ages (60–74) before/after Sep 2016
- Can examine heterogeneity by sex (male/female life tables available)
- Cause-specific mortality from `POL/Cause/` data (cardiovascular, respiratory, etc.)

**Challenges:**
- HMD is annual, policy was September 2016 — first full treatment year is 2017
- Age-based trends may differ inherently (aging effects)
- Need to account for differential pre-trends across age groups

### Strategy 2: Cross-Country Difference-in-Differences
**Idea:** Compare Poland's elderly mortality trends to comparable countries that did NOT implement a similar drug subsidy program.

**Treatment:** Poland, post-2016
**Control:** Comparable countries (Visegrad: CZE, SVK, HUN; broader EU: AUT, DEU, etc.)

**Data:** Cross-country HMD files (`hmd_statistics_20251211/deaths/Deaths_1x1/Deaths_1x1.txt` and corresponding exposures/rates)

**Specification:**
- Two-way FE: country + year FE, or country-age + year FE
- Focus on elderly age groups (65+, 75+) vs younger age groups as additional control
- Triple-difference: (Poland vs other countries) × (elderly vs younger) × (pre vs post)
- Can test parallel trends pre-2016

**Comparator selection:**
- Visegrad group (CZE, SVK, HUN): similar post-communist healthcare systems
- Broader Central/Eastern European: EST, LTU, LVA, HRV, SVN, BGR
- Exclude countries with their own major drug subsidy reforms around 2016

### Strategy 3: Synthetic Control (Cohort Perspective)
**Idea:** Construct a "synthetic Poland" from weighted combination of donor countries to estimate the counterfactual mortality trajectory.

**Unit of analysis:** Age-specific mortality rates (or cohort-based life expectancy)

**Donor pool:** All 36 non-Poland HMD countries (or subset based on pre-treatment fit)

**Approach:**
- Abadie, Diamond & Hainmueller (2010) synthetic control method
- Pre-treatment period: ~2000–2015 (or earlier)
- Post-treatment: 2016–latest available year
- Can do this separately for different age groups (65+, 75+) and by sex
- Cohort perspective: track mortality of specific birth cohorts as they age through eligibility
- Permutation-based inference (placebo tests on donor countries)

---

## 3. Implementation Phases

### Phase 0: Project Setup (This Session)
- [x] Inventory all data and papers
- [ ] Update CLAUDE.md for this project
- [ ] Create folder structure (scripts/python/, Paper/, etc.)
- [ ] Install missing Python packages (seaborn, linearmodels, scikit-learn)
- [ ] Create requirements.txt
- [ ] Symlink or reference data directory from project root

### Phase 1: Data Exploration & Preparation
- [ ] Read and parse all HMD data formats (understand Mx, Deaths, Exposures, life tables)
- [ ] Build unified data loading pipeline in Python
- [ ] Create clean analysis datasets:
  - Poland age×year mortality panel
  - Cross-country age×year mortality panel
  - Cause-specific mortality for Poland
- [ ] Descriptive statistics and initial visualizations:
  - Poland mortality trends by age group over time
  - Cross-country mortality comparisons
  - Pre/post policy visual inspection
- [ ] Summarize key papers (Majewska & Zaremba, Kaestner et al.)

### Phase 2: Within-Poland Analysis
- [ ] Define treatment/control age groups precisely
- [ ] Event study specification and estimation
- [ ] DiD with flexible age trends
- [ ] Cause-specific mortality analysis
- [ ] By-sex heterogeneity
- [ ] Robustness checks (bandwidth, age window, pre-trend tests)
- [ ] Publication-quality figures

### Phase 3: Cross-Country DiD
- [ ] Select comparator countries (with justification)
- [ ] Construct balanced panel
- [ ] Parallel trends validation
- [ ] Two-way FE estimation
- [ ] Triple-difference specification
- [ ] Robustness to country selection
- [ ] Publication-quality figures

### Phase 4: Synthetic Control
- [ ] Implement SCM for elderly mortality
- [ ] Select pre-treatment matching variables
- [ ] Construct synthetic Poland
- [ ] Placebo tests (in-space and in-time)
- [ ] Cohort-based analysis
- [ ] Publication-quality figures

### Phase 5: Paper Writing
- [ ] LaTeX paper structure
- [ ] Introduction and motivation
- [ ] Policy background (drawing on Majewska & Zaremba)
- [ ] Literature review
- [ ] Data description
- [ ] Empirical strategy
- [ ] Results
- [ ] Discussion and robustness
- [ ] Conclusion
- [ ] Tables and figures
- [ ] Bibliography

---

## 4. Folder Structure (Proposed)

```
claude-code-my-workflow/
├── CLAUDE.md                          # Updated for this project
├── MEMORY.md                          # Project learnings
├── Bibliography_base.bib              # All citations
├── Data -> ../Data                    # Symlink to data directory
├── Paper/                             # LaTeX paper
│   ├── main.tex                       # Main paper file
│   ├── sections/                      # Individual sections
│   ├── tables/                        # Generated tables
│   └── figures/                       # Publication figures
├── scripts/
│   ├── python/                        # Analysis scripts
│   │   ├── 00_data_loading.py         # HMD data parsers
│   │   ├── 01_descriptive.py          # Descriptive analysis
│   │   ├── 02_within_poland_did.py    # Strategy 1
│   │   ├── 03_cross_country_did.py    # Strategy 2
│   │   ├── 04_synthetic_control.py    # Strategy 3
│   │   └── utils.py                   # Shared utilities
│   └── config.py                      # Paths and constants
├── Figures/                           # Output figures
├── explorations/                      # Sandbox for experimentation
├── master_supporting_docs/
│   └── supporting_papers/             # Key papers (PDFs)
├── quality_reports/
│   ├── plans/                         # This plan lives here
│   └── session_logs/
└── requirements.txt                   # Python dependencies
```

---

## 5. Key Decisions Needed from User

1. **LaTeX installation:** No LaTeX compiler found on system. Options:
   - Install MacTeX (recommended for full capability)
   - Write in LaTeX but compile via Overleaf
   - Write paper in a different format initially (Markdown → LaTeX later)

2. **Comparator countries for cross-country DiD:** I propose starting with Visegrad (CZE, SVK, HUN) plus broader CEE. Do you have preferences?

3. **Time scope:** HMD Poland data starts 1958. How far back should we go for pre-treatment? I suggest 2000–2015 as baseline, 2016–latest as post.

4. **Cause-specific analysis:** The cause-of-death data uses coded categories (S000–S016). Should we focus on cardiovascular (most relevant to drug policy) or be comprehensive?

5. **Paper scope:** First draft as a working paper, or more polished for submission?

6. **Data location:** The `Data/` folder is outside the git repo. Should I create a symlink, copy relevant files, or reference by absolute path in scripts?

---

## 6. Environment Issues

- **Python OK:** 3.14.2 with core scientific stack
- **Missing packages:** seaborn, linearmodels, scikit-learn (will install via pip)
- **LaTeX NOT installed:** Need resolution before Phase 5
- **No Homebrew:** May limit installation options

---

## Verification Steps
- [ ] All HMD data loads without errors
- [ ] Descriptive stats match known values (Poland population ~38M)
- [ ] Pre-treatment parallel trends hold visually
- [ ] Regression outputs are sensible (correct signs, magnitudes)
- [ ] All figures render at publication quality
- [ ] Paper compiles without errors
- [ ] Bibliography is complete
