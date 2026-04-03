"""
05_decomposition.py — RQ2: Within-between decomposition of statewide racial gaps.

Decomposes the Black-White (BW) and Hispanic-White (HW) proficiency gap into:
  - Within component (W): gaps that exist inside the same geographic unit
  - Between component (B): gap attributable to racial groups attending units
                           with systematically different average performance

Decomposition formula (applied per year × subject × grade × gap-pair):

  T = p̄_w − p̄_b                      (total enrollment-weighted statewide gap)
  p̄_d = (n_w·p_w + n_b·p_b) / (n_w + n_b)   (unit combined mean)
  B = Σ_d p̄_d · (n_w^d/N_w − n_b^d/N_b)     (between component)
  W = T − B                                    (within component; sums exactly)

Computed at three levels:
  1. District  (panel_district_race.parquet)
  2. County    (district panel aggregated to county)
  3. School    (panel_school_race.parquet, collapsed to school×race×year first)

Inputs:
  output/data/panel_district_race.parquet
  output/data/panel_school_race.parquet

Outputs:
  output/tables/decomposition_results.csv
  output/figures/fig03_decomposition_bw.{pdf,png}
  output/figures/fig04_district_scatter.{pdf,png}
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
PANEL_DIST = ROOT / "output" / "data" / "panel_district_race.parquet"
PANEL_SCHOOL = ROOT / "output" / "data" / "panel_school_race.parquet"
OUT_TABLES = ROOT / "output" / "tables"
OUT_FIGS = ROOT / "output" / "figures"

OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EXCLUDE_RACES = {"Unknown", "Unknown/Suppressed"}

RACE_COLORS = {
    "White":    "#1b7837",
    "Black":    "#762a83",
    "Hispanic": "#f1a340",
}

GAP_PAIRS = [
    ("White", "Black",    "BW", "Black–White"),
    ("White", "Hispanic", "HW", "Hispanic–White"),
]

SUBJECT_LABEL = {"ELA": "ELA", "Mathematics": "Math"}
GRADE_ORDER = [3, 4, 5, 6, 7, 8]

FIG_DPI = 150
plt.rcParams.update({
    "font.family": "DejaVu Sans",
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
# Core decomposition
# ---------------------------------------------------------------------------

def decompose_gap(
    unit_df: pd.DataFrame,
    race_a: str,
    race_b: str,
    unit_col: str,
) -> dict:
    """
    Compute T, B, W for race_a minus race_b within a single
    (year, subject, grade) cell.

    Parameters
    ----------
    unit_df  : rows for this cell, must have columns
               [unit_col, 'race', 'pct_proficient', 'n_tested']
    race_a   : majority/reference group (White)
    race_b   : minority group (Black or Hispanic)
    unit_col : grouping identifier ('district_code', 'county', 'school_code')

    Returns
    -------
    dict with keys: T, B, W, B_pct, W_pct, n_units_a, n_units_b, n_units_both
    """
    a = (
        unit_df[unit_df["race"] == race_a]
        .set_index(unit_col)[["pct_proficient", "n_tested"]]
        .dropna()
        .rename(columns={"pct_proficient": "p_a", "n_tested": "n_a"})
    )
    b = (
        unit_df[unit_df["race"] == race_b]
        .set_index(unit_col)[["pct_proficient", "n_tested"]]
        .dropna()
        .rename(columns={"pct_proficient": "p_b", "n_tested": "n_b"})
    )

    # Units where both groups appear with valid data
    both = a.join(b, how="inner")

    n_units_a    = len(a)
    n_units_b    = len(b)
    n_units_both = len(both)

    if both.empty or both["n_a"].sum() == 0 or both["n_b"].sum() == 0:
        return {
            "T": np.nan, "B": np.nan, "W": np.nan,
            "B_pct": np.nan, "W_pct": np.nan,
            "n_units_a": n_units_a, "n_units_b": n_units_b,
            "n_units_both": n_units_both,
        }

    N_a = both["n_a"].sum()
    N_b = both["n_b"].sum()

    p_bar_a = (both["p_a"] * both["n_a"]).sum() / N_a
    p_bar_b = (both["p_b"] * both["n_b"]).sum() / N_b

    T = p_bar_a - p_bar_b

    # Combined unit mean
    both["p_d"] = (both["n_a"] * both["p_a"] + both["n_b"] * both["p_b"]) / (both["n_a"] + both["n_b"])

    B = (both["p_d"] * (both["n_a"] / N_a - both["n_b"] / N_b)).sum()
    W = T - B

    B_pct = 100 * B / T if T != 0 else np.nan
    W_pct = 100 * W / T if T != 0 else np.nan

    return {
        "T": T, "B": B, "W": W,
        "B_pct": B_pct, "W_pct": W_pct,
        "n_units_a": n_units_a, "n_units_b": n_units_b,
        "n_units_both": n_units_both,
    }


def run_decomposition(
    df: pd.DataFrame,
    unit_col: str,
    level_label: str,
) -> pd.DataFrame:
    """
    Loop over all (year, subject, grade) cells and gap pairs.
    Returns a long DataFrame of decomposition results.
    """
    records = []
    years = sorted(df["year"].unique())
    subjects = sorted(df["subject"].unique())

    for year in years:
        for subj in subjects:
            for grade in GRADE_ORDER:
                cell = df[
                    (df["year"] == year) &
                    (df["subject"] == subj) &
                    (df["grade"] == grade)
                ]
                if cell.empty:
                    continue
                for race_a, race_b, pair_label, _ in GAP_PAIRS:
                    res = decompose_gap(cell, race_a, race_b, unit_col)
                    records.append({
                        "level": level_label,
                        "year": year,
                        "subject": subj,
                        "grade": grade,
                        "gap_pair": pair_label,
                        **res,
                    })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Grade-weighted summary
# ---------------------------------------------------------------------------

def grade_summary(decomp: pd.DataFrame, df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Average T, B, W across grades, weighted by total tested enrollment.
    """
    enroll = (
        df_raw[df_raw["race"].isin(["White", "Black", "Hispanic"])]
        .groupby(["year", "subject", "grade"])["n_tested"]
        .sum()
        .rename("total_n")
        .reset_index()
    )
    merged = decomp.merge(enroll, on=["year", "subject", "grade"], how="left")

    def wavg(g):
        valid = g.dropna(subset=["T", "total_n"])
        if valid.empty:
            return pd.Series({"T": np.nan, "B": np.nan, "W": np.nan})
        w = valid["total_n"]
        return pd.Series({
            "T": np.average(valid["T"], weights=w),
            "B": np.average(valid["B"], weights=w),
            "W": np.average(valid["W"], weights=w),
        })

    summary = (
        merged.groupby(["level", "year", "subject", "gap_pair"])
        .apply(wavg, include_groups=False)
        .reset_index()
    )
    summary["B_pct"] = 100 * summary["B"] / summary["T"]
    summary["W_pct"] = 100 * summary["W"] / summary["T"]
    return summary


# ---------------------------------------------------------------------------
# Load district data
# ---------------------------------------------------------------------------

def load_district_panel() -> pd.DataFrame:
    df = pd.read_parquet(PANEL_DIST)
    df = df[
        df["primary_analysis"] &
        ~df["race"].isin(EXCLUDE_RACES) &
        ~df["suppressed"]
    ].copy()
    df["grade"] = df["grade"].astype(int)
    return df


def make_county_panel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate district panel to county level by summing n_tested and
    computing weighted-average pct_proficient.
    """
    groups = ["county", "year", "subject", "grade", "race"]
    county = (
        df.groupby(groups, sort=False)
        .apply(
            lambda g: pd.Series({
                "pct_proficient": np.average(g["pct_proficient"], weights=g["n_tested"])
                if g["n_tested"].sum() > 0 else np.nan,
                "n_tested": g["n_tested"].sum(),
            }),
            include_groups=False,
        )
        .reset_index()
    )
    return county


# ---------------------------------------------------------------------------
# Load school data (for school-level decomposition)
# ---------------------------------------------------------------------------

def load_school_panel() -> pd.DataFrame:
    """
    Load school panel, collapse to school×race×year (across grade+subject)
    using weighted average, then apply suppression threshold.
    """
    df = pd.read_parquet(PANEL_SCHOOL)
    df = df[
        df["primary_analysis"] &
        ~df["race"].isin(EXCLUDE_RACES)
    ].copy()
    df["grade"] = df["grade"].astype(int)

    # Aggregate to school × race × year × subject × grade (keep structure for decomp)
    # For school-level decomp we need non-suppressed data; filter after aggregation
    df = df[~df["suppressed"]].copy()
    return df


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def save_fig(fig: plt.Figure, stem: str) -> None:
    for ext in ("pdf", "png"):
        fig.savefig(OUT_FIGS / f"{stem}.{ext}", dpi=FIG_DPI, bbox_inches="tight")
    print(f"  Saved {stem}.pdf / .png")


def fig_decomposition(summary: pd.DataFrame) -> None:
    """
    Stacked bar: within (solid) + between (hatched) for BW and HW gaps.
    Rows = gap pair; Columns = geographic level; x-axis = year.
    """
    levels = ["District", "County", "School"]
    gap_pairs_labels = [("BW", "Black–White"), ("HW", "Hispanic–White")]
    colors_within  = {"BW": RACE_COLORS["Black"],    "HW": RACE_COLORS["Hispanic"]}
    colors_between = {"BW": "#c2a5cf",               "HW": "#fde0a3"}  # lighter shades

    subjects = ["ELA", "Mathematics"]
    # For simplicity, average ELA and Math together for this figure
    subj_avg = (
        summary.groupby(["level", "year", "gap_pair"])[["T", "B", "W"]]
        .mean()
        .reset_index()
    )
    subj_avg["B_pct"] = 100 * subj_avg["B"] / subj_avg["T"]
    subj_avg["W_pct"] = 100 * subj_avg["W"] / subj_avg["T"]

    years = sorted(subj_avg["year"].unique())
    x = np.arange(len(years))
    fig, axes = plt.subplots(
        len(gap_pairs_labels), len(levels),
        figsize=(13, 7), sharey="row", sharex=True
    )

    for row_i, (pair_code, pair_label) in enumerate(gap_pairs_labels):
        for col_i, level in enumerate(levels):
            ax = axes[row_i, col_i]
            data = subj_avg[
                (subj_avg["level"] == level) &
                (subj_avg["gap_pair"] == pair_code)
            ].set_index("year")

            within_vals  = [data.loc[y, "W"] if y in data.index else np.nan for y in years]
            between_vals = [data.loc[y, "B"] if y in data.index else np.nan for y in years]

            bars_w = ax.bar(x, within_vals, label="Within",
                            color=colors_within[pair_code], alpha=0.9, edgecolor="white")
            bars_b = ax.bar(x, between_vals, bottom=within_vals, label="Between",
                            color=colors_between[pair_code], alpha=0.9,
                            hatch="///", edgecolor="white")

            # Total gap label on top
            for xi, (w, b) in enumerate(zip(within_vals, between_vals)):
                if not (np.isnan(w) or np.isnan(b)):
                    ax.text(xi, w + b + 0.3, f"{w+b:.1f}", ha="center", va="bottom",
                            fontsize=7.5, color="#333333")

            ax.set_xticks(x)
            ax.set_xticklabels(years, rotation=40, ha="right", fontsize=8)
            ax.set_ylim(bottom=0)
            ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f pp"))

            if col_i == 0:
                ax.set_ylabel(f"{pair_label}\ngap (pp)", fontsize=9)
            if row_i == 0:
                ax.set_title(level, fontsize=11, fontweight="bold")

    # Shared legend
    patch_w = mpatches.Patch(color="#762a83", alpha=0.9, label="Within-unit gap")
    patch_b = mpatches.Patch(color="#c2a5cf", alpha=0.9, hatch="///", label="Between-unit gap")
    fig.legend(handles=[patch_w, patch_b], loc="lower center", ncol=2,
               fontsize=9, framealpha=0.9, bbox_to_anchor=(0.5, -0.04))

    fig.suptitle(
        "Within-Between Decomposition of Racial Proficiency Gaps\n"
        "Forward Exam — Primary Years 2015–2023 (ELA and Math averaged)",
        fontsize=11, fontweight="bold"
    )
    fig.text(0.5, -0.10,
             "Note: Total bar height = total statewide gap (pp). "
             "Within = gap inside same unit; Between = gap from different unit assignment.\n"
             "Only units with both White and minority students (non-suppressed) included.",
             ha="center", fontsize=8, color="#555555")
    plt.tight_layout()
    save_fig(fig, "fig03_decomposition_bw")
    plt.close(fig)


def fig_district_scatter(df: pd.DataFrame) -> None:
    """
    District scatter: Black (x) vs White (y) ELA proficiency, pooled across primary years.
    Size = total district enrollment (White + Black). MMSD labeled.
    """
    # Aggregate to district × race, pooled years (weighted mean across year/grade/subject)
    ela = df[df["subject"] == "ELA"].copy()

    def _wmean(g):
        return np.average(g["pct_proficient"], weights=g["n_tested"]) if g["n_tested"].sum() > 0 else np.nan

    dist_race = (
        ela[ela["race"].isin(["White", "Black"])]
        .groupby(["district_code", "district_name", "race"])
        .apply(_wmean, include_groups=False)
        .rename("pct_proficient")
        .reset_index()
    )

    wide = dist_race.pivot_table(
        index=["district_code", "district_name"],
        columns="race",
        values="pct_proficient"
    ).reset_index().dropna(subset=["White", "Black"])
    wide.columns.name = None

    # Enrollment for sizing (sum White + Black n_tested)
    enroll = (
        ela[ela["race"].isin(["White", "Black"])]
        .groupby("district_code")["n_tested"]
        .sum()
        .rename("total_n")
    )
    wide = wide.join(enroll, on="district_code")
    wide["total_n"] = wide["total_n"].fillna(100)

    # Scatter
    fig, ax = plt.subplots(figsize=(8, 7))

    # Size: log-scaled enrollment
    sizes = 20 + 400 * (np.log1p(wide["total_n"]) / np.log1p(wide["total_n"].max()))

    scatter = ax.scatter(
        wide["Black"], wide["White"],
        s=sizes, alpha=0.45,
        color="#762a83", edgecolors="white", linewidth=0.5
    )

    # Parity line
    lim = max(wide["White"].max(), wide["Black"].max()) + 3
    ax.plot([0, lim], [0, lim], "--", color="#888888", linewidth=1, label="Parity (gap = 0)")

    # Label MMSD
    mmsd = wide[wide["district_name"] == "Madison Metropolitan"]
    if not mmsd.empty:
        row = mmsd.iloc[0]
        ax.scatter(row["Black"], row["White"], s=220, color="#e31a1c",
                   zorder=5, edgecolors="white", linewidth=1.2)
        ax.annotate("MMSD", (row["Black"], row["White"]),
                    xytext=(row["Black"] + 0.8, row["White"] - 2.5),
                    fontsize=9, color="#e31a1c", fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color="#e31a1c", lw=0.8))

    # Axes
    ax.set_xlabel("Black student proficiency rate (ELA, %, pooled 2015–2023)", fontsize=10)
    ax.set_ylabel("White student proficiency rate (ELA, %, pooled 2015–2023)", fontsize=10)
    ax.set_title(
        "District-Level Black vs. White ELA Proficiency\n"
        "Wisconsin Districts — Forward Exam Primary Years",
        fontsize=11, fontweight="bold"
    )
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))

    # Legend for bubble size
    for n_ref, label in [(500, "500"), (5000, "5,000"), (30000, "30,000")]:
        s_ref = 20 + 400 * (np.log1p(n_ref) / np.log1p(wide["total_n"].max()))
        ax.scatter([], [], s=s_ref, color="#762a83", alpha=0.5, label=f"N={label}")
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9, title="Combined enrollment")

    ax.text(0.98, 0.02,
            "Note: Each point = one school district, pooled across primary years.\n"
            "Size ∝ log(White + Black enrollment). Dashed line = parity.",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7.5, color="#555555")
    plt.tight_layout()
    save_fig(fig, "fig04_district_scatter")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 65)
    print("05_decomposition.py — RQ2: Within-between decomposition")
    print("=" * 65)

    # --- District level ---
    print("\nLoading district panel...")
    df_dist = load_district_panel()
    print(f"  {len(df_dist):,} non-suppressed rows")

    print("\nRunning district-level decomposition...")
    decomp_dist = run_decomposition(df_dist, "district_code", "District")

    # --- County level ---
    print("\nBuilding county panel...")
    df_county = make_county_panel(df_dist)
    print(f"  {len(df_county):,} county-level rows")

    print("Running county-level decomposition...")
    decomp_county = run_decomposition(df_county, "county", "County")

    # --- School level ---
    print("\nLoading school panel...")
    df_school = load_school_panel()
    print(f"  {len(df_school):,} non-suppressed school rows")

    print("Running school-level decomposition...")
    decomp_school = run_decomposition(df_school, "school_code", "School")

    # --- Combine and summarize ---
    all_decomp = pd.concat([decomp_dist, decomp_county, decomp_school], ignore_index=True)

    # Grade-weighted summary (use district raw for enrollment weights)
    print("\nComputing grade-weighted summaries...")
    summary_dist   = grade_summary(decomp_dist,   df_dist)
    summary_county = grade_summary(decomp_county, df_dist)
    summary_school = grade_summary(decomp_school, df_dist)
    summary_all    = pd.concat([summary_dist, summary_county, summary_school], ignore_index=True)

    # Save raw decomposition
    out_decomp = OUT_TABLES / "decomposition_results.csv"
    all_decomp.to_csv(out_decomp, index=False)
    print(f"\nSaved raw results: {out_decomp}")

    out_summary = OUT_TABLES / "decomposition_summary.csv"
    summary_all.to_csv(out_summary, index=False)
    print(f"Saved grade-averaged summary: {out_summary}")

    # Print key results
    print("\nKey decomposition results (district level, ELA, BW gap):")
    bw_ela = summary_dist[
        (summary_dist["gap_pair"] == "BW") &
        (summary_dist["subject"] == "ELA")
    ][["year", "T", "B", "W", "B_pct", "W_pct"]].set_index("year")
    print(bw_ela.round(1).to_string())

    print("\nKey decomposition results (district level, ELA, HW gap):")
    hw_ela = summary_dist[
        (summary_dist["gap_pair"] == "HW") &
        (summary_dist["subject"] == "ELA")
    ][["year", "T", "B", "W", "B_pct", "W_pct"]].set_index("year")
    print(hw_ela.round(1).to_string())

    # --- Figures ---
    print("\nGenerating figures...")
    fig_decomposition(summary_all)
    fig_district_scatter(df_dist)

    print("\nDone.")


if __name__ == "__main__":
    main()
