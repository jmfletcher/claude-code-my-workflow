"""
08_act_gaps.py — ACT grade-11 racial gaps (2015-16 to 2022-23).

Wisconsin mandates ACT testing for all grade-11 public school students
(funded by the state since 2015-16), giving near-universal participation
across all demographic groups. This makes Wisconsin ACT data unusually
clean for racial gap analysis — unlike voluntary ACT states where
high-ability students self-select into testing.

IMPORTANT CAVEAT: Students who drop out before grade 11 are not tested.
Black and Hispanic students have higher dropout rates than White students,
so the ACT sample is positively selected for minority students relative
to the grades 3-8 Forward Exam sample. Any BW/HW gap found here
therefore understates the gap for the full cohort.

Metrics used:
  • AVERAGE_SCORE: mean ACT score (1-36 scale); no suppression at district level
  • college_ready_rate: % meeting college-readiness benchmarks
    (English ≥18, Math ≥22, Reading ≥22, Science ≥23 per ACT national benchmarks)

Primary subjects: Composite (overall), Mathematics, English
(English ≈ Forward Exam ELA; Math ≈ Forward Exam Mathematics)

Decomposition formula (identical to scripts 05 and 07):
  T = ā_w − ā_b    (enrollment-weighted statewide gap in mean score)
  B = Σ_d ā_d · (n_w^d/N_w − n_b^d/N_b)
  W = T − B

Analysis window: 2015-16 through 2022-23
  • 2019-20 excluded: no ACT administered (COVID school closures)
  • 2020-21 included in sensitivity check (Appendix C extension)

Inputs:
  Data/raw/act/act_graduates_certified_YYYY-YY.zip

Outputs:
  output/data/panel_act_district_race.parquet
  output/tables/act_state_gaps.csv
  output/tables/act_decomposition.csv
  output/tables/act_mmsd_peers.csv
  output/tables/act_mmsd_vs_nonmmsd_white.csv
  output/figures/fig05_act_gap_trends.{pdf,png}
  output/figures/fig06_act_decomposition.{pdf,png}
  output/figures/fig07_act_mmsd_vs_peers.{pdf,png}
  output/figures/fig08_act_pipeline.{pdf,png}
"""

from pathlib import Path
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT      = Path(__file__).resolve().parent.parent
ACT_DIR   = ROOT / "Data" / "raw" / "act"
FWD_PANEL = ROOT / "output" / "data" / "panel_district_race.parquet"
OUT_DATA  = ROOT / "output" / "data"
OUT_TABLES = ROOT / "output" / "tables"
OUT_FIGS   = ROOT / "output" / "figures"

for d in (OUT_DATA, OUT_TABLES, OUT_FIGS):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ANALYSIS_YEARS = [
    "2015-16", "2016-17", "2017-18", "2018-19", "2021-22", "2022-23",
]
# 2020-21 available but COVID-disrupted; kept for sensitivity check
ALL_YEARS = ANALYSIS_YEARS + ["2020-21"]

PRIMARY_SUBJECTS = ["Composite", "Mathematics", "English"]
SUBJECT_LABEL = {
    "Composite":   "ACT Composite",
    "Mathematics": "ACT Mathematics",
    "English":     "ACT English",
}

PRIMARY_RACES  = ["White", "Black", "Hispanic"]
RACE_COLORS = {
    "White":    "#1b7837",
    "Black":    "#762a83",
    "Hispanic": "#f1a340",
}
GAP_PAIRS = [
    ("White", "Black",    "BW", "Black–White"),
    ("White", "Hispanic", "HW", "Hispanic–White"),
]
GAP_COLORS = {"BW": "#762a83", "HW": "#f1a340"}

# MMSD district code in DPI data
MMSD_NAME = "Madison Metropolitan"

PEER_DISTRICTS = {
    "Milwaukee":           "Milwaukee",
    "Racine Unified":      "Racine",
    "Kenosha":             "Kenosha",
    "Green Bay Area":      "Green Bay Area Public",
    "Beloit":              "Beloit",
    "Sun Prairie Area":    "Sun Prairie Area",
    "Appleton Area":       "Appleton Area",
    "Waukesha":            "Waukesha",
    "Janesville":          "Janesville",
    "West Allis-W. Milw.": "West Allis-West Milwaukee",
    "Verona Area":         "Verona Area",
    "Middleton-C.P. Area": "Middleton-Cross Plains Area",
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
# Load ACT data
# ---------------------------------------------------------------------------

def load_one_year(year: str) -> pd.DataFrame:
    """Load a single ACT graduates zip file and return cleaned district-race rows."""
    path = ACT_DIR / f"act_graduates_certified_{year}.zip"
    if not path.exists():
        print(f"  WARNING: {path.name} not found — skipping {year}")
        return pd.DataFrame()

    with zipfile.ZipFile(path) as z:
        csv_files = [f for f in z.namelist() if f.endswith(".csv") and "layout" not in f]
        if not csv_files:
            return pd.DataFrame()
        with z.open(csv_files[0]) as f:
            df = pd.read_csv(f, low_memory=False)

    df["year"] = year
    return df


def load_all_act(years: list[str]) -> pd.DataFrame:
    """Load and concatenate ACT files for the given years."""
    frames = [load_one_year(y) for y in years]
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True)


def clean_act(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to district-level Race/Ethnicity rows for primary subjects.
    Deduplicate to one row per district × race × subject × year (keeping
    AVERAGE_SCORE and computing college_ready_rate from the STUDENT_COUNT split).

    The raw data has up to two rows per group for benchmark subjects
    (Below College Ready / College Ready). AVERAGE_SCORE is identical in both.
    We pivot to get one row with avg_score and cr_rate.
    """
    df = raw[
        (raw["AGENCY_TYPE"] == "School District")
        & (raw["GROUP_BY"] == "Race/Ethnicity")
        & (raw["GROUP_BY_VALUE"].isin(PRIMARY_RACES))
        & (raw["TEST_SUBJECT"].isin(PRIMARY_SUBJECTS))
    ].copy()

    # Parse numeric columns
    df["AVERAGE_SCORE"] = pd.to_numeric(df["AVERAGE_SCORE"], errors="coerce")
    df["STUDENT_COUNT"] = pd.to_numeric(df["STUDENT_COUNT"], errors="coerce")
    df["GROUP_COUNT"]   = pd.to_numeric(df["GROUP_COUNT"],   errors="coerce")

    # Rename for clarity
    df = df.rename(columns={
        "DISTRICT_CODE":  "district_code",
        "DISTRICT_NAME":  "district_name",
        "GROUP_BY_VALUE": "race",
        "TEST_SUBJECT":   "subject",
        "AVERAGE_SCORE":  "avg_score",
        "GROUP_COUNT":    "n_tested",
    })

    # Average score: take first non-null value per group (same across CR rows)
    avg = (
        df.groupby(["year", "district_code", "district_name", "subject", "race"])
        .agg(avg_score=("avg_score", "first"), n_tested=("n_tested", "first"))
        .reset_index()
    )

    # College-ready rate: STUDENT_COUNT where COLLEGE_READINESS == 'College Ready'
    cr = (
        df[df["COLLEGE_READINESS"] == "College Ready"]
        .groupby(["year", "district_code", "district_name", "subject", "race"])
        ["STUDENT_COUNT"]
        .sum()
        .reset_index()
        .rename(columns={"STUDENT_COUNT": "cr_count"})
    )

    out = avg.merge(cr, on=["year", "district_code", "district_name", "subject", "race"],
                    how="left")
    # For Composite, no benchmark → cr_rate is NaN (use avg_score only)
    out["cr_rate"] = out["cr_count"] / out["n_tested"]
    out["suppressed"] = out["avg_score"].isna()

    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return np.nan
    return float((values[mask] * weights[mask]).sum() / weights[mask].sum())


# ---------------------------------------------------------------------------
# State-level gaps
# ---------------------------------------------------------------------------

def compute_state_gaps(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Enrollment-weighted state mean avg_score by race × year × subject."""
    state = (
        panel[panel["year"].isin(ANALYSIS_YEARS)]
        .groupby(["year", "subject", "race"])
        .apply(
            lambda g: pd.Series({"avg_score": weighted_mean(g["avg_score"], g["n_tested"])}),
            include_groups=False,
        )
        .reset_index()
    )

    records = []
    for year in ANALYSIS_YEARS:
        for subj in PRIMARY_SUBJECTS:
            cell = (
                state[(state["year"] == year) & (state["subject"] == subj)]
                .set_index("race")["avg_score"]
            )
            if "White" not in cell or pd.isna(cell.get("White", np.nan)):
                continue
            for _ra, rb, pair_label, pair_desc in GAP_PAIRS:
                if rb not in cell or pd.isna(cell.get(rb, np.nan)):
                    continue
                records.append({
                    "year": year, "subject": subj,
                    "gap_pair": pair_label, "gap_desc": pair_desc,
                    "avg_score_white": cell["White"],
                    "avg_score_minority": cell[rb],
                    "gap": cell["White"] - cell[rb],
                })

    return state, pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Within-between decomposition
# ---------------------------------------------------------------------------

def decompose_gap(unit_df: pd.DataFrame, race_a: str, race_b: str) -> dict:
    a = (
        unit_df[unit_df["race"] == race_a]
        .set_index("district_code")[["avg_score", "n_tested"]]
        .dropna()
        .rename(columns={"avg_score": "p_a", "n_tested": "n_a"})
    )
    b = (
        unit_df[unit_df["race"] == race_b]
        .set_index("district_code")[["avg_score", "n_tested"]]
        .dropna()
        .rename(columns={"avg_score": "p_b", "n_tested": "n_b"})
    )
    both = a.join(b, how="inner")
    n_a, n_b = len(a), len(b)
    n_both = len(both)

    if both.empty or both["n_a"].sum() == 0 or both["n_b"].sum() == 0:
        return {"T": np.nan, "B": np.nan, "W": np.nan,
                "B_pct": np.nan, "W_pct": np.nan,
                "n_units_a": n_a, "n_units_b": n_b, "n_units_both": n_both}

    N_a = both["n_a"].sum()
    N_b = both["n_b"].sum()
    p_bar_a = (both["p_a"] * both["n_a"]).sum() / N_a
    p_bar_b = (both["p_b"] * both["n_b"]).sum() / N_b
    T = p_bar_a - p_bar_b

    p_d = (both["n_a"] * both["p_a"] + both["n_b"] * both["p_b"]) / (both["n_a"] + both["n_b"])
    B = (p_d * (both["n_a"] / N_a - both["n_b"] / N_b)).sum()
    W = T - B

    return {
        "T": T, "B": B, "W": W,
        "B_pct": 100 * B / T if T != 0 else np.nan,
        "W_pct": 100 * W / T if T != 0 else np.nan,
        "n_units_a": n_a, "n_units_b": n_b, "n_units_both": n_both,
    }


def run_decomposition(panel: pd.DataFrame) -> pd.DataFrame:
    records = []
    for year in ANALYSIS_YEARS:
        for subj in PRIMARY_SUBJECTS:
            cell = panel[(panel["year"] == year) & (panel["subject"] == subj)]
            if cell.empty:
                continue
            for ra, rb, pair_label, pair_desc in GAP_PAIRS:
                res = decompose_gap(cell, ra, rb)
                records.append({
                    "year": year, "subject": subj,
                    "gap_pair": pair_label, "gap_desc": pair_desc,
                    **res,
                })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# MMSD comparisons
# ---------------------------------------------------------------------------

def build_peer_name_map(panel: pd.DataFrame) -> dict[str, str]:
    """Map canonical peer labels to actual district names in the panel."""
    all_names = panel["district_name"].unique()
    mapping: dict[str, str] = {}
    for canonical, target in PEER_DISTRICTS.items():
        # Exact match first, then partial
        if target in all_names:
            mapping[canonical] = target
        else:
            matches = [n for n in all_names if target.lower() in n.lower()]
            if matches:
                mapping[canonical] = matches[0]
    return mapping


def mmsd_vs_peers(panel: pd.DataFrame) -> pd.DataFrame:
    peer_map = build_peer_name_map(panel)
    records = []

    for dist_label, dist_name in [(MMSD_NAME, MMSD_NAME)] + list(peer_map.items()):
        sub = panel[(panel["district_name"] == dist_name) & panel["year"].isin(ANALYSIS_YEARS)]
        if sub.empty:
            continue
        tier = "MMSD" if dist_label == MMSD_NAME else PEER_TIERS.get(dist_label, "Other")
        for (year, subject, race), grp in sub.groupby(["year", "subject", "race"]):
            if race not in PRIMARY_RACES:
                continue
            avg = grp["avg_score"].dropna()
            n   = grp["n_tested"].dropna()
            records.append({
                "district_label": dist_label if dist_label != MMSD_NAME else MMSD_NAME,
                "tier": tier,
                "year": year, "subject": subject, "race": race,
                "avg_score": avg.iloc[0] if not avg.empty else np.nan,
                "n_tested":  n.iloc[0]   if not n.empty   else np.nan,
            })

    return pd.DataFrame(records)


def mmsd_vs_nonmmsd_white(panel: pd.DataFrame) -> pd.DataFrame:
    """Compare MMSD Black/Hispanic avg ACT score to non-MMSD White avg score."""
    act = panel[panel["year"].isin(ANALYSIS_YEARS)].copy()

    mmsd_minority = (
        act[(act["district_name"] == MMSD_NAME) & act["race"].isin(["Black", "Hispanic"])]
        .groupby(["year", "subject", "race"])
        .apply(
            lambda g: pd.Series({"avg_score": weighted_mean(g["avg_score"], g["n_tested"])}),
            include_groups=False,
        )
        .reset_index()
    )
    mmsd_minority["group"] = "MMSD " + mmsd_minority["race"]

    nonmmsd_white = (
        act[(act["district_name"] != MMSD_NAME) & (act["race"] == "White")]
        .groupby(["year", "subject"])
        .apply(
            lambda g: pd.Series({"avg_score": weighted_mean(g["avg_score"], g["n_tested"])}),
            include_groups=False,
        )
        .reset_index()
    )
    nonmmsd_white["race"]  = "White"
    nonmmsd_white["group"] = "Non-MMSD White"

    return pd.concat([
        mmsd_minority[["year", "subject", "race", "group", "avg_score"]],
        nonmmsd_white[["year", "subject", "race", "group", "avg_score"]],
    ], ignore_index=True)


# ---------------------------------------------------------------------------
# Pipeline comparison with Forward Exam
# ---------------------------------------------------------------------------

def build_pipeline_gaps(act_gaps: pd.DataFrame, fwd_panel_path: Path) -> pd.DataFrame:
    """
    Assemble a 'pipeline' table comparing BW gaps at:
      - Forward Exam grades 3-8 (proficiency rate, pp)
      - ACT grade 11 (avg score gap, ACT points)
    Both in the overlapping years 2015-16 to 2022-23.
    Returns long DataFrame with columns: year, subject_era, gap_pair, T, metric.
    """
    fwd = pd.read_parquet(fwd_panel_path)
    PRIMARY_YEARS_FWD = ["2015-16", "2016-17", "2017-18", "2018-19", "2021-22", "2022-23"]

    def wm(vals, weights):
        m = vals.notna() & weights.notna() & (weights > 0)
        if not m.any():
            return np.nan
        return (vals[m] * weights[m]).sum() / weights[m].sum()

    # Forward Exam: state BW gap in proficiency rate (avg across grades 3-8)
    fwd_sub = fwd[fwd["year"].isin(PRIMARY_YEARS_FWD) & fwd["race"].isin(["White", "Black", "Hispanic"])]
    fwd_state = (
        fwd_sub.groupby(["year", "subject", "race"])
        .apply(lambda g: pd.Series({"pct": wm(g["pct_proficient"], g["n_tested"])}),
               include_groups=False)
        .reset_index()
    )

    fwd_records = []
    subj_map = {"ELA": "ELA (grades 3–8)", "Mathematics": "Math (grades 3–8)"}
    for year in PRIMARY_YEARS_FWD:
        for subj in ["ELA", "Mathematics"]:
            cell = fwd_state[(fwd_state["year"] == year) & (fwd_state["subject"] == subj)].set_index("race")["pct"]
            for ra, rb, pair, _ in GAP_PAIRS:
                if ra not in cell or rb not in cell:
                    continue
                fwd_records.append({
                    "year": year, "era": "Forward Exam (Gr 3–8)",
                    "subject_era": subj_map.get(subj, subj),
                    "gap_pair": pair,
                    "T": cell[ra] - cell[rb],
                    "metric": "Proficiency rate gap (pp)",
                })

    # ACT: state BW gap in avg score
    act_records = []
    act_subj_map = {
        "English":     "English (grade 11)",
        "Mathematics": "Math (grade 11)",
        "Composite":   "Composite (grade 11)",
    }
    for _, row in act_gaps.iterrows():
        act_records.append({
            "year": row["year"], "era": "ACT (Gr 11)",
            "subject_era": act_subj_map.get(row["subject"], row["subject"]),
            "gap_pair": row["gap_pair"],
            "T": row["gap"],
            "metric": "ACT score gap (points)",
        })

    return pd.concat(
        [pd.DataFrame(fwd_records), pd.DataFrame(act_records)],
        ignore_index=True,
    )


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def _save_fig(name: str) -> None:
    for ext in ("pdf", "png"):
        plt.savefig(OUT_FIGS / f"{name}.{ext}", dpi=FIG_DPI, bbox_inches="tight")
    plt.close()


def fig_act_gap_trends(gaps: pd.DataFrame) -> None:
    """fig05: BW and HW ACT score gaps by year, three panels (Composite, Math, English)."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=False)
    fig.suptitle(
        "Wisconsin ACT Racial Score Gaps by Year (Grade 11, 2015–16 to 2022–23)\n"
        "Enrollment-Weighted Statewide Mean; Excludes 2019–20 (no testing)",
        fontsize=11, fontweight="bold", y=1.01,
    )

    for ax, subj in zip(axes, PRIMARY_SUBJECTS):
        sub = gaps[gaps["subject"] == subj]
        for _ra, _rb, pair_label, pair_desc in GAP_PAIRS:
            pair_sub = sub[sub["gap_pair"] == pair_label].sort_values("year")
            if pair_sub.empty:
                continue
            ax.plot(
                pair_sub["year"], pair_sub["gap"],
                marker="o", linewidth=2.0,
                color=GAP_COLORS[pair_label],
                label=pair_desc,
            )
        ax.set_title(SUBJECT_LABEL[subj], fontsize=10, fontweight="bold")
        ax.set_xlabel("Year")
        ax.tick_params(axis="x", rotation=35)
        ax.legend(fontsize=8)
        ax.set_ylabel("White − Minority (ACT points)")

    fig.tight_layout()
    _save_fig("fig05_act_gap_trends")
    print("  Saved fig05_act_gap_trends")


def fig_act_decomposition(decomp: pd.DataFrame) -> None:
    """fig06: Stacked within/between bar for ACT Composite and Math/English."""
    subjs_to_show = ["Composite", "Mathematics", "English"]
    valid = decomp[decomp["T"].notna() & (decomp["T"] > 0)].copy()

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle(
        "ACT Within-Between Decomposition of Racial Score Gaps\n"
        "(District Level, 2015–16 to 2022–23)",
        fontsize=11, fontweight="bold",
    )

    between_color = "#4393c3"
    within_color  = "#d6604d"
    bar_width = 0.55

    for row_i, (_ra, _rb, pair_label, pair_desc) in enumerate(GAP_PAIRS):
        for col_i, subj in enumerate(subjs_to_show):
            ax = axes[row_i][col_i]
            sub = valid[(valid["gap_pair"] == pair_label) & (valid["subject"] == subj)].sort_values("year")
            if sub.empty:
                ax.set_visible(False)
                continue

            x = np.arange(len(sub))
            ax.bar(x, sub["W_pct"].values, bar_width, label="Within",  color=within_color,  alpha=0.85)
            ax.bar(x, sub["B_pct"].values, bar_width, bottom=sub["W_pct"].values,
                   label="Between", color=between_color, alpha=0.85)
            ax.axhline(50, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
            ax.set_xticks(x)
            ax.set_xticklabels(sub["year"].tolist(), rotation=35, ha="right", fontsize=8)
            ax.set_ylim(0, 108)
            ax.set_ylabel("Share of Total Gap (%)")
            ax.set_title(f"{pair_desc}\n{SUBJECT_LABEL[subj]}", fontsize=9)
            for xi, (_, row) in enumerate(sub.iterrows()):
                ax.text(xi, 104, f"{row['T']:.1f}", ha="center", fontsize=7, color="#333333")
            if row_i == 0 and col_i == 0:
                ax.legend(fontsize=8)

    fig.tight_layout()
    _save_fig("fig06_act_decomposition")
    print("  Saved fig06_act_decomposition")


def fig_act_mmsd_vs_peers(comp: pd.DataFrame) -> None:
    """fig07: MMSD Black/Hispanic ACT Composite and Math vs peer districts."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle(
        "ACT Scores: MMSD vs. Peer Districts (Grade 11)\n"
        "(Black and Hispanic Students, 2015–16 to 2022–23)",
        fontsize=11, fontweight="bold",
    )

    tier_styles = {
        "MMSD":          {"lw": 2.8, "ls": "-",  "zo": 10},
        "Tier 1":        {"lw": 1.5, "ls": "-",  "zo": 5},
        "Tier 2":        {"lw": 1.2, "ls": "--", "zo": 4},
        "Madison region":{"lw": 1.2, "ls": ":",  "zo": 4},
    }

    for row_i, race in enumerate(["Black", "Hispanic"]):
        for col_i, subj in enumerate(["Composite", "Mathematics"]):
            ax = axes[row_i][col_i]
            sub = comp[(comp["race"] == race) & (comp["subject"] == subj)]

            for dist_label in sorted(sub["district_label"].unique()):
                dsub = sub[sub["district_label"] == dist_label].sort_values("year")
                if dsub["avg_score"].notna().sum() < 2:
                    continue
                tier = dsub["tier"].iloc[0]
                st = tier_styles.get(tier, {"lw": 1.0, "ls": "-", "zo": 3})
                color = RACE_COLORS.get(race, "#888888") if tier == "MMSD" else None

                ax.plot(
                    dsub["year"], dsub["avg_score"],
                    linewidth=st["lw"], linestyle=st["ls"], zorder=st["zo"],
                    color=color,
                    alpha=1.0 if tier in ("MMSD", "Tier 1") else 0.55,
                    marker="o" if tier == "MMSD" else None,
                    markersize=4,
                    label=dist_label,
                )

            ax.set_title(f"{race} — {SUBJECT_LABEL[subj]}", fontsize=10)
            ax.tick_params(axis="x", rotation=35)
            ax.set_ylabel("Mean ACT Score (1–36)")
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, fontsize=7, ncol=2, loc="upper left")

    fig.tight_layout()
    _save_fig("fig07_act_mmsd_vs_peers")
    print("  Saved fig07_act_mmsd_vs_peers")


def fig_pipeline(pipeline: pd.DataFrame) -> None:
    """
    fig08: Educational pipeline figure.
    Two panels: BW gap and HW gap.
    X-axis: Forward Exam grades 3-8 (ELA, Math) → ACT grade 11 (English, Math, Composite).
    Y-axis: gap in native units (pp for Forward, ACT points for ACT).
    Shows average across primary years as bars with individual year dots.
    """
    # Compute mean across years for each subject_era × gap_pair
    mean_gaps = (
        pipeline.groupby(["subject_era", "gap_pair", "metric"])["T"]
        .agg(mean_T="mean", std_T="std")
        .reset_index()
    )

    ORDER = [
        "ELA (grades 3–8)",
        "Math (grades 3–8)",
        "English (grade 11)",
        "Math (grade 11)",
        "Composite (grade 11)",
    ]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(
        "Educational Pipeline: Racial Achievement Gaps at Grades 3–8 vs. Grade 11\n"
        "(Wisconsin, 2015–16 to 2022–23; Forward Exam proficiency pp / ACT score points)",
        fontsize=11, fontweight="bold", y=1.01,
    )

    pair_labels = {"BW": "Black–White Gap", "HW": "Hispanic–White Gap"}
    pair_colors = {"BW": "#762a83", "HW": "#f1a340"}

    for ax, pair in zip(axes, ["BW", "HW"]):
        sub_mean = mean_gaps[mean_gaps["gap_pair"] == pair]
        sub_all  = pipeline[pipeline["gap_pair"] == pair]

        # Get values in ORDER
        x_vals, y_means, y_std, x_labels, colors = [], [], [], [], []
        for i, subj_era in enumerate(ORDER):
            row = sub_mean[sub_mean["subject_era"] == subj_era]
            if row.empty:
                continue
            x_vals.append(i)
            y_means.append(row["mean_T"].values[0])
            y_std.append(row["std_T"].values[0] if not pd.isna(row["std_T"].values[0]) else 0)
            x_labels.append(subj_era)
            colors.append("#4d9de0" if "grades 3" in subj_era else "#e15554")

        ax.bar(range(len(x_vals)), y_means, color=colors, alpha=0.75, width=0.5)
        ax.errorbar(range(len(x_vals)), y_means, yerr=y_std, fmt="none",
                    color="black", capsize=4, linewidth=1)

        # Scatter individual years
        for xi, subj_era in enumerate(x_labels):
            yr_vals = sub_all[sub_all["subject_era"] == subj_era]["T"]
            ax.scatter([xi] * len(yr_vals), yr_vals, color="black", zorder=5,
                       s=15, alpha=0.6)

        # Dividing line between Forward and ACT
        fwd_count = sum(1 for s in x_labels if "grades 3" in s)
        ax.axvline(fwd_count - 0.5, color="#888888", linewidth=1.0, linestyle="--")
        ax.text(fwd_count / 2 - 0.5, max(y_means) * 1.02, "Forward\nExam",
                ha="center", fontsize=8, color="#555555")
        ax.text(fwd_count + (len(x_labels) - fwd_count) / 2 - 0.5,
                max(y_means) * 1.02, "ACT",
                ha="center", fontsize=8, color="#555555")

        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels, rotation=25, ha="right", fontsize=8)
        ax.set_title(pair_labels[pair], fontsize=11, fontweight="bold",
                     color=pair_colors[pair])
        ax.set_ylabel("Gap (pp or ACT points)")

    fig.tight_layout()
    _save_fig("fig08_act_pipeline")
    print("  Saved fig08_act_pipeline")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading ACT data …")
    raw = load_all_act(ANALYSIS_YEARS)
    print(f"  Raw rows: {len(raw):,}")

    panel = clean_act(raw)
    panel.to_parquet(OUT_DATA / "panel_act_district_race.parquet", index=False)
    print(f"  District × race panel: {len(panel):,} rows")
    print(f"  Districts: {panel['district_name'].nunique()}")
    print(f"  Suppression: {panel['suppressed'].mean()*100:.1f}%")
    print()

    # ---- State-level gaps -----------------------------------------------
    print("Computing state-level ACT gaps …")
    state_df, gaps_df = compute_state_gaps(panel)
    gaps_df.to_csv(OUT_TABLES / "act_state_gaps.csv", index=False)
    print()
    print("  BW Composite gaps:")
    bw_c = gaps_df[(gaps_df["gap_pair"] == "BW") & (gaps_df["subject"] == "Composite")]
    print(bw_c[["year", "avg_score_white", "avg_score_minority", "gap"]].round(2).to_string(index=False))
    print()

    # ---- Decomposition --------------------------------------------------
    print("Running within-between decomposition …")
    decomp = run_decomposition(panel)
    decomp.to_csv(OUT_TABLES / "act_decomposition.csv", index=False)
    bw_d = decomp[(decomp["gap_pair"] == "BW") & (decomp["subject"] == "Composite")]
    print("  BW Composite decomposition:")
    print(bw_d[["year", "T", "B_pct", "W_pct", "n_units_both"]].round(1).to_string(index=False))
    print()

    # ---- MMSD comparisons -----------------------------------------------
    print("Building MMSD vs peer district comparison …")
    peers_df = mmsd_vs_peers(panel)
    peers_df.to_csv(OUT_TABLES / "act_mmsd_peers.csv", index=False)
    print(f"  Records: {len(peers_df):,}")

    nonmmsd_df = mmsd_vs_nonmmsd_white(panel)
    nonmmsd_df.to_csv(OUT_TABLES / "act_mmsd_vs_nonmmsd_white.csv", index=False)
    print()

    # ---- Pipeline figure ------------------------------------------------
    print("Building pipeline comparison …")
    pipeline = build_pipeline_gaps(gaps_df, FWD_PANEL)
    pipeline.to_csv(OUT_TABLES / "act_pipeline_gaps.csv", index=False)
    print()

    # ---- Figures --------------------------------------------------------
    print("Generating figures …")
    fig_act_gap_trends(gaps_df)
    fig_act_decomposition(decomp)
    fig_act_mmsd_vs_peers(peers_df)
    fig_pipeline(pipeline)
    print()

    print("Done — ACT analysis complete.")
    print(f"  Tables → {OUT_TABLES}")
    print(f"  Figures → {OUT_FIGS}")


if __name__ == "__main__":
    main()
