"""
03_cross_country_did.py
Strategy 2: Cross-Country Difference-in-Differences.
Compares Poland's elderly mortality to comparable countries.
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
    FIRST_FULL_TREATMENT_YEAR, BASELINE_START,
    ALL_COMPARATORS, POLICY_YEAR_75,
)

DATA_DIR = PROCESSED_DIR

COUNTRY_NAMES = {
    "POL": "Poland", "CZE": "Czech Rep.", "SVK": "Slovakia", "HUN": "Hungary",
    "EST": "Estonia", "LTU": "Lithuania", "LVA": "Latvia", "HRV": "Croatia",
    "SVN": "Slovenia", "BGR": "Bulgaria", "AUT": "Austria", "DEU": "Germany",
    "ESP": "Spain", "ITA": "Italy",
}


def load_data():
    cross_ag = pd.read_parquet(DATA_DIR / "cross_country_age_groups.parquet")
    return cross_ag


def build_cross_country_panel(cross_ag, comparators, elderly_ages=None, exclude_covid=True):
    """Build panel for cross-country DiD."""
    if elderly_ages is None:
        elderly_ages = ["75-79", "80-84"]

    countries = ["POL"] + comparators
    df = cross_ag[cross_ag["Country"].isin(countries)].copy()

    if exclude_covid:
        df = df[~df["Year"].isin([2020, 2021])].copy()

    df["poland"] = (df["Country"] == "POL").astype(int)
    df["elderly"] = df["AgeGroup"].isin(elderly_ages).astype(int)
    df["post"] = (df["Year"] >= FIRST_FULL_TREATMENT_YEAR).astype(int)

    df["log_mx"] = np.log(df["mx_total"].clip(lower=1e-8))
    df["log_mx_male"] = np.log(df["mx_male"].clip(lower=1e-8))
    df["log_mx_female"] = np.log(df["mx_female"].clip(lower=1e-8))

    # Interaction terms
    df["pol_post"] = df["poland"] * df["post"]
    df["pol_elderly"] = df["poland"] * df["elderly"]
    df["elderly_post"] = df["elderly"] * df["post"]
    df["triple"] = df["poland"] * df["elderly"] * df["post"]

    df["country_age"] = df["Country"] + "_" + df["AgeGroup"]

    return df


# ── 1. Simple cross-country DiD (elderly only) ──────────────────────

def estimate_simple_did(df):
    """Simple DiD: Poland vs comparators, elderly groups only, pre/post."""
    elderly = df[df["elderly"] == 1].copy()

    results = {}
    for sex, dep in [("Total", "log_mx"), ("Male", "log_mx_male"), ("Female", "log_mx_female")]:
        model = smf.ols(
            f"{dep} ~ pol_post + C(country_age) + C(Year)",
            data=elderly
        ).fit(cov_type="cluster", cov_kwds={"groups": elderly["Country"]})

        results[sex] = {
            "coef": model.params.get("pol_post", np.nan),
            "se": model.bse.get("pol_post", np.nan),
            "pval": model.pvalues.get("pol_post", np.nan),
            "n": model.nobs,
        }
    return results


# ── 2. Triple-difference: (Poland × Elderly × Post) ─────────────────

def estimate_triple_diff(df):
    """Triple-diff: Poland × Elderly × Post, with full interactions and FE."""
    results = {}
    for sex, dep in [("Total", "log_mx"), ("Male", "log_mx_male"), ("Female", "log_mx_female")]:
        model = smf.ols(
            f"{dep} ~ triple + pol_post + pol_elderly + elderly_post + C(country_age) + C(Year)",
            data=df
        ).fit(cov_type="cluster", cov_kwds={"groups": df["Country"]})

        results[sex] = {
            "coef": model.params.get("triple", np.nan),
            "se": model.bse.get("triple", np.nan),
            "pval": model.pvalues.get("triple", np.nan),
            "n": model.nobs,
        }
    return results


# ── 3. Event study (year-by-year Poland × Elderly interactions) ──────

def estimate_cross_country_event_study(df):
    """Event study with year-by-Poland-by-Elderly interactions."""
    df = df.copy()
    ref_year = 2015
    years = sorted(df["Year"].unique())

    dummies = []
    for yr in years:
        if yr == ref_year:
            continue
        col = f"triple_{yr}"
        df[col] = ((df["Year"] == yr) & (df["poland"] == 1) & (df["elderly"] == 1)).astype(int)
        dummies.append(col)

    formula = "log_mx ~ " + " + ".join(dummies) + " + C(country_age) + C(Year)"
    model = smf.ols(formula, data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["Country"]}
    )

    event_coefs = []
    for yr in years:
        if yr == ref_year:
            event_coefs.append({"Year": yr, "coef": 0.0, "se": 0.0})
            continue
        col = f"triple_{yr}"
        if col in model.params:
            event_coefs.append({
                "Year": yr,
                "coef": model.params[col],
                "se": model.bse[col],
            })

    edf = pd.DataFrame(event_coefs)
    edf["ci_lo"] = edf["coef"] - 1.96 * edf["se"]
    edf["ci_hi"] = edf["coef"] + 1.96 * edf["se"]
    return edf


def fig_cross_country_event_study(event_df, set_name):
    """Plot cross-country event study."""
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.fill_between(event_df["Year"], event_df["ci_lo"], event_df["ci_hi"],
                     alpha=0.2, color="darkgreen")
    ax.plot(event_df["Year"], event_df["coef"], "o-", color="darkgreen",
            markersize=5, linewidth=1.5)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(POLICY_YEAR_75 + 0.5, color="red", linestyle="--", alpha=0.7,
               label="Drugs 75+ (Sep 2016)")

    ax.set_xlabel("Year")
    ax.set_ylabel("Triple-Diff Coefficient (Log Mortality)")
    ax.set_title(f"Cross-Country Event Study: Poland vs {set_name}",
                 fontweight="bold")
    ax.legend()
    ax.xaxis.set_major_locator(mticker.MultipleLocator(2))

    fig.tight_layout()
    safe_name = set_name.replace(" ", "_").replace("-", "_").lower()
    fig.savefig(FIGURES_DIR / f"fig9_cross_country_es_{safe_name}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / f"fig9_cross_country_es_{safe_name}.png", bbox_inches="tight", dpi=300)
    plt.close()


# ── 4. Visualization: Poland vs comparators time series ──────────────

def fig_cross_country_trends(cross_ag, comparators, set_name):
    """Time series of elderly mortality: Poland vs comparator average."""
    elderly_groups = ["75-79", "80-84"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for ax, sex, title in zip(axes, ["total", "male"], ["Both Sexes", "Male"]):
        # Poland
        pol = cross_ag[
            (cross_ag["Country"] == "POL") & (cross_ag["AgeGroup"].isin(elderly_groups))
        ].groupby("Year").agg({f"deaths_{sex}": "sum", f"exp_{sex}": "sum"}).reset_index()
        pol["mx"] = pol[f"deaths_{sex}"] / pol[f"exp_{sex}"]

        # Comparator average
        comp = cross_ag[
            (cross_ag["Country"].isin(comparators)) & (cross_ag["AgeGroup"].isin(elderly_groups))
        ].groupby("Year").agg({f"deaths_{sex}": "sum", f"exp_{sex}": "sum"}).reset_index()
        comp["mx"] = comp[f"deaths_{sex}"] / comp[f"exp_{sex}"]

        ax.plot(pol["Year"], pol["mx"] * 1000, "r-", linewidth=2, label="Poland")
        ax.plot(comp["Year"], comp["mx"] * 1000, "b--", linewidth=1.5, label=f"{set_name} avg")
        ax.axvline(POLICY_YEAR_75, color="red", linestyle=":", alpha=0.5)
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Year")
        ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

    axes[0].set_ylabel("Mortality Rate Ages 75-84 (per 1,000)")
    axes[0].legend()

    fig.suptitle(f"Elderly Mortality: Poland vs {set_name}", fontweight="bold", y=1.02)
    fig.tight_layout()
    safe_name = set_name.replace(" ", "_").replace("-", "_").lower()
    fig.savefig(FIGURES_DIR / f"fig10_trends_{safe_name}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / f"fig10_trends_{safe_name}.png", bbox_inches="tight", dpi=300)
    plt.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Strategy 2: Cross-Country Difference-in-Differences")
    print("=" * 60)

    cross_ag = load_data()

    all_results = []

    for set_name, comparators in ALL_COMPARATORS.items():
        print(f"\n{'─' * 40}")
        print(f"Comparator set: {set_name} ({', '.join(comparators)})")
        print(f"{'─' * 40}")

        # Check data availability
        available = cross_ag[cross_ag["Country"].isin(comparators)]["Country"].unique()
        missing = set(comparators) - set(available)
        if missing:
            print(f"  WARNING: Missing countries: {missing}")
            comparators = [c for c in comparators if c in available]

        df = build_cross_country_panel(cross_ag, comparators)

        print(f"\n  Panel: {len(df)} obs, {df.Country.nunique()} countries, "
              f"years {df.Year.min()}-{df.Year.max()}")

        # Simple DiD
        print("\n  Simple DiD (elderly only):")
        simple = estimate_simple_did(df)
        for sex, res in simple.items():
            print(f"    {sex}: coef = {res['coef']:.4f} (SE = {res['se']:.4f}), p = {res['pval']:.4f}")
            all_results.append({
                "Set": set_name, "Spec": "Simple DiD", "Sex": sex, **res
            })

        # Triple-diff
        print("\n  Triple-Difference:")
        triple = estimate_triple_diff(df)
        for sex, res in triple.items():
            print(f"    {sex}: coef = {res['coef']:.4f} (SE = {res['se']:.4f}), p = {res['pval']:.4f}")
            all_results.append({
                "Set": set_name, "Spec": "Triple-Diff", "Sex": sex, **res
            })

        # Event study
        print("\n  Event study...")
        event_df = estimate_cross_country_event_study(df)
        fig_cross_country_event_study(event_df, set_name)
        print(f"    Saved event study figure for {set_name}")

        # Trends figure
        fig_cross_country_trends(cross_ag, comparators, set_name)
        print(f"    Saved trends figure for {set_name}")

    # Save all results
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(TABLES_DIR / "table4_cross_country_did.csv", index=False)

    print("\n" + "=" * 60)
    print("Cross-country DiD analysis complete.")
    print("=" * 60)
