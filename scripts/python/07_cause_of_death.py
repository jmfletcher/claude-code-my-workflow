"""
07_cause_of_death.py
Cause-of-death analysis for the appendix.
Examines whether drug-responsive causes declined differentially for 75+ after the policy.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from config import FIGURES_DIR, TABLES_DIR, PROCESSED_DIR

CAUSE_LABELS = {
    "S000": "All causes",
    "S002": "Neoplasms",
    "S004": "Endocrine/metabolic",
    "S007": "Circulatory system",
    "S008": "Respiratory system",
    "S009": "Digestive system",
}

DRUG_RESPONSIVE = ["S007", "S008", "S004"]


def load_and_prepare():
    df = pd.read_parquet(PROCESSED_DIR / "poland_cause_of_death.parquet")
    # Sex: 1=male, 2=female, 3=total; rates per 100,000
    df = df[df["Sex"] == 3].copy()  # total
    df = df[~df["Year"].isin([2020, 2021])].copy()
    return df


def build_elderly_series(df, causes, age_cols_treated=["m75", "m80", "m85p"],
                         age_cols_control=["m65", "m70"]):
    """Build time series of average mortality rate for treated and control ages, by cause."""
    rows = []
    for cause in causes:
        cdf = df[df["Cause"] == cause].copy()
        for _, row in cdf.iterrows():
            year = row["Year"]
            # Treated: average of 75-79, 80-84, 85+ rates
            treated_vals = [row[c] for c in age_cols_treated if c in row.index and pd.notna(row[c]) and row[c] != "."]
            control_vals = [row[c] for c in age_cols_control if c in row.index and pd.notna(row[c]) and row[c] != "."]
            treated_vals = [float(v) for v in treated_vals if str(v).replace(".", "").replace("-", "").strip() != ""]
            control_vals = [float(v) for v in control_vals if str(v).replace(".", "").replace("-", "").strip() != ""]

            if treated_vals and control_vals:
                rows.append({
                    "Year": year,
                    "Cause": cause,
                    "CauseLabel": CAUSE_LABELS.get(cause, cause),
                    "Treated_Rate": np.mean(treated_vals),
                    "Control_Rate": np.mean(control_vals),
                })
    return pd.DataFrame(rows)


def fig_cause_specific_trends(series_df):
    """Plot cause-specific mortality trends for treated vs control ages."""
    causes_to_plot = ["S007", "S008", "S004", "S002"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    for ax, cause in zip(axes.flat, causes_to_plot):
        cdf = series_df[series_df["Cause"] == cause].sort_values("Year")
        label = CAUSE_LABELS.get(cause, cause)

        ax.plot(cdf["Year"], cdf["Treated_Rate"] / 1000, "r-o", markersize=3,
                linewidth=1.5, label="Ages 75+ (treated)")
        ax.plot(cdf["Year"], cdf["Control_Rate"] / 1000, "b--s", markersize=3,
                linewidth=1.5, label="Ages 65-74 (control)")
        ax.axvline(2016.5, color="gray", linestyle="--", alpha=0.5)
        ax.set_title(f"{label}", fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel("Mortality Rate (per 1,000)")
        ax.legend(fontsize=8)
        ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

    fig.suptitle("Cause-Specific Mortality: Treated vs Control Ages",
                 fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figA2_cause_specific_did.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "figA2_cause_specific_did.png", bbox_inches="tight", dpi=300)
    plt.close()
    print("  Saved figA2_cause_specific_did")


def table_cause_specific_changes(series_df):
    """Compute pre-post changes for treated and control ages by cause."""
    rows = []
    for cause in ["S000", "S007", "S008", "S004", "S002", "S009"]:
        cdf = series_df[series_df["Cause"] == cause]
        pre = cdf[cdf["Year"].between(2000, 2015)]
        post = cdf[cdf["Year"].between(2017, 2019)]

        if len(pre) == 0 or len(post) == 0:
            continue

        pre_t = pre["Treated_Rate"].mean()
        post_t = post["Treated_Rate"].mean()
        pre_c = pre["Control_Rate"].mean()
        post_c = post["Control_Rate"].mean()

        chg_t = (post_t - pre_t) / pre_t * 100
        chg_c = (post_c - pre_c) / pre_c * 100
        diff_in_diff = chg_t - chg_c

        rows.append({
            "Cause": CAUSE_LABELS.get(cause, cause),
            "Pre Treated (per 100k)": f"{pre_t:.0f}",
            "Post Treated (per 100k)": f"{post_t:.0f}",
            "Change Treated (%)": f"{chg_t:.1f}",
            "Pre Control (per 100k)": f"{pre_c:.0f}",
            "Post Control (per 100k)": f"{post_c:.0f}",
            "Change Control (%)": f"{chg_c:.1f}",
            "DiD (pp)": f"{diff_in_diff:.1f}",
        })

    result = pd.DataFrame(rows)
    result.to_csv(TABLES_DIR / "tableA4_cause_specific.csv", index=False)
    print("\n  Cause-specific pre/post changes:")
    print(result.to_string(index=False))
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("Cause-of-Death Analysis")
    print("=" * 60)

    df = load_and_prepare()
    series_df = build_elderly_series(df, list(CAUSE_LABELS.keys()))

    print("\n1. Cause-specific trends figure:")
    fig_cause_specific_trends(series_df)

    print("\n2. Cause-specific pre/post changes table:")
    table_cause_specific_changes(series_df)

    print("\nDone.")
