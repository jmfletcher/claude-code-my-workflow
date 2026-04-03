"""
06_robustness.py
================
Panel Conditioning (UK cohorts) — robustness checks.

The treated week sits at week_in_year = 8 out of 9 (asymmetric: 7 control
weeks before, 1 after). This script tests six alternative specifications
plus a permutation / randomisation-inference test:

  R1  Narrow window-1:  weeks 5–9 only  (3 pre + 1 post = 4 controls)
  R2  Narrow window-2:  weeks 6–9 only  (2 pre + 1 post = 3 controls)
  R3  Log outcome:      log(rate + ε) instead of level rate
  R4  Leave-one-out NSHD: drop NSHD group, keep NCDS + BCS70
  R5  Leave-one-out NCDS: drop NCDS group, keep NSHD + BCS70
  R6  Leave-one-out BCS70: drop BCS70 group, keep NSHD + NCDS

  R7  Permutation test (exact): rotate the treated label to each of the
      8 alternative week positions within the target birth years,
      re-estimate the baseline regression, and report the rank-based
      permutation p-value. With only 3 treated clusters, conventional
      clustered SEs may not reliably control size; permutation inference
      does not rely on asymptotic approximations.

Baseline (B): weeks 1–9, level rate, all three cohorts, birth-year FE.

Outputs:
  output/tables/06_robustness_coef.csv
  output/tables/06_permutation_dist.csv   (placebo coefficients)
  output/figures/fig06_robustness.pdf/.png
  output/figures/fig06_permutation.pdf/.png

Run from repo root:
    python3 analysis/06_robustness.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT    = Path(__file__).resolve().parent.parent
OUT_TAB = ROOT / "output" / "tables"
OUT_FIG = ROOT / "output" / "figures"
OUT_TAB.mkdir(parents=True, exist_ok=True)
OUT_FIG.mkdir(parents=True, exist_ok=True)

AGE_AGG = OUT_TAB / "01_age_aggregated.csv"

TREATED_WIY = 8   # week_in_year position of the treated week in each cluster
N_PER_WEEK  = 15_334.0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_data() -> pd.DataFrame:
    df = pd.read_csv(AGE_AGG)
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df = df[df["age"].between(1, 69)].copy()
    # String-encode FE variables
    df["birth_year_str"] = df["birth_year"].astype(str)
    df["age_str"]        = df["age"].astype(str)
    df["wiy_str"]        = df["week_in_year"].astype(str)
    return df


def run_ols(formula: str, data: pd.DataFrame, cluster_col: str,
            label: str) -> dict | None:
    if len(data) < 30 or data["cohort"].nunique() < 2:
        print(f"  [SKIP] {label}: insufficient data ({len(data)} rows)")
        return None
    try:
        r = smf.ols(formula, data=data).fit(
            cov_type="cluster",
            cov_kwds={"groups": data[cluster_col]},
        )
        idx = next((i for i in r.params.index if i == "cohort"), None)
        if idx is None:
            idx = next((i for i in r.params.index if "cohort" in i), None)
        if idx is None:
            return None
        ci = r.conf_int()
        return {
            "spec":  label,
            "coef":  float(r.params[idx]),
            "se":    float(r.bse[idx]),
            "t":     float(r.tvalues[idx]),
            "pval":  float(r.pvalues[idx]),
            "ci_lo": float(ci.loc[idx, 0]),
            "ci_hi": float(ci.loc[idx, 1]),
            "n":     int(r.nobs),
        }
    except Exception as e:
        print(f"  [WARN] {label}: {e}")
        return None


BASE_FORMULA = "rate ~ cohort + C(age_str) + C(birth_year_str) + C(wiy_str)"
LOG_FORMULA  = "log_rate ~ cohort + C(age_str) + C(birth_year_str) + C(wiy_str)"

# ---------------------------------------------------------------------------
# Run all specifications
# ---------------------------------------------------------------------------

def run_all(df: pd.DataFrame) -> list[dict]:
    results = []

    # Baseline
    r = run_ols(BASE_FORMULA, df, "birth_week", "B: Baseline (all weeks, level rate)")
    if r:
        results.append(r)

    # R1: Narrow window — weeks 5–9 only (3 pre + 1 post control)
    df_r1 = df[(df["week_in_year"] >= 5) | (df["cohort"] == 1)].copy()
    df_r1 = df_r1[df_r1["week_in_year"].isin(range(5, TREATED_WIY + 2))]
    r = run_ols(BASE_FORMULA, df_r1, "birth_week", "R1: Narrow window (weeks 5–9)")
    if r:
        results.append(r)

    # R2: Very narrow window — weeks 6–9 only (2 pre + 1 post control)
    df_r2 = df[df["week_in_year"].isin(range(6, TREATED_WIY + 2))].copy()
    r = run_ols(BASE_FORMULA, df_r2, "birth_week", "R2: Narrow window (weeks 6–9)")
    if r:
        results.append(r)

    # R3: Log outcome
    eps = 0.001  # avoid log(0)
    df_r3 = df.copy()
    df_r3["log_rate"] = np.log(df_r3["rate"].clip(lower=eps))
    r = run_ols(LOG_FORMULA, df_r3, "birth_week", "R3: Log outcome (log rate)")
    if r:
        results.append(r)

    # R4: Leave out NSHD (keep NCDS + BCS70)
    df_r4 = df[df["group"].isin([2, 3])].copy()
    r = run_ols(BASE_FORMULA, df_r4, "birth_week", "R4: Drop NSHD (NCDS + BCS70)")
    if r:
        results.append(r)

    # R5: Leave out NCDS (keep NSHD + BCS70)
    df_r5 = df[df["group"].isin([1, 3])].copy()
    r = run_ols(BASE_FORMULA, df_r5, "birth_week", "R5: Drop NCDS (NSHD + BCS70)")
    if r:
        results.append(r)

    # R6: Leave out BCS70 (keep NSHD + NCDS)
    df_r6 = df[df["group"].isin([1, 2])].copy()
    r = run_ols(BASE_FORMULA, df_r6, "birth_week", "R6: Drop BCS70 (NSHD + NCDS)")
    if r:
        results.append(r)

    return results


# ---------------------------------------------------------------------------
# Permutation / randomisation inference
# ---------------------------------------------------------------------------

# Target birth years for each group (the year the cohort study selected)
TARGET_YEARS = {1: 1946, 2: 1958, 3: 1970}

def run_permutation(df: pd.DataFrame) -> dict:
    """Rotate the treated label to each of the 8 alternative week positions
    (1–7, 9) in the target birth years and estimate the baseline regression.
    Returns the distribution of placebo coefficients and the rank-based
    permutation p-value.
    """
    target_mask = pd.Series(False, index=df.index)
    for grp, yr in TARGET_YEARS.items():
        target_mask |= ((df["group"] == grp) & (df["birth_year"] == yr))

    alt_positions = [p for p in range(1, 10) if p != TREATED_WIY]
    placebo_rows = []

    for pos in alt_positions:
        df_p = df.copy()
        df_p["cohort"] = 0
        df_p.loc[target_mask & (df_p["week_in_year"] == pos), "cohort"] = 1

        if df_p["cohort"].sum() == 0:
            continue
        r = run_ols(BASE_FORMULA, df_p, "birth_week",
                    f"Placebo pos={pos}")
        if r:
            placebo_rows.append({"position": pos, "coef": r["coef"],
                                  "se": r["se"], "pval": r["pval"]})

    if not placebo_rows:
        return {}

    placebo_df = pd.DataFrame(placebo_rows)

    # Estimate the true coefficient using the actual treated indicator
    true_r = run_ols(BASE_FORMULA, df, "birth_week", "True (pos=8)")
    if true_r is None:
        return {}
    true_coef = true_r["coef"]

    # Rank of true estimate in the full distribution (true + 8 placebos)
    all_coefs = list(placebo_df["coef"]) + [true_coef]
    n_total   = len(all_coefs)
    rank_1s   = sum(c >= true_coef for c in all_coefs)  # 1-sided (>=)
    perm_pval = rank_1s / n_total

    print(f"\n  Permutation test:")
    print(f"    True estimate:  {true_coef:.4f}")
    print(f"    Placebo range:  [{placebo_df['coef'].min():.4f}, "
          f"{placebo_df['coef'].max():.4f}]")
    print(f"    Rank (1-sided): {rank_1s} / {n_total}")
    print(f"    Permutation p:  {perm_pval:.3f}")

    return {
        "placebo_df":     placebo_df,
        "true_coef":      true_coef,
        "perm_pval_1s":   perm_pval,
        "n_total":        n_total,
    }


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

BLUE  = "#1a5276"
GRAY  = "#5d6d7e"
LGRAY = "#d5d8dc"
GREEN = "#1e8449"

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": LGRAY, "grid.linewidth": 0.6,
    "figure.dpi": 150,
})


def make_robustness_figure(results: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))

    y = np.arange(len(results))
    # Baseline row gets a distinct colour
    colors = []
    for _, row in results.iterrows():
        if row["spec"].startswith("B:"):
            colors.append(BLUE)
        elif row["pval"] < 0.05:
            colors.append(GREEN)
        else:
            colors.append(GRAY)

    ax.hlines(y, results["ci_lo"], results["ci_hi"],
              colors=colors, linewidth=2.5)
    ax.scatter(results["coef"], y, color=colors, s=65, zorder=5)
    ax.axvline(0, color="black", linewidth=0.9, linestyle="--")

    # Dotted line at baseline coefficient
    baseline_coef = results.loc[results["spec"].str.startswith("B:"), "coef"].iloc[0]
    ax.axvline(baseline_coef, color=BLUE, linewidth=0.9, linestyle=":", alpha=0.7)

    ax.set_yticks(y)
    ax.set_yticklabels(results["spec"], fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("Cohort coefficient (95% CI)", fontsize=10)
    ax.set_title(
        "Robustness checks: panel conditioning effect on mortality\n"
        "Blue = baseline; green = p < 0.05; grey = p ≥ 0.05",
        fontsize=11
    )

    # N annotation
    for i, row in results.reset_index(drop=True).iterrows():
        ax.text(results["ci_hi"].max() + 0.005, i,
                f"N={int(row['n']):,}", va="center", fontsize=8, color=GRAY)

    fig.tight_layout()
    for ext in ("pdf", "png"):
        p = OUT_FIG / f"fig06_robustness.{ext}"
        fig.savefig(p, bbox_inches="tight", dpi=300)
        print(f"  Saved: {p.name}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Permutation figure
# ---------------------------------------------------------------------------

def make_permutation_figure(placebo_df: pd.DataFrame, true_coef: float,
                             perm_pval: float) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(placebo_df["coef"], bins=8, color=LGRAY, edgecolor="white",
            zorder=2, label="Placebo estimates (alt. positions)")
    ax.axvline(true_coef, color=BLUE, linewidth=2.0, linestyle="-",
               label=f"True estimate ({true_coef:.3f})")
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Cohort coefficient", fontsize=10)
    ax.set_ylabel("Count of placebo positions", fontsize=10)
    ax.set_title(
        f"Permutation distribution: true vs. placebo estimates\n"
        f"1-sided permutation p = {perm_pval:.3f}  "
        f"(blue = true estimate at position 8)",
        fontsize=10,
    )
    ax.legend(fontsize=9)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        p = OUT_FIG / f"fig06_permutation.{ext}"
        fig.savefig(p, bbox_inches="tight", dpi=300)
        print(f"  Saved: {p.name}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("  06_robustness.py — robustness checks")
    print("=" * 70)

    if not AGE_AGG.exists():
        print(f"[ERROR] Run 01_load_and_clean.py first: {AGE_AGG}")
        sys.exit(1)

    print("\nLoading data...")
    df = load_data()
    print(f"  Baseline: {len(df):,} rows, {df['cohort'].sum():,} treated,",
          f"{(df['cohort']==0).sum():,} control")
    print(f"  week_in_year range: {df['week_in_year'].min()}–{df['week_in_year'].max()}",
          f"  |  treated at position: {TREATED_WIY}")

    print("\nRunning specifications (R1–R6)...")
    raw = run_all(df)

    results = pd.DataFrame(raw)
    results.to_csv(OUT_TAB / "06_robustness_coef.csv", index=False)

    print("\n\nRobustness check results:")
    print(results[["spec", "coef", "se", "pval", "n"]].to_string(index=False))

    print("\nRunning permutation test (R7)...")
    perm = run_permutation(df)

    if perm:
        perm["placebo_df"].to_csv(OUT_TAB / "06_permutation_dist.csv", index=False)
        import json
        perm_summary = {
            "true_coef":    perm["true_coef"],
            "perm_pval_1s": perm["perm_pval_1s"],
            "n_total":      perm["n_total"],
            "placebo_coefs": list(perm["placebo_df"]["coef"]),
        }
        (OUT_TAB / "06_permutation_summary.json").write_text(
            json.dumps(perm_summary, indent=2))
        print("\nGenerating permutation figure...")
        make_permutation_figure(
            perm["placebo_df"], perm["true_coef"], perm["perm_pval_1s"])

    print("\nGenerating robustness figure...")
    make_robustness_figure(results)

    print("\nDone.")
