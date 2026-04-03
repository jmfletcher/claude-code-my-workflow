"""
06_mmsd_peers.py — RQ3: MMSD deep-dive and cross-district comparisons.

Three sub-analyses:
  1. MMSD minority vs peer district minority (Tier 1 + Tier 2)
  2. MMSD minority vs non-MMSD White statewide
  3. Within-MMSD school distribution + school-level decomposition

Peer district tiers (exact district_name strings from DPI panel):
  Tier 1 — major urban:
    Milwaukee, Racine Unified, Kenosha, Green Bay Area Public, Beloit
  Tier 2 — mid-size:
    Sun Prairie Area, Appleton Area, Waukesha, Janesville,
    West Allis-West Milwaukee
  Madison region:
    Verona Area, Middleton-Cross Plains Area

Inputs:
  output/data/panel_district_race.parquet
  output/data/panel_school_race.parquet

Outputs:
  output/tables/mmsd_vs_peers.csv
  output/tables/mmsd_vs_nonmmsd_white.csv
  output/figures/fig05_mmsd_vs_peers_black.{pdf,png}
  output/figures/fig06_mmsd_vs_peers_hispanic.{pdf,png}
  output/figures/fig07_mmsd_vs_nonmmsd_white.{pdf,png}
  output/figures/fig08_mmsd_within_schools.{pdf,png}
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
PANEL_DIST   = ROOT / "output" / "data" / "panel_district_race.parquet"
PANEL_SCHOOL = ROOT / "output" / "data" / "panel_school_race.parquet"
OUT_TABLES   = ROOT / "output" / "tables"
OUT_FIGS     = ROOT / "output" / "figures"

OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MMSD_NAME = "Madison Metropolitan"
EXCLUDE_RACES = {"Unknown", "Unknown/Suppressed"}

PEER_TIERS = {
    "Tier 1":          ["Milwaukee", "Racine Unified", "Kenosha",
                        "Green Bay Area Public", "Beloit"],
    "Tier 2":          ["Sun Prairie Area", "Appleton Area", "Waukesha",
                        "Janesville", "West Allis-West Milwaukee"],
    "Madison region":  ["Verona Area", "Middleton-Cross Plains Area"],
}

ALL_PEERS = [d for districts in PEER_TIERS.values() for d in districts]

RACE_COLORS = {
    "White":    "#1b7837",
    "Black":    "#762a83",
    "Hispanic": "#f1a340",
    "Asian":    "#2166ac",
}

SUBJECT_LABEL = {"ELA": "ELA", "Mathematics": "Math"}
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
# Load helpers
# ---------------------------------------------------------------------------

def load_district_panel() -> pd.DataFrame:
    df = pd.read_parquet(PANEL_DIST)
    df = df[
        df["primary_analysis"] &
        ~df["race"].isin(EXCLUDE_RACES)
    ].copy()
    df["grade"] = df["grade"].astype(int)
    return df


def load_school_panel() -> pd.DataFrame:
    df = pd.read_parquet(PANEL_SCHOOL)
    df = df[
        df["primary_analysis"] &
        ~df["race"].isin(EXCLUDE_RACES)
    ].copy()
    df["grade"] = df["grade"].astype(int)
    return df


def weighted_mean(g: pd.DataFrame) -> float:
    valid = g.dropna(subset=["pct_proficient", "n_tested"])
    if valid.empty or valid["n_tested"].sum() == 0:
        return np.nan
    return np.average(valid["pct_proficient"], weights=valid["n_tested"])


def collapse_to_district_year(
    df: pd.DataFrame,
    districts: list,
    races: list,
) -> pd.DataFrame:
    """
    Collapse grade × subject to get district × race × year proficiency.
    Only non-suppressed rows contribute; suppressed flag set on aggregate.
    """
    sub = df[
        df["district_name"].isin(districts) &
        df["race"].isin(races) &
        ~df["suppressed"]
    ].copy()

    agg = (
        sub.groupby(["district_name", "race", "year", "subject"])
        .apply(weighted_mean, include_groups=False)
        .rename("pct_proficient")
        .reset_index()
    )
    # Also compute total n_tested for annotation
    n_agg = (
        sub.groupby(["district_name", "race", "year", "subject"])["n_tested"]
        .sum()
        .rename("n_tested")
        .reset_index()
    )
    return agg.merge(n_agg, on=["district_name", "race", "year", "subject"])


# ---------------------------------------------------------------------------
# Sub-analysis 1: MMSD minority vs peer minority
# ---------------------------------------------------------------------------

def sa1_peer_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns district × race × year × subject proficiency for MMSD + all peers.
    """
    all_districts = [MMSD_NAME] + ALL_PEERS
    races = ["Black", "Hispanic", "White"]
    result = collapse_to_district_year(df, all_districts, races)

    # Add tier label
    tier_map = {d: tier for tier, dlist in PEER_TIERS.items() for d in dlist}
    tier_map[MMSD_NAME] = "MMSD"
    result["tier"] = result["district_name"].map(tier_map)
    return result


# ---------------------------------------------------------------------------
# Sub-analysis 2: MMSD minority vs non-MMSD White
# ---------------------------------------------------------------------------

def sa2_mmsd_vs_nonmmsd_white(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare MMSD Black and Hispanic proficiency to non-MMSD White statewide.
    Returns a year × subject summary table.
    """
    # Non-MMSD White
    nonmmsd_white = df[
        (df["district_name"] != MMSD_NAME) &
        (df["race"] == "White") &
        ~df["suppressed"]
    ].copy()

    nonmmsd_agg = (
        nonmmsd_white.groupby(["year", "subject", "grade"])
        .apply(weighted_mean, include_groups=False)
        .rename("pct_proficient")
        .reset_index()
    )
    # Grade-weighted mean for non-MMSD White
    nonmmsd_enroll = (
        nonmmsd_white.groupby(["year", "subject", "grade"])["n_tested"]
        .sum()
        .rename("n_tested")
        .reset_index()
    )
    nonmmsd_merged = nonmmsd_agg.merge(nonmmsd_enroll, on=["year", "subject", "grade"])

    nonmmsd_yr_subj = (
        nonmmsd_merged.groupby(["year", "subject"])
        .apply(lambda g: np.average(g["pct_proficient"], weights=g["n_tested"])
               if g["n_tested"].sum() > 0 else np.nan,
               include_groups=False)
        .rename("pct_proficient")
        .reset_index()
    )
    nonmmsd_yr_subj["district_name"] = "Non-MMSD Wisconsin"
    nonmmsd_yr_subj["race"] = "White"

    # MMSD Black and Hispanic (collapse_to_district_year already weight-averages across grades)
    mmsd_races = collapse_to_district_year(df, [MMSD_NAME], ["Black", "Hispanic"])
    mmsd_yr_subj = mmsd_races[["district_name", "race", "year", "subject", "pct_proficient"]]

    combined = pd.concat([
        nonmmsd_yr_subj[["district_name", "race", "year", "subject", "pct_proficient"]],
        mmsd_yr_subj[["district_name", "race", "year", "subject", "pct_proficient"]],
    ], ignore_index=True)

    return combined


# ---------------------------------------------------------------------------
# Sub-analysis 3: Within-MMSD school distribution
# ---------------------------------------------------------------------------

def sa3_mmsd_schools(df_school: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate MMSD school panel to school × race × year (collapsing grade + subject).
    Apply suppression threshold on aggregate (n_tested >= 10).
    """
    mmsd = df_school[
        df_school["district_name"] == MMSD_NAME
    ].copy()

    # Separate suppressed/non-suppressed — sum n_tested across all, only use non-suppressed for pct
    n_agg = (
        mmsd.groupby(["school_name", "school_code", "race", "year"])["n_tested"]
        .sum()
        .rename("n_tested_total")
        .reset_index()
    )

    pct_agg = (
        mmsd[~mmsd["suppressed"]]
        .groupby(["school_name", "school_code", "race", "year"])
        .apply(weighted_mean, include_groups=False)
        .rename("pct_proficient")
        .reset_index()
    )

    school_agg = n_agg.merge(pct_agg, on=["school_name", "school_code", "race", "year"], how="left")
    school_agg["suppressed_agg"] = school_agg["n_tested_total"] < 10
    return school_agg


def mmsd_school_decomposition(school_agg: pd.DataFrame) -> pd.DataFrame:
    """
    Apply within-between decomposition across MMSD schools for each year.
    Returns year-level decomposition table.
    """
    records = []
    for year in sorted(school_agg["year"].unique()):
        yr = school_agg[school_agg["year"] == year].copy()
        for race_a, race_b, pair_label in [("White", "Black", "BW"), ("White", "Hispanic", "HW")]:
            a = yr[(yr["race"] == race_a) & ~yr["suppressed_agg"] & yr["pct_proficient"].notna()]
            b = yr[(yr["race"] == race_b) & ~yr["suppressed_agg"] & yr["pct_proficient"].notna()]
            both = a.set_index("school_code")[["pct_proficient", "n_tested_total"]].join(
                b.set_index("school_code")[["pct_proficient", "n_tested_total"]],
                lsuffix="_a", rsuffix="_b"
            ).dropna()

            if both.empty or both["n_tested_total_a"].sum() == 0 or both["n_tested_total_b"].sum() == 0:
                continue

            N_a = both["n_tested_total_a"].sum()
            N_b = both["n_tested_total_b"].sum()
            p_bar_a = (both["pct_proficient_a"] * both["n_tested_total_a"]).sum() / N_a
            p_bar_b = (both["pct_proficient_b"] * both["n_tested_total_b"]).sum() / N_b
            T = p_bar_a - p_bar_b
            p_d = (both["n_tested_total_a"] * both["pct_proficient_a"] +
                   both["n_tested_total_b"] * both["pct_proficient_b"]) / \
                  (both["n_tested_total_a"] + both["n_tested_total_b"])
            B = (p_d * (both["n_tested_total_a"] / N_a - both["n_tested_total_b"] / N_b)).sum()
            W = T - B
            records.append({
                "year": year, "gap_pair": pair_label,
                "T": T, "B": B, "W": W,
                "B_pct": 100 * B / T if T else np.nan,
                "W_pct": 100 * W / T if T else np.nan,
                "n_schools": len(both),
            })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def save_fig(fig: plt.Figure, stem: str) -> None:
    for ext in ("pdf", "png"):
        fig.savefig(OUT_FIGS / f"{stem}.{ext}", dpi=FIG_DPI, bbox_inches="tight")
    print(f"  Saved {stem}.pdf / .png")


def fig_mmsd_vs_peers(peer_df: pd.DataFrame, minority_race: str,
                      fig_stem: str, race_label: str) -> None:
    """
    Two panels (ELA, Math): MMSD minority as thick line; peers as thin colored lines.
    Tier 1 peers in solid lines, Tier 2 and Madison region dashed.
    """
    subjects = ["ELA", "Mathematics"]
    year_order = sorted(peer_df["year"].unique())

    tier_linestyle = {
        "MMSD":           (RACE_COLORS[minority_race], 2.8, "solid"),
        "Tier 1":         ("#444444",                  1.0, "solid"),
        "Tier 2":         ("#888888",                  0.8, "dashed"),
        "Madison region": ("#aaaaaa",                  0.8, "dotted"),
    }

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    for col_i, subj in enumerate(subjects):
        ax = axes[col_i]
        subj_df = peer_df[
            (peer_df["race"] == minority_race) &
            (peer_df["subject"] == subj)
        ]

        for district in subj_df["district_name"].unique():
            dist_data = subj_df[subj_df["district_name"] == district].set_index("year")
            tier = (dist_data["tier"].iloc[0]
                    if "tier" in dist_data.columns else "Tier 1")
            color, lw, ls = tier_linestyle.get(tier, ("#cccccc", 0.8, "solid"))
            vals = [dist_data.loc[y, "pct_proficient"] if y in dist_data.index else np.nan
                    for y in year_order]

            label = district if tier == "MMSD" else None
            ax.plot(range(len(year_order)), vals,
                    color=color, linewidth=lw, linestyle=ls,
                    marker="o", markersize=3 if tier != "MMSD" else 5,
                    label=label, zorder=5 if tier == "MMSD" else 2, alpha=0.7)

        ax.set_xticks(range(len(year_order)))
        ax.set_xticklabels(year_order, rotation=40, ha="right", fontsize=9)
        ax.set_title(SUBJECT_LABEL[subj], fontsize=11, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.set_ylim(bottom=0, top=100)
        if col_i == 0:
            ax.set_ylabel(f"{race_label} proficiency rate (%)", fontsize=10)

    # Shared legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color=RACE_COLORS[minority_race], linewidth=2.5,
               label=f"MMSD {race_label}"),
        Line2D([0], [0], color="#444444", linewidth=1.0, label="Tier 1 peers"),
        Line2D([0], [0], color="#888888", linewidth=0.8, linestyle="dashed",
               label="Tier 2 peers"),
        Line2D([0], [0], color="#aaaaaa", linewidth=0.8, linestyle="dotted",
               label="Madison region peers"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=4,
               fontsize=8.5, framealpha=0.9, bbox_to_anchor=(0.5, -0.07))

    fig.suptitle(
        f"MMSD {race_label} Students vs. Peer Districts — Forward Exam Primary Years",
        fontsize=11, fontweight="bold"
    )
    fig.text(0.5, -0.13,
             f"Note: Each line = district-level {race_label} proficiency, "
             "enrollment-weighted across grades. "
             "Primary years: 2015-16 to 2022-23 (excludes 2019-20, 2020-21).\n"
             "Suppressed district-year cells excluded (shown as gaps).",
             ha="center", fontsize=8, color="#555555")
    plt.tight_layout()
    save_fig(fig, fig_stem)
    plt.close(fig)


def fig_mmsd_vs_nonmmsd_white(combined_df: pd.DataFrame) -> None:
    """
    Two panels (ELA, Math): MMSD Black (purple), MMSD Hispanic (orange),
    non-MMSD Wisconsin White (green).
    """
    subjects = ["ELA", "Mathematics"]
    series_def = [
        (MMSD_NAME,          "Black",    "MMSD Black",            RACE_COLORS["Black"],    2.2, "solid"),
        (MMSD_NAME,          "Hispanic", "MMSD Hispanic",         RACE_COLORS["Hispanic"], 2.2, "solid"),
        ("Non-MMSD Wisconsin","White",   "Wisconsin White (non-MMSD)", RACE_COLORS["White"], 2.2, "dashed"),
    ]

    year_order = sorted(combined_df["year"].unique())
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    for col_i, subj in enumerate(subjects):
        ax = axes[col_i]
        subj_df = combined_df[combined_df["subject"] == subj]

        for dist, race, label, color, lw, ls in series_def:
            data = subj_df[
                (subj_df["district_name"] == dist) &
                (subj_df["race"] == race)
            ].set_index("year")
            vals = [data.loc[y, "pct_proficient"] if y in data.index else np.nan
                    for y in year_order]
            ax.plot(range(len(year_order)), vals,
                    color=color, linewidth=lw, linestyle=ls,
                    marker="o", markersize=5, label=label)

        ax.set_xticks(range(len(year_order)))
        ax.set_xticklabels(year_order, rotation=40, ha="right", fontsize=9)
        ax.set_title(SUBJECT_LABEL[subj], fontsize=11, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.set_ylim(bottom=0, top=100)
        if col_i == 0:
            ax.set_ylabel("Proficiency rate (%)", fontsize=10)
        if col_i == 1:
            ax.legend(fontsize=8.5, loc="upper right", framealpha=0.9)

    fig.suptitle(
        "MMSD Minority Students vs. Wisconsin White Students (Non-MMSD)\n"
        "Forward Exam — Primary Years 2015–2023",
        fontsize=11, fontweight="bold"
    )
    fig.text(0.5, -0.04,
             "Note: MMSD minority = district-level enrollment-weighted proficiency. "
             "Non-MMSD White = statewide White proficiency excluding Madison Metropolitan.\n"
             "Primary years: 2015-16 to 2022-23 (excludes 2019-20, 2020-21).",
             ha="center", fontsize=8, color="#555555")
    plt.tight_layout()
    save_fig(fig, "fig07_mmsd_vs_nonmmsd_white")
    plt.close(fig)


def fig_mmsd_within_schools(school_agg: pd.DataFrame, decomp_df: pd.DataFrame) -> None:
    """
    Box plots: distribution of school-level proficiency within MMSD by race and year.
    Inset table shows within-school decomposition B_pct for BW gap.
    """
    races = ["White", "Black", "Hispanic"]
    year_order = sorted(school_agg["year"].unique())
    colors = {r: RACE_COLORS[r] for r in races}

    valid = school_agg[
        ~school_agg["suppressed_agg"] &
        school_agg["race"].isin(races) &
        school_agg["pct_proficient"].notna()
    ]

    fig, ax = plt.subplots(figsize=(12, 6))

    n_years = len(year_order)
    n_races = len(races)
    group_width = 0.8
    bar_width = group_width / n_races
    positions = []
    all_bp = []

    for yi, year in enumerate(year_order):
        yr_data = valid[valid["year"] == year]
        for ri, race in enumerate(races):
            pos = yi * (n_races + 1) * bar_width + ri * bar_width + bar_width / 2
            positions.append(pos)
            vals = yr_data[yr_data["race"] == race]["pct_proficient"].dropna().values
            all_bp.append(vals)

    bp = ax.boxplot(
        all_bp,
        positions=positions,
        widths=bar_width * 0.7,
        patch_artist=True,
        medianprops=dict(color="black", linewidth=1.5),
        whiskerprops=dict(linewidth=0.8),
        capprops=dict(linewidth=0.8),
        flierprops=dict(marker="o", markersize=2.5, alpha=0.4),
        showfliers=True,
    )

    # Color by race
    for i, patch in enumerate(bp["boxes"]):
        race = races[i % n_races]
        patch.set_facecolor(colors[race])
        patch.set_alpha(0.7)
    for i, flier in enumerate(bp["fliers"]):
        flier.set(markerfacecolor=colors[races[i % n_races]], alpha=0.4)

    # X-tick labels: year group centers
    group_centers = [
        yi * (n_races + 1) * bar_width + (n_races - 1) * bar_width / 2
        for yi in range(n_years)
    ]
    ax.set_xticks(group_centers)
    ax.set_xticklabels(year_order, fontsize=9)
    ax.set_ylabel("School-level proficiency rate (%)", fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_ylim(bottom=0, top=105)
    ax.set_title(
        "Distribution of School-Level Proficiency Within MMSD by Race\n"
        "Forward Exam — Primary Years 2015–2023",
        fontsize=11, fontweight="bold"
    )

    # Legend
    from matplotlib.patches import Patch
    legend_handles = [Patch(facecolor=colors[r], alpha=0.7, label=r) for r in races]
    ax.legend(handles=legend_handles, fontsize=9, loc="upper right", framealpha=0.9)

    # Add BW decomposition annotation (B_pct)
    bw_decomp = decomp_df[decomp_df["gap_pair"] == "BW"][["year", "T", "B_pct", "W_pct"]].set_index("year")
    ann_lines = ["Between-school share of MMSD BW gap:"]
    for year in year_order:
        if year in bw_decomp.index:
            row = bw_decomp.loc[year]
            ann_lines.append(f"  {year}: {row['B_pct']:.0f}% between ({row['T']:.1f} pp total)")
    ax.text(0.01, 0.02, "\n".join(ann_lines),
            transform=ax.transAxes, fontsize=7.5, va="bottom",
            color="#333333", family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="#cccccc"))

    ax.text(0.5, -0.08,
            "Note: Each box = distribution of school-level proficiency for that race group in MMSD "
            "(non-suppressed schools only).\n"
            "Proficiency = enrollment-weighted mean across grade/subject within each school × year.",
            transform=ax.transAxes, ha="center", fontsize=8, color="#555555")
    plt.tight_layout()
    save_fig(fig, "fig08_mmsd_within_schools")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 65)
    print("06_mmsd_peers.py — RQ3: MMSD deep-dive and peer comparisons")
    print("=" * 65)

    df_dist   = load_district_panel()
    df_school = load_school_panel()

    # --- Sub-analysis 1: MMSD vs peers ---
    print("\n[SA1] Building MMSD vs peer comparison...")
    peer_df = sa1_peer_comparison(df_dist)
    print(f"  Districts in peer comparison: {peer_df['district_name'].nunique()}")
    print(f"  Rows: {len(peer_df):,}")
    peer_df.to_csv(OUT_TABLES / "mmsd_vs_peers.csv", index=False)
    print(f"  Saved: output/tables/mmsd_vs_peers.csv")

    # Print MMSD Black ELA summary
    mmsd_blk = peer_df[
        (peer_df["district_name"] == MMSD_NAME) &
        (peer_df["race"] == "Black") &
        (peer_df["subject"] == "ELA")
    ][["year", "pct_proficient", "n_tested"]]
    print(f"\n  MMSD Black ELA proficiency by year:\n{mmsd_blk.to_string(index=False)}")

    # --- Sub-analysis 2: MMSD minority vs non-MMSD White ---
    print("\n[SA2] MMSD minority vs non-MMSD White...")
    combined_df = sa2_mmsd_vs_nonmmsd_white(df_dist)
    combined_df.to_csv(OUT_TABLES / "mmsd_vs_nonmmsd_white.csv", index=False)
    print(f"  Saved: output/tables/mmsd_vs_nonmmsd_white.csv")

    pivot_check = combined_df[combined_df["subject"] == "ELA"].pivot_table(
        index="year", columns=["district_name", "race"], values="pct_proficient"
    )
    print(f"\n  ELA proficiency comparison:\n{pivot_check.round(1).to_string()}")

    # --- Sub-analysis 3: Within-MMSD schools ---
    print("\n[SA3] Within-MMSD school distribution...")
    school_agg = sa3_mmsd_schools(df_school)
    decomp_df  = mmsd_school_decomposition(school_agg)
    print(f"  MMSD school agg rows: {len(school_agg):,}")
    print(f"\n  MMSD within-school BW decomposition:")
    bw = decomp_df[decomp_df["gap_pair"] == "BW"]
    print(bw[["year", "T", "B", "W", "B_pct", "W_pct", "n_schools"]].round(1).to_string(index=False))

    # --- Figures ---
    print("\nGenerating figures...")
    fig_mmsd_vs_peers(peer_df, "Black",    "fig05_mmsd_vs_peers_black",    "Black")
    fig_mmsd_vs_peers(peer_df, "Hispanic", "fig06_mmsd_vs_peers_hispanic", "Hispanic")
    fig_mmsd_vs_nonmmsd_white(combined_df)
    fig_mmsd_within_schools(school_agg, decomp_df)

    print("\nDone.")


if __name__ == "__main__":
    main()
