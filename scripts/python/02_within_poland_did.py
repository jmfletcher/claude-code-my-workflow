"""
02_within_poland_did.py
Strategy 1: Within-Poland age-based Difference-in-Differences.
Exploits the age-75 eligibility threshold introduced in September 2016.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import statsmodels.formula.api as smf
from config import (
    FIGURES_DIR, TABLES_DIR, PROJECT_ROOT, PROCESSED_DIR,
    POLICY_YEAR_75, FIRST_FULL_TREATMENT_YEAR,
    BASELINE_START,
)

DATA_DIR = PROCESSED_DIR


def load_data():
    pol = pd.read_parquet(DATA_DIR / "poland_mortality_1x1.parquet")
    pol_ag = pd.read_parquet(DATA_DIR / "poland_age_groups.parquet")
    return pol, pol_ag


# ── 1. Single-year age DiD around the 75 threshold ──────────────────────

def build_did_panel(pol, age_window=10, exclude_covid=True):
    """
    Build a DiD panel using single-year ages around the 75 threshold.
    Treatment: ages 75-84, Control: ages 65-74.
    """
    lower = 75 - age_window
    upper = 75 + age_window - 1

    df = pol[(pol["Age"] >= lower) & (pol["Age"] <= upper)].copy()

    if exclude_covid:
        df = df[~df["Year"].isin([2020, 2021])].copy()

    df["treated_age"] = (df["Age"] >= 75).astype(int)
    df["post"] = (df["Year"] >= FIRST_FULL_TREATMENT_YEAR).astype(int)
    df["did"] = df["treated_age"] * df["post"]

    df["log_mx"] = np.log(df["mx_total"].clip(lower=1e-8))
    df["log_mx_male"] = np.log(df["mx_male"].clip(lower=1e-8))
    df["log_mx_female"] = np.log(df["mx_female"].clip(lower=1e-8))

    df["age_fe"] = df["Age"].astype(str)
    df["year_fe"] = df["Year"].astype(str)

    return df


def estimate_basic_did(df):
    """Simple 2x2 DiD on log mortality."""
    results = {}
    for sex, dep in [("Total", "log_mx"), ("Male", "log_mx_male"), ("Female", "log_mx_female")]:
        model = smf.ols(f"{dep} ~ treated_age * post", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["Age"]}
        )
        results[sex] = {
            "coef": model.params.get("treated_age:post", np.nan),
            "se": model.bse.get("treated_age:post", np.nan),
            "pval": model.pvalues.get("treated_age:post", np.nan),
            "n": model.nobs,
        }
        print(f"  {sex}: DiD coef = {results[sex]['coef']:.4f} (SE = {results[sex]['se']:.4f}), "
              f"p = {results[sex]['pval']:.4f}")
    return results


def estimate_twfe_did(df):
    """Two-way FE DiD with age and year fixed effects."""
    results = {}
    for sex, dep in [("Total", "log_mx"), ("Male", "log_mx_male"), ("Female", "log_mx_female")]:
        model = smf.ols(f"{dep} ~ did + C(age_fe) + C(year_fe)", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["Age"]}
        )
        results[sex] = {
            "coef": model.params.get("did", np.nan),
            "se": model.bse.get("did", np.nan),
            "pval": model.pvalues.get("did", np.nan),
            "n": model.nobs,
            "r2": model.rsquared,
        }
        print(f"  {sex}: TWFE coef = {results[sex]['coef']:.4f} (SE = {results[sex]['se']:.4f}), "
              f"p = {results[sex]['pval']:.4f}, R² = {results[sex]['r2']:.4f}")
    return results


# ── 2. Event study around the 2016 policy ─────────────────────────────

def estimate_event_study(df):
    """Event study with year-by-treatment interactions."""
    df = df.copy()
    ref_year = 2015
    years = sorted(df["Year"].unique())

    df["event_year"] = df["Year"]
    dummies = []
    for yr in years:
        if yr == ref_year:
            continue
        col = f"yr_{yr}"
        df[col] = ((df["Year"] == yr) & (df["treated_age"] == 1)).astype(int)
        dummies.append(col)

    formula = "log_mx ~ " + " + ".join(dummies) + " + C(age_fe) + C(year_fe)"
    model = smf.ols(formula, data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["Age"]}
    )

    event_coefs = []
    for yr in years:
        if yr == ref_year:
            event_coefs.append({"Year": yr, "coef": 0.0, "se": 0.0, "ci_lo": 0.0, "ci_hi": 0.0})
            continue
        col = f"yr_{yr}"
        if col in model.params:
            coef = model.params[col]
            se = model.bse[col]
            event_coefs.append({
                "Year": yr, "coef": coef, "se": se,
                "ci_lo": coef - 1.96 * se, "ci_hi": coef + 1.96 * se
            })

    return pd.DataFrame(event_coefs)


def fig_event_study(event_df, title_suffix=""):
    """Plot event study coefficients."""
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.fill_between(event_df["Year"], event_df["ci_lo"], event_df["ci_hi"],
                     alpha=0.2, color="steelblue")
    ax.plot(event_df["Year"], event_df["coef"], "o-", color="steelblue",
            markersize=5, linewidth=1.5)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(POLICY_YEAR_75 + 0.5, color="red", linestyle="--", alpha=0.7,
               label="Drugs 75+ (Sep 2016)")

    ax.set_xlabel("Year")
    ax.set_ylabel("DiD Coefficient (Log Mortality)")
    ax.set_title(f"Event Study: Effect of Free Drugs on Elderly Mortality{title_suffix}",
                 fontweight="bold")
    ax.legend()
    ax.xaxis.set_major_locator(mticker.MultipleLocator(2))

    fig.tight_layout()
    suffix = title_suffix.replace(" ", "_").replace("(", "").replace(")", "").lower()
    fig.savefig(FIGURES_DIR / f"fig7_event_study{suffix}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / f"fig7_event_study{suffix}.png", bbox_inches="tight", dpi=300)
    plt.close()
    return fig


# ── 3. Age-group DiD (5-year groups) ────────────────────────────────

def estimate_age_group_did(pol_ag, exclude_covid=True):
    """DiD using 5-year age groups."""
    df = pol_ag[pol_ag["AgeGroup"].isin(["60-64", "65-69", "70-74", "75-79", "80-84"])].copy()

    if exclude_covid:
        df = df[~df["Year"].isin([2020, 2021])].copy()

    df["treated"] = df["AgeMin"].apply(lambda x: 1 if x >= 75 else 0)
    df["post"] = (df["Year"] >= FIRST_FULL_TREATMENT_YEAR).astype(int)
    df["did"] = df["treated"] * df["post"]
    df["log_mx"] = np.log(df["mx_total"].clip(lower=1e-8))

    model = smf.ols("log_mx ~ did + C(AgeGroup) + C(Year)", data=df).fit(
        cov_type="HC1"
    )
    print(f"\n  Age-group TWFE: coef = {model.params['did']:.4f} "
          f"(SE = {model.bse['did']:.4f}), p = {model.pvalues['did']:.4f}")
    return model


# ── 4. Robustness: varying the age bandwidth ────────────────────────

def robustness_bandwidth(pol):
    """Estimate DiD with varying age bandwidths around 75."""
    results = []
    for bw in [5, 7, 10, 12, 15]:
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
    print("\n  Bandwidth robustness:")
    print(df_results.to_string(index=False))
    return df_results


def fig_robustness_bandwidth(bw_results):
    """Plot bandwidth robustness."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(bw_results["Bandwidth"], bw_results["Coef"],
                yerr=1.96 * bw_results["SE"],
                fmt="o-", color="steelblue", capsize=4, markersize=6)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Age Bandwidth (years from threshold)")
    ax.set_ylabel("DiD Coefficient (Log Mortality)")
    ax.set_title("Robustness: DiD Estimates by Age Bandwidth", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig8_robustness_bandwidth.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "fig8_robustness_bandwidth.png", bbox_inches="tight", dpi=300)
    plt.close()
    print("  Saved fig8_robustness_bandwidth")


# ── 5. By-sex analysis ──────────────────────────────────────────────

def estimate_by_sex(pol):
    """Separate DiD estimates for males and females."""
    df = build_did_panel(pol, age_window=10)
    results = {}
    for sex, dep in [("Male", "log_mx_male"), ("Female", "log_mx_female")]:
        model = smf.ols(f"{dep} ~ did + C(age_fe) + C(year_fe)", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["Age"]}
        )
        results[sex] = {
            "coef": model.params["did"],
            "se": model.bse["did"],
            "pval": model.pvalues["did"],
        }
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Strategy 1: Within-Poland Age-Based DiD")
    print("=" * 60)

    pol, pol_ag = load_data()

    # Build panel
    print("\n1. Basic DiD (no fixed effects):")
    df = build_did_panel(pol, age_window=10)
    basic_results = estimate_basic_did(df)

    print("\n2. Two-Way FE DiD:")
    twfe_results = estimate_twfe_did(df)

    print("\n3. Event Study:")
    event_df = estimate_event_study(df)
    fig_event_study(event_df)
    print("  Saved fig7_event_study")

    # By sex event studies
    for sex, dep in [("Male", "log_mx_male"), ("Female", "log_mx_female")]:
        df_sex = df.copy()
        df_sex["log_mx"] = df_sex[dep]
        ev = estimate_event_study(df_sex)
        fig_event_study(ev, f" ({sex})")

    print("\n4. Age-Group DiD:")
    ag_model = estimate_age_group_did(pol_ag)

    print("\n5. Robustness by bandwidth:")
    bw_results = robustness_bandwidth(pol)
    fig_robustness_bandwidth(bw_results)

    print("\n6. By-sex estimates:")
    sex_results = estimate_by_sex(pol)
    for sex, res in sex_results.items():
        print(f"  {sex}: coef = {res['coef']:.4f} (SE = {res['se']:.4f}), p = {res['pval']:.4f}")

    # Save main results table
    main_results = []
    for spec, res_dict in [("Basic DiD", basic_results), ("TWFE DiD", twfe_results)]:
        for sex, res in res_dict.items():
            main_results.append({"Specification": spec, "Sex": sex, **res})
    pd.DataFrame(main_results).to_csv(TABLES_DIR / "table3_within_poland_did.csv", index=False)

    print("\n" + "=" * 60)
    print("Within-Poland DiD analysis complete.")
    print("=" * 60)
