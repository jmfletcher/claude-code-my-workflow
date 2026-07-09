"""
10_econ_school_scatter.py — School-level Not Econ Disadv vs. Econ Disadv (ELA).

Parallel to the school-level White vs. Black scatter (09_school_scatter.py): horizontal
axis = higher-SES proxy (non-economically disadvantaged), vertical = economically
disadvantaged (DPI ``Economic Status`` groups).

Inputs:
  output/data/panel_school_econ.parquet  (from 02_load_and_clean.py)

Outputs:
  output/figures/fig_A10_econ_school_scatter.{pdf,png}

Run from repo root:
  python3 analysis/10_econ_school_scatter.py
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
PANEL_ECON = ROOT / "output" / "data" / "panel_school_econ.parquet"
OUT_FIGS = ROOT / "output" / "figures"

OUT_FIGS.mkdir(parents=True, exist_ok=True)

MMSD_NAME = "Madison Metropolitan"
MILWAUKEE_NAME = "Milwaukee"

NED = "Not Econ Disadv"
ED = "Econ Disadv"

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
    df = pd.read_parquet(PANEL_ECON)
    df = df[
        df["primary_analysis"]
        & (df["subject"] == "ELA")
        & ~df["suppressed"]
        & df["econ_status"].isin([NED, ED])
    ].copy()
    df["grade"] = df["grade"].astype(int)

    def _wmean(g: pd.DataFrame) -> float:
        v = g.dropna(subset=["pct_proficient", "n_tested"])
        if v.empty or v["n_tested"].sum() == 0:
            return np.nan
        return float(np.average(v["pct_proficient"], weights=v["n_tested"]))

    # Group by codes only: school/district names change across years, and grouping
    # on names splits a renamed school into two points. Attach most recent name.
    df = df.sort_values("year", kind="stable")
    names = (
        df.groupby(["district_code", "school_code"], sort=False)
        [["district_name", "school_name"]]
        .last()
        .reset_index()
    )
    out = (
        df.groupby(["district_code", "school_code", "econ_status"], sort=False)
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


def pearson_subs(sub: pd.DataFrame, xcol: str, ycol: str) -> dict[str, tuple[float, int]]:
    out: dict[str, tuple[float, int]] = {}
    masks = {
        "(a) Overall": pd.Series(True, index=sub.index),
        "(b) MMSD": sub["bucket"] == "MMSD",
        "(c) Milwaukee": sub["bucket"] == "Milwaukee",
        "(d) Other": sub["bucket"] == "Other",
    }
    for label, m in masks.items():
        s = sub.loc[m, [xcol, ycol]].dropna()
        x = s[xcol].to_numpy(dtype=float)
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


def _format_corr_lines(corrs: dict[str, tuple[float, int]]) -> str:
    parts = []
    for key in ["(a) Overall", "(b) MMSD", "(c) Milwaukee", "(d) Other"]:
        r, n = corrs[key]
        if np.isnan(r):
            parts.append(f"{key} r=— (n={n:,})")
        else:
            parts.append(f"{key} r={r:.3f} (n={n:,})")
    row1 = "; ".join(parts[:2])
    row2 = "; ".join(parts[2:])
    return f"Pearson correlations (non-ED vs. ED proficiency):\n{row1}\n{row2}"


def fig_econ_scatter(pooled: pd.DataFrame) -> None:
    wide = pooled.pivot_table(
        index=["district_code", "school_code"],
        columns="econ_status",
        values="pct_proficient",
    ).reset_index()
    wide.columns.name = None
    wide = wide.merge(
        pooled[["district_code", "school_code", "district_name", "school_name"]]
        .drop_duplicates(["district_code", "school_code"]),
        on=["district_code", "school_code"], how="left",
    )

    wide = wide.dropna(subset=[NED, ED])
    wide["bucket"] = wide["district_name"].map(district_bucket)

    corrs = pearson_subs(wide, NED, ED)
    corr_text = _format_corr_lines(corrs)
    for line in corr_text.split("\n"):
        print(f"  {line}")

    lim = float(max(wide[NED].max(), wide[ED].max()) + 5)

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.plot([0, lim], [0, lim], "--", color="#888888", linewidth=1, zorder=1)

    for bucket, color, z in [
        ("Other", COLOR_OTHER, 2),
        ("Milwaukee", COLOR_MKE, 3),
        ("MMSD", COLOR_MMSD, 4),
    ]:
        pts = wide[wide["bucket"] == bucket]
        ax.scatter(
            pts[NED],
            pts[ED],
            s=28,
            alpha=0.55,
            color=color,
            edgecolors="white",
            linewidth=0.35,
            zorder=z,
            label=f"{bucket} (n={len(pts):,})",
        )

    ax.set_xlabel("Not economically disadvantaged — proficiency (ELA, %, pooled)", fontsize=10)
    ax.set_ylabel("Economically disadvantaged — proficiency (ELA, %, pooled)", fontsize=10)
    ax.set_xlim(left=0, right=lim)
    ax.set_ylim(bottom=0, top=lim)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_title(
        "School-Level ELA Proficiency: Non-ED vs. ED (DPI Economic Status)\n"
        "Wisconsin Public Schools — Forward Exam Primary Years (2015–2023)",
        fontsize=11,
        fontweight="bold",
    )
    ax.legend(fontsize=8, loc="lower right", framealpha=0.92)

    note = (
        "Note: Each point is one school × district. Proficiency is enrollment-weighted across "
        "grades 3–8 and primary years (excludes 2019–20 and 2020–21). "
        "A school appears only if both economic-status proficiency rates are non-suppressed. "
        "DPI Unknown economic-status cells are excluded. "
        "Dashed line = parity (no ED–non-ED gap at the school level). "
        "This cut is not nested with race; it describes poverty status, not racial composition."
    )
    fig.text(0.5, -0.02, note, ha="center", fontsize=8, color="#555555")
    fig.text(0.5, -0.14, corr_text, ha="center", fontsize=7.5, color="#555555")

    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT_FIGS / f"fig_A10_econ_school_scatter.{ext}", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  Saved fig_A10_econ_school_scatter.pdf / .png")


def main() -> None:
    print("=" * 65)
    print("10_econ_school_scatter.py — school-level ED vs non-ED")
    print("=" * 65)
    pooled = load_school_ela_pooled()
    print(f"  Pooled school×status rows: {len(pooled):,}")
    fig_econ_scatter(pooled)
    print("Done.")


if __name__ == "__main__":
    main()
