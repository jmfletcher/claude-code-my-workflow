"""
04_synthetic_control.py
Strategy 3: Synthetic Control Method.
Constructs a synthetic Poland from donor countries and runs placebo tests.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy.optimize import minimize
from config import (
    FIGURES_DIR, TABLES_DIR, PROJECT_ROOT, PROCESSED_DIR,
    FIRST_FULL_TREATMENT_YEAR, BASELINE_START, POLICY_YEAR_75,
    VISEGRAD, CEE_BROAD, END_YEAR,
)

DATA_DIR = PROCESSED_DIR
POST_END_YEAR = END_YEAR if END_YEAR is not None else 2023

# Countries to exclude from donor pool (implemented similar policies or data issues)
EXCLUDE_DONORS = []  # adjust if needed


def load_data():
    cross_ag = pd.read_parquet(DATA_DIR / "cross_country_age_groups.parquet")
    return cross_ag


def prepare_scm_data(cross_ag, age_groups, outcome_col="mx_total",
                     pre_start=2000, pre_end=2015, post_end=None,
                     exclude_covid=True):
    """Prepare data matrix for SCM: rows = years, columns = countries."""
    if post_end is None:
        post_end = POST_END_YEAR
    df = cross_ag[cross_ag["AgeGroup"].isin(age_groups)].copy()

    if exclude_covid:
        df = df[~df["Year"].isin([2020, 2021])]

    # Aggregate across age groups (weighted by exposure)
    sex = outcome_col.split("_")[1]
    agg = df.groupby(["Country", "Year"]).agg({
        f"deaths_{sex}": "sum", f"exp_{sex}": "sum"
    }).reset_index()
    agg["mx"] = agg[f"deaths_{sex}"] / agg[f"exp_{sex}"]

    # Pivot to wide format
    wide = agg.pivot(index="Year", columns="Country", values="mx")
    wide = wide[(wide.index >= pre_start) & (wide.index <= post_end)]

    # Separate treated and donors
    if "POL" not in wide.columns:
        raise ValueError("Poland not found in data")

    treated = wide["POL"]
    donors = wide.drop(columns=["POL"] + EXCLUDE_DONORS, errors="ignore")

    # Drop donors with missing data in pre-period
    pre_mask = donors.index <= pre_end
    donors = donors.loc[:, donors.loc[pre_mask].notna().all()]

    return treated, donors, pre_end


def synthetic_control(treated, donors, pre_end):
    """
    Estimate synthetic control weights via constrained optimization.
    Minimizes pre-treatment MSPE subject to weights summing to 1, non-negative.
    """
    pre_mask = treated.index <= pre_end
    Y1 = treated[pre_mask].values
    Y0 = donors[pre_mask].values

    n_donors = Y0.shape[1]

    def objective(w):
        synthetic = Y0 @ w
        return np.sum((Y1 - synthetic) ** 2)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = [(0, 1)] * n_donors
    w0 = np.ones(n_donors) / n_donors

    result = minimize(objective, w0, method="SLSQP",
                      bounds=bounds, constraints=constraints,
                      options={"maxiter": 1000, "ftol": 1e-12})

    weights = result.x
    weights[weights < 1e-4] = 0
    weights = weights / weights.sum()
    weights_series = pd.Series(weights, index=donors.columns)

    # Construct synthetic: for each year use only donors with non-NaN so post-period is not truncated
    synthetic_vals = np.zeros(len(donors))
    for i, year in enumerate(donors.index):
        row = donors.iloc[i]
        valid = row.notna()
        if valid.sum() == 0:
            synthetic_vals[i] = np.nan
        else:
            w = weights_series[valid].values.copy()
            w_sum = w.sum()
            if w_sum <= 0:
                synthetic_vals[i] = np.nan
            else:
                w = w / w_sum
                synthetic_vals[i] = np.dot(row[valid].values, w)
    synthetic_series = pd.Series(synthetic_vals, index=donors.index, name="Synthetic")

    # Pre-treatment MSPE
    pre_mspe = np.mean((Y1 - donors[pre_mask].values @ weights) ** 2)

    return weights, synthetic_series, pre_mspe


def placebo_test(treated, donors, pre_end, n_placebos=None):
    """Run placebo tests: treat each donor as if it were treated."""
    if n_placebos is None:
        n_placebos = len(donors.columns)

    placebo_gaps = {}

    for i, donor_name in enumerate(donors.columns[:n_placebos]):
        # Create a "treated" unit from this donor
        placebo_treated = donors[donor_name]
        placebo_donors = donors.drop(columns=[donor_name])

        # Add Poland back as a donor
        all_donors_with_pol = placebo_donors.copy()
        all_donors_with_pol["POL"] = treated

        try:
            _, placebo_synthetic, mspe = synthetic_control(
                placebo_treated, all_donors_with_pol, pre_end
            )
            gap = placebo_treated - placebo_synthetic
            placebo_gaps[donor_name] = gap
        except Exception:
            continue

    return placebo_gaps


def fig_synthetic_control(treated, synthetic, pre_end, title_suffix=""):
    """Plot treated vs synthetic control."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Panel A: Levels
    ax = axes[0]
    ax.plot(treated.index, treated.values * 1000, "r-", linewidth=2, label="Poland")
    ax.plot(synthetic.index, synthetic.values * 1000, "b--", linewidth=1.5, label="Synthetic Poland")
    ax.axvline(pre_end + 0.5, color="gray", linestyle="--", alpha=0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Mortality Rate (per 1,000)")
    ax.set_title("A. Poland vs Synthetic Poland", fontweight="bold")
    ax.legend()
    ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

    # Panel B: Gap
    ax = axes[1]
    gap = (treated - synthetic) * 1000
    ax.plot(gap.index, gap.values, "k-o", markersize=3, linewidth=1.5)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(pre_end + 0.5, color="gray", linestyle="--", alpha=0.5)
    ax.fill_between(gap.index, 0, gap.values,
                     where=gap.index > pre_end, alpha=0.2, color="red")
    # Annotate COVID gap (2020-2021 excluded)
    if gap.index.max() > 2019:
        ax.axvspan(2019.5, 2021.5, alpha=0.1, color="orange", label="COVID (excluded)")
        ax.legend(fontsize=8)
    ax.set_xlabel("Year")
    ax.set_ylabel("Gap (per 1,000)")
    ax.set_title("B. Treatment Effect (Poland - Synthetic)", fontweight="bold")
    ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

    fig.suptitle(f"Synthetic Control: Elderly Mortality{title_suffix}",
                 fontweight="bold", y=1.02)
    fig.tight_layout()

    suffix = title_suffix.replace(" ", "_").replace("(", "").replace(")", "").lower()
    fig.savefig(FIGURES_DIR / f"fig11_synthetic_control{suffix}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / f"fig11_synthetic_control{suffix}.png", bbox_inches="tight", dpi=300)
    plt.close()


def fig_placebo_tests(treated, synthetic, placebo_gaps, pre_end, title_suffix=""):
    """Plot placebo test results."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Placebo gaps in gray
    for name, gap in placebo_gaps.items():
        ax.plot(gap.index, gap.values * 1000, color="gray", alpha=0.2, linewidth=0.8)

    # Poland gap in red
    poland_gap = (treated - synthetic) * 1000
    ax.plot(poland_gap.index, poland_gap.values, "r-", linewidth=2.5, label="Poland")

    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(pre_end + 0.5, color="gray", linestyle="--", alpha=0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Gap in Mortality Rate (per 1,000)")
    ax.set_title(f"Placebo Tests: Poland vs Donor Countries{title_suffix}",
                 fontweight="bold")
    ax.legend()
    ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

    fig.tight_layout()
    suffix = title_suffix.replace(" ", "_").replace("(", "").replace(")", "").lower()
    fig.savefig(FIGURES_DIR / f"fig12_placebo{suffix}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / f"fig12_placebo{suffix}.png", bbox_inches="tight", dpi=300)
    plt.close()


def report_weights(weights, donor_names, top_n=10):
    """Report the SCM weights."""
    wdf = pd.DataFrame({"Country": donor_names, "Weight": weights})
    wdf = wdf[wdf["Weight"] > 0.001].sort_values("Weight", ascending=False)
    print(f"\n  Top {min(top_n, len(wdf))} donor weights:")
    for _, row in wdf.head(top_n).iterrows():
        print(f"    {row['Country']}: {row['Weight']:.3f}")
    return wdf


def compute_post_treatment_effect(treated, synthetic, pre_end, post_end=None):
    """Compute average post-treatment effect, optionally restricted to post_end."""
    post_mask = treated.index > pre_end
    if post_end is not None:
        post_mask = post_mask & (treated.index <= post_end)
    gap = treated[post_mask] - synthetic[post_mask]
    gap = gap.dropna()
    avg_gap = gap.mean()
    avg_pct = (gap / treated[post_mask].loc[gap.index]).mean() * 100
    return avg_gap, avg_pct


def compute_p_value(treated, synthetic, placebo_gaps, pre_end):
    """
    Compute p-value from placebo test distribution.
    Ratio of post/pre MSPE for Poland vs placebos.
    """
    pre = treated.index <= pre_end
    post = treated.index > pre_end

    pol_gap = treated - synthetic
    pol_pre_mspe = np.mean(pol_gap[pre] ** 2)
    pol_post_mspe = np.mean(pol_gap[post] ** 2)
    pol_ratio = pol_post_mspe / pol_pre_mspe if pol_pre_mspe > 0 else np.inf

    ratios = [pol_ratio]
    for name, pgap in placebo_gaps.items():
        common_idx = pgap.index.intersection(treated.index)
        if len(common_idx) == 0:
            continue
        pre_idx = [i for i in common_idx if i <= pre_end]
        post_idx = [i for i in common_idx if i > pre_end]
        if len(pre_idx) == 0 or len(post_idx) == 0:
            continue
        pre_mspe = np.mean(pgap[pre_idx] ** 2)
        post_mspe = np.mean(pgap[post_idx] ** 2)
        ratio = post_mspe / pre_mspe if pre_mspe > 0 else 0
        ratios.append(ratio)

    p_value = np.mean([r >= pol_ratio for r in ratios])
    return p_value, pol_ratio


if __name__ == "__main__":
    print("=" * 60)
    print("Strategy 3: Synthetic Control Method")
    print("=" * 60)

    cross_ag = load_data()
    results_summary = []

    for age_label, age_groups in [("75-84", ["75-79", "80-84"]),
                                   ("65-84", ["65-69", "70-74", "75-79", "80-84"])]:
        for sex_label, sex_col in [("Total", "mx_total"), ("Male", "mx_male")]:
            config_label = f"Ages {age_label}, {sex_label}"
            print(f"\n{'─' * 50}")
            print(f"Configuration: {config_label}")
            print(f"{'─' * 50}")

            try:
                treated, donors, pre_end = prepare_scm_data(
                    cross_ag, age_groups.copy(), outcome_col=sex_col
                )
                print(f"  Treated: {len(treated)} years, Donors: {len(donors.columns)} countries")
                print(f"  Pre-period: {treated.index.min()}-{pre_end}, "
                      f"Post-period: {pre_end+1}-{treated.index.max()}")

                # Estimate SCM
                weights, synthetic, pre_mspe = synthetic_control(treated, donors, pre_end)
                report_weights(weights, donors.columns.tolist())

                # Treatment effect — primary: 2016-2019 (clean pre-COVID)
                avg_gap_clean, avg_pct_clean = compute_post_treatment_effect(
                    treated, synthetic, pre_end, post_end=2019
                )
                # Secondary: full post-period (includes 2022-2023 COVID aftermath)
                avg_gap_full, avg_pct_full = compute_post_treatment_effect(
                    treated, synthetic, pre_end
                )
                print(f"\n  Avg gap 2016-2019: {avg_gap_clean*1000:.2f} per 1,000 ({avg_pct_clean:.1f}%)")
                print(f"  Avg gap full period: {avg_gap_full*1000:.2f} per 1,000 ({avg_pct_full:.1f}%)")

                # Figure
                fig_synthetic_control(treated, synthetic, pre_end, f" ({config_label})")
                print(f"  Saved synthetic control figure")

                # Placebo tests (limit to ~20 for speed)
                print("  Running placebo tests...")
                placebo_gaps = placebo_test(treated, donors, pre_end, n_placebos=20)
                print(f"  Completed {len(placebo_gaps)} placebo tests")

                fig_placebo_tests(treated, synthetic, placebo_gaps, pre_end, f" ({config_label})")
                print(f"  Saved placebo figure")

                # P-value (based on clean period 2016-2019)
                p_val, ratio = compute_p_value(treated, synthetic, placebo_gaps, pre_end)
                print(f"  Post/Pre MSPE ratio: {ratio:.2f}")
                print(f"  Placebo p-value: {p_val:.3f}")

                results_summary.append({
                    "Config": config_label,
                    "N Donors": len(donors.columns),
                    "Pre-MSPE": pre_mspe,
                    "Avg Gap 2016-19 (per 1000)": avg_gap_clean * 1000,
                    "Avg Gap 2016-19 (%)": avg_pct_clean,
                    "Avg Gap Full (per 1000)": avg_gap_full * 1000,
                    "Avg Gap Full (%)": avg_pct_full,
                    "MSPE Ratio": ratio,
                    "P-value": p_val,
                })

            except Exception as e:
                print(f"  ERROR: {e}")
                continue

    # Save results
    if results_summary:
        rdf = pd.DataFrame(results_summary)
        rdf.to_csv(TABLES_DIR / "table5_synthetic_control.csv", index=False)
        print("\n\nSummary of all configurations:")
        print(rdf.to_string(index=False))

    # Save donor weights for main specification
    print("\n" + "=" * 60)
    print("Synthetic control analysis complete.")
    print("=" * 60)
