"""Survey-weighted adult mortality logit (NHIS-LMF 1986-2018) in Python.

Mirrors scripts/nhis_svy_mortality_logit.do but uses pandas + statsmodels GLM
with cluster-robust standard errors on (strata, psu) as a Taylor-linearization
approximation to Stata's `svy linearized`.

Pipeline:
    1. Read nhis_with_coresident_minors.parquet (produced by
       scripts/nhis_coresident_minors.py).
    2. Build raceth5, nk_under18, minors_mean_age_ctr, nkf, age_c, yeardec.
    3. Define two samples:
         parent  = parentrole_hh==1 and 18 <= age <= 64  (primary)
         all     = age >= 18                              (sensitivity)
    4. Fit four weighted GLM logits per sample (mfull, mcounts, mfact, mint).
    5. Joint Wald tests (statsmodels wald_test).
    6. Adjusted Pr(died) by nk_under18 (counterfactual averaging on the
       analytic sample).
    7. Weighted vs unweighted death-rate QC table by nkf x raceth5.
    8. Write tidy CSVs to results/py/.

Variance caveat:
    statsmodels GLM with cov_type='cluster' implements the cluster-robust
    sandwich estimator using (strata, psu) tuples as clusters. This matches
    Stata's design-based linearization in the within-PSU contribution but
    does NOT subtract stratum means. For typical NHIS analyses with many
    PSUs per stratum this is a small conservative effect on SEs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tools.sm_exceptions import PerfectSeparationError


# ----------------------------------------------------------------------------
# Variable construction
# ----------------------------------------------------------------------------

def build_analytic_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Add died outcome, raceth5, nk_under18, minors_mean_age_ctr, nkf,
    age_c, yeardec, and sample flags. Returns a NEW frame (does not mutate
    in place).
    """
    out = df.copy()

    # Outcome: died only defined for mortelig==1
    out["died"] = pd.Series(np.nan, index=out.index, dtype="float64")
    elig = out["mortelig"].eq(1)
    out.loc[elig & out["mortstat"].eq(1), "died"] = 1.0
    out.loc[elig & out["mortstat"].eq(2), "died"] = 0.0

    # Hispanic + bridged race recode (matches the Stata cascade)
    hisp = out["hispeth"].between(20, 70, inclusive="both")
    race_nhx = pd.Series(pd.NA, index=out.index, dtype="Int8")

    # racenew (post-1997)
    racenew = out["racenew"]
    race_nhx = race_nhx.mask((~hisp) & racenew.eq(100), 1)
    race_nhx = race_nhx.mask((~hisp) & racenew.eq(200), 2)
    race_nhx = race_nhx.mask((~hisp) & racenew.eq(400), 3)
    race_nhx = race_nhx.mask((~hisp) & racenew.eq(300), 4)

    # racea fallback (pre-1997)
    racea = out["racea"]
    asian_codes = [400, 410, 411, 412, 413, 414, 415, 416, 417, 419,
                   420, 430, 431, 432, 433, 434]
    aian_codes  = [300, 310, 320, 330, 340, 350]
    race_nhx = race_nhx.mask(race_nhx.isna() & (~hisp) & racea.eq(100), 1)
    race_nhx = race_nhx.mask(race_nhx.isna() & (~hisp) & racea.eq(200), 2)
    race_nhx = race_nhx.mask(race_nhx.isna() & (~hisp) & racea.isin(asian_codes), 3)
    race_nhx = race_nhx.mask(race_nhx.isna() & (~hisp) & racea.isin(aian_codes), 4)
    race_nhx = race_nhx.where(~(race_nhx.isna() & ~hisp), 5)

    # raceth5: 1 Hisp / 2 NH White / 3 NH Black / 4 NH Asian-PI / 5 NH AIAN+other+mult
    out["raceth5"] = pd.Series(pd.NA, index=out.index, dtype="Int8")
    out.loc[hisp, "raceth5"] = 1
    out.loc[(~hisp) & race_nhx.eq(1), "raceth5"] = 2
    out.loc[(~hisp) & race_nhx.eq(2), "raceth5"] = 3
    out.loc[(~hisp) & race_nhx.eq(3), "raceth5"] = 4
    out.loc[(~hisp) & race_nhx.isin([4, 5]), "raceth5"] = 5
    out["raceth5"] = out["raceth5"].fillna(5).astype("Int8")

    # Children: count + mean age (zero when no minor)
    nk = out["n_fam_childminor017"].astype("float64").fillna(0.0)
    nk = nk.clip(lower=0, upper=8)
    out["nk_under18"] = nk

    has_minor = nk > 0
    mean_age = out["hh_mean_child_age"].astype("float64").fillna(0.0)
    out["minors_mean_age_ctr"] = np.where(has_minor, mean_age, 0.0)

    nkf = nk.where(nk <= 2, 3).clip(lower=0, upper=3).astype("int8")
    out["nkf"] = nkf

    # Period (decade FE)
    yeardec = pd.Series(pd.NA, index=out.index, dtype="Int8")
    yeardec = yeardec.mask(out["year"].between(1986, 1989), 1)
    yeardec = yeardec.mask(out["year"].between(1990, 1999), 2)
    yeardec = yeardec.mask(out["year"].between(2000, 2009), 3)
    yeardec = yeardec.mask(out["year"].between(2010, 2018), 4)
    out["yeardec"] = yeardec

    # Common eligibility for the survey design
    common = (
        out["astatflg"].isin([1, 6])
        & out["sex"].isin([1, 2])
        & out["died"].isin([0.0, 1.0])
        & out["strata"].notna()
        & out["psu"].notna()
        & out["mortwtsa"].notna()
        & (out["mortwtsa"] > 0)
        & out["raceth5"].notna()
        & out["yeardec"].notna()
    )

    out["subpop_all"]    = (common & out["adult_agerestr"].eq(1)).astype("int8")
    out["subpop_parent"] = (
        common
        & out["parentrole_hh"].eq(1)
        & out["age"].between(18, 64, inclusive="both")
    ).astype("int8")

    return out


# ----------------------------------------------------------------------------
# Design matrix helpers (pure pandas / numpy to keep things explicit)
# ----------------------------------------------------------------------------

def _dummy_cols(s: pd.Series, prefix: str, drop_level) -> pd.DataFrame:
    """One-hot encode an integer-coded categorical series, dropping the
    reference level. Returns float64 columns with informative names.
    """
    levels = sorted(int(v) for v in pd.unique(s.dropna()))
    keep   = [v for v in levels if v != drop_level]
    out    = pd.DataFrame(index=s.index)
    for lv in keep:
        out[f"{prefix}_{lv}"] = (s == lv).astype("float64")
    return out


def make_design(
    df: pd.DataFrame,
    model: str,
    age_mean: float,
) -> tuple[pd.DataFrame, list[str]]:
    """Build the regressor matrix for one of the four model specs.

    Returns
    -------
    X       : DataFrame with intercept first
    bvars   : names of regressors that should be tested for the "kid block"
              joint Wald test ([] if not applicable to this model).
    """
    age_c = (df["age"].astype("float64") - age_mean)
    base = pd.DataFrame({
        "const":     1.0,
        "sex_male":  (df["sex"] == 1).astype("float64"),
        "age_c":     age_c,
        "age_c_sq":  age_c ** 2,
    }, index=df.index)
    base = pd.concat([
        base,
        _dummy_cols(df["raceth5"].astype("Int16"), "race", drop_level=2),
        _dummy_cols(df["yeardec"].astype("Int16"), "yeardec", drop_level=1),
    ], axis=1)

    if model == "mfull":
        base["nk_under18"]           = df["nk_under18"].astype("float64")
        base["minors_mean_age_ctr"]  = df["minors_mean_age_ctr"].astype("float64")
        return base, ["nk_under18", "minors_mean_age_ctr"]

    if model == "mcounts":
        base["nk_under18"] = df["nk_under18"].astype("float64")
        return base, ["nk_under18"]

    if model == "mfact":
        nkf_dummies = _dummy_cols(df["nkf"].astype("Int16"), "nkf", drop_level=0)
        base = pd.concat([base, nkf_dummies], axis=1)
        base["minors_mean_age_ctr"] = df["minors_mean_age_ctr"].astype("float64")
        return base, list(nkf_dummies.columns) + ["minors_mean_age_ctr"]

    if model == "mint":
        base["nk_under18"]              = df["nk_under18"].astype("float64")
        base["minors_mean_age_ctr"]     = df["minors_mean_age_ctr"].astype("float64")
        base["nk_x_meanage"]            = (
            df["nk_under18"].astype("float64")
            * df["minors_mean_age_ctr"].astype("float64")
        )
        return base, ["nk_under18", "minors_mean_age_ctr", "nk_x_meanage"]

    raise ValueError(f"unknown model {model!r}")


# ----------------------------------------------------------------------------
# Estimation
# ----------------------------------------------------------------------------

def _cluster_robust_cov(X: np.ndarray, y: np.ndarray, w: np.ndarray,
                         beta: np.ndarray, clusters: np.ndarray) -> np.ndarray:
    """Design-based cluster-robust sandwich variance for a weighted logit.

    Bread:    B = sum_i w_i * p_i*(1-p_i) * x_i x_i'
    Score_i:  g_i = w_i * (y_i - p_i) * x_i
    Cluster:  U_c = sum_{i in c} g_i
    Meat:     M = sum_c U_c U_c'
    Var:      V = (B^-1) M (B^-1)
    """
    eta = X @ beta
    p   = 1.0 / (1.0 + np.exp(-eta))
    pq  = p * (1.0 - p)

    XW = X * (w * pq)[:, None]
    bread = XW.T @ X
    bread_inv = np.linalg.pinv(bread)

    resid = w * (y - p)
    scores = X * resid[:, None]

    # Encode clusters as integer codes for fast aggregation
    if clusters.dtype.kind in ("U", "O", "S"):
        codes, _ = pd.factorize(clusters, sort=False)
    else:
        codes = np.asarray(clusters, dtype=np.int64)
    cl_order = np.argsort(codes, kind="stable")
    codes_sorted = codes[cl_order]
    scores_sorted = scores[cl_order]
    boundaries = np.flatnonzero(np.diff(codes_sorted)) + 1
    chunks = np.split(scores_sorted, boundaries)
    Uc = np.vstack([chunk.sum(axis=0) for chunk in chunks])

    meat = Uc.T @ Uc
    cov = bread_inv @ meat @ bread_inv

    # Standard small-sample correction: M / (M - 1) where M = # clusters
    M = Uc.shape[0]
    if M > 1:
        cov = cov * (M / (M - 1.0))
    return cov


def fit_weighted_logit(y: pd.Series, X: pd.DataFrame, w: pd.Series,
                       clusters: pd.Series):
    """Binomial GLM (point estimates) + design-based cluster-robust SE."""
    y_arr = y.to_numpy(dtype="float64")
    X_arr = X.to_numpy(dtype="float64")
    w_arr = w.to_numpy(dtype="float64")
    cl_arr = clusters.to_numpy()

    model = sm.GLM(y_arr, X_arr, family=sm.families.Binomial(),
                   freq_weights=w_arr)
    result = model.fit(maxiter=200)

    cov = _cluster_robust_cov(X_arr, y_arr, w_arr, result.params, cl_arr)
    result._design_cov = cov
    result._design_se  = np.sqrt(np.diag(cov))
    result._n_clusters = int(pd.Series(cl_arr).nunique())
    result._exog_names = list(X.columns)
    return result


def tidy_coef(result, exog_names: list[str], model_name: str,
              sample_name: str) -> pd.DataFrame:
    params = np.asarray(result.params)
    se     = np.asarray(result._design_se)
    z      = np.where(se > 0, params / se, np.nan)
    from scipy.stats import norm
    pval   = 2.0 * (1.0 - norm.cdf(np.abs(z)))
    crit   = norm.ppf(0.975)
    ll     = params - crit * se
    ul     = params + crit * se
    return pd.DataFrame({
        "term":    exog_names,
        "b":       params,
        "se":      se,
        "z":       z,
        "pvalue":  pval,
        "ll":      ll,
        "ul":      ul,
        "or":      np.exp(params),
        "or_low":  np.exp(ll),
        "or_high": np.exp(ul),
        "model":   model_name,
        "sample":  sample_name,
    })


def joint_wald(result, exog_names: list[str], terms: list[str],
               label: str) -> dict:
    """Multi-degree-of-freedom Wald test on the listed terms."""
    if not terms:
        return {"test": label, "F": np.nan, "df1": np.nan,
                "df2": np.nan, "pvalue": np.nan}
    idx = [exog_names.index(t) for t in terms if t in exog_names]
    if not idx:
        return {"test": label, "F": np.nan, "df1": np.nan,
                "df2": np.nan, "pvalue": np.nan}
    R = np.zeros((len(idx), len(exog_names)))
    for i, j in enumerate(idx):
        R[i, j] = 1.0
    Rb = R @ result.params
    cov = R @ result._design_cov @ R.T
    try:
        cov_inv = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        cov_inv = np.linalg.pinv(cov)
    chi2 = float(Rb @ cov_inv @ Rb)
    df1 = len(idx)
    df2 = max(result._n_clusters - 1, 1)
    F = chi2 / df1
    from scipy.stats import f as f_dist
    pval = 1.0 - f_dist.cdf(F, df1, df2)
    return {"test": label, "F": F, "df1": float(df1),
            "df2": float(df2), "pvalue": float(pval)}


def predicted_pr_by_nk(result, df: pd.DataFrame, model: str, age_mean: float,
                       weights: pd.Series, nk_values=(0, 1, 2, 3, 4)) -> pd.DataFrame:
    """Counterfactual adjusted Pr(died) by setting nk_under18 := k for the
    full subpopulation, then taking the weighted mean.
    """
    rows = []
    for k in nk_values:
        sim = df.copy()
        sim["nk_under18"] = float(k)
        # When mfull / mint / mcounts use nk_under18 as a continuous regressor
        # we leave minors_mean_age_ctr at observed value (Stata `margins`
        # default: held at sample values, not zero).
        X_sim, _ = make_design(sim, model, age_mean)
        # Some specs (mfact) use nkf rather than nk; rebuild nkf consistently
        if model == "mfact":
            nkf_val = min(int(k), 3)
            for col in [c for c in X_sim.columns if c.startswith("nkf_")]:
                lv = int(col.split("_")[-1])
                X_sim[col] = 1.0 if lv == nkf_val else 0.0
        if model == "mint":
            X_sim["nk_x_meanage"] = X_sim["nk_under18"] * X_sim["minors_mean_age_ctr"]
        X_sim = X_sim[result._exog_names]
        lin = X_sim.to_numpy(dtype="float64") @ result.params
        pr  = 1.0 / (1.0 + np.exp(-lin))
        w   = weights.to_numpy(dtype="float64")
        mean_pr = float(np.sum(pr * w) / np.sum(w))
        rows.append({"nk_under18": k, "pr_died": mean_pr})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# QC table
# ----------------------------------------------------------------------------

def qc_nkf_raceth5(sub: pd.DataFrame) -> pd.DataFrame:
    grp = sub.groupby(["nkf", "raceth5"], observed=True, dropna=False)
    out = grp.apply(lambda g: pd.Series({
        "n_uw":    len(g),
        "n_w":     float(g["mortwtsa"].sum()),
        "died_uw": float(g["died"].sum()),
        "died_w":  float((g["died"] * g["mortwtsa"]).sum()),
    }), include_groups=False).reset_index()
    out["rate_uw"]  = out["died_uw"] / out["n_uw"]
    out["rate_wtd"] = out["died_w"]  / out["n_w"]
    return out


# ----------------------------------------------------------------------------
# Main driver
# ----------------------------------------------------------------------------

MODELS = ("mfull", "mcounts", "mfact", "mint")
SAMPLES = ("parent", "all")


def main() -> int:
    proj_root = Path(__file__).resolve().parent.parent
    in_path   = proj_root / "nhis_with_coresident_minors.parquet"
    out_dir   = proj_root / "results" / "py"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        print(f"ERROR: cannot find {in_path}. Run scripts/nhis_coresident_minors.py first.",
              file=sys.stderr)
        return 2

    print(f"Reading {in_path.name} ...", flush=True)
    df = pd.read_parquet(in_path)
    print(f"  {len(df):,} rows", flush=True)

    print("Building analytic frame ...", flush=True)
    df = build_analytic_frame(df)

    for sample in SAMPLES:
        sub = df.loc[df[f"subpop_{sample}"] == 1].copy()
        print(f"\n=== Sample: {sample} ({len(sub):,} rows) ===", flush=True)
        if sub.empty:
            print("  empty sample, skipping", flush=True)
            continue

        age_mean = float(sub["age"].mean())
        sub["age_c"] = sub["age"].astype("float64") - age_mean

        clusters = sub["strata"].astype("int64").astype(str) + "_" \
                 + sub["psu"].astype("int64").astype(str)

        jt_records = []
        all_coefs  = []

        for model_name in MODELS:
            print(f"  fitting {model_name} ...", flush=True)
            X, kid_terms = make_design(sub, model_name, age_mean)
            exog_names   = list(X.columns)
            y = sub["died"].astype("float64")
            try:
                result = fit_weighted_logit(y, X, sub["mortwtsa"], clusters)
            except PerfectSeparationError:
                print(f"    perfect separation in {model_name}; skipping", flush=True)
                continue
            result._exog_names = exog_names

            coef_tbl = tidy_coef(result, exog_names, model_name, sample)
            coef_tbl.to_csv(out_dir / f"coef_{model_name}_{sample}.csv", index=False)
            all_coefs.append(coef_tbl)

            # Joint tests
            if model_name == "mfull":
                jt_records.append(joint_wald(result, exog_names,
                                             ["nk_under18", "minors_mean_age_ctr"],
                                             "mfull_joint_nk_meanage"))
                jt_records.append(joint_wald(result, exog_names,
                                             ["nk_under18"], "mfull_nk_only"))
                jt_records.append(joint_wald(result, exog_names,
                                             ["minors_mean_age_ctr"],
                                             "mfull_meanage_only"))
                # Also the adjusted Pr(died) plot data from mfull
                pr_tbl = predicted_pr_by_nk(result, sub, "mfull", age_mean,
                                            sub["mortwtsa"])
                pr_tbl.insert(0, "sample", sample)
                pr_tbl.to_csv(out_dir / f"margins_pr_died_{sample}.csv", index=False)
            elif model_name == "mcounts":
                jt_records.append(joint_wald(result, exog_names,
                                             ["nk_under18"], "mcounts_nk"))
            elif model_name == "mfact":
                nkf_terms = [c for c in exog_names if c.startswith("nkf_")]
                jt_records.append(joint_wald(result, exog_names, nkf_terms,
                                             "mfact_joint_nkf"))
                jt_records.append(joint_wald(result, exog_names,
                                             ["minors_mean_age_ctr"],
                                             "mfact_meanage"))
            elif model_name == "mint":
                jt_records.append(joint_wald(result, exog_names,
                                             ["nk_x_meanage"], "mint_interaction"))
                jt_records.append(joint_wald(result, exog_names,
                                             ["nk_under18", "minors_mean_age_ctr",
                                              "nk_x_meanage"],
                                             "mint_joint_all_kid_terms"))

        if jt_records:
            pd.DataFrame(jt_records).to_csv(
                out_dir / f"jointtests_{sample}.csv", index=False
            )
        if all_coefs:
            pd.concat(all_coefs, ignore_index=True).to_csv(
                out_dir / f"coef_all_models_{sample}.csv", index=False
            )

        qc = qc_nkf_raceth5(sub)
        qc.to_csv(out_dir / f"qc_nkf_x_raceth5_{sample}.csv", index=False)

        print(f"  wrote outputs for sample={sample}", flush=True)

    print(f"\nDone. Outputs under: {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
