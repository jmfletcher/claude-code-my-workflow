"""
05_robustness_extended.py
Additional robustness checks for the within-Poland DiD:
  - Placebo treatment dates (appendix)
  - TWFE with age-specific linear trends
  - Narrow bandwidth (73-77)
  - Pre-COVID only (2017-2019)
  - Power calculations for cross-country designs
"""
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import statsmodels.formula.api as smf
from config import (
    FIGURES_DIR, TABLES_DIR, PROJECT_ROOT, PROCESSED_DIR,
    POLICY_YEAR_75, FIRST_FULL_TREATMENT_YEAR, BASELINE_START,
)

DATA_DIR = PROCESSED_DIR


def load_data():
    pol = pd.read_parquet(DATA_DIR / "poland_mortality_1x1.parquet")
    cross_ag = pd.read_parquet(DATA_DIR / "cross_country_age_groups.parquet")
    return pol, cross_ag


def build_did_panel(pol, age_window=10, exclude_covid=True, post_year=None):
    """Build DiD panel; optionally override the post-treatment year."""
    if post_year is None:
        post_year = FIRST_FULL_TREATMENT_YEAR
    lower = 75 - age_window
    upper = 75 + age_window - 1
    df = pol[(pol["Age"] >= lower) & (pol["Age"] <= upper)].copy()
    if exclude_covid:
        df = df[~df["Year"].isin([2020, 2021])].copy()
    df["treated_age"] = (df["Age"] >= 75).astype(int)
    df["post"] = (df["Year"] >= post_year).astype(int)
    df["did"] = df["treated_age"] * df["post"]
    df["log_mx"] = np.log(df["mx_total"].clip(lower=1e-8))
    df["log_mx_male"] = np.log(df["mx_male"].clip(lower=1e-8))
    df["log_mx_female"] = np.log(df["mx_female"].clip(lower=1e-8))
    df["age_fe"] = df["Age"].astype(str)
    df["year_fe"] = df["Year"].astype(str)
    return df


# ── 1. Placebo treatment dates ──────────────────────────────────────

def placebo_treatment_dates(pol):
    """Estimate DiD with fake treatment dates in the pre-period."""
    results = []
    for fake_year in [2005, 2007, 2009, 2011, 2013]:
        df = pol[(pol["Age"] >= 65) & (pol["Age"] <= 84) &
                 (pol["Year"] >= 2000) & (pol["Year"] <= 2015)].copy()
        df["treated_age"] = (df["Age"] >= 75).astype(int)
        df["post"] = (df["Year"] >= fake_year).astype(int)
        df["did"] = df["treated_age"] * df["post"]
        df["log_mx"] = np.log(df["mx_total"].clip(lower=1e-8))
        df["age_fe"] = df["Age"].astype(str)
        df["year_fe"] = df["Year"].astype(str)

        model = smf.ols("log_mx ~ did + C(age_fe) + C(year_fe)", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["Age"]}
        )
        results.append({
            "Placebo Year": fake_year,
            "Coef": model.params.get("did", np.nan),
            "SE": model.bse.get("did", np.nan),
            "P-value": model.pvalues.get("did", np.nan),
            "N": int(model.nobs),
        })

    # Add the actual treatment year for comparison
    df_actual = build_did_panel(pol, age_window=10)
    model_actual = smf.ols("log_mx ~ did + C(age_fe) + C(year_fe)", data=df_actual).fit(
        cov_type="cluster", cov_kwds={"groups": df_actual["Age"]}
    )
    results.append({
        "Placebo Year": f"{FIRST_FULL_TREATMENT_YEAR} (actual)",
        "Coef": model_actual.params.get("did", np.nan),
        "SE": model_actual.bse.get("did", np.nan),
        "P-value": model_actual.pvalues.get("did", np.nan),
        "N": int(model_actual.nobs),
    })

    df_results = pd.DataFrame(results)
    df_results.to_csv(TABLES_DIR / "tableA1_placebo_dates.csv", index=False)
    print("\n  Placebo treatment dates:")
    print(df_results.to_string(index=False))
    return df_results


def fig_placebo_dates(placebo_results):
    """Plot placebo and actual coefficients."""
    fig, ax = plt.subplots(figsize=(8, 5))

    placebos = placebo_results[~placebo_results["Placebo Year"].astype(str).str.contains("actual")]
    actual = placebo_results[placebo_results["Placebo Year"].astype(str).str.contains("actual")]

    ax.errorbar(range(len(placebos)), placebos["Coef"].values,
                yerr=1.96 * placebos["SE"].values,
                fmt="o", color="gray", capsize=4, markersize=6, label="Placebo dates")

    ax.errorbar([len(placebos)], actual["Coef"].values,
                yerr=1.96 * actual["SE"].values,
                fmt="D", color="red", capsize=5, markersize=8, label="Actual (2017)")

    ax.axhline(0, color="black", linewidth=0.8)
    labels = list(placebos["Placebo Year"].astype(str)) + ["2017\n(actual)"]
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_xlabel("Treatment Year")
    ax.set_ylabel("DiD Coefficient (Log Mortality)")
    ax.set_title("Placebo Treatment Dates", fontweight="bold")
    ax.legend()

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figA1_placebo_dates.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "figA1_placebo_dates.png", bbox_inches="tight", dpi=300)
    plt.close()
    print("  Saved figA1_placebo_dates")


# ── 2. TWFE with age-specific linear trends ─────────────────────────

def twfe_with_age_trends(pol):
    """TWFE DiD adding age-specific linear time trends."""
    df = build_did_panel(pol, age_window=10)
    df["year_num"] = df["Year"] - 2000
    df["age_trend"] = df["Age"] * df["year_num"]

    results = {}
    for sex, dep in [("Total", "log_mx"), ("Male", "log_mx_male"), ("Female", "log_mx_female")]:
        # Without age trends (baseline)
        m_base = smf.ols(f"{dep} ~ did + C(age_fe) + C(year_fe)", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["Age"]}
        )
        # With age-specific linear trends
        m_trend = smf.ols(f"{dep} ~ did + C(age_fe) + C(year_fe) + age_trend", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["Age"]}
        )

        results[sex] = {
            "coef_base": m_base.params["did"],
            "se_base": m_base.bse["did"],
            "pval_base": m_base.pvalues["did"],
            "coef_trend": m_trend.params["did"],
            "se_trend": m_trend.bse["did"],
            "pval_trend": m_trend.pvalues["did"],
        }
        print(f"  {sex}: Base = {results[sex]['coef_base']:.4f} (p={results[sex]['pval_base']:.4f}), "
              f"With trend = {results[sex]['coef_trend']:.4f} (p={results[sex]['pval_trend']:.4f})")

    rows = []
    for sex, r in results.items():
        rows.append({"Sex": sex, "Spec": "TWFE (baseline)", "Coef": r["coef_base"],
                      "SE": r["se_base"], "P-value": r["pval_base"]})
        rows.append({"Sex": sex, "Spec": "TWFE + age×year trend", "Coef": r["coef_trend"],
                      "SE": r["se_trend"], "P-value": r["pval_trend"]})
    pd.DataFrame(rows).to_csv(TABLES_DIR / "tableA2_age_trends.csv", index=False)
    return results


# ── 3. Narrow bandwidth (73–77) ─────────────────────────────────────

def narrow_bandwidth(pol):
    """DiD with very narrow bandwidth: ages 73-77 (2 years each side of 75)."""
    results = []
    for bw in [2, 3, 4, 5, 7, 10]:
        df = build_did_panel(pol, age_window=bw)
        model = smf.ols("log_mx ~ did + C(age_fe) + C(year_fe)", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["Age"]}
        )
        results.append({
            "Bandwidth": bw,
            "Ages": f"{75-bw}-{75+bw-1}",
            "Coef": model.params.get("did", np.nan),
            "SE": model.bse.get("did", np.nan),
            "P-value": model.pvalues.get("did", np.nan),
            "N": int(model.nobs),
        })

    df_results = pd.DataFrame(results)
    df_results.to_csv(TABLES_DIR / "table2_robustness_bandwidth.csv", index=False)
    print("\n  Extended bandwidth robustness (including narrow):")
    print(df_results.to_string(index=False))
    return df_results


def fig_bandwidth_extended(bw_results):
    """Plot extended bandwidth robustness including narrow windows."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(bw_results["Bandwidth"], bw_results["Coef"],
                yerr=1.96 * bw_results["SE"],
                fmt="o-", color="steelblue", capsize=4, markersize=6)
    ax.axhline(0, color="black", linewidth=0.8)
    for _, row in bw_results.iterrows():
        ax.annotate(row["Ages"], (row["Bandwidth"], row["Coef"]),
                    textcoords="offset points", xytext=(0, 12),
                    fontsize=8, ha="center", color="gray")
    ax.set_xlabel("Age Bandwidth (years from threshold)")
    ax.set_ylabel("DiD Coefficient (Log Mortality)")
    ax.set_title("Robustness: DiD Estimates by Age Bandwidth", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig8_robustness_bandwidth.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "fig8_robustness_bandwidth.png", bbox_inches="tight", dpi=300)
    plt.close()
    print("  Saved fig8_robustness_bandwidth")


# ── 4. Pre-COVID only (2017–2019) ────────────────────────────────────

def pre_covid_only(pol):
    """DiD using only 2017-2019 as post-period."""
    df = pol[(pol["Age"] >= 65) & (pol["Age"] <= 84)].copy()
    df = df[df["Year"].between(2000, 2019)].copy()
    df["treated_age"] = (df["Age"] >= 75).astype(int)
    df["post"] = (df["Year"] >= FIRST_FULL_TREATMENT_YEAR).astype(int)
    df["did"] = df["treated_age"] * df["post"]
    df["log_mx"] = np.log(df["mx_total"].clip(lower=1e-8))
    df["log_mx_male"] = np.log(df["mx_male"].clip(lower=1e-8))
    df["log_mx_female"] = np.log(df["mx_female"].clip(lower=1e-8))
    df["age_fe"] = df["Age"].astype(str)
    df["year_fe"] = df["Year"].astype(str)

    results = {}
    for sex, dep in [("Total", "log_mx"), ("Male", "log_mx_male"), ("Female", "log_mx_female")]:
        model = smf.ols(f"{dep} ~ did + C(age_fe) + C(year_fe)", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["Age"]}
        )
        results[sex] = {
            "coef": model.params["did"],
            "se": model.bse["did"],
            "pval": model.pvalues["did"],
            "n": model.nobs,
        }
        print(f"  {sex}: coef = {results[sex]['coef']:.4f} (SE = {results[sex]['se']:.4f}), "
              f"p = {results[sex]['pval']:.4f}")
    return results


# ── 5. Power calculation for cross-country DiD ──────────────────────

def power_calculation(cross_ag):
    """
    Back-of-envelope power calculation.
    If the true effect is a 2% reduction in log mortality for elderly,
    how likely are we to detect it in the cross-country design?
    """
    elderly = cross_ag[cross_ag["AgeGroup"].isin(["75-79", "80-84"])].copy()
    elderly = elderly[~elderly["Year"].isin([2020, 2021])].copy()
    elderly["log_mx"] = np.log(elderly["mx_total"].clip(lower=1e-8))

    residual_sd = elderly.groupby(["Country", "AgeGroup"])["log_mx"].apply(
        lambda x: x.diff().std()
    ).mean()

    n_countries = elderly["Country"].nunique()
    n_years_post = len([y for y in elderly["Year"].unique() if y >= 2017])
    n_years_pre = len([y for y in elderly["Year"].unique() if y < 2017])
    n_age_groups = 2

    total_post_obs = n_countries * n_years_post * n_age_groups
    se_approx = residual_sd / np.sqrt(total_post_obs)

    effects = [0.01, 0.02, 0.03, 0.05, 0.08]
    results = []
    for effect in effects:
        z_score = abs(effect) / se_approx
        power = 1 - 0.5 * (1 + math.erf(-((z_score - 1.96) / np.sqrt(2))))
        results.append({
            "True Effect (log pts)": effect,
            "True Effect (%)": f"{(np.exp(-effect)-1)*100:.1f}%",
            "Approx SE": f"{se_approx:.4f}",
            "Power (approx)": f"{power:.2f}",
        })

    df_results = pd.DataFrame(results)
    df_results.to_csv(TABLES_DIR / "tableA3_power_calculation.csv", index=False)
    print("\n  Power calculation (cross-country DiD):")
    print(f"  Residual SD of log-mortality changes: {residual_sd:.4f}")
    print(f"  Countries: {n_countries}, Post-years: {n_years_post}, Age groups: {n_age_groups}")
    print(f"  Approx SE: {se_approx:.4f}")
    print(df_results.to_string(index=False))
    return df_results, residual_sd


if __name__ == "__main__":
    print("=" * 60)
    print("Extended Robustness Checks")
    print("=" * 60)

    pol, cross_ag = load_data()

    print("\n1. Placebo treatment dates (appendix):")
    placebo_results = placebo_treatment_dates(pol)
    fig_placebo_dates(placebo_results)

    print("\n2. TWFE with age-specific linear trends:")
    age_trend_results = twfe_with_age_trends(pol)

    print("\n3. Extended bandwidth robustness (including narrow):")
    bw_results = narrow_bandwidth(pol)
    fig_bandwidth_extended(bw_results)

    print("\n4. Pre-COVID only (2017-2019):")
    precovid = pre_covid_only(pol)

    print("\n5. Power calculation:")
    power_results, _ = power_calculation(cross_ag)

    print("\n" + "=" * 60)
    print("Extended robustness complete.")
    print("=" * 60)
