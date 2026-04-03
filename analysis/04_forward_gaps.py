"""
04_forward_gaps.py — RQ1: Statewide racial proficiency gaps (Forward Exam era).

Computes enrollment-weighted statewide proficiency by race × year × subject × grade,
then Black-White (BW) and Hispanic-White (HW) gaps. Produces trend and by-grade figures.

DATA ERA: Forward Exam only. Primary analysis window: 2015-16 to 2022-23
(excluding 2019-20 [missing] and 2020-21 [COVID disruption]).

Inputs:
  output/data/panel_district_race.parquet

Outputs:
  output/tables/state_proficiency_by_race.csv
  output/tables/state_gaps_summary.csv
  output/figures/fig01_gap_trends.{pdf,png}
  output/figures/fig02_gaps_by_grade.{pdf,png}
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "output" / "data" / "panel_district_race.parquet"
OUT_TABLES = ROOT / "output" / "tables"
OUT_FIGS = ROOT / "output" / "figures"

OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FOCUS_RACES = ["White", "Black", "Hispanic", "Asian"]
EXCLUDE_RACES = {"Unknown", "Unknown/Suppressed"}

RACE_COLORS = {
    "White":           "#1b7837",
    "Black":           "#762a83",
    "Hispanic":        "#f1a340",
    "Asian":           "#2166ac",
    "American Indian": "#d7191c",
    "Two or More Races": "#878787",
}

SUBJECT_LABEL = {"ELA": "ELA (Reading/Writing)", "Mathematics": "Mathematics"}
GRADE_ORDER = [3, 4, 5, 6, 7, 8]

FIG_DPI = 150
FIG_FONT = "DejaVu Sans"
plt.rcParams.update({
    "font.family": FIG_FONT,
    "font.size": 10,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "axes.grid": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.6,
    "axes.grid.axis": "y",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


# ---------------------------------------------------------------------------
# Load and filter
# ---------------------------------------------------------------------------

def load_panel() -> pd.DataFrame:
    df = pd.read_parquet(PANEL)
    df = df[
        df["primary_analysis"] &
        ~df["race"].isin(EXCLUDE_RACES) &
        ~df["suppressed"]
    ].copy()
    df["grade"] = df["grade"].astype(int)
    print(f"Loaded {len(df):,} non-suppressed primary rows")
    return df


# ---------------------------------------------------------------------------
# Compute weighted state proficiency
# ---------------------------------------------------------------------------

def weighted_mean(group: pd.DataFrame) -> float:
    """Enrollment-weighted mean proficiency for a group."""
    valid = group.dropna(subset=["pct_proficient", "n_tested"])
    if valid.empty or valid["n_tested"].sum() == 0:
        return np.nan
    return np.average(valid["pct_proficient"], weights=valid["n_tested"])


def state_proficiency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrollment-weighted statewide proficiency by race × year × subject × grade.
    Uses district-level rows (each district is one observation; weight = n_tested).
    """
    result = (
        df.groupby(["race", "year", "subject", "grade"], sort=True)
        .apply(weighted_mean, include_groups=False)
        .rename("pct_proficient")
        .reset_index()
    )

    # Also track how many districts contributed (for QC)
    n_districts = (
        df.groupby(["race", "year", "subject", "grade"])["district_code"]
        .nunique()
        .rename("n_districts")
        .reset_index()
    )
    result = result.merge(n_districts, on=["race", "year", "subject", "grade"])
    return result


def compute_gaps(state_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot to wide (races as columns), compute BW and HW gaps.
    Returns a DataFrame with columns: year, subject, grade, White, Black, Hispanic,
    BW_gap, HW_gap (all in percentage points).
    """
    wide = state_df.pivot_table(
        index=["year", "subject", "grade"],
        columns="race",
        values="pct_proficient"
    ).reset_index()
    wide.columns.name = None

    for race in ["White", "Black", "Hispanic"]:
        if race not in wide.columns:
            wide[race] = np.nan

    wide["BW_gap"] = wide["White"] - wide["Black"]
    wide["HW_gap"] = wide["White"] - wide["Hispanic"]
    return wide


def grade_weighted_mean(gaps: pd.DataFrame, df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Average gaps across grades (3-8), weighted by total enrollment in that grade-cell.
    Returns year × subject summary.
    """
    # Total enrollment per (year, subject, grade) across all districts for White+Black
    enroll = (
        df_raw[df_raw["race"].isin(["White", "Black", "Hispanic"])]
        .groupby(["year", "subject", "grade"])["n_tested"]
        .sum()
        .rename("total_n")
        .reset_index()
    )
    merged = gaps.merge(enroll, on=["year", "subject", "grade"], how="left")

    def _wavg(g):
        valid = g.dropna(subset=["total_n"])
        if valid.empty:
            return pd.Series({"BW_gap": np.nan, "HW_gap": np.nan})
        return pd.Series({
            "BW_gap": np.average(valid["BW_gap"].fillna(np.nan),
                                 weights=valid["total_n"]) if valid["BW_gap"].notna().any() else np.nan,
            "HW_gap": np.average(valid["HW_gap"].fillna(np.nan),
                                 weights=valid["total_n"]) if valid["HW_gap"].notna().any() else np.nan,
        })

    summary = (
        merged.groupby(["year", "subject"])
        .apply(_wavg, include_groups=False)
        .reset_index()
    )
    return summary


# ---------------------------------------------------------------------------
# Figure helpers
# ---------------------------------------------------------------------------

def save_fig(fig: plt.Figure, stem: str) -> None:
    for ext in ("pdf", "png"):
        path = OUT_FIGS / f"{stem}.{ext}"
        fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight")
    print(f"  Saved {stem}.pdf / .png")


# ---------------------------------------------------------------------------
# Figure 1: Gap trends over time
# ---------------------------------------------------------------------------

def fig_gap_trends(gaps: pd.DataFrame, summary: pd.DataFrame) -> None:
    """
    Two columns (ELA, Math) × two rows (BW gap, HW gap).
    Thin lines = individual grades; bold = grade-weighted average.
    """
    subjects = ["ELA", "Mathematics"]
    gap_pairs = [("BW_gap", "Black–White"), ("HW_gap", "Hispanic–White")]
    colors = {"BW_gap": RACE_COLORS["Black"], "HW_gap": RACE_COLORS["Hispanic"]}

    # Year ordering
    year_order = sorted(gaps["year"].unique())

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey="row", sharex=True)

    for col_i, subj in enumerate(subjects):
        for row_i, (gap_col, gap_label) in enumerate(gap_pairs):
            ax = axes[row_i, col_i]
            subj_gaps = gaps[gaps["subject"] == subj]
            subj_summary = summary[summary["subject"] == subj]

            # Thin lines per grade
            for grade in GRADE_ORDER:
                g_data = subj_gaps[subj_gaps["grade"] == grade].set_index("year")
                vals = [g_data.loc[y, gap_col] if y in g_data.index else np.nan
                        for y in year_order]
                ax.plot(range(len(year_order)), vals,
                        color=colors[gap_col], alpha=0.25, linewidth=1.0,
                        marker="o", markersize=3)

            # Bold average line
            avg_vals = [
                subj_summary[subj_summary["year"] == y][gap_col].values[0]
                if len(subj_summary[subj_summary["year"] == y]) > 0 else np.nan
                for y in year_order
            ]
            ax.plot(range(len(year_order)), avg_vals,
                    color=colors[gap_col], linewidth=2.5,
                    marker="o", markersize=5, label=f"{gap_label} (avg)")

            ax.axhline(0, color="black", linewidth=0.7, linestyle="--")
            ax.set_xticks(range(len(year_order)))
            ax.set_xticklabels(year_order, rotation=40, ha="right", fontsize=9)
            ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f pp"))
            ax.set_ylim(bottom=0)

            if col_i == 0:
                ax.set_ylabel(f"{gap_label}\ngap (pp)", fontsize=9)
            if row_i == 0:
                ax.set_title(SUBJECT_LABEL[subj], fontsize=11, fontweight="bold")

            # Annotation for thin lines
            if row_i == 0 and col_i == 1:
                ax.plot([], [], color=colors[gap_col], alpha=0.3, linewidth=1,
                        label="Individual grades (3–8)")
                ax.legend(fontsize=8, loc="upper right", framealpha=0.9)

    fig.suptitle(
        "Statewide Racial Proficiency Gaps — Forward Exam (Primary Years 2015–2023)",
        fontsize=12, fontweight="bold", y=1.01
    )
    fig.text(0.5, -0.02,
             "Note: Thin lines = individual grades 3–8. Bold = grade-enrollment-weighted average.\n"
             "Primary years: 2015-16 to 2022-23, excluding 2019-20 (no testing) and 2020-21 (COVID disruption).",
             ha="center", fontsize=8, color="#555555")
    plt.tight_layout()
    save_fig(fig, "fig01_gap_trends")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: Gaps by grade (pooled)
# ---------------------------------------------------------------------------

def fig_gaps_by_grade(gaps: pd.DataFrame) -> None:
    """
    Two-panel figure (ELA, Math). For each subject: bar chart of BW and HW gap by grade,
    pooled across primary years (simple mean across years, weighted by n_tested not available
    at this stage → use unweighted mean of the grade-level annual gaps as an approximation).
    """
    subjects = ["ELA", "Mathematics"]
    gap_cols = [("BW_gap", "Black–White"), ("HW_gap", "Hispanic–White")]
    gap_colors = [RACE_COLORS["Black"], RACE_COLORS["Hispanic"]]

    pooled = (
        gaps.groupby(["subject", "grade"])[["BW_gap", "HW_gap"]]
        .mean()
        .reset_index()
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    x = np.arange(len(GRADE_ORDER))
    bar_width = 0.35

    for col_i, subj in enumerate(subjects):
        ax = axes[col_i]
        subj_data = pooled[pooled["subject"] == subj].set_index("grade")

        for i, (gap_col, gap_label) in enumerate(gap_cols):
            vals = [subj_data.loc[g, gap_col] if g in subj_data.index else np.nan
                    for g in GRADE_ORDER]
            ax.bar(x + i * bar_width, vals, bar_width,
                   label=gap_label, color=gap_colors[i], alpha=0.85, edgecolor="white")

        ax.set_xticks(x + bar_width / 2)
        ax.set_xticklabels([f"Grade {g}" for g in GRADE_ORDER], fontsize=9)
        ax.set_xlabel("Grade", fontsize=10)
        if col_i == 0:
            ax.set_ylabel("Proficiency gap (percentage points)", fontsize=10)
        ax.set_title(SUBJECT_LABEL[subj], fontsize=11, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f pp"))
        ax.set_ylim(bottom=0)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.legend(fontsize=9, loc="upper right", framealpha=0.9)

    fig.suptitle(
        "Statewide Racial Proficiency Gaps by Grade — Forward Exam (Pooled 2015–2023)",
        fontsize=12, fontweight="bold"
    )
    fig.text(0.5, -0.03,
             "Note: Bars show mean gap across primary years 2015-16 to 2022-23 "
             "(excludes 2019-20, 2020-21). White minus Black or Hispanic proficiency rate.",
             ha="center", fontsize=8, color="#555555")
    plt.tight_layout()
    save_fig(fig, "fig02_gaps_by_grade")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 65)
    print("04_forward_gaps.py — RQ1: Statewide racial proficiency gaps")
    print("=" * 65)

    df = load_panel()

    print("\nComputing state-level proficiency by race × year × subject × grade...")
    state_df = state_proficiency(df)
    gaps = compute_gaps(state_df)
    summary = grade_weighted_mean(gaps, df)

    # --- Tables ---
    out_prof = OUT_TABLES / "state_proficiency_by_race.csv"
    state_df.to_csv(out_prof, index=False)
    print(f"\nSaved: {out_prof}")

    out_gaps = OUT_TABLES / "state_gaps_summary.csv"
    gaps.to_csv(out_gaps, index=False)
    print(f"Saved: {out_gaps}")

    # --- Print summary ---
    print("\nGrade-averaged gaps by year and subject:")
    pivot = summary.pivot_table(
        index="year", columns="subject", values=["BW_gap", "HW_gap"]
    )
    pivot.columns = [f"{c[0]}_{c[1]}" for c in pivot.columns]
    print(pivot.round(1).to_string())

    # --- Figures ---
    print("\nGenerating figures...")
    fig_gap_trends(gaps, summary)
    fig_gaps_by_grade(gaps)

    print("\nDone.")


if __name__ == "__main__":
    main()
