# Agent Handoff — Wisconsin Mortality Project

**Date:** March 12, 2026
**PI:** Jason Fletcher, University of Wisconsin-Madison
**Workspace:** `claude-code-my-workflow/`

---

## 1. What This Project Is

An empirical analysis of the **Black-White life expectancy gap in Wisconsin, 2005-2017**, disaggregated into three regions: **Milwaukee County**, **Dane County (Madison)**, and the **rest of the state**. The project partially replicates Roberts et al. (2019, BMC Public Health) and extends it with geographic decomposition and counterfactual analysis.

**There is NO cause-of-death decomposition.** The analysis is restricted to all-cause life expectancy.

---

## 2. What Has Been Built

### Analysis Pipeline (`scripts/python/analysis.py`, ~1780 lines)

A single monolithic script that runs end-to-end in ~60 seconds. It has 7 phases:

| Phase | What It Does | Key Outputs |
|-------|-------------|-------------|
| **1** | Load mortality + population data, filter to 2005-2017 non-Hispanic B/W, aggregate by age group × race × sex × geography, pool into 3-year windows (center years 2006-2016) | `output/pooled_data.parquet` |
| **2** | Build abridged life tables (Chiang 1968 / Preston et al. 2001), compute e0 for all group×year combinations, validate against Roberts et al. (2019) | `output/life_expectancy_results.parquet`, replication within 0.1-0.4 yr |
| **3** | Extend life tables to Milwaukee, Dane, Rest-of-WI | Gap ranges: 3.8 yr (Rest-of-WI males) to 9.2 yr (Milwaukee males) in 2015-17 |
| **2B** | Bootstrap CIs: 500 replicates, Poisson(deaths), fixed N; 95% CI for e0 and B-W gap | `output/tables/le_with_ci.csv`, `output/tables/gap_ci.csv` |
| **3B** | Counterfactual mortality-replacement exercises (3 exercises) | `output/tables/cf1_*.csv`, `cf2_*.csv`, `cf3_*.csv` |
| **3C** | Formal decomposition: Gap_SW = Σ(π_g × gap_g) + White_comp + residual | `output/tables/table4_gap_decomposition.csv`, `Figures/fig7_*.png`, `fig8_*.png` |
| **4** | Publication-ready figures (6 figures: LE trends, gap trends by geography, bar chart, map) | `Figures/fig1-6_*.pdf` and `.png` |
| **5** | Wisconsin county map with highlighted regions | `Figures/fig6_wisconsin_map_bw_gap.png` |
| **6** | Publication-ready CSV tables (3 tables + decomposition) | `output/tables/table1-4_*.csv` |

### Paper (`paper/generate_paper.py`, 1003 lines → `paper/wisconsin_mortality_paper.pdf`, 20 pages)

A Python script using `fpdf2` that generates the full PDF paper. Structure:

| Section | Content |
|---------|---------|
| **Abstract** | Highlights composition + counterfactual findings |
| **1. Introduction** | Frames Milwaukee's population share as central, previews counterfactual contributions |
| **2. Background** | Compositional lens, counterfactual logic, Wisconsin context |
| **3. Data and Methods** | 3.1 Data Sources, 3.2 Life Table Construction (notes overlapping 3-year windows / smoothed trends), 3.3 Counterfactual Framework, 3.4 Formal Gap Decomposition, **3.5 Bootstrap Confidence Intervals**, 3.6 Sensitivity and Uncertainty |
| **4. Results** | 4.1 Geographic Variation (Table 1, Fig 1), 4.2 Trends (Figs 2-3), 4.3 Change Over Time (Table 2), **4.4 Decomposing the Statewide Gap (Table 3, Figs 4-5)**, 4.5 Counterfactual Exercises (Tables 4-5) |
| **5. Discussion** | Four principal findings including decomposition results |
| **6. Conclusion** | Policy implications |
| **Appendix A** | Wisconsin county map (Fig A1) |
| **Appendix B** | Replication of Roberts et al. (Table B1, Figs B1-B2) |
| **Appendix C** | C.1 Sample context (Table C1: deaths, person-years, crude rate by geography/sex/race); C.2 County concentration (Table C2); narrative that Wisconsin is not unique |
| **References** | 9 references |

**Important:** The paper uses `fpdf2` with default Helvetica fonts. All text is wrapped in an `ascii_safe()` function that converts Unicode characters (en-dashes, curly quotes, etc.) to ASCII equivalents. If you add text with Unicode, it MUST go through `ascii_safe()` or you'll get `UnicodeEncodingException`.

---

## 3. Key Findings

### Statewide Gap (2015-2017)
- Male B-W gap: **7.9 years** (White 78.0, Black 70.0)
- Female B-W gap: **5.7 years** (White 82.3, Black 76.5)

### Geographic Variation (2015-2017, Males)
| Region | White LE | Black LE | B-W Gap |
|--------|:---:|:---:|:---:|
| Milwaukee | 77.5 | 68.3 | **9.2** |
| Dane | 80.2 | 71.7 | **8.5** |
| Rest of WI | 77.8 | 73.9 | **3.8** |
| Statewide | 78.0 | 70.0 | **7.9** |

### Decomposition (2016, Males)
| Component | π (Black share) | Local gap | Contribution | % of total |
|-----------|:---:|:---:|:---:|:---:|
| Milwaukee | 60% | 9.2 yr | 5.6 yr | **70%** |
| Dane | 8.5% | 8.5 yr | 0.7 yr | 9% |
| Rest of WI | 31% | 3.8 yr | 1.2 yr | 15% |
| Adjustments | — | — | 0.4 yr | 5% |
| **Total** | | | **7.9 yr** | **100%** |

- **Composition penalty**: 2.6 years (if Black Wisconsinites were distributed like White Wisconsinites, the weighted gap would drop from 7.5 to 4.9 years)

### Counterfactual Highlights (2016, Males)
- **CF1**: If MKE Black had Rest-of-WI Black mortality → statewide gap drops from 7.9 to 4.2 yr (nearly 50% reduction)
- **CF2**: If MKE Black had Dane Black mortality → gap drops to 5.6 yr
- **CF3**: If Dane White had Rest-of-WI White mortality → Dane gap drops from 8.5 to 6.1 yr (Dane White advantage accounts for ~28%)

### Trends (2005-07 → 2015-17)
- Male gap **widened** in all regions; worst in Dane (+3.2 yr, driven by 2.4-yr decline in Black male LE)
- Female gap narrowed statewide (-0.5 yr), roughly stable in Milwaukee

---

## 4. File Map

### Scripts
| File | Lines | Purpose |
|------|:---:|---------|
| `scripts/python/analysis.py` | ~1780 | All analysis: data prep, life tables, decomposition, counterfactuals, figures, tables |
| `paper/generate_paper.py` | ~1010 | Generates PDF paper using fpdf2 |

### Data (gitignored, must be present locally)
| File | Description |
|------|-------------|
| `Data/mortality/wi59_17.csv` | Individual death records, Wisconsin 1959-2017 |
| `Data/population/wi.1969_2023.singleages.through89.90plus.txt` | CDC bridged-race population, fixed-width |
| `Data/shp/cb_2018_us_county_500k.*` | US county shapefile (used for map) |

### Outputs
| File | Description |
|------|-------------|
| `output/pooled_data.parquet` | Pooled deaths + population by 3-year window |
| `output/life_expectancy_results.parquet` | All e0 values by year × race × sex × geography |
| `output/tables/table1_le_trends_all_geographies.csv` | Full LE + gap trends, all years |
| `output/tables/table2_wide_2016.csv` | LE by race/sex/geography, 2015-17 |
| `output/tables/table3_gap_change_2006_vs_2016.csv` | Gap change 2005-07 vs 2015-17 |
| `output/tables/table4_gap_decomposition.csv` | Full decomposition: π, gaps, contributions, composition effects |
| `output/tables/cf1_milwaukee_to_restofwi.csv` | Counterfactual 1 results |
| `output/tables/cf2_milwaukee_to_dane.csv` | Counterfactual 2 results |
| `output/tables/cf3_dane_white_to_restofwi.csv` | Counterfactual 3 results |
| `output/tables/le_with_ci.csv` | Life expectancy with 95% bootstrap CI (e0_lo, e0_hi) |
| `output/tables/gap_ci.csv` | B-W gap 95% bootstrap CI by geography/sex |
| `output/tables/change_ci.csv` | Gap change 95% bootstrap CI (2005-07 vs 2015-17) when available |
| `output/tables/table6_sample_context_2016.csv` | Deaths, person-years, crude rate by geography/sex/race, 2015-17 (Appendix C.1) |
| `output/tables/county_black_population_proportions.csv` | State, county with largest share of state Black pop, share % (Appendix C.2) |

### Figures (all have .pdf and .png versions)
| File | Paper ref | Content |
|------|:---------:|---------|
| `fig1_male_le_trends_statewide` | B1 | Male LE trends (statewide, replication) |
| `fig2_female_le_trends_statewide` | B2 | Female LE trends (statewide, replication) |
| `fig3_male_bw_gap_by_geography` | 2 | Male B-W gap by geography over time |
| `fig4_female_bw_gap_by_geography` | 3 | Female B-W gap by geography over time |
| `fig5_le_by_race_geography_2016` | 1 | Bar chart: LE by race × geography, 2015-17 |
| `fig6_wisconsin_map_bw_gap` | A1 | County map with gap annotations |
| `fig7_gap_decomposition_stacked` | 4 | **Stacked bar decomposition of statewide gap** |
| `fig8_decomp_components` | 5 | Population shares + local gaps (decomp components) |

### Paper
| File | Description |
|------|-------------|
| `paper/wisconsin_mortality_paper.pdf` | Current 20-page working paper |
| `paper/generate_paper.py` | Script that builds the PDF |
| `paper/QC_chatgpt_review_verification.md` | QC report: ChatGPT review checklist (Done/Partial/Not done) and recommendations |

---

## 5. Technical Notes

### Running the analysis
```bash
python3 scripts/python/analysis.py
```
Requires: `pandas`, `numpy`, `matplotlib`, `geopandas`, `pathlib`. Takes ~60 seconds. Must run with full permissions (sandbox restriction on sysctlbyname). Outputs all figures, tables, and parquet files.

### Regenerating the paper
```bash
python3 paper/generate_paper.py
```
Requires: `fpdf2`. Reads figures from `Figures/` and tables from `output/tables/`. Takes ~10 seconds.

### Life table method
- **Chiang (1968) abridged life table**, 19 age groups: <1, 1-4, 5-9, ..., 80-84, 85+
- Infant nax: Coale-Demeny formulas from Preston et al. (2001, Table 3.3)
- Open interval (85+): nax = 1/M
- Zero-death cells: substitute 0.5 deaths
- 3-year pooling: SUM both deaths and population across 3 years (not average population — this was a critical bug fix). Moving windows overlap; trend figures are smoothed and not independent year-by-year.

### Data quirks
- Population file has `origin=9` for all records (no Hispanic breakdown) — minor upward bias in denominators for non-Hispanic groups
- Mortality data has Hispanic origin coded for 2005+ records, filtered to non-Hispanic (codes < 200)
- Dane County Black population is small (~50k over 3 years, ~260 male deaths, ~158 female deaths per 3-year window) — estimates are noisy

### Decomposition math
```
Gap_SW = Σ_g (π_g × gap_g) + White_comp + residual

where:
  π_g         = Black pop share in geography g
  gap_g       = e0_W_g - e0_B_g (local B-W gap)
  White_comp  = e0_W_actual - Σ(π_g × e0_W_g)
                (adjustment because White pop is distributed differently from Black pop)
  residual    = Σ(π_g × e0_B_g) - e0_B_actual
                (nonlinearity: e0 isn't exactly a weighted average)

Composition effect = Σ(π_g × gap_g) - Σ(ω_g × gap_g)
  where ω_g = White pop share in geography g
  Measures how much Black geographic concentration inflates the statewide gap
```

---

## 6. What Has NOT Been Done / Potential Next Steps

**Recent updates (ChatGPT review QC):** A QC agent (`.claude/agents/qc-chatgpt-review.md`) verifies the 14 ChatGPT external-review items. A verification run produced `paper/QC_chatgpt_review_verification.md` (8 Done, 5 Partial, 2 Not done). Two fixes were applied: (1) **Female gap sentence** — text now states rest of Wisconsin has the smallest female gap (4.3 yr) and Dane’s gap (5.4) is intermediate with highest Black female LE (78.3); (2) **Overlapping 3-year windows** — §3.2 now states that moving windows overlap and that trend figures should be interpreted as smoothed, not independent year-by-year. PDF regenerated.

1. **Cause-of-death decomposition** — explicitly excluded from scope, but would identify which causes drive the gap (opioids, homicide, chronic disease)
2. **Age-specific decomposition (Arriaga)** — would identify which age groups contribute most to the gap
3. ~~**Confidence intervals / bootstrapping**~~ — **Done.** Phase 2B: 500-replicate Poisson bootstrap; `le_with_ci.csv` and `gap_ci.csv`; paper reports 95% CIs where appropriate.
4. **Post-2017 data** — analysis stops before COVID-19
5. **Formal peer review / journal submission** — paper is a working draft
6. **Sensitivity analyses** — e.g., alternative age groupings, different pooling windows, Hispanic population adjustment
7. **Modular refactoring** — `analysis.py` is monolithic; could be split into modules
8. **Git commit** — no commits have been made with the current analysis work (only config changes were committed in earlier sessions)

---

## 7. Configuration Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project config loaded every session — project summary, folder structure, data codebook, replication targets |
| `MEMORY.md` | Persistent learned facts ([LEARN] entries) — data quirks, method notes, workflow patterns |
| `.claude/agents/domain-reviewer.md` | Domain review lens customized for demography/epidemiology |
| `.claude/agents/python-reviewer.md` | Python code review agent customized for life table methods |
| `.claude/agents/qc-chatgpt-review.md` | **QC agent:** verifies whether each ChatGPT external-review edit has been implemented (read-only checklist) |
| `.claude/rules/python-code-conventions.md` | Python coding standards for this project |
| `.claude/rules/replication-protocol.md` | Protocol for validating against Roberts et al. |
| `.claude/skills/data-analysis/SKILL.md` | End-to-end Python analysis workflow |
| `.claude/skills/review-python/SKILL.md` | Python code review skill |
| `.gitignore` | Excludes `Data/`, `Papers/`, `output/`, Python artifacts |

---

## 8. Key Decisions Made by the PI

1. **Python over R** — all analysis in Python (pandas/numpy/matplotlib), not R
2. **No cause-of-death analysis** — life expectancy gaps only
3. **2005-2017 window** — not the full 1959-2017 range available in the mortality file
4. **Three geographies** — Milwaukee, Dane, Rest-of-WI (not individual counties)
5. **Replication in appendix** — Roberts et al. validation moved to Appendix B; main paper focuses on geographic decomposition and counterfactuals
6. **Decomposition + counterfactuals as central narrative** — the paper's main argument is that the "Wisconsin gap" is really a Milwaukee story, quantified via the formal decomposition
7. **fpdf2 for paper generation** — no LaTeX distribution available; PDF built programmatically

---

## 9. How to Re-run Everything

```bash
# 1. Generate all analysis outputs, figures, and tables
python3 scripts/python/analysis.py

# 2. Regenerate the paper PDF
python3 paper/generate_paper.py

# Paper appears at: paper/wisconsin_mortality_paper.pdf
```

Both scripts are self-contained and idempotent. The analysis script reads from `Data/` and writes to `Figures/` and `output/`. The paper script reads from `Figures/` and `output/tables/` and writes the PDF.
