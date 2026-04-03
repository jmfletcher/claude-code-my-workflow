"""
07_wkce_gaps.py — Appendix D: WKCE-era racial scale-score gaps (2008-09 to 2013-14).

Mirrors the Forward Exam analyses (scripts 04-06) but uses mean scale scores
rather than proficiency rates — the WKCE's vertically scaled score is on a
developmental continuum (designed to be comparable across years within this era).

Analysis window: 2008-09 through 2013-14
  • 2006-07 excluded: no valid data in panel
  • 2007-08 excluded: n_tested is entirely missing (cannot weight state averages)

Subjects: Reading, Math  (parallel to Forward Exam ELA / Mathematics)
Grades  : 3–8           (parallel to Forward Exam; grade 10 excluded for comparability)
Races   : White, Black, Hispanic (primary analysis); Amer Indian, Asian/PI noted)

Decomposition formula (identical to 05_decomposition.py):
  T = p̄_a − p̄_b
  B = Σ_d  p̄_d · (n_a^d/N_a − n_b^d/N_b)
  W = T − B

Inputs:
  output/data/panel_wkce_district_race.parquet

Outputs:
  output/tables/wkce_state_gaps.csv
  output/tables/wkce_decomposition.csv
  output/tables/wkce_mmsd_peers.csv
  output/figures/fig_A1_wkce_gap_trends.{pdf,png}
  output/figures/fig_A2_wkce_gaps_by_grade.{pdf,png}
  output/figures/fig_A3_wkce_decomposition.{pdf,png}
  output/figures/fig_A4_wkce_mmsd_vs_peers.{pdf,png}
  output/figures/fig_A5_wkce_mmsd_vs_nonmmsd_white.{pdf,png}
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
PANEL = ROOT / "output" / "data" / "panel_wkce_district_race.parquet"
OUT_TABLES = ROOT / "output" / "tables"
OUT_FIGS = ROOT / "output" / "figures"

OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ANALYSIS_YEARS = [
    "2008-09", "2009-10", "2010-11", "2011-12", "2012-13", "2013-14",
]

PRIMARY_SUBJECTS = ["Reading", "Math"]
GRADE_ORDER = [3, 4, 5, 6, 7, 8]
PRIMARY_RACES = ["White", "Black", "Hispanic"]

RACE_COLORS = {
    "White":    "#1b7837",
    "Black":    "#762a83",
    "Hispanic": "#f1a340",
}

GAP_PAIRS = [
    ("White", "Black",    "BW", "Black–White"),
    ("White", "Hispanic", "HW", "Hispanic–White"),
]

GAP_COLORS = {
    "BW": "#762a83",
    "HW": "#f1a340",
}

SUBJECT_LABEL = {"Reading": "Reading", "Math": "Mathematics"}

# MMSD uses multiple truncated names across different file vintages
MMSD_NAMES = {"MADISON", "MADISON METROPO", "MADISON MET"}
MMSD_CANONICAL = "Madison Metropolitan SD"

# Peer district lookup: canonical label → set of WKCE district_name variants
PEER_DISTRICTS = {
    # Tier 1 — major urban
    "Milwaukee":           {"MILWAUKEE"},
    "Racine Unified":      {"RACINE"},
    "Kenosha":             {"KENOSHA"},
    "Green Bay Area":      {"GREEN BAY", "GREEN BAY AREA"},
    "Beloit":              {"BELOIT"},
    # Tier 2 — mid-size
    "Sun Prairie Area":    {"SUN PRAIRIE"},
    "Appleton Area":       {"APPLETON", "APPLETON AREA"},
    "Waukesha":            {"WAUKESHA"},
    "Janesville":          {"JANESVILLE"},
    "West Allis-W. Milw.": {"WEST ALLIS"},
    # Madison region
    "Verona Area":         {"VERONA", "VERONA AREA"},
    "Middleton-C.P. Area": {"MIDDLETON CROSS", "MIDDLETON CR"},
}

PEER_TIERS = {
    "Milwaukee":           "Tier 1",
    "Racine Unified":      "Tier 1",
    "Kenosha":             "Tier 1",
    "Green Bay Area":      "Tier 1",
    "Beloit":              "Tier 1",
    "Sun Prairie Area":    "Tier 2",
    "Appleton Area":       "Tier 2",
    "Waukesha":            "Tier 2",
    "Janesville":          "Tier 2",
    "West Allis-W. Milw.": "Tier 2",
    "Verona Area":         "Madison region",
    "Middleton-C.P. Area": "Madison region",
}

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
# Load and clean
# ---------------------------------------------------------------------------

def load_panel() -> pd.DataFrame:
    df = pd.read_parquet(PANEL)

    # Normalize grade to integer (handles both "03" and "3")
    df["grade"] = (
        df["grade"].astype(str).str.lstrip("0").replace("", "0").astype(int)
    )

    # Tag MMSD rows with a canonical label
    df["is_mmsd"] = df["district_name"].isin(MMSD_NAMES)
    df.loc[df["is_mmsd"], "district_name_clean"] = MMSD_CANONICAL

    # Build canonical peer name column
    raw_to_canonical: dict[str, str] = {}
    for canonical, variants in PEER_DISTRICTS.items():
        for v in variants:
            raw_to_canonical[v] = canonical
    df["peer_label"] = df["district_name"].map(raw_to_canonical)

    # Restrict to primary analysis window and scope
    df = df[
        df["year"].isin(ANALYSIS_YEARS)
        & df["grade"].isin(GRADE_ORDER)
        & df["subject"].isin(PRIMARY_SUBJECTS)
        & df["race"].isin(PRIMARY_RACES)
    ].copy()

    return df


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Enrollment-weighted mean; returns NaN if no valid pair exists."""
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return np.nan
    return float((values[mask] * weights[mask]).sum() / weights[mask].sum())


def collapse_to_district(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate grade-level rows to district × race × year × subject.
    Only include rows where mean_ss is not suppressed.
    Returns columns: district_name, year, subject, race, mean_ss, n_tested, n_grades.
    """
    def agg_fn(g):
        valid = g["mean_ss"].notna()
        return pd.Series({
            "mean_ss":  weighted_mean(g["mean_ss"], g["n_tested"]),
            "n_tested": g.loc[valid, "n_tested"].sum() if valid.any() else np.nan,
            "n_grades": valid.sum(),
        })

    out = (
        df.groupby(
            ["year", "district_name", "district_code", "subject", "race"],
            dropna=False,
        )
        .apply(agg_fn, include_groups=False)
        .reset_index()
    )
    return out


# ---------------------------------------------------------------------------
# State-level gaps
# ---------------------------------------------------------------------------

def compute_state_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute enrollment-weighted state mean SS by race×year×subject,
    then BW and HW gaps.
    """
    # State mean by race × year × subject (aggregate across districts AND grades)
    def state_mean(g):
        return pd.Series({
            "mean_ss": weighted_mean(g["mean_ss"], g["n_tested"]),
            "n_tested": g["n_tested"].sum(),
        })

    state = (
        df.groupby(["year", "subject", "race"])
        .apply(state_mean, include_groups=False)
        .reset_index()
    )

    records = []
    for year in ANALYSIS_YEARS:
        for subj in PRIMARY_SUBJECTS:
            cell = state[(state["year"] == year) & (state["subject"] == subj)]
            cell = cell.set_index("race")["mean_ss"]
            if "White" not in cell or pd.isna(cell["White"]):
                continue
            for _ra, rb, pair_label, pair_desc in GAP_PAIRS:
                if rb not in cell or pd.isna(cell[rb]):
                    continue
                records.append({
                    "year": year,
                    "subject": subj,
                    "gap_pair": pair_label,
                    "gap_desc": pair_desc,
                    "mean_ss_white": cell["White"],
                    "mean_ss_minority": cell[rb],
                    "gap": cell["White"] - cell[rb],
                })

    gaps = pd.DataFrame(records)
    return state, gaps


def compute_state_gaps_by_grade(df: pd.DataFrame) -> pd.DataFrame:
    """
    Average BW/HW gaps by grade (pooled across years and districts).
    """
    def grade_mean(g):
        return pd.Series({
            "mean_ss": weighted_mean(g["mean_ss"], g["n_tested"]),
        })

    by_grade = (
        df.groupby(["year", "subject", "grade", "race"])
        .apply(grade_mean, include_groups=False)
        .reset_index()
    )

    records = []
    for subj in PRIMARY_SUBJECTS:
        for grade in GRADE_ORDER:
            for year in ANALYSIS_YEARS:
                cell = by_grade[
                    (by_grade["year"] == year)
                    & (by_grade["subject"] == subj)
                    & (by_grade["grade"] == grade)
                ].set_index("race")["mean_ss"]
                if "White" not in cell or pd.isna(cell.get("White", np.nan)):
                    continue
                for _ra, rb, pair_label, _ in GAP_PAIRS:
                    if rb not in cell or pd.isna(cell.get(rb, np.nan)):
                        continue
                    records.append({
                        "year": year,
                        "subject": subj,
                        "grade": grade,
                        "gap_pair": pair_label,
                        "gap": cell["White"] - cell[rb],
                    })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Within-between decomposition (mirrors 05_decomposition.py)
# ---------------------------------------------------------------------------

def decompose_gap(unit_df: pd.DataFrame, race_a: str, race_b: str, unit_col: str) -> dict:
    """
    Compute T, B, W for race_a minus race_b within a single cell.
    unit_df must have columns [unit_col, 'race', 'mean_ss', 'n_tested'].
    """
    a = (
        unit_df[unit_df["race"] == race_a]
        .set_index(unit_col)[["mean_ss", "n_tested"]]
        .dropna()
        .rename(columns={"mean_ss": "p_a", "n_tested": "n_a"})
    )
    b = (
        unit_df[unit_df["race"] == race_b]
        .set_index(unit_col)[["mean_ss", "n_tested"]]
        .dropna()
        .rename(columns={"mean_ss": "p_b", "n_tested": "n_b"})
    )

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

    both["p_d"] = (
        (both["n_a"] * both["p_a"] + both["n_b"] * both["p_b"])
        / (both["n_a"] + both["n_b"])
    )
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


def run_decomposition(dist_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run within-between decomposition on the district-level collapsed panel.
    Loops over year × subject cells.
    """
    records = []
    for year in ANALYSIS_YEARS:
        for subj in PRIMARY_SUBJECTS:
            cell = dist_df[
                (dist_df["year"] == year) & (dist_df["subject"] == subj)
            ]
            if cell.empty:
                continue
            for ra, rb, pair_label, pair_desc in GAP_PAIRS:
                res = decompose_gap(cell, ra, rb, "district_name")
                records.append({
                    "year": year,
                    "subject": subj,
                    "gap_pair": pair_label,
                    "gap_desc": pair_desc,
                    **res,
                })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# MMSD and peer comparisons
# ---------------------------------------------------------------------------

def mmsd_vs_peers(dist_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare MMSD mean SS to peer districts for Black and Hispanic students.
    Returns a long DataFrame with district_label, tier, year, subject, race, mean_ss.
    """
    records = []

    # MMSD rows
    mmsd_raw = dist_df[dist_df["district_name"].isin(MMSD_NAMES)].copy()
    mmsd_agg = (
        mmsd_raw.groupby(["year", "subject", "race"])
        .apply(
            lambda g: pd.Series({
                "mean_ss": weighted_mean(g["mean_ss"], g["n_tested"]),
                "n_tested": g["n_tested"].sum(),
            }),
            include_groups=False,
        )
        .reset_index()
    )
    for _, row in mmsd_agg.iterrows():
        records.append({
            "district_label": MMSD_CANONICAL,
            "tier": "MMSD",
            "year": row["year"],
            "subject": row["subject"],
            "race": row["race"],
            "mean_ss": row["mean_ss"],
            "n_tested": row["n_tested"],
        })

    # Peer district rows
    for canonical, variants in PEER_DISTRICTS.items():
        peer_raw = dist_df[dist_df["district_name"].isin(variants)].copy()
        if peer_raw.empty:
            continue
        peer_agg = (
            peer_raw.groupby(["year", "subject", "race"])
            .apply(
                lambda g: pd.Series({
                    "mean_ss": weighted_mean(g["mean_ss"], g["n_tested"]),
                    "n_tested": g["n_tested"].sum(),
                }),
                include_groups=False,
            )
            .reset_index()
        )
        for _, row in peer_agg.iterrows():
            records.append({
                "district_label": canonical,
                "tier": PEER_TIERS[canonical],
                "year": row["year"],
                "subject": row["subject"],
                "race": row["race"],
                "mean_ss": row["mean_ss"],
                "n_tested": row["n_tested"],
            })

    return pd.DataFrame(records)


def mmsd_vs_nonmmsd_white(df: pd.DataFrame, dist_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare MMSD Black / Hispanic mean SS to non-MMSD White mean SS.
    """
    # MMSD minority
    mmsd_raw = dist_df[dist_df["district_name"].isin(MMSD_NAMES)].copy()
    mmsd_minority = (
        mmsd_raw[mmsd_raw["race"].isin(["Black", "Hispanic"])]
        .groupby(["year", "subject", "race"])
        .apply(
            lambda g: pd.Series({
                "mean_ss": weighted_mean(g["mean_ss"], g["n_tested"]),
                "n_tested": g["n_tested"].sum(),
            }),
            include_groups=False,
        )
        .reset_index()
    )
    mmsd_minority["group"] = "MMSD " + mmsd_minority["race"]

    # Non-MMSD White
    nonmmsd_white_raw = df[~df["district_name"].isin(MMSD_NAMES) & (df["race"] == "White")].copy()
    nonmmsd_white = (
        nonmmsd_white_raw.groupby(["year", "subject"])
        .apply(
            lambda g: pd.Series({
                "mean_ss": weighted_mean(g["mean_ss"], g["n_tested"]),
                "n_tested": g["n_tested"].sum(),
            }),
            include_groups=False,
        )
        .reset_index()
    )
    nonmmsd_white["race"] = "White"
    nonmmsd_white["group"] = "Non-MMSD White"

    combined = pd.concat([
        mmsd_minority[["year", "subject", "race", "group", "mean_ss", "n_tested"]],
        nonmmsd_white[["year", "subject", "race", "group", "mean_ss", "n_tested"]],
    ], ignore_index=True)

    return combined


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def _save_fig(name: str) -> None:
    for ext in ("pdf", "png"):
        plt.savefig(OUT_FIGS / f"{name}.{ext}", dpi=FIG_DPI, bbox_inches="tight")
    plt.close()


def fig_gap_trends(gaps: pd.DataFrame) -> None:
    """
    fig_A1: BW and HW scale-score gaps by year, two panels (Reading, Math).
    """
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)

    for ax, subj in zip(axes, PRIMARY_SUBJECTS):
        sub = gaps[gaps["subject"] == subj]
        for ra, rb, pair_label, pair_desc in GAP_PAIRS:
            pair_sub = sub[sub["gap_pair"] == pair_label].sort_values("year")
            if pair_sub.empty:
                continue
            ax.plot(
                pair_sub["year"], pair_sub["gap"],
                marker="o", linewidth=2.0,
                color=GAP_COLORS[pair_label],
                label=pair_desc,
            )

        ax.set_title(SUBJECT_LABEL[subj], fontsize=11, fontweight="bold")
        ax.set_xlabel("School Year")
        ax.tick_params(axis="x", rotation=35)
        ax.legend(fontsize=9)

    axes[0].set_ylabel("White minus Minority\nMean Scale Score (points)")
    fig.suptitle(
        "Wisconsin WKCE-Era Racial Scale-Score Gaps\n"
        "(Enrollment-Weighted Statewide Mean, Grades 3–8, 2008–09 to 2013–14)",
        fontsize=11, fontweight="bold", y=1.01,
    )
    fig.tight_layout()
    _save_fig("fig_A1_wkce_gap_trends")
    print("  Saved fig_A1_wkce_gap_trends")


def fig_gaps_by_grade(grade_gaps: pd.DataFrame) -> None:
    """
    fig_A2: BW/HW gaps by grade, two panels (Reading, Math), pooled across years.
    """
    # Average across years
    mean_by_grade = (
        grade_gaps.groupby(["subject", "grade", "gap_pair"])["gap"]
        .mean()
        .reset_index()
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)

    bar_width = 0.35
    x = np.arange(len(GRADE_ORDER))

    for ax, subj in zip(axes, PRIMARY_SUBJECTS):
        sub = mean_by_grade[mean_by_grade["subject"] == subj]
        for i, (ra, rb, pair_label, pair_desc) in enumerate(GAP_PAIRS):
            pair_data = (
                sub[sub["gap_pair"] == pair_label]
                .set_index("grade")
                .reindex(GRADE_ORDER)["gap"]
            )
            ax.bar(
                x + (i - 0.5) * bar_width,
                pair_data.values,
                width=bar_width,
                color=GAP_COLORS[pair_label],
                alpha=0.85,
                label=pair_desc,
            )

        ax.set_xticks(x)
        ax.set_xticklabels([f"Gr {g}" for g in GRADE_ORDER])
        ax.set_title(SUBJECT_LABEL[subj], fontsize=11, fontweight="bold")
        ax.set_xlabel("Grade")
        ax.legend(fontsize=9)

    axes[0].set_ylabel("White minus Minority\nMean Scale Score (points, avg. 2008–2014)")
    fig.suptitle(
        "WKCE Racial Scale-Score Gaps by Grade\n"
        "(Pooled 2008–09 to 2013–14)",
        fontsize=11, fontweight="bold", y=1.01,
    )
    fig.tight_layout()
    _save_fig("fig_A2_wkce_gaps_by_grade")
    print("  Saved fig_A2_wkce_gaps_by_grade")


def fig_decomposition(decomp: pd.DataFrame) -> None:
    """
    fig_A3: Stacked bar of within/between shares of scale-score gap, by year × subject.
    """
    valid = decomp[decomp["T"].notna() & (decomp["T"] > 0)].copy()

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=False)
    fig.suptitle(
        "WKCE Within-Between Decomposition of Racial Scale-Score Gaps\n"
        "(District Level, Grades 3–8 Aggregated, 2008–09 to 2013–14)",
        fontsize=11, fontweight="bold",
    )

    bar_width = 0.55
    between_color = "#4393c3"
    within_color  = "#d6604d"

    for row_i, (ra, rb, pair_label, pair_desc) in enumerate(GAP_PAIRS):
        for col_i, subj in enumerate(PRIMARY_SUBJECTS):
            ax = axes[row_i][col_i]
            sub = valid[
                (valid["gap_pair"] == pair_label) & (valid["subject"] == subj)
            ].sort_values("year")
            if sub.empty:
                ax.set_visible(False)
                continue

            years = sub["year"].tolist()
            x = np.arange(len(years))

            ax.bar(x, sub["W_pct"].values, bar_width, label="Within", color=within_color, alpha=0.85)
            ax.bar(x, sub["B_pct"].values, bar_width, bottom=sub["W_pct"].values,
                   label="Between", color=between_color, alpha=0.85)

            ax.axhline(50, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
            ax.set_xticks(x)
            ax.set_xticklabels(years, rotation=35, ha="right", fontsize=8)
            ax.set_ylim(0, 105)
            ax.set_ylabel("Share of Total Gap (%)")
            ax.set_title(f"{pair_desc} — {SUBJECT_LABEL[subj]}", fontsize=10)
            if row_i == 0 and col_i == 0:
                ax.legend(fontsize=8)

            # Annotate total T
            for xi, (_, row) in enumerate(sub.iterrows()):
                ax.text(xi, 102, f"{row['T']:.1f}", ha="center", va="center",
                        fontsize=7, color="#333333")

    fig.tight_layout()
    _save_fig("fig_A3_wkce_decomposition")
    print("  Saved fig_A3_wkce_decomposition")


def fig_mmsd_vs_peers(comp: pd.DataFrame) -> None:
    """
    fig_A4: MMSD minority mean SS vs peer districts, one panel per subject × race.
    Tier 1 peers shown as solid lines; Tier 2 / Madison region as dashed.
    MMSD shown bold.
    """
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharey=False)
    fig.suptitle(
        "WKCE-Era Mean Scale Scores: MMSD vs. Peer Districts\n"
        "(Minority Students, Grades 3–8, 2008–09 to 2013–14)",
        fontsize=11, fontweight="bold",
    )

    tier_styles = {
        "MMSD":          {"lw": 2.8, "ls": "-",  "zorder": 10},
        "Tier 1":        {"lw": 1.5, "ls": "-",  "zorder": 5},
        "Tier 2":        {"lw": 1.2, "ls": "--", "zorder": 4},
        "Madison region":{"lw": 1.2, "ls": ":",  "zorder": 4},
    }

    for row_i, race in enumerate(["Black", "Hispanic"]):
        for col_i, subj in enumerate(PRIMARY_SUBJECTS):
            ax = axes[row_i][col_i]
            sub = comp[(comp["race"] == race) & (comp["subject"] == subj)]

            for dist_label in sorted(sub["district_label"].unique()):
                dsub = sub[sub["district_label"] == dist_label].sort_values("year")
                if dsub["mean_ss"].notna().sum() < 2:
                    continue
                tier = dsub["tier"].iloc[0]
                style = tier_styles.get(tier, {"lw": 1.0, "ls": "-", "zorder": 3})
                color = RACE_COLORS.get(race, "#888888") if tier == "MMSD" else "#aaaaaa"

                label_str = dist_label if tier == "MMSD" else (
                    dist_label if tier == "Tier 1" else dist_label
                )
                ax.plot(
                    dsub["year"], dsub["mean_ss"],
                    linewidth=style["lw"], linestyle=style["ls"],
                    zorder=style["zorder"],
                    color=color if tier == "MMSD" else None,
                    alpha=1.0 if tier in ("MMSD", "Tier 1") else 0.55,
                    label=label_str,
                    marker="o" if tier == "MMSD" else None,
                    markersize=4,
                )

            ax.set_title(f"{race} — {SUBJECT_LABEL[subj]}", fontsize=10)
            ax.set_xlabel("")
            ax.tick_params(axis="x", rotation=35)
            ax.set_ylabel("Mean Scale Score")

            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, fontsize=7, ncol=2, loc="upper left")

    fig.tight_layout()
    _save_fig("fig_A4_wkce_mmsd_vs_peers")
    print("  Saved fig_A4_wkce_mmsd_vs_peers")


def fig_mmsd_vs_nonmmsd_white(comp: pd.DataFrame) -> None:
    """
    fig_A5: MMSD Black / Hispanic mean SS vs non-MMSD White mean SS.
    Two panels: Reading, Math.
    """
    GROUP_COLORS = {
        "MMSD Black":     "#762a83",
        "MMSD Hispanic":  "#f1a340",
        "Non-MMSD White": "#1b7837",
    }

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    fig.suptitle(
        "WKCE-Era Mean Scale Scores: MMSD Minorities vs. Non-MMSD White Students\n"
        "(Grades 3–8, 2008–09 to 2013–14)",
        fontsize=11, fontweight="bold", y=1.02,
    )

    for ax, subj in zip(axes, PRIMARY_SUBJECTS):
        sub = comp[comp["subject"] == subj]
        for grp in ["Non-MMSD White", "MMSD Black", "MMSD Hispanic"]:
            gsub = sub[sub["group"] == grp].sort_values("year")
            if gsub.empty:
                continue
            ax.plot(
                gsub["year"], gsub["mean_ss"],
                marker="o", markersize=4,
                linewidth=2.0 if grp == "Non-MMSD White" else 1.8,
                color=GROUP_COLORS.get(grp, "#888888"),
                label=grp,
            )

        ax.set_title(SUBJECT_LABEL[subj], fontsize=11, fontweight="bold")
        ax.set_xlabel("School Year")
        ax.tick_params(axis="x", rotation=35)
        ax.legend(fontsize=9)

    axes[0].set_ylabel("Mean Scale Score")
    fig.tight_layout()
    _save_fig("fig_A5_wkce_mmsd_vs_nonmmsd_white")
    print("  Saved fig_A5_wkce_mmsd_vs_nonmmsd_white")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading WKCE panel …")
    df = load_panel()
    print(f"  Filtered panel: {len(df):,} rows")
    print(f"  Years: {sorted(df['year'].unique())}")
    print(f"  Districts: {df['district_name'].nunique()}")
    print()

    # ---- State-level gaps ------------------------------------------------
    print("Computing state-level scale-score gaps …")
    state_df, gaps_df = compute_state_gaps(df)
    state_df.to_csv(OUT_TABLES / "wkce_state_mean_ss.csv", index=False)
    gaps_df.to_csv(OUT_TABLES / "wkce_state_gaps.csv", index=False)
    print(f"  Gap records: {len(gaps_df)}")
    print()

    print("  BW gaps (Reading, 2008-14):")
    bw = gaps_df[(gaps_df["gap_pair"] == "BW") & (gaps_df["subject"] == "Reading")]
    print(bw[["year", "gap"]].to_string(index=False))
    print()

    grade_gaps = compute_state_gaps_by_grade(df)

    # ---- District-level aggregation for decomp and peers ---------------
    print("Aggregating to district × race × year × subject …")
    dist_df = collapse_to_district(df)
    print(f"  District-level rows: {len(dist_df):,}")
    suppression = dist_df["mean_ss"].isna().mean()
    print(f"  Suppression rate at district level: {suppression*100:.1f}%")
    print()

    # ---- Within-between decomposition -----------------------------------
    print("Running within-between decomposition …")
    decomp = run_decomposition(dist_df)
    decomp.to_csv(OUT_TABLES / "wkce_decomposition.csv", index=False)
    print("  Sample decomposition (BW Reading):")
    sub = decomp[(decomp["gap_pair"] == "BW") & (decomp["subject"] == "Reading")]
    print(sub[["year", "T", "B", "W", "B_pct", "W_pct", "n_units_both"]].to_string(index=False))
    print()

    # ---- MMSD peer comparison -------------------------------------------
    print("Building MMSD vs. peer district comparison …")
    peers_df = mmsd_vs_peers(dist_df)
    peers_df.to_csv(OUT_TABLES / "wkce_mmsd_peers.csv", index=False)
    print(f"  Records: {len(peers_df):,}")
    print()

    print("Building MMSD minority vs. non-MMSD White comparison …")
    nonmmsd_df = mmsd_vs_nonmmsd_white(df, dist_df)
    nonmmsd_df.to_csv(OUT_TABLES / "wkce_mmsd_vs_nonmmsd_white.csv", index=False)
    print()

    # ---- Figures ---------------------------------------------------------
    print("Generating figures …")
    fig_gap_trends(gaps_df)
    fig_gaps_by_grade(grade_gaps)
    fig_decomposition(decomp)
    fig_mmsd_vs_peers(peers_df)
    fig_mmsd_vs_nonmmsd_white(nonmmsd_df)
    print()

    print("Done — WKCE appendix analysis complete.")
    print(f"  Tables → {OUT_TABLES}")
    print(f"  Figures → {OUT_FIGS}")


if __name__ == "__main__":
    main()
