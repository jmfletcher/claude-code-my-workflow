"""
16_place_correlation_dotplot.py — Dot plot of school-level correlations by place.

One row per place (statewide samples and named districts from the cross-state
analysis). Red dot = White-Black Pearson r, blue dot = White-Hispanic r, both
computed across schools within the place (from 15_multistate_school_scatter.py).
Rows ordered by the White-Black correlation. Only estimates based on at least
MIN_SCHOOLS schools are shown (small college-town districts mostly drop out).

Inputs:
  output/tables/multistate_school_correlations.csv

Outputs:
  output/figures/fig13_place_correlation_dotplot.{pdf,png}

Run from repo root:
  python3 analysis/16_place_correlation_dotplot.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CORR_CSV = ROOT / "output" / "tables" / "multistate_school_correlations.csv"
OUT_FIGS = ROOT / "output" / "figures"
OUT_FIGS.mkdir(parents=True, exist_ok=True)

MIN_SCHOOLS = 16  # matches the report-wide reporting threshold (MIN_N_CORR in script 15)

COLOR_BW = "#e31a1c"  # White-Black
COLOR_HW = "#2166ac"  # White-Hispanic

FIG_DPI = 150
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

STATE_NAMES = {
    "WI": "Wisconsin", "CA": "California", "TX": "Texas", "IL": "Illinois",
    "NY": "New York", "OH": "Ohio", "GA": "Georgia", "NC": "North Carolina",
    "NJ": "New Jersey",
}


def place_label(row: pd.Series) -> str | None:
    """Display label per place; None to drop the subsample."""
    sub = row["subsample"]
    if sub == "Overall":
        return f"{STATE_NAMES[row['state']]} (statewide)"
    if sub == "Other":
        return None  # residual category, not a 'place'
    return f"{sub} ({row['state']})"


def main() -> None:
    print("=" * 65)
    print("16_place_correlation_dotplot.py — correlations by place")
    print("=" * 65)

    df = pd.read_csv(CORR_CSV)
    df["place"] = df.apply(place_label, axis=1)
    df = df.dropna(subset=["place"])

    wide = df.pivot_table(index="place", columns="panel",
                          values=["pearson_r", "n_schools"], aggfunc="first")
    r_bw = wide[("pearson_r", "White vs. Black")]
    r_hw = wide[("pearson_r", "White vs. Hispanic")]
    n_bw = wide[("n_schools", "White vs. Black")]
    n_hw = wide[("n_schools", "White vs. Hispanic")]

    out = pd.DataFrame({"r_bw": r_bw, "r_hw": r_hw, "n_bw": n_bw, "n_hw": n_hw})
    out.loc[out["n_bw"] < MIN_SCHOOLS, "r_bw"] = np.nan
    out.loc[out["n_hw"] < MIN_SCHOOLS, "r_hw"] = np.nan
    dropped = out[out["r_bw"].isna() & out["r_hw"].isna()].index.tolist()
    out = out.dropna(subset=["r_bw", "r_hw"], how="all")

    # order by White-Black r (places without a reliable B-W estimate sort by H-W)
    out = out.sort_values(["r_bw", "r_hw"]).reset_index()

    fig, ax = plt.subplots(figsize=(8.5, 0.42 * len(out) + 2.2))
    y = np.arange(len(out))

    ax.axvline(0, color="#bbbbbb", linewidth=0.8, zorder=1)
    for yi in y:
        ax.axhline(yi, color="#eeeeee", linewidth=0.6, zorder=0)

    ax.scatter(out["r_bw"], y, s=70, color=COLOR_BW, zorder=3,
               edgecolors="white", linewidth=0.6, label="White–Black")
    ax.scatter(out["r_hw"], y, s=70, color=COLOR_HW, zorder=3,
               edgecolors="white", linewidth=0.6, label="White–Hispanic")

    # numeric labels next to each dot
    for yi, row in zip(y, out.itertuples()):
        if not np.isnan(row.r_bw):
            ax.annotate(f"{row.r_bw:.2f}", (row.r_bw, yi), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=7, color=COLOR_BW)
        if not np.isnan(row.r_hw):
            ax.annotate(f"{row.r_hw:.2f}", (row.r_hw, yi), textcoords="offset points",
                        xytext=(0, -14), ha="center", fontsize=7, color=COLOR_HW)

    def _ylab(row) -> str:
        ns = []
        if not np.isnan(row.r_bw):
            ns.append(f"{int(row.n_bw):,}")
        if not np.isnan(row.r_hw):
            ns.append(f"{int(row.n_hw):,}")
        return f"{row.place}  (n={'/'.join(ns)})"

    ax.set_yticks(y)
    ax.set_yticklabels([_ylab(r) for r in out.itertuples()], fontsize=9)
    bold_places = {"Madison (MMSD) (WI)", "Wisconsin (statewide)"}
    for tick, row in zip(ax.get_yticklabels(), out.itertuples()):
        if row.place in bold_places:
            tick.set_fontweight("bold")

    ax.set_xlim(-0.35, 1.0)
    ax.set_xlabel("Pearson correlation between White and minority school-level ELA proficiency")
    ax.set_title(
        "School-Level White–Black and White–Hispanic Proficiency Correlations by Place\n"
        f"Statewide samples and named districts with at least {MIN_SCHOOLS} schools",
        fontsize=11, fontweight="bold",
    )
    ax.legend(loc="upper left", fontsize=9, framealpha=0.92)

    dropped_note = ", ".join(sorted(dropped)) if dropped else "none"
    note = (
        f"Note: Each row is a place; dots are Pearson correlations across schools within the place "
        f"(ELA, grades 3–8, pooled recent years; see cross-state report for years and tests by state). "
        f"Rows ordered by the White–Black correlation. Estimates based on fewer than {MIN_SCHOOLS} "
        f"schools are omitted; the only college-town districts that qualify are Madison and "
        f"Athens–Clarke County (omitted entirely: {dropped_note}). Correlations are within-state "
        f"objects; proficiency levels are not comparable across states."
    )
    fig.text(0.02, -0.01, note, ha="left", va="top", fontsize=7.5,
             color="#555555", wrap=True)

    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT_FIGS / f"fig13_place_correlation_dotplot.{ext}",
                    dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  {len(out)} places shown; dropped (all estimates n<{MIN_SCHOOLS}): {dropped_note}")
    print("  Saved fig13_place_correlation_dotplot.pdf / .png")


if __name__ == "__main__":
    main()
