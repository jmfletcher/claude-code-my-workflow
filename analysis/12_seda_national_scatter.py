"""
12_seda_national_scatter.py — National context: White vs. Black / White vs. Hispanic ELA means.

Uses SEDA 6.0 geographic-district pooled file (not DPI). Each point is one *geographic*
school district (SEDA's attendance-zone aggregation), not a single school. Public
school-pool files do not include race-specific means per school; district poolsub does.

Metric: cs_mn_lrn_rla_eb = empirical-Bayes ELA/reading mean in cohort-scale (CS) units
(national reference). Not comparable to Wisconsin Forward proficiency percentages.

Highlights Wisconsin Madison Metropolitan and Milwaukee districts when name-matched.

Outputs:
  output/figures/fig11_seda_national_district_scatter_bw_hw.{pdf,png}

Prerequisites:
  python3 analysis/11_download_seda.py

Run from repo root:
  python3 analysis/12_seda_national_scatter.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

ROOT = Path(__file__).resolve().parent.parent
SEDA_CSV = ROOT / "Data" / "raw" / "seda" / "seda_geodist_poolsub_cs_6.0.csv"
OUT_FIGS = ROOT / "output" / "figures"

OUT_FIGS.mkdir(parents=True, exist_ok=True)

COLOR_MMSD = "#e31a1c"
COLOR_MKE = "#2166ac"
COLOR_OTHER = "#737373"

FIG_DPI = 150
MIN_N = 30  # mirror DPI spirit; SEDA uses tot_asmts_rla

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


def load_race_elas() -> pd.DataFrame:
    if not SEDA_CSV.is_file():
        raise FileNotFoundError(
            f"Missing {SEDA_CSV}. Run: python3 analysis/11_download_seda.py"
        )
    df = pd.read_csv(SEDA_CSV, low_memory=False)
    base = df[(df["gap"] == 0) & (df["subcat"] == "race")].copy()

    w = base[base["subgroup"] == "wht"][
        ["sedalea", "sedaleaname", "stateabb", "cs_mn_lrn_rla_eb", "tot_asmts_rla"]
    ].rename(
        columns={
            "sedaleaname": "district_name",
            "stateabb": "state",
            "cs_mn_lrn_rla_eb": "ela_wht",
            "tot_asmts_rla": "n_wht",
        }
    )
    b = base[base["subgroup"] == "blk"][
        ["sedalea", "cs_mn_lrn_rla_eb", "tot_asmts_rla"]
    ].rename(
        columns={"cs_mn_lrn_rla_eb": "ela_blk", "tot_asmts_rla": "n_blk"}
    )
    h = base[base["subgroup"] == "hsp"][
        ["sedalea", "cs_mn_lrn_rla_eb", "tot_asmts_rla"]
    ].rename(
        columns={"cs_mn_lrn_rla_eb": "ela_hsp", "tot_asmts_rla": "n_hsp"}
    )

    m = w.merge(b, on="sedalea", how="inner").merge(h, on="sedalea", how="inner")
    m = m[
        (m["n_wht"] >= MIN_N)
        & (m["n_blk"] >= MIN_N)
        & (m["n_hsp"] >= MIN_N)
        & m["ela_wht"].notna()
        & m["ela_blk"].notna()
        & m["ela_hsp"].notna()
    ].copy()
    return m


def bucket(name: str, state: str) -> str:
    n = str(name)
    st = str(state)
    if st == "WI" and "Madison" in n and "Metropolitan" in n:
        return "MMSD (SEDA geo.)"
    if st == "WI" and "Milwaukee" in n:
        return "Milwaukee (SEDA geo.)"
    return "Other"


def pearson_block(sub: pd.DataFrame, ycol: str) -> dict[str, tuple[float, int]]:
    out: dict[str, tuple[float, int]] = {}
    masks = {
        "(a) Overall": pd.Series(True, index=sub.index),
        "(b) MMSD": sub["bucket"].str.startswith("MMSD"),
        "(c) Milwaukee": sub["bucket"].str.startswith("Milwaukee"),
        "(d) Other": sub["bucket"] == "Other",
    }
    for label, m in masks.items():
        s = sub.loc[m, ["ela_wht", ycol]].dropna()
        x = s["ela_wht"].to_numpy(float)
        y = s[ycol].to_numpy(float)
        n = len(x)
        if n < 2 or np.std(x) < 1e-12 or np.std(y) < 1e-12:
            out[label] = (float("nan"), n)
        else:
            out[label] = (float(pearsonr(x, y)[0]), n)
    return out


def main() -> None:
    print("=" * 65)
    print("12_seda_national_scatter.py — SEDA national district ELA race scatter")
    print("=" * 65)
    wide = load_race_elas()
    print(f"  Districts with White, Black, Hispanic ELA (n≥{MIN_N} each): {len(wide):,}")

    wide["bucket"] = [bucket(r.district_name, r.state) for _, r in wide.iterrows()]
    print("  WI Madison Metropolitan matches:", wide["bucket"].str.startswith("MMSD").sum())
    print("  WI Milwaukee matches:", wide["bucket"].str.startswith("Milwaukee").sum())

    sub_a = wide.copy()
    sub_b = wide.copy()
    corr_bw = pearson_block(sub_a, "ela_blk")
    corr_hw = pearson_block(sub_b, "ela_hsp")

    def _fmt_corrs(title: str, yl: str, d: dict[str, tuple[float, int]]) -> str:
        parts = []
        for k in ["(a) Overall", "(b) MMSD", "(c) Milwaukee", "(d) Other"]:
            r, n = d[k]
            parts.append(f"{k} r={'—' if np.isnan(r) else f'{r:.3f}'} (n={n:,})")
        return f"{title} (White vs. {yl}):\n" + "; ".join(parts[:2]) + "\n" + "; ".join(parts[2:])

    line_a = _fmt_corrs("Panel A", "Black", corr_bw)
    line_b = _fmt_corrs("Panel B", "Hispanic", corr_hw)
    print(line_a)
    print(line_b)

    lo = float(
        min(
            wide["ela_wht"].min(),
            wide["ela_blk"].min(),
            wide["ela_hsp"].min(),
        )
        - 0.08
    )
    hi = float(
        max(
            wide["ela_wht"].max(),
            wide["ela_blk"].max(),
            wide["ela_hsp"].max(),
        )
        + 0.08
    )

    def _scatter(ax: plt.Axes, ycol: str, ylabel: str, letter: str) -> None:
        sub = wide.dropna(subset=["ela_wht", ycol]).copy()
        ax.plot([lo, hi], [lo, hi], "--", color="#888888", linewidth=1, zorder=1)
        order = [
            ("Other", COLOR_OTHER, 2),
            ("Milwaukee (SEDA geo.)", COLOR_MKE, 3),
            ("MMSD (SEDA geo.)", COLOR_MMSD, 4),
        ]
        for bname, color, z in order:
            pts = sub[sub["bucket"] == bname]
            ax.scatter(
                pts["ela_wht"],
                pts[ycol],
                s=26,
                alpha=0.5,
                color=color,
                edgecolors="white",
                linewidth=0.3,
                zorder=z,
                label=f"{bname} (n={len(pts):,})",
            )
        ax.set_xlabel("White students: mean ELA/reading (cohort scale, EB)", fontsize=10)
        ax.set_ylabel(
            f"{ylabel} students: mean ELA/reading (cohort scale, EB)",
            fontsize=10,
        )
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
        ax.set_title(f"({letter}) Geographic district: White vs. {ylabel}", fontsize=11, fontweight="bold")
        ax.legend(fontsize=7.5, loc="lower right", framealpha=0.92)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6))
    _scatter(axes[0], "ela_blk", "Black", "A")
    _scatter(axes[1], "ela_hsp", "Hispanic", "B")

    fig.suptitle(
        "National Context (SEDA 6.0): White vs. Black and White vs. Hispanic ELA Means\n"
        "Geographic School Districts — Cohort Scale (Not Forward Exam Proficiency)",
        fontsize=11,
        fontweight="bold",
        y=1.02,
    )
    note = (
        "Note: Stanford Education Data Archive (SEDA) 6.0, geographic district file "
        f"(pooled grades/years). Each point is one district with ≥{MIN_N} tested students "
        "per group (tot_asmts_rla). Vertical/horizontal axes are empirical-Bayes ELA estimates "
        "in cohort-scale units (national reference), not percentage proficient. "
        "Dashed line = parity. MMSD/Milwaukee labels apply only to Wisconsin districts whose "
        "SEDA names contain “Madison Metropolitan” or “Milwaukee.” "
        "Cite: Reardon et al., SEDA 6.0, https://edopportunity.org/ ."
    )
    fig.text(0.5, -0.02, note, ha="center", fontsize=8, color="#555555")
    fig.text(0.5, -0.11, line_a, ha="center", fontsize=7.5, color="#555555")
    fig.text(0.5, -0.19, line_b, ha="center", fontsize=7.5, color="#555555")
    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(
            OUT_FIGS / f"fig11_seda_national_district_scatter_bw_hw.{ext}",
            dpi=FIG_DPI,
            bbox_inches="tight",
        )
    plt.close(fig)
    print("  Saved fig11_seda_national_district_scatter_bw_hw.pdf / .png")
    print("Done.")


if __name__ == "__main__":
    main()
