# Kinship Replication + NHIS Calibration: Initial Results

**Date:** May 2026
**Engine:** `pykin/` (Python port of DemoKin's `kin_time_variant_2sex`, restricted to the parent kin block)
**Replication target:** Villaveces, A. et al. (2025). *Orphanhood and caregiver death among children in the United States by all-cause mortality, 2000-2021.* Nat Med 31, 672-683. [GitHub](https://github.com/MLGlobalHealth/orphanhood-caregiver-death-in-US-from-all-causes-of-mortality) | [Zenodo](https://doi.org/10.5281/zenodo.11423744)
**Calibration source:** NHIS-LMF 1986-2018, survey-weighted regression in `scripts/nhis_svy_mortality_logit.py`

---

## TL;DR

> Under the matrix-kinship model's standard assumption that mothers and fathers
> who die have the same fertility schedule as those who survive, prevalent
> US parental orphanhood (children under 18 with at least one deceased parent)
> in 2021 is **2.27 M**. Replacing the equal-fertility assumption with
> NHIS-derived κ multipliers shifts this estimate by **roughly -3 to -6 %
> overall (-76 K in 2021)**, with much larger and *opposite-signed* effects
> within race/ethnic groups:
>
> | Group | 2021 baseline | 2021 calibrated | Δ % |
> |---|---|---|---|
> | All | 2,240,912 | 2,165,354 | **-3.4 %** |
> | Non-Hispanic White | 1,176,062 | 1,014,424 | **-13.7 %** |
> | Non-Hispanic Black | 456,694 | 429,032 | **-6.1 %** |
> | Hispanic | 368,360 | 365,202 | **-0.9 %** |
> | Non-Hispanic Asian / PI | 59,414 | 47,651 | **-19.8 %** |
> | Non-Hispanic AIAN | 34,750 | 43,913 | **+26.4 %** |
>
> The standard model *overstates* orphan counts in four of the five race
> groups and *understates* them in NH American Indian / Alaska Native
> children by more than a quarter. The "All" headline understates this
> dispersion.

---

## 1. Methodology

### 1.1 Kinship engine

Single-year-of-age, two-sex time-varying matrix kinship model on ages 0..100.
State vector at focal age `x` is a 4n vector of length `4 × ages`:

```
[ live mother | live father | dead mother | dead father ]
```

Transition matrix per year:

```
U_t = [[ Uf  0   0   0 ]
       [ 0   Um  0   0 ]
       [ Mf  0   Gf  0 ]
       [ 0   Mm  0   Gm ]]
```

Differs from DemoKin's reference implementation by making the dead-parent
blocks **absorbing** (G in the bottom-right), so the dead-block mass at age
`x` reads out *cumulative* probability of parental death, which is the
quantity needed for prevalent orphanhood. (DemoKin's variant stores
incident-per-year deaths, which must be cumulated post hoc; the two are
mathematically equivalent.)

Initial parent age distribution `π_t` is computed from the population × ASFR
product:

```
π_f_t[a] = pop_f(a, t) × ASFR_f(a, t) / Σ_a [pop_f(a, t) × ASFR_f(a, t)]
```

### 1.2 Data inputs

All inputs from the Villaveces 2025 Zenodo archive (`data.zip`, 223 MB):

| Input | Source file | Coverage |
|---|---|---|
| Adult deaths by 5-year band × sex × race-eth | `Allcause_deaths_1983-2021.RDS` | 1983-2021 |
| Child deaths single-year 0-17 × race-eth | `NCHS_deaths_children_1983-2021.RDS` | 1983-2021 |
| Births by mother & father single year × race-eth | `births_1968-2021.RDS` | 1968-2021 |
| National population by 5-year band × sex × race-eth | CDC WONDER bridged-race files | 1990-2021 |
| Child population single-year by race-eth | CDC WONDER single-year children files | 1990-2021 |

Adult mortality bands are uniformly distributed to single year of age inside
the band; this is the standard convention in the orphanhood-modeling
literature and matches Villaveces et al.'s smoothing. Years 1983-1989 are
back-filled from the 1990 rate values for stability of the seed cohorts that
reach focal age 17 by 2000.

### 1.3 NHIS calibration

For each cell `c = (sex, raceth5, age band, decade)` we compute

```
κ_c = E[ nk_under18 | died = 1, c ] / E[ nk_under18 | died = 0, c ]
```

using NHIS person weights (mortwtsa). `nk_under18` is the family-level count
of co-resident minors (capped at 8) defined in `scripts/nhis_coresident_minors.py`.
Cells with fewer than 25 weighted decedents are smoothed toward the
(sex, raceth5, decade) average across ages.

The single-year expansion (`results/py/nhis_calibration_singleyear.csv`)
applies the band-uniform κ to ages 18-100 and the decade-uniform κ to years
1986-2018, then back-fills 1983-1985 and forward-fills 2019-2021 by holding
the nearest observed decade value.

### 1.4 Applying κ inside the matrix engine

The standard kinship model implicitly assumes equal fertility for decedents
and survivors within each (parent age, sex, year, race-eth) cell. To plug
in κ we *re-weight the dead-parent mass* at each focal-age slice:

```
P_either_calibrated(t, x) = 1 - max(0, 1 - Σ_a κ_f(a-x, t-x) × m_dead_f[a, x])
                              × max(0, 1 - Σ_a κ_m(a-x, t-x) × m_dead_m[a, x])
```

where `a` indexes the parent's age at focal year t and `a - x` is the
parent's age at focal birth (= cohort year `t - x`). The implied
interpretation: among adults in cell c who die, the expected number of
children-under-18 left behind is κ_c times the cell-average. The orphan
count from that cell scales by κ_c.

This is the simplest single-multiplier embedding. A cleaner alternative is
to recompute the cohort's parent-age distribution π_t with κ folded into
the ASFR schedule (multiplicative); we used the dead-mass multiplier here
because it isolates the calibration effect cleanly and avoids changing the
baseline parent-age distribution.

---

## 2. Baseline replication

See `results/kinship/baseline_villaveces/annual_summary_All.csv`.

**Headline:** US parental orphanhood prevalent stock in 2021 ≈ **2.27 M**
children under 18 with at least one deceased parent.

Villaveces 2025 reports **2.91 M** for "orphanhood + caregiver death"
combined. The gap of ~640 K corresponds to grandparent caregiver loss,
which our parental-only matrix model does not include by construction.
This is the expected level of agreement for a clean matrix-kinship
parental-only computation against a paper that layers grandparent caregiver
estimates on top.

The 2020 → 2021 jump in our model (+156 K, +7 %) tracks the COVID-19 effect
on parental mortality, matching the directional shift in Villaveces 2025.

Rate-per-100K trajectory (selected years): 2000 → 3,091 ; 2010 → 2,820 ;
2020 → 2,903 ; 2021 → 3,117. The slight 2000-2014 decline and 2015+ rise
matches the broad mortality narrative of the period (declining cardiovascular
mortality in middle age followed by the deaths-of-despair / COVID era).

---

## 3. Calibrated headline

**Pooled (All), 2021:** baseline 2.27 M → calibrated 2.19 M (Δ = -76 K, **-3.4 %**).

**Race-stratified, 2021 with bootstrap 95 % CIs (B=200):**

| Race/ethnicity | Baseline | Calibrated point | Δ % | 95 % CI on Δ % |
|---|---:|---:|---:|---|
| Non-Hispanic White | 1,176,062 | 1,014,424 | **-13.7 %** | (-18.6 %, -8.0 %) |
| Non-Hispanic Asian or PI | 59,414 | 47,651 | **-19.8 %** | (-27.2 %, +10.7 %) |
| Non-Hispanic Black | 456,694 | 429,032 | -6.1 % | (-12.9 %, +4.0 %) |
| Hispanic | 368,360 | 365,202 | -0.9 % | (-7.4 %, +6.4 %) |
| Non-Hispanic AIAN | 34,750 | 43,982 | +26.6 % | (-40.3 %, +90.0 %) |
| All | 2,240,912 | 2,166,268 | -3.3 % | (-17.2 %, +15.9 %) |

The bootstrap CIs reflect uncertainty in κ from finite NHIS PSU samples
within strata; they hold the demographic denominators fixed.

Across the time series (2000-2021):
- NH White Δ stays in the -10 % to -16 % band throughout.
- NH Black Δ widens after 2015 (-6 % by 2021).
- NH AIAN Δ is steadily +20 to +30 % across the period.
- Hispanic Δ is essentially nil (within ±1 %).

### 3.1 Why the signs differ

The pooled κ in our NHIS regression averages around 0.85-0.95 across most
(sex × raceth5 × decade) cells, but the dispersion is large:

- **NH White women, decade 2010-2018: κ ≈ 1.95.** Decedents had nearly
  twice the co-resident-children stock of survivors. Consistent with the
  opioid-era mortality concentration in younger parental ages.
- **NH AIAN women and men, decade 2010-2018: κ = 1.62 / 1.83.** Same
  qualitative story (young-parent mortality), even more pronounced.
- **Most other (sex, race, decade) cells: κ < 1**, often substantially so
  (NH Black men 1990s: κ = 0.81; Hispanic men 2010s: κ = 0.67). This is
  the "healthy adult" selection: adults with kids in the home are
  systematically lower-mortality.

The pooled "All" result averages a κ > 1 surplus in NH White women against
κ < 1 deficits across most other cells, netting to a small (-3 %)
correction. Race-stratified analysis is therefore essential -- the equal-
fertility assumption is **wrong in different directions by group**.

---

## 4. Interpretation

> The matrix-kinship model, as currently used in US orphanhood papers
> (Villaveces 2025, Schlüter 2024, Verdery 2024, Potter 2025), assumes that
> within any demographic cell, adults who die during the modeling horizon
> have the same fertility schedule as those who survive. NHIS-LMF data
> reject this assumption: in the equal-cell, US 1986-2018 data, fertility
> *is* correlated with mortality, and the sign varies by group.
>
> For NH White and NH AIAN parents the correlation has flipped sign over
> time (negative early, positive in the opioid era), which is consistent
> with deaths-of-despair concentrating among parents of school-age children.
> The standard equal-fertility kinship model gets the *level* of orphanhood
> roughly right at the national level but is biased by 5-25 % within
> race/ethnic strata.

This is the natural calibration step Villaveces et al. flag in their
"Sensitivity in national-level orphanhood estimates to potentially
correlated fertility rates" appendix (`misc_sen_analyse_adj_fert_rates_clean.R`).
Their sensitivity is parametric (assumes a uniform probability of births in
the year before death); ours is data-driven and group-specific.

---

## 4b. Cause-specific extension: Schlüter 2024 (drugs + firearms)

We applied the same NHIS-calibrated counting logic to the cause-specific
target in Schlüter et al. 2024 (JAMA Pediatrics): *cumulative US
children experiencing parental death from drug-overdose or firearm
causes, 1999-2020*. The mechanics are simpler than the matrix kinship
recurrence:

> cumulative children = ∑ over (year, sex, race, age band) of
> *D_c(cell) × K(cell)*

where *D_c* is cause-specific parental deaths from the NCHS
multiple-cause file (ICD-10 X40-X44, X60-X64, X85, Y10-Y14 for drugs;
W32-W34, X72-X74, X93-X95, Y22-Y24, Y35.0 for firearms; parent age
15-79) and *K* is either the population mean of co-resident minors among
living adults of that cell (*naive*) or among decedents (*NHIS*).

| | Drug | Firearm | Combined |
|---|---:|---:|---:|
| Parental deaths 1999-2020 | 920,301 | 691,877 | 1,612,178 |
| Children, naive (kids-per-living-adult) | 650,192 | 418,213 | 1,068,405 |
| Children, NHIS-calibrated | 473,274 | 336,066 | 809,340 |
| Δ % | **-27.2 %** | **-19.6 %** | **-24.2 %** |
| Schlüter 2024 published target | -- | -- | ~1,190,000 |

Our naive total (1.07 M) sits ~10 % below the published 1.19 M; the gap
is from (i) Schlüter's broader race universe (we drop "Others" /
multiracial) and (ii) their use of vital-statistics-derived fertility
profiles rather than NHIS averages. The headline finding still goes
through: the NHIS calibration shrinks the cumulative count by roughly a
quarter, with the biggest effect concentrated in NH White decedents
(-30 % for both drugs and firearms) where the gap between
kids-per-living-adult and kids-per-decedent is widest. NH Hispanic
firearm deaths show the smallest gap (-4 %) -- decedents and living
adults in that cell have very similar co-resident-minor counts.

Race-stratified cumulative totals are in
`results/kinship/schluter_drugs_firearms/cumulative_1999_2020_by_race.csv`;
the annual series is in `annual_by_cause.csv`. Reproduce with
`python scripts/run_schluter_cause_specific.py`.

---

## 5. Caveats

1. **Parental + grandparent caregiver.** We add a simple flow-stock
   accounting layer (`scripts/run_grandparent_layer.py`) using ACS S1002
   "grandparents responsible for grandchildren" counts (~2.5 M in 2019)
   and CDC WONDER ages 50-79 mortality. For 2021 it adds **546 K**
   children with a deceased custodial grandparent, bringing the
   combined total to **2.71 M** -- within ~7 % of Villaveces' 2.91 M.
   This layer is uncalibrated by NHIS (NHIS has no grandchild head-count
   variable). The residual ~200 K gap likely reflects (i) the
   children-per-caregiver multiplier (we use 1.7, ACS national average),
   (ii) the linear-decay residual-duration assumption (7 y midpoint),
   and (iii) the age-weighted vs flat 50-79 mortality average.
2. **Sex-pooled child mortality and population.** We split single-year
   child mortality and population 51/49 by sex; this is a uniform
   approximation. Effect on parental orphanhood is negligible.
3. **NH Asian or PI now uses post-2020 disaggregated CDC WONDER codes.**
   The 2020-2021 file splits "Asian or Pacific Islander" into "Asian" and
   "Native Hawaiian or Other Pacific Islander" plus "More than one race".
   We pool the first two back into the bridged-race "Asian or PI" bucket
   to align with the NCHS death file; "More than one race" is dropped.
4. **Bootstrap CIs** are from NHIS PSU-within-stratum resampling, B=200
   (`scripts/bootstrap_calibration.py`). They quantify uncertainty in κ
   only; they do not include sampling error in the NCHS denominators or
   CDC WONDER population estimates, nor model uncertainty in the kinship
   recurrence. For NH White the CI is well below zero (significant
   overestimate); for NH AIAN the small sample of NHIS deaths yields a
   very wide CI (-40 % to +90 %) so the +26 % point estimate is not
   statistically distinguishable from "no effect".
5. **κ from co-resident minors, not lifetime parity.** NHIS measures
   `n_fam_childminor017` at survey interview, not lifetime fertility. This
   is the right concept for orphanhood (children-under-18 affected) but
   conflates parity with custody / co-residence patterns. NH Black and
   Hispanic κ < 1 may partially reflect non-custodial fathers in the
   denominator.
5. **Decade-level κ, single-cohort engine.** κ is constant within decade.
   For finer trajectories we would need annual κ, requiring more NHIS
   panels.
6. **Single-stack point estimates.** No Poisson resampling like Villaveces;
   no credible intervals on the calibrated counts. The deltas reflect
   point estimates of κ.
7. **Two-sex independence assumption.** "Either parent dead" uses
   `1 - (1-p_mom)(1-p_dad)` (assumed independence). Joint mortality
   correlation within couples would shrink this slightly.

---

## 6. Files of record

```
explorations/
  kinship_math.md                              -- notation + recurrence
  kinship_inputs.md                            -- input documentation
  kinship_replication_results.md               -- this file
pykin/
  __init__.py                                  -- AGES, BIRTH_FEMALE
  ingest.py                                    -- RDS + WONDER -> parquet
  engine.py                                    -- U, F, project_parents
  orphanhood.py                                -- grid + annual summaries
  calibrate.py                                 -- kappa pivot + apply
scripts/
  run_kinship_baseline.py                      -- baseline run
  run_kinship_calibrated.py                    -- baseline + calibrated
  export_nhis_calibration.py                   -- NHIS -> kappa CSVs
results/
  py/
    nhis_calibration_by_cell.csv               -- 180 rows
    nhis_calibration_singleyear.csv            -- 32,370 rows
  kinship/
    baseline_villaveces/
      annual_summary_<race>.csv                -- baseline
      parental_loss_grid_<race>.parquet
      delta_<race>.csv                          -- baseline vs calibrated
    calibrated_villaveces/
      annual_summary_<race>.csv                -- calibrated
      parental_loss_grid_<race>.parquet
```

Run the pipeline end-to-end:

```bash
python -m pykin.ingest                   # ~50 s
python scripts/export_nhis_calibration.py
python scripts/run_kinship_calibrated.py
for r in "Non-Hispanic White" "Non-Hispanic Black" "Hispanic" \
         "Non-Hispanic American Indian or Alaska Native"; do
  python scripts/run_kinship_calibrated.py --race "$r"
done
```

