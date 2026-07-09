"""
09_school_scatter.py — School-level White vs. Black / White vs. Hispanic ELA scatter.

Panel A: X = White proficiency, Y = Black proficiency (school level).
Panel B: X = White proficiency, Y = Hispanic proficiency.

Sample: Wisconsin public schools with non-suppressed proficiency for both races in each
panel (DPI suppression threshold). Rates pooled across primary Forward Exam years and
grades 3–8, enrollment-weighted within school (ELA only; matches district scatter logic).

Colors: Madison Metropolitan, Milwaukee, all other districts.

Outputs:
  output/figures/fig09_school_scatter_bw_hw.{pdf,png}

Run from repo root:
  python3 analysis/09_school_scatter.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

ROOT = Path(__file__).resolve().parent.parent
PANEL_SCHOOL = ROOT / "output" / "data" / "panel_school_race.parquet"
OUT_FIGS = ROOT / "output" / "figures"

OUT_FIGS.mkdir(parents=True, exist_ok=True)

MMSD_NAME = "Madison Metropolitan"
MILWAUKEE_NAME = "Milwaukee"

EXCLUDE_RACES = {"Unknown", "Unknown/Suppressed"}

# Distinct colors for districts (not race palette — avoids clash with parity interpretation)
COLOR_MMSD = "#e31a1c"
COLOR_MKE = "#2166ac"
COLOR_OTHER = "#737373"

FIG_DPI = 150
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.grid": True,
        "grid.color": "#dddddd",
        "grid.linewidth": 0.6,
        "axes.grid.axis": "both",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def load_school_ela_pooled() -> pd.DataFrame:
    df = pd.read_parquet(PANEL_SCHOOL)
    df = df[
        df["primary_analysis"]
        & ~df["race"].isin(EXCLUDE_RACES)
        & (df["subject"] == "ELA")
        & ~df["suppressed"]
        & df["race"].isin(["White", "Black", "Hispanic"])
    ].copy()
    df["grade"] = df["grade"].astype(int)

    def _wmean(g: pd.DataFrame) -> float:
        v = g.dropna(subset=["pct_proficient", "n_tested"])
        if v.empty or v["n_tested"].sum() == 0:
            return np.nan
        return float(np.average(v["pct_proficient"], weights=v["n_tested"]))

    # Group by codes only: school/district NAMES change across years (e.g. MMSD's
    # Falk -> Milele Chikasa Anana), and grouping on names splits a renamed school
    # into two points. Attach the most recent name for labeling.
    df = df.sort_values("year", kind="stable")
    names = (
        df.groupby(["district_code", "school_code"], sort=False)
        [["district_name", "school_name"]]
        .last()
        .reset_index()
    )
    out = (
        df.groupby(["district_code", "school_code", "race"], sort=False)
        .apply(_wmean, include_groups=False)
        .rename("pct_proficient")
        .reset_index()
    )
    return out.merge(names, on=["district_code", "school_code"], how="left")


def district_bucket(name: str) -> str:
    if name == MMSD_NAME:
        return "MMSD"
    if name == MILWAUKEE_NAME:
        return "Milwaukee"
    return "Other"


def pearson_white_minority(sub: pd.DataFrame, ycol: str) -> dict[str, tuple[float, int]]:
    """
    Pearson r between White and ycol for (a) overall, (b) MMSD, (c) Milwaukee, (d) other.
    Returns mapping label -> (r, n); r is NaN if n < 2 or zero variance.
    """
    out: dict[str, tuple[float, int]] = {}
    masks = {
        "(a) Overall": pd.Series(True, index=sub.index),
        "(b) MMSD": sub["bucket"] == "MMSD",
        "(c) Milwaukee": sub["bucket"] == "Milwaukee",
        "(d) Other": sub["bucket"] == "Other",
    }
    for label, m in masks.items():
        s = sub.loc[m, ["White", ycol]].dropna()
        x = s["White"].to_numpy(dtype=float)
        y = s[ycol].to_numpy(dtype=float)
        n = int(len(x))
        if n < 2:
            out[label] = (float("nan"), n)
            continue
        if np.std(x) < 1e-12 or np.std(y) < 1e-12:
            out[label] = (float("nan"), n)
            continue
        r, _ = pearsonr(x, y)
        out[label] = (float(r), n)
    return out


def _format_corr_lines(panel: str, yname: str, corrs: dict[str, tuple[float, int]]) -> str:
    parts = []
    for key in ["(a) Overall", "(b) MMSD", "(c) Milwaukee", "(d) Other"]:
        r, n = corrs[key]
        if np.isnan(r):
            parts.append(f"{key} r=— (n={n:,})")
        else:
            parts.append(f"{key} r={r:.3f} (n={n:,})")
    head = f"{panel} (White vs. {yname}):"
    row1 = "; ".join(parts[:2])
    row2 = "; ".join(parts[2:])
    return f"{head}\n{row1}\n{row2}"


def fig_school_scatter(pooled: pd.DataFrame) -> None:
    wide = pooled.pivot_table(
        index=["district_code", "school_code"],
        columns="race",
        values="pct_proficient",
    ).reset_index()
    wide.columns.name = None
    wide = wide.merge(
        pooled[["district_code", "school_code", "district_name", "school_name"]]
        .drop_duplicates(["district_code", "school_code"]),
        on=["district_code", "school_code"], how="left",
    )

    wide["bucket"] = wide["district_name"].map(district_bucket)

    sub_a = wide.dropna(subset=["White", "Black"]).copy()
    sub_b = wide.dropna(subset=["White", "Hispanic"]).copy()
    corr_bw = pearson_white_minority(sub_a, "Black")
    corr_hw = pearson_white_minority(sub_b, "Hispanic")

    line_a = _format_corr_lines("Panel A", "Black", corr_bw)
    line_b = _format_corr_lines("Panel B", "Hispanic", corr_hw)
    for line in (line_a, line_b):
        print(f"  {line}")

    lim = float(
        max(
            sub_a["White"].max(),
            sub_a["Black"].max(),
            sub_b["White"].max(),
            sub_b["Hispanic"].max(),
        )
        + 5
    )

    def _scatter(ax: plt.Axes, ycol: str, ylabel: str, letter: str) -> None:
        sub = wide.dropna(subset=["White", ycol]).copy()
        ax.plot([0, lim], [0, lim], "--", color="#888888", linewidth=1, zorder=1)

        for bucket, color, z in [
            ("Other", COLOR_OTHER, 2),
            ("Milwaukee", COLOR_MKE, 3),
            ("MMSD", COLOR_MMSD, 4),
        ]:
            pts = sub[sub["bucket"] == bucket]
            ax.scatter(
                pts["White"],
                pts[ycol],
                s=28,
                alpha=0.55,
                color=color,
                edgecolors="white",
                linewidth=0.35,
                zorder=z,
                label=f"{bucket} (n={len(pts):,})",
            )

        ax.set_xlabel("White student proficiency (ELA, %, pooled)", fontsize=10)
        ax.set_ylabel(f"{ylabel} student proficiency (ELA, %, pooled)", fontsize=10)
        ax.set_xlim(left=0, right=lim)
        ax.set_ylim(bottom=0, top=lim)
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.set_title(f"({letter}) School-level: White vs. {ylabel}", fontsize=11, fontweight="bold")
        ax.legend(fontsize=8, loc="lower right", framealpha=0.92)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6), sharey=False)
    _scatter(axes[0], "Black", "Black", "A")
    _scatter(axes[1], "Hispanic", "Hispanic", "B")

    fig.suptitle(
        "School-Level ELA Proficiency: White vs. Black and White vs. Hispanic\n"
        "Wisconsin Public Schools — Forward Exam Primary Years (2015–2023)",
        fontsize=11,
        fontweight="bold",
        y=1.02,
    )
    note_base = (
        "Note: Each point is one school × district. Proficiency is enrollment-weighted across "
        "grades 3–8 and primary years (excludes 2019–20 and 2020–21). "
        "A school appears in a panel only if both proficiency rates are non-suppressed (DPI n<10 rule). "
        "Dashed line = parity (no racial gap at the school level). "
        "Correlations are Pearson $r$ between horizontal (White) and vertical (Black or Hispanic) axes."
    )
    fig.text(
        0.5,
        -0.02,
        note_base,
        ha="center",
        fontsize=8,
        color="#555555",
    )
    fig.text(
        0.5,
        -0.12,
        line_a,
        ha="center",
        fontsize=7.5,
        color="#555555",
    )
    fig.text(
        0.5,
        -0.20,
        line_b,
        ha="center",
        fontsize=7.5,
        color="#555555",
    )
    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT_FIGS / f"fig09_school_scatter_bw_hw.{ext}", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  Saved fig09_school_scatter_bw_hw.pdf / .png")


def main() -> None:
    print("=" * 65)
    print("09_school_scatter.py — school-level race scatter")
    print("=" * 65)
    pooled = load_school_ela_pooled()
    print(f"  Pooled school×race rows: {len(pooled):,}")
    fig_school_scatter(pooled)
    print("Done.")


if __name__ == "__main__":
    main()
