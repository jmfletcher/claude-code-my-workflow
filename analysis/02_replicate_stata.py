"""
02_replicate_stata.py
=====================
Panel Conditioning (UK cohorts) — Python replication of legacy Stata regressions.

Replicates:
  Age Final.do      → pooled OLS: rate ~ cohort + age_needed FE + year FE + week_in_year FE,
                       clustered by week (two specifications)
  Age Intervals.do  → same model in 10-year age bins (0–9, 10–19, ..., 60–69)

Runs on TWO datasets and compares:
  (A) Legacy: Old Attempts and Results/Terrence/mortality age final.csv
  (B) Fresh:  output/tables/01_age_aggregated.csv  (built from raw ONS XLS by 01_load_and_clean.py)

Tolerance goal: cohort coefficient to match within 3 significant figures across A and B.

Key design notes
----------------
- cohort = 1  →  treated birth week (NSHD/NCDS/BCS70 selected week)
- cohort = 0  →  control birth weeks (8 adjacent weeks per cohort group)
- Stata `cluster(week)` → statsmodels cov_type="cluster", groups=week
- Stata `b0.year`       → base year = first year in sample (reference category)
- Stata `b0.week_in_year` → base week = 1
- Stata `b5.week_in_year` → base week = 5 (second specification in Age Final.do)

Run from repo root:
    python3 analysis/02_replicate_stata.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# ---------------------------------------------------------------------------
# Paths & output dirs
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
LEGACY_AGE = ROOT / "Old Attempts and Results" / "Terrence" / "mortality age final.csv"
FRESH_AGE  = ROOT / "output" / "tables" / "01_age_aggregated.csv"
OUT_TABLES = ROOT / "output" / "tables"
OUT_TABLES.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_legacy() -> pd.DataFrame:
    """Load the age-resolved legacy CSV and return a clean DataFrame."""
    df = pd.read_csv(LEGACY_AGE)
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    n_before = len(df)
    df = df.dropna(subset=["rate"])
    print(f"  Legacy: {len(df):,} rows (dropped {n_before - len(df)} missing rate)")
    # Column name alignment
    df = df.rename(columns={"age_needed": "age"})
    # Cluster variable: legacy uses 'week' column
    if "week" not in df.columns:
        df["week"] = df["week_in_year"]
    for col in ["age", "year", "week_in_year", "week"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df


def load_fresh() -> pd.DataFrame:
    """Load the fresh ONS-derived age-aggregated CSV.

    Column mapping to match legacy regression variables:
      fresh 'birth_week'  → 'week'       (cluster variable)
      fresh 'birth_year'  → 'year'       (birth-year FE; matches legacy 'year' column)
      fresh 'age'                         (age-at-death FE; matches legacy 'age_needed')
      fresh 'week_in_year'               (week-within-cluster FE)
      fresh 'cohort'                     (treatment indicator)
    """
    if not FRESH_AGE.exists():
        print(f"  [WARN] Fresh data not found at {FRESH_AGE}. Run 01_load_and_clean.py first.")
        return pd.DataFrame()
    df = pd.read_csv(FRESH_AGE)
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    n_before = len(df)
    df = df.dropna(subset=["rate"])
    print(f"  Fresh:  {len(df):,} rows (dropped {n_before - len(df)} missing rate)")
    # Rename to match legacy variable names used in the regression formula
    df = df.rename(columns={
        "birth_week": "week",    # cluster variable
        "birth_year": "year",    # birth-year FE (NOT death year)
    })
    for col in ["age", "year", "week_in_year", "week"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df


# ---------------------------------------------------------------------------
# Regression helpers
# ---------------------------------------------------------------------------

def run_ols_clustered(formula: str, data: pd.DataFrame, cluster_col: str,
                      label: str) -> pd.Series:
    """Fit OLS with cluster-robust SEs; return tidy coefficient Series."""
    model = smf.ols(formula, data=data)
    result = model.fit(
        cov_type="cluster",
        cov_kwds={"groups": data[cluster_col]},
    )
    coef = result.params
    se = result.bse
    pval = result.pvalues
    tidy = pd.DataFrame({
        "coef": coef,
        "se": se,
        "t": coef / se,
        "pval": pval,
        "ci_lo": coef - 1.96 * se,
        "ci_hi": coef + 1.96 * se,
    })
    print(f"\n{'─'*60}")
    print(f"Model: {label}")
    print(f"Formula: {formula}")
    print(f"N = {int(result.nobs):,}   R² = {result.rsquared:.4f}")
    # Show only the cohort coefficient (main treatment estimate)
    cohort_row = tidy.loc[tidy.index.str.startswith("cohort")]
    print(f"\n  TREATMENT (cohort) coefficient(s):")
    print(cohort_row.to_string())
    return result


def run_age_intervals(data: pd.DataFrame, age_bins: list[tuple[int, int]]) -> list[dict]:
    """
    Replicate Age Intervals.do: run the base regression within each age bin.
    Returns list of dicts with {label, coef, se, pval, n}.
    """
    results = []
    formula = "rate ~ cohort + C(age) + C(year) + C(week_in_year)"
    for lo, hi in age_bins:
        mask = (data["age"].astype(int) >= lo) & (data["age"].astype(int) < hi)
        subset = data[mask].copy()
        if len(subset) < 20:
            print(f"  Skipping age {lo}–{hi-1}: only {len(subset)} rows")
            continue
        label = f"Age {lo}–{hi-1}"
        result = run_ols_clustered(formula, subset, "week", label)
        cohort_idx = [i for i in result.params.index if "cohort" in i]
        if cohort_idx:
            idx = cohort_idx[0]
            results.append({
                "age_bin": label,
                "coef": result.params[idx],
                "se": result.bse[idx],
                "t": result.tvalues[idx],
                "pval": result.pvalues[idx],
                "ci_lo": result.conf_int().loc[idx, 0],
                "ci_hi": result.conf_int().loc[idx, 1],
                "n": int(result.nobs),
            })
    return results


# Age bins available per cohort group (defined by ONS observation window)
COHORT_AGE_BINS = {
    1: [(20, 30), (30, 40), (40, 50), (50, 60), (60, 70)],   # NSHD: ages 22–69
    2: [(10, 20), (20, 30), (30, 40), (40, 50), (50, 58)],   # NCDS: ages 10–57
    3: [(0, 10),  (10, 20), (20, 30), (30, 40), (40, 46)],   # BCS70: ages 0–45
}
COHORT_NAMES = {1: "NSHD 1946", 2: "NCDS 1958", 3: "BCS70 1970"}


# ---------------------------------------------------------------------------
# By-cohort analysis
# ---------------------------------------------------------------------------

def run_by_cohort(df: pd.DataFrame) -> list[dict]:
    """
    Run pooled + age-interval regressions separately for each of the three
    cohort groups. Returns list of dicts suitable for CSV/JSON output.
    """
    results = []
    formula = "rate ~ cohort + C(age) + C(year) + C(week_in_year)"

    for grp, name in COHORT_NAMES.items():
        sub = df[df["year"].astype(int).isin(
            # year = birth_year in this dataset
            {1: range(1944, 1949), 2: range(1956, 1961), 3: range(1968, 1973)}[grp]
        )].copy()

        if len(sub) < 30:
            print(f"  [SKIP] {name}: insufficient rows ({len(sub)})")
            continue

        print(f"\n{'─'*60}")
        print(f"  Cohort group: {name}")
        r = run_ols_clustered(formula, sub, "week", f"[{name}] pooled")

        cohort_idx = [i for i in r.params.index if i == "cohort"]
        if not cohort_idx:
            cohort_idx = [i for i in r.params.index if "cohort" in i]
        if not cohort_idx:
            continue
        idx = cohort_idx[0]

        results.append({
            "group":   grp,
            "study":   name,
            "age_bin": "Pooled",
            "coef":    r.params[idx],
            "se":      r.bse[idx],
            "t":       r.tvalues[idx],
            "pval":    r.pvalues[idx],
            "ci_lo":   r.conf_int().loc[idx, 0],
            "ci_hi":   r.conf_int().loc[idx, 1],
            "n":       int(r.nobs),
        })

        # Age-interval regressions within cohort
        age_intervals = run_age_intervals(sub, COHORT_AGE_BINS[grp])
        for row in age_intervals:
            row["group"] = grp
            row["study"] = name
            results.append(row)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_one_dataset(df: pd.DataFrame, label: str) -> dict:
    """Run Spec 1 pooled + age-interval regressions on one dataset. Return results dict."""
    print(f"\n{'='*70}")
    print(f"  Dataset: {label}")
    print(f"{'='*70}")

    formula = "rate ~ cohort + C(age) + C(year) + C(week_in_year)"
    r1 = run_ols_clustered(formula, df, "week",
                           f"[{label}] Spec 1 — pooled")

    age_bins = [(0, 10), (10, 20), (20, 30), (30, 40),
                (40, 50), (50, 60), (60, 70)]
    intervals = run_age_intervals(df, age_bins)

    return {"pooled": r1, "intervals": intervals}


def compare_results(res_legacy: dict, res_fresh: dict) -> None:
    """Print a side-by-side comparison of cohort coefficients."""
    print(f"\n{'='*70}")
    print("  CROSS-DATASET COMPARISON (tolerance goal: 3 sig figs)")
    print(f"{'='*70}")

    # Pooled
    coef_l = res_legacy["pooled"].params.filter(like="cohort").iloc[0]
    se_l   = res_legacy["pooled"].bse.filter(like="cohort").iloc[0]
    coef_f = res_fresh["pooled"].params.filter(like="cohort").iloc[0]
    se_f   = res_fresh["pooled"].bse.filter(like="cohort").iloc[0]
    match  = "✅" if abs(coef_l - coef_f) < 0.001 else "⚠️"
    print(f"\n  Pooled cohort coefficient:")
    print(f"    Legacy: {coef_l:.6f}  (SE {se_l:.6f})")
    print(f"    Fresh:  {coef_f:.6f}  (SE {se_f:.6f})")
    print(f"    Diff:   {coef_f - coef_l:.6f}  {match}")

    # Age intervals
    if res_legacy["intervals"] and res_fresh["intervals"]:
        df_l = pd.DataFrame(res_legacy["intervals"]).set_index("age_bin")
        df_f = pd.DataFrame(res_fresh["intervals"]).set_index("age_bin")
        print(f"\n  Age-interval cohort coefficients:")
        print(f"  {'Age':10s}  {'Legacy':>10s}  {'Fresh':>10s}  {'Diff':>10s}  Match")
        for bin_label in df_l.index:
            if bin_label in df_f.index:
                cl = df_l.loc[bin_label, "coef"]
                cf = df_f.loc[bin_label, "coef"]
                ok = "✅" if abs(cl - cf) < 0.01 else "⚠️"
                print(f"  {bin_label:10s}  {cl:10.4f}  {cf:10.4f}  {cf-cl:10.4f}  {ok}")


if __name__ == "__main__":
    print("=" * 70)
    print("  Replication: Stata Age Final.do + Age Intervals.do → Python")
    print("  Running on BOTH legacy and fresh-ONS datasets for cross-validation")
    print("=" * 70)

    print("\nLoading datasets...")
    df_legacy = load_legacy()
    df_fresh  = load_fresh()

    # -----------------------------------------------------------
    # Run on legacy data
    # -----------------------------------------------------------
    res_legacy = run_one_dataset(df_legacy, "LEGACY")

    # -----------------------------------------------------------
    # Run on fresh ONS data (if available)
    # -----------------------------------------------------------
    res_fresh = None
    if not df_fresh.empty:
        res_fresh = run_one_dataset(df_fresh, "FRESH (ONS)")

    # -----------------------------------------------------------
    # Cross-dataset comparison
    # -----------------------------------------------------------
    if res_fresh is not None:
        compare_results(res_legacy, res_fresh)

    # -----------------------------------------------------------
    # Save outputs (use legacy as canonical until fully validated)
    # -----------------------------------------------------------
    r1 = res_legacy["pooled"]
    for suffix, result in [("spec1_pooled", r1)]:
        tidy = pd.DataFrame({
            "coef": result.params,
            "se": result.bse,
            "t": result.tvalues,
            "pval": result.pvalues,
            "ci_lo": result.conf_int()[0],
            "ci_hi": result.conf_int()[1],
        })
        tidy.to_csv(OUT_TABLES / f"02_{suffix}_full.csv")

    interval_results = res_legacy["intervals"]
    if interval_results:
        df_intervals = pd.DataFrame(interval_results)
        df_intervals.to_csv(OUT_TABLES / "02_age_intervals_cohort_coef.csv", index=False)
        print(f"\n\nAge-interval cohort coefficients (legacy, canonical):")
        print(df_intervals.to_string(index=False))

    # Save fresh-data intervals too if available
    if res_fresh and res_fresh["intervals"]:
        df_fresh_int = pd.DataFrame(res_fresh["intervals"])
        df_fresh_int.to_csv(OUT_TABLES / "02_fresh_age_intervals_cohort_coef.csv", index=False)

    # -----------------------------------------------------------
    # By-cohort analysis (legacy data, canonical)
    # -----------------------------------------------------------
    print("\n\n" + "="*70)
    print("  By-cohort regressions (NSHD / NCDS / BCS70 separately)")
    print("="*70)
    by_cohort_results = run_by_cohort(df_legacy)
    if by_cohort_results:
        df_bc = pd.DataFrame(by_cohort_results)
        df_bc.to_csv(OUT_TABLES / "02_by_cohort_coef.csv", index=False)
        print(f"\n\nBy-cohort summary:")
        print(df_bc[["study","age_bin","coef","se","pval","n"]].to_string(index=False))

    import importlib
    session = {
        "python": sys.version,
        "packages": {
            pkg: importlib.import_module(pkg).__version__
            for pkg in ["pandas", "statsmodels", "numpy"]
        },
        "data_sources": {
            "legacy": str(LEGACY_AGE),
            "fresh":  str(FRESH_AGE),
        }
    }
    with open(OUT_TABLES / "02_session_info.json", "w") as f:
        json.dump(session, f, indent=2)

    print(f"\n\nOutputs written to {OUT_TABLES}")
    print("Done.")
