"""
01_descriptive.py
Descriptive analysis and publication-quality figures for the paper.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from config import (
    FIGURES_DIR, TABLES_DIR, PROJECT_ROOT, PROCESSED_DIR, END_YEAR,
    POLICY_YEAR_75, POLICY_YEAR_65, BASELINE_START,
    VISEGRAD, CEE_BROAD, CAUSE_CODES, DRUG_RELEVANT_CAUSES,
)

DATA_DIR = PROCESSED_DIR
POST_END_YEAR = END_YEAR if END_YEAR is not None else 2023


def load_data():
    pol = pd.read_parquet(DATA_DIR / "poland_mortality_1x1.parquet")
    pol_ag = pd.read_parquet(DATA_DIR / "poland_age_groups.parquet")
    cross_ag = pd.read_parquet(DATA_DIR / "cross_country_age_groups.parquet")
    pol_cause = pd.read_parquet(DATA_DIR / "poland_cause_of_death.parquet")
    return pol, pol_ag, cross_ag, pol_cause


def fig1_poland_mortality_by_age_group(pol_ag):
    """Poland mortality rates by age group over time, with policy lines."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=False)

    groups = ["60-64", "65-69", "70-74", "75-79", "80-84", "85-89"]
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(groups)))

    for ax, sex, title in zip(axes, ["mx_total", "mx_male", "mx_female"],
                                ["Both Sexes", "Male", "Female"]):
        for g, c in zip(groups, colors):
            sub = pol_ag[pol_ag["AgeGroup"] == g].sort_values("Year")
            ax.plot(sub["Year"], sub[sex] * 1000, label=g, color=c, linewidth=1.5)

        ax.axvline(POLICY_YEAR_75, color="red", linestyle="--", alpha=0.7, linewidth=1)
        ax.axvline(POLICY_YEAR_65, color="blue", linestyle="--", alpha=0.7, linewidth=1)
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Year")
        ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

    axes[0].set_ylabel("Death Rate (per 1,000)")
    axes[0].legend(title="Age Group", fontsize=8, loc="upper right")

    fig.suptitle("Poland: Age-Specific Mortality Rates, 2000-2023", fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig1_poland_mortality_by_age.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "fig1_poland_mortality_by_age.png", bbox_inches="tight", dpi=300)
    plt.close()
    print("  Saved fig1_poland_mortality_by_age")


def fig2_poland_mortality_treated_vs_control(pol_ag):
    """Mortality rate ratio: treated (75+) vs control (60-74)."""
    treated_groups = ["75-79", "80-84", "85-89"]
    control_groups = ["60-64", "65-69", "70-74"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for ax, sex, title in zip(axes, ["mx_total", "mx_male"],
                                ["Both Sexes", "Male"]):
        # Aggregate treated and control
        treated = pol_ag[pol_ag["AgeGroup"].isin(treated_groups)].groupby("Year").agg({
            f"deaths_{sex.split('_')[1]}": "sum",
            f"exp_{sex.split('_')[1]}": "sum"
        }).reset_index()
        s = sex.split("_")[1]
        treated["mx"] = treated[f"deaths_{s}"] / treated[f"exp_{s}"]

        control = pol_ag[pol_ag["AgeGroup"].isin(control_groups)].groupby("Year").agg({
            f"deaths_{s}": "sum",
            f"exp_{s}": "sum"
        }).reset_index()
        control["mx"] = control[f"deaths_{s}"] / control[f"exp_{s}"]

        merged = treated[["Year", "mx"]].merge(
            control[["Year", "mx"]], on="Year", suffixes=("_treated", "_control")
        )
        merged["ratio"] = merged["mx_treated"] / merged["mx_control"]
        # Normalize to 2015
        base = merged.loc[merged["Year"] == 2015, "ratio"].values[0]
        merged["ratio_norm"] = merged["ratio"] / base

        ax.plot(merged["Year"], merged["ratio_norm"], "k-o", markersize=4)
        ax.axvline(POLICY_YEAR_75, color="red", linestyle="--", alpha=0.7, label="Drugs 75+ (2016)")
        ax.axvline(POLICY_YEAR_65, color="blue", linestyle="--", alpha=0.7, label="Drugs 65+ (2023)")
        ax.axhline(1.0, color="gray", linestyle=":", alpha=0.5)
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel("Mortality Ratio (75+ / 60-74)\nNormalized to 2015 = 1")
        ax.legend(fontsize=9)
        ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

    fig.suptitle("Poland: Relative Mortality of Treated vs Control Age Groups",
                 fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_treated_vs_control_ratio.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "fig2_treated_vs_control_ratio.png", bbox_inches="tight", dpi=300)
    plt.close()
    print("  Saved fig2_treated_vs_control_ratio")


def fig3_cross_country_elderly_mortality(cross_ag):
    """Elderly (75+) mortality comparison: Poland vs Visegrad."""
    elderly_groups = ["75-79", "80-84", "85-89"]
    countries = ["POL"] + VISEGRAD

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    country_colors = {"POL": "red", "CZE": "steelblue", "SVK": "green", "HUN": "orange"}
    country_names = {"POL": "Poland", "CZE": "Czech Republic", "SVK": "Slovakia", "HUN": "Hungary"}

    for ax, sex, title in zip(axes, ["total", "male"], ["Both Sexes", "Male"]):
        for ctry in countries:
            sub = cross_ag[
                (cross_ag["Country"] == ctry) & (cross_ag["AgeGroup"].isin(elderly_groups))
            ].copy()
            agg = sub.groupby("Year").agg({
                f"deaths_{sex}": "sum", f"exp_{sex}": "sum"
            }).reset_index()
            agg["mx"] = agg[f"deaths_{sex}"] / agg[f"exp_{sex}"]

            lw = 2.5 if ctry == "POL" else 1.2
            ax.plot(agg["Year"], agg["mx"] * 1000, label=country_names.get(ctry, ctry),
                    color=country_colors.get(ctry, "gray"), linewidth=lw)

        ax.axvline(POLICY_YEAR_75, color="red", linestyle="--", alpha=0.5, linewidth=1)
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Year")
        ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

    axes[0].set_ylabel("Death Rate, Ages 75-89 (per 1,000)")
    axes[0].legend(fontsize=9)

    fig.suptitle("Elderly Mortality: Poland vs Visegrad Countries", fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig3_cross_country_elderly.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "fig3_cross_country_elderly.png", bbox_inches="tight", dpi=300)
    plt.close()
    print("  Saved fig3_cross_country_elderly")


def fig4_parallel_trends_check(cross_ag):
    """Pre-trend check: Poland vs Visegrad average, by age group."""
    groups = ["60-64", "65-69", "70-74", "75-79", "80-84"]

    fig, axes = plt.subplots(1, len(groups), figsize=(18, 4), sharey=False)

    for ax, g in zip(axes, groups):
        # Poland
        pol = cross_ag[(cross_ag["Country"] == "POL") & (cross_ag["AgeGroup"] == g)].sort_values("Year")

        # Visegrad average
        vis = cross_ag[
            (cross_ag["Country"].isin(VISEGRAD)) & (cross_ag["AgeGroup"] == g)
        ].groupby("Year").agg({"deaths_total": "sum", "exp_total": "sum"}).reset_index()
        vis["mx_total"] = vis["deaths_total"] / vis["exp_total"]

        # Normalize both to 2010
        pol_base = pol.loc[pol["Year"] == 2010, "mx_total"].values
        vis_base = vis.loc[vis["Year"] == 2010, "mx_total"].values
        if len(pol_base) > 0 and len(vis_base) > 0 and pol_base[0] > 0 and vis_base[0] > 0:
            ax.plot(pol["Year"], pol["mx_total"] / pol_base[0], "r-", linewidth=2, label="Poland")
            ax.plot(vis["Year"], vis["mx_total"] / vis_base[0], "b--", linewidth=1.5, label="Visegrad avg")

        ax.axvline(POLICY_YEAR_75, color="red", linestyle=":", alpha=0.5)
        ax.set_title(f"Ages {g}", fontweight="bold", fontsize=10)
        ax.set_xlabel("Year")
        ax.axhline(1.0, color="gray", linestyle=":", alpha=0.3)
        ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

    axes[0].set_ylabel("Mortality (2010 = 1)")
    axes[0].legend(fontsize=8)

    fig.suptitle("Parallel Trends Check: Poland vs Visegrad Average (Normalized to 2010)",
                 fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig4_parallel_trends.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "fig4_parallel_trends.png", bbox_inches="tight", dpi=300)
    plt.close()
    print("  Saved fig4_parallel_trends")


def fig5_cause_specific_mortality(pol_cause):
    """Cause-specific death rates for drug-relevant causes, ages 75+."""
    # The cause data has age-specific rates in columns m0, m1, m5, m10, ..., m85p
    # We need the elderly columns
    elderly_cols = ["m75", "m80", "m85p"]
    available_cols = [c for c in elderly_cols if c in pol_cause.columns]

    if not available_cols:
        print("  WARNING: No elderly age columns found in cause data, skipping fig5")
        return

    causes_to_plot = {k: v for k, v in CAUSE_CODES.items() if k in DRUG_RELEVANT_CAUSES}

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    for ax, (code, name) in zip(axes.flat, causes_to_plot.items()):
        for sex_val, sex_name, color in [(1, "Female", "darkred"), (2, "Male", "navy")]:
            sub = pol_cause[(pol_cause["Cause"] == code) & (pol_cause["Sex"] == sex_val)].copy()
            if sub.empty:
                continue
            sub = sub.sort_values("Year")
            # Average across elderly age groups
            sub["mx_elderly"] = sub[available_cols].mean(axis=1)
            ax.plot(sub["Year"], sub["mx_elderly"], color=color, linewidth=1.5, label=sex_name)

        ax.axvline(POLICY_YEAR_75, color="red", linestyle="--", alpha=0.5, linewidth=1)
        ax.set_title(name, fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel("Death Rate (per 100,000)")
        ax.legend(fontsize=8)

    fig.suptitle("Poland: Cause-Specific Elderly Mortality (Ages 75+)", fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig5_cause_specific.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "fig5_cause_specific.png", bbox_inches="tight", dpi=300)
    plt.close()
    print("  Saved fig5_cause_specific")


def table1_summary_statistics(pol_ag, cross_ag):
    """Summary statistics table for the paper."""
    # Poland pre-period stats
    pre = pol_ag[pol_ag["Year"].between(BASELINE_START, 2015)]
    post = pol_ag[pol_ag["Year"].between(2017, POST_END_YEAR)]

    rows = []
    for ag in ["60-64", "65-69", "70-74", "75-79", "80-84", "85-89"]:
        pre_sub = pre[pre["AgeGroup"] == ag]
        post_sub = post[post["AgeGroup"] == ag]
        rows.append({
            "Age Group": ag,
            "Pre-Policy Mortality (per 1000)": f"{pre_sub['mx_total'].mean() * 1000:.1f}",
            "Post-Policy Mortality (per 1000)": f"{post_sub['mx_total'].mean() * 1000:.1f}",
            "Change (%)": f"{((post_sub['mx_total'].mean() - pre_sub['mx_total'].mean()) / pre_sub['mx_total'].mean()) * 100:.1f}",
            "Avg Annual Deaths": f"{pre_sub['deaths_total'].mean():,.0f}",
            "Avg Exposure": f"{pre_sub['exp_total'].mean():,.0f}",
        })

    table = pd.DataFrame(rows)
    table.to_csv(TABLES_DIR / "table1_summary_statistics.csv", index=False)
    print("  Saved table1_summary_statistics.csv")
    print(table.to_string(index=False))
    return table


def fig6_log_mortality_age_profiles(pol):
    """Log mortality age profiles for selected years."""
    fig, ax = plt.subplots(figsize=(10, 6))
    years = [2005, 2010, 2015, 2017, 2019]
    if POST_END_YEAR >= 2022:
        years.append(2022)
    colors = plt.cm.coolwarm(np.linspace(0, 1, len(years)))

    for yr, c in zip(years, colors):
        sub = pol[(pol["Year"] == yr) & (pol["Age"].between(55, 95))].sort_values("Age")
        ax.plot(sub["Age"], np.log(sub["mx_total"]), color=c, linewidth=1.5, label=str(yr))

    ax.axvline(75, color="red", linestyle="--", alpha=0.5, label="Age 75 threshold")
    ax.axvline(65, color="blue", linestyle="--", alpha=0.5, label="Age 65 threshold")
    ax.set_xlabel("Age")
    ax.set_ylabel("Log Mortality Rate")
    ax.set_title("Poland: Age-Mortality Profiles by Year", fontweight="bold")
    ax.legend(fontsize=9, ncol=2)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig6_log_mortality_profiles.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "fig6_log_mortality_profiles.png", bbox_inches="tight", dpi=300)
    plt.close()
    print("  Saved fig6_log_mortality_profiles")


if __name__ == "__main__":
    print("=" * 60)
    print("Descriptive Analysis")
    print("=" * 60)

    pol, pol_ag, cross_ag, pol_cause = load_data()

    print("\nGenerating figures...")
    fig1_poland_mortality_by_age_group(pol_ag)
    fig2_poland_mortality_treated_vs_control(pol_ag)
    fig3_cross_country_elderly_mortality(cross_ag)
    fig4_parallel_trends_check(cross_ag)
    fig5_cause_specific_mortality(pol_cause)
    fig6_log_mortality_age_profiles(pol)

    print("\nGenerating tables...")
    table1_summary_statistics(pol_ag, cross_ag)

    print("\n" + "=" * 60)
    print("Descriptive analysis complete.")
    print(f"Figures saved to: {FIGURES_DIR}")
    print(f"Tables saved to: {TABLES_DIR}")
    print("=" * 60)
