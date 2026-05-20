# NHIS Survey-Weighted Mortality Results

This folder holds the outputs of the survey-weighted mortality regressions in
`[../scripts/nhis_svy_mortality_logit.do](../scripts/nhis_svy_mortality_logit.do)`
and the parallel R cross-check in
`[../scripts/nhis_svy_mortality_logit.R](../scripts/nhis_svy_mortality_logit.R)`.

## Pipelines

Three parallel implementations of the same pipeline are kept in this repo.
Python is the primary stack going forward; Stata and R are retained for QC.

### Python (primary)
1. `[../scripts/nhis_coresident_minors.py](../scripts/nhis_coresident_minors.py)`
   reads the IPUMS NHIS fixed-width extract `nhis_00002.dat` with
   `pandas.read_fwf`, rescales weights, builds household-level and
   family-level co-resident-minor counts and mean/min/max child age, and
   writes `nhis_with_coresident_minors.parquet`.
2. `[../scripts/nhis_svy_mortality_logit.py](../scripts/nhis_svy_mortality_logit.py)`
   builds the analytic frame in memory, fits four weighted GLM logits
   per sample with `statsmodels.GLM`, and computes a **manual cluster-robust
   sandwich variance** keyed on `(strata, psu)` (see Variance caveat below).
   Outputs land under `results/py/`.

### Stata (QC)
1. `[../scripts/nhis_coresident_minors.do](../scripts/nhis_coresident_minors.do)`
   builds `nhis_with_coresident_minors.dta`.
2. `[../scripts/nhis_svy_mortality_logit.do](../scripts/nhis_svy_mortality_logit.do)`
   declares the survey design with `svyset psu [pweight=mortwtsa],
   strata(strata)` and fits the same four models. Outputs land under
   `results/`.

### R (QC)
`[../scripts/nhis_svy_mortality_logit.R](../scripts/nhis_svy_mortality_logit.R)`
re-fits with the R `survey` package on the Stata-built `.dta`. Outputs land
under `results/r_cross/`.

### Variance caveat (Python vs Stata)

`statsmodels.GLM` does not implement a full design-based variance estimator
(`svy linearized`). The Python pipeline computes the cluster-robust sandwich
manually:

- Bread: `sum_i w_i p_i (1 - p_i) x_i x_i'`
- Cluster score: `U_c = sum_{i in cluster c} w_i (y_i - p_i) x_i`,
  where each cluster is a `(strata, psu)` tuple
- Meat: `sum_c U_c U_c'`
- Sandwich: `Bread^-1 . Meat . Bread^-1`, scaled by `M / (M - 1)`

This matches Stata's `svy linearized` in the within-PSU contribution but does
NOT subtract stratum means. With NHIS having many PSUs per stratum the
difference is small (Stata SEs typically a touch smaller). Practical
significance changes only at the edge of the 5% threshold.

## Design

| Element | Choice |
|--------|--------|
| Outcome | `died` = `mortstat==1` vs `mortstat==2`, only if `mortelig==1` |
| Design | `svyset psu [pweight=mortwtsa], strata(strata) singleunit(scale)` |
| Period | Decade fixed effects: 1986-1989, 1990s, 2000s, 2010-2018 |
| Sex ref | Female (`ib2.sex`) |
| Race/eth ref | Non-Hispanic White (`ib2.raceth5`) |

## Two analytic samples

- **Primary - parent-role:** `parentrole_hh == 1` AND age 18-64.
  Cleanest attribution of household minors to the adult on each row, because
  RELATE in NHIS is to the householder, not to each adult.
- **Sensitivity - all adults:** age 18+. Broader but child-attribution is noisier.

## Models

| Model | Key kid terms | Joint test exported |
|------|----------------|---------------------|
| `mfull` | `nk_under18` + `minors_mean_age_ctr` | Both jointly + each alone |
| `mcounts` | `nk_under18` only | Slope on count |
| `mfact` | `ib0.nkf` (0 / 1 / 2 / 3+) + `minors_mean_age_ctr` | `testparm i.nkf`, mean age |
| `mint` | `c.nk_under18##c.minors_mean_age_ctr` | Interaction and all kid terms jointly |

All four models are fit twice: once with `subpop_parent`, once with
`subpop_all`. Stored estimates are named `<model>_<sample>` (e.g. `mfull_parent`).

## File layout (after a clean run)

```
results/
  py/                                 Python primary outputs
    coef_<model>_<sample>.csv         per-model tidy coefficients (b, se, OR, CI)
    coef_all_models_<sample>.csv      stacked across models
    jointtests_<sample>.csv           joint Wald tests
    margins_pr_died_<sample>.csv      adjusted Pr(died) at nk_under18 = 0..4
    qc_nkf_x_raceth5_<sample>.csv     weighted + unweighted death rates
  coef_<model>_<sample>.csv           Stata QC outputs (same names)
  jointtests_<sample>.csv
  margins_pr_died_<sample>.csv
  marginsplot_<sample>.gph / .png
  qc_nkf_x_raceth5_<sample>.csv
  r_cross/                            R cross-check outputs
    coef_<model>_<sample>.csv
    jointtests_<sample>.csv
    coef_all_models.csv
    jointtests_all.csv
```

## Running

```bash
# Python (primary)
cd "/Users/jmfletcher/Dropbox/AI Agents/Cursor Projects/NHIS Mortality"
python3 scripts/nhis_coresident_minors.py      # ~70s
python3 scripts/nhis_svy_mortality_logit.py    # ~15s

# Stata (QC) - requires Stata 17+
stata -b do scripts/nhis_svy_mortality_logit.do

# R cross-check - requires the Stata-built .dta
Rscript scripts/nhis_svy_mortality_logit.R
```

## Caveats (carry through to interpretation)

1. **RELATE is to the householder, not to each adult.** A non-parent
   householder/partner could still get household minors attributed to them;
   the parent-role primary sample mitigates this but does not eliminate it.
2. **Co-residence != completed parity.** Nonresident children (older kids who
   moved out, noncustodial parents, kids living with the other parent) are
   invisible.
3. **`mortucodld` is a coarse 10-cause grouping**, not fine-cause; analyses
   using cause-specific orphanhood require linkage to richer NCHS files.
4. **These are weighted associations.** The intended use is to *calibrate*
   kinship-model assumptions about fertility differences by mortality risk
   (see `[../deep-research-report.md](../deep-research-report.md)`), not to
   estimate a causal effect of fertility on mortality.
5. **Period fixed effects matter.** 1986-2018 spans large regime changes
   (HIV/AIDS era, opioid crisis, mid-life mortality reversals); always read
   the kid-term coefficients with the decade dummies in mind.
