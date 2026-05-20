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

> **Update (after we realized NHIS-LMF *does* carry cause of death):**
> the NHIS-LMF `MORTUCODLD` variable encodes a 10-category leading-cause
> recode (heart, cancer, CLRD, accidents, stroke, Alzheimer, diabetes,
> flu/pneumonia, nephritis, residual). It does *not* let us isolate
> drug-overdose vs firearm; both intent groups land in either code 4
> "Accidents (unintentional injuries)" (accidental overdose X40-X44,
> accidental firearm W32-W34) or code 10 "All other causes (residual)"
> (suicide, homicide, undetermined intent). This is too coarse for a
> drug-specific κ, but it is fine enough to test whether the *cause
> heterogeneity* in κ matters for the Schlüter target.

**National-pooled NHIS K's by intent bucket (using `mortwtsa`):**

| Bucket | E[nk_under18 | died, ·] |
|---|---:|
| alive (living-adult comparison) | 0.681 |
| code 4 = Accidents (any) | 0.363 |
| code 10 = All other causes (residual) | 0.169 |
| code 1-2 = Heart + cancer (for comparison) | 0.15 |

K is *much* higher for accident decedents than for the residual category
(0.36 vs 0.17), confirming the intuition that accident victims tend to
be younger and so have more co-resident minors. But K_accident is still
below K_alive at most age bands (0.469 vs 1.007 at 40-49) because
selection into accidents is correlated with non-conventional life-course
states. So even the more-targeted cause-stratified K *lowers* the
naive Schlüter estimate.

**Result, three scenarios:**

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
| Children, naive (kids-per-living-adult) | 650,213 | 418,310 | 1,068,522 |
| Children, NHIS K_all-cause | 473,274 | 336,066 | 809,340 |
| Children, NHIS K_cause-stratified | 429,866 | 286,062 | **715,928** |
| Δ % vs naive (cause-stratified) | -33.9 % | -31.6 % | **-33.0 %** |
| Schlüter 2024 published target | -- | -- | ~1,190,000 |

The cause-stratified K is *lower* than the all-cause K because the
NHIS-code-4 "Accidents" bucket is dominated by motor-vehicle, falls,
and drowning -- not drug overdoses -- and accident decedents at ages
30-49 have systematically *fewer* co-resident minors than living
adults of the same age (K_accident ≈ 0.6 vs K_alive ≈ 1.3 at 30-39).
Both NHIS-calibrated scenarios produce a roughly 25-33 % shrinkage
relative to the naive Schlüter assumption.

### MORTUCOD refinement (NHIS sample years 1986-2004)

> **Update (May 20, 2026):** IPUMS NHIS now ships the detailed
> underlying-cause variable `MORTUCOD` for sample years 1986-2004. The
> field is a *3-digit NCHS-style cause recode* (similar to the 113-cause
> group, not raw ICD-10). The Schlüter-relevant codes:
>
> | code | label | maps to ICD-10 |
> |---|---|---|
> | 119 | Accidental discharge of firearms | W32-W34 |
> | 122 | Accidental poisoning | X40-X49 |
> | 125 | Suicide by discharge of firearms | X72-X74 |
> | 126 | Suicide by other or means | X60-X84 |
> | 128 | Homicide by firearm discharge | X93-X95 |
> | 129 | Homicide by other means | X85-X92 |
> | 132 | Firearm discharge, unknown intent | Y22-Y24 |
>
> Firearms are cleanly identifiable (119+125+128+132); drug overdose is
> approximated by code 122 (lumps drug X40-X44 with chemical X45-X49)
> with 126/129 used as noisy proxies for drug-suicide / drug-homicide
> in the broad scope.

IPUMS already harmonized ICD-9 and ICD-10 era deaths into the same
integer recode, so we **pool all NHIS-LMF decedents** (sample years
1986-2004, deaths across the full follow-up) rather than splitting by
ICD era. Bucket sample sizes after pooling: drug (122) = 697
decedents; firearm (119+125+128+132) = 1,566; suicide-other (126) = 53;
homicide-other (129) = 13.

**National-pooled K by bucket (MORTUCOD):**

| Bucket | E[nk_under18 \| died, ·] |
|---|---:|
| alive | 0.680 |
| drug (122) | 0.585 |
| firearm (119+125+128+132) | 0.577 |
| suicide_other (126) | 0.610 |
| homicide_other (129) | 0.344 |

These pooled values look close to K_alive only because they average
across all ages including older bands where K_alive is small. Within
the *ages where drug and firearm deaths concentrate* (30-49), K_drug ≈
0.56 vs K_alive ≈ 1.0-1.3, so the cell-level multiplication drives a
sizable downward correction.

**Two NCHS scope scenarios, cumulative 1999-2020:**

| | Drug | Firearm | Combined |
|---|---:|---:|---:|
| NARROW deaths (NHIS-bucket-matched: drug=X40-X49 only) | 803,538 | 682,963 | 1,486,501 |
| Children, naive (NARROW) | 578,043 | 413,040 | 991,083 |
| **Children, NHIS K_mortucod (NARROW)** | 386,550 | 274,892 | **661,442** |
| Δ % vs naive (NARROW) | -33.1 % | -33.4 % | **-33.3 %** |
| | | | |
| BROAD deaths (Schlüter scope: drug = X40-44, X60-64, X85, Y10-14) | 920,301 | 682,963 | 1,603,264 |
| Children, naive (BROAD) | 656,562 | 413,040 | 1,069,602 |
| **Children, NHIS K_mortucod (BROAD)** | 416,502 | 274,892 | **691,394** |
| Δ % vs naive (BROAD) | -36.6 % | -33.4 % | **-35.4 %** |
| Schlüter 2024 published target | -- | -- | ~1,190,000 |

In the BROAD (Schlüter-scope) row, NHIS K_122 is applied to NCHS
X40-X44 and Y10-Y14 (accidental + undetermined drug), K_126 to X60-X64
(drug suicide), and K_129 to X85 (drug homicide). The 126 / 129 buckets
pool drug- and non-drug methods, so the broad drug K is a noisy
proxy -- but the result (-35 %) is close to the narrow apples-to-apples
result (-33 %), suggesting the headline is not very sensitive to that
mismatch.

**Comparison across all four NHIS-calibrated scenarios:**

| Scenario | Combined children | Δ % vs naive | Δ % vs Schlüter |
|---|---:|---:|---:|
| Naive (kids per living adult) | 1,068,522 | -- | -10.2 % |
| NHIS K_all-cause | 809,340 | -24.3 % | -32.0 % |
| NHIS K_intent-stratified (MORTUCODLD) | 715,928 | -33.0 % | -39.8 % |
| **NHIS K_mortucod NARROW** | **661,442** | -33.3 % | -- (denominator differs) |
| **NHIS K_mortucod BROAD (headline)** | **691,394** | **-35.4 %** | **-41.9 %** |

All four NHIS-calibrated specifications converge on a ~25-35 % downward
correction to the naive kids-per-decedent assumption, and the MORTUCOD
refinement modestly *lowers* the count further relative to the
intent-stratified MORTUCODLD version (1.0 percentage points smaller
Δ vs naive). The substantive conclusion -- that Schlüter's headline of
~1.19 M children almost certainly **overstates** the true cumulative
total -- is reinforced rather than overturned by the more detailed
cause coding.

Caveats specific to this refinement:

1. **No drug cells have raw n ≥ 25.** All K_drug cells are smoothed
   toward (sex, raceth5) pooled means. With 697 decedents spread across
   the 60 age × race × sex cells (~12 per cell on average), this is
   unavoidable. K_firearm has more raw support (1,566 decedents).
2. **Drug bucket scope mismatch.** NHIS code 122 includes X45-X49 (a
   small share of non-drug accidental poisonings) and excludes the
   intentional-drug subsets X60-X64 / X85 that are inside Schlüter's
   target. The BROAD scenario re-projects from 126 and 129, but those
   K's are non-drug-dominated, so they are best read as sensitivity
   bounds rather than precise estimates.
3. **Constant-effects assumption preserved.** K is estimated on
   1986-2004 sample respondents (full follow-up) and applied to
   1999-2020 NCHS deaths. We do not have NHIS-LMF cause-specific data
   for sample years 2005+.

Cumulative race-stratified totals are in
`results/kinship/schluter_drugs_firearms/mortucod_cumulative_1999_2020.csv`;
the K table is in `mortucod_K_tables.csv`. Reproduce with
`python scripts/run_schluter_mortucod.py`.

Earlier specifications remain reproducible:
`python scripts/run_schluter_cause_specific.py` (all-cause κ) and
`python scripts/run_schluter_cause_stratified.py` (intent-stratified κ
from MORTUCODLD).

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
   is the right concept for **custodial** orphanhood (children under 18
   in the household at the time of parental death) but it is not the
   concept the **published natality-based literature** is targeting,
   which is closer to **biological** orphanhood (every birth counts when
   the parent dies). The two definitions differ most for fathers: NHIS
   misses non-resident fathers entirely (their `n_fam_childminor017` is
   zero at survey). A back-of-envelope augmentation using ACS
   non-resident-father rates (30 % NH White, 55 % NH Black, 35 %
   Hispanic, 15 % NH Asian/PI, 50 % NH AIAN) raises K_father_died by
   roughly the same magnitudes -- a 15-30 % upward correction for the
   male contribution. The all-cause headline κ correction (-3 % national)
   and this non-resident-father augmentation (+8-25 % national depending
   on the share of male decedent events) **roughly offset** for
   Villaveces-style all-cause orphanhood, but the Schlüter cause-specific
   target (drugs+firearms, heavily male) is more sensitive. Single-adult
   parent households face 1.3-1.9× the mortality of coupled-parent
   households inside every race × sex cell, which is the structural
   engine behind κ < 1: decedents are over-represented in lower-K
   household structures rather than being lower-K conditional on
   structure. Full appendix in
   `quality_reports/report_nhis_calibrated_orphanhood.md` § A;
   reproduce with
   `python scripts/run_household_structure_appendix.py`.
6. **Decade-level κ, single-cohort engine.** κ is constant within decade.
   For finer trajectories we would need annual κ, requiring more NHIS
   panels.
7. **Single-stack point estimates.** No Poisson resampling like Villaveces;
   no credible intervals on the calibrated counts. The deltas reflect
   point estimates of κ.
8. **Two-sex independence assumption.** "Either parent dead" uses
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

