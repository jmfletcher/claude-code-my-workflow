"""
15_multistate_school_scatter.py — Figure 12 replicated for other states.

For each state: Panel A = school-level White vs. Black proficiency, Panel B =
White vs. Hispanic (ELA, pooled over available recent years and grades 3-8).
Colors: largest urban district (Milwaukee analog), college-town district
(MMSD analog), all other schools. Pearson r by subsample in figure notes.

Wisconsin is included from the existing Forward panel (2015-16 to 2022-23
primary years) for apples-to-apples presentation.

IMPORTANT: proficiency levels are NOT comparable across states (different
tests and cut scores). The comparable objects are the within-state scatter
shape and correlations.

Outputs:
  output/figures/fig12_{st}_school_scatter.{pdf,png}   (one per state)
  output/tables/multistate_school_correlations.csv

Run from repo root:
  python3 analysis/15_multistate_school_scatter.py
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
PANEL_MULTI = ROOT / "output" / "data" / "panel_school_race_multistate.parquet"
PANEL_WI = ROOT / "output" / "data" / "panel_school_race.parquet"
OUT_FIGS = ROOT / "output" / "figures"
OUT_TABLES = ROOT / "output" / "tables"
OUT_FIGS.mkdir(parents=True, exist_ok=True)
OUT_TABLES.mkdir(parents=True, exist_ok=True)

COLOR_COLLEGE = "#e31a1c"   # MMSD analog (red)
COLOR_URBAN = "#2166ac"     # Milwaukee analog (blue)
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


def _match(df: pd.DataFrame, how: str, val: str) -> pd.Series:
    if how == "name":
        return df["district_name"].astype(str) == val
    if how == "name_contains":
        return df["district_name"].astype(str).str.contains(val, case=False, na=False)
    if how == "name_startswith":
        return df["district_name"].astype(str).str.startswith(val)
    if how == "district_id":
        return df["district_id"].astype(str) == val
    raise ValueError(how)


# Per-state config: display name, test label, urban/college anchors, years note.
STATE_CONFIG: dict[str, dict] = {
    "WI": {
        "name": "Wisconsin", "test": "Forward Exam",
        "years_note": "2015-16 to 2022-23 primary years",
        "urban": ("name", "Milwaukee", "Milwaukee"),
        "college": ("name", "Madison Metropolitan", "Madison (MMSD)"),
    },
    "CA": {
        "name": "California", "test": "CAASPP Smarter Balanced (Standard Met+)",
        "years_note": "2022-23 to 2024-25",
        "urban": ("name", "Los Angeles Unified", "Los Angeles"),
        "college": ("name", "Berkeley Unified", "Berkeley"),
    },
    "TX": {
        "name": "Texas", "test": "STAAR (Meets Grade Level+)",
        "years_note": "2022-23 and 2023-24",
        "urban": ("name", "HOUSTON ISD", "Houston"),
        "college": ("name", "COLLEGE STATION ISD", "College Station"),
    },
    "IL": {
        "name": "Illinois", "test": "IAR (Proficient, Levels 4-5)",
        "years_note": "2023-24 and 2024-25",
        "urban": ("name", "Chicago Public Schools District 299", "Chicago"),
        "college": ("name", "Evanston CCSD 65", "Evanston"),
    },
    "NY": {
        "name": "New York", "test": "NYS 3-8 Tests (Levels 3-4)",
        "years_note": "2022-23 to 2024-25",
        "urban": ("name_startswith", "NYC GEOG DIST", "New York City"),
        "college": ("name", "ITHACA CITY SD", "Ithaca"),
    },
    "OH": {
        "name": "Ohio", "test": "Ohio State Tests (Proficient+)",
        "years_note": "2022-23 to 2024-25",
        "urban": ("name_contains", "Columbus City", "Columbus"),
        "college": ("name_contains", "Athens City", "Athens"),
    },
    "GA": {
        "name": "Georgia", "test": "Milestones EOG (Proficient+Distinguished)",
        "years_note": "2022-23 to 2024-25",
        "urban": ("name", "Atlanta Public Schools", "Atlanta"),
        "college": ("name", "Clarke County", "Athens (Clarke Co.)"),
    },
    "NC": {
        "name": "North Carolina", "test": "NC EOG (Grade Level Proficient)",
        "years_note": "2022-23 to 2024-25",
        "urban": ("district_id", "600", "Charlotte-Mecklenburg"),
        "college": ("district_id", "681", "Chapel Hill-Carrboro"),
    },
    "NJ": {
        "name": "New Jersey", "test": "NJSLA (Met+Exceeded)",
        "years_note": "2022-23 to 2024-25",
        "urban": ("name", "Newark Public School District", "Newark"),
        "college": ("name", "Princeton Public School District", "Princeton"),
    },
}


def load_wi() -> pd.DataFrame:
    """WI Forward panel -> same long schema as the multistate panel (ELA rows)."""
    df = pd.read_parquet(PANEL_WI)
    df = df[
        df["primary_analysis"]
        & (df["subject"] == "ELA")
        & ~df["suppressed"]
        & df["race"].isin(["White", "Black", "Hispanic"])
    ].copy()
    return pd.DataFrame({
        "state": "WI",
        "district_id": df["district_code"].astype(str),
        "district_name": df["district_name"],
        "school_id": df["district_code"].astype(str) + "-" + df["school_code"].astype(str),
        "school_name": df["school_name"],
        "race": df["race"],
        "n_tested": df["n_tested"],
        "pct_proficient": df["pct_proficient"],
    })


def pool_schools(df: pd.DataFrame) -> pd.DataFrame:
    """School × race pooled ELA rate: n-weighted where counts exist, else simple mean.

    Group by school_id only (IDs are unique statewide in every state's coding
    system): school and district *names* change across years (renames, district
    reorganizations), and grouping on names would split those schools into
    multiple points. Names attached from the most recent year.
    """
    df = df.dropna(subset=["pct_proficient"])
    if "year" in df.columns:
        df = df.sort_values("year", kind="stable")
    names = (
        df.groupby("school_id", sort=False, dropna=False)
        [["district_id", "district_name", "school_name"]]
        .last()
        .reset_index()
    )

    def _agg(g: pd.DataFrame) -> float:
        w = g.dropna(subset=["n_tested"])
        if len(w) and w["n_tested"].sum() > 0:
            return float(np.average(w["pct_proficient"], weights=w["n_tested"]))
        return float(g["pct_proficient"].mean())

    pooled = (
        df.groupby(["school_id", "race"], sort=False, dropna=False)
        .apply(_agg, include_groups=False)
        .rename("pct_proficient")
        .reset_index()
    )
    return pooled.merge(names, on="school_id", how="left")


# Reporting threshold: correlations from subsamples with fewer than 16 schools
# are too noisy to report (SE of r near 0 is ~1/sqrt(n-3) ≈ 0.28 at n=15).
MIN_N_CORR = 16


def pearson_subs(sub: pd.DataFrame, ycol: str, masks: dict[str, pd.Series]
                 ) -> dict[str, tuple[float, int]]:
    out: dict[str, tuple[float, int]] = {}
    for label, m in masks.items():
        s = sub.loc[m, ["White", ycol]].dropna()
        x, y = s["White"].to_numpy(float), s[ycol].to_numpy(float)
        n = len(x)
        if n < MIN_N_CORR or np.std(x) < 1e-12 or np.std(y) < 1e-12:
            out[label] = (float("nan"), n)
        else:
            out[label] = (float(pearsonr(x, y)[0]), n)
    return out


def _format_corr_lines(panel: str, yname: str, corrs: dict[str, tuple[float, int]]) -> str:
    parts = []
    for key, (r, n) in corrs.items():
        r_str = "—" if np.isnan(r) else f"{r:.3f}"
        parts.append(f"{key} r={r_str} (n={n:,})")
    head = f"{panel} (White vs. {yname}):"
    row1 = "; ".join(parts[:2])
    row2 = "; ".join(parts[2:])
    return f"{head}\n{row1}\n{row2}"


def fig_state_scatter(st: str, pooled: pd.DataFrame, results: list[dict]) -> None:
    cfg = STATE_CONFIG[st]
    # pivot on school_id alone: pivoting on name columns drops schools whose
    # district/school name is missing in the source files (e.g. some NY rows)
    wide = pooled.pivot_table(
        index="school_id", columns="race", values="pct_proficient"
    ).reset_index()
    wide.columns.name = None
    wide = wide.merge(
        pooled[["school_id", "district_id", "district_name", "school_name"]]
        .drop_duplicates("school_id"),
        on="school_id", how="left",
    )
    for race in ["White", "Black", "Hispanic"]:
        if race not in wide.columns:
            wide[race] = np.nan

    u_how, u_val, u_label = cfg["urban"]
    c_how, c_val, c_label = cfg["college"]
    is_urban = _match(wide, u_how, u_val)
    is_college = _match(wide, c_how, c_val)
    wide["bucket"] = np.select([is_college, is_urban], ["college", "urban"], "other")

    sub_a = wide.dropna(subset=["White", "Black"]).copy()
    sub_b = wide.dropna(subset=["White", "Hispanic"]).copy()
    if len(sub_a) < 10 and len(sub_b) < 10:
        print(f"  [{st}] too few overlapping schools; skipping figure")
        return

    def masks_for(sub: pd.DataFrame) -> dict[str, pd.Series]:
        return {
            "(a) Overall": pd.Series(True, index=sub.index),
            f"(b) {c_label}": sub["bucket"] == "college",
            f"(c) {u_label}": sub["bucket"] == "urban",
            "(d) Other": sub["bucket"] == "other",
        }

    corr_bw = pearson_subs(sub_a, "Black", masks_for(sub_a))
    corr_hw = pearson_subs(sub_b, "Hispanic", masks_for(sub_b))
    for panel, ycol, corrs in [("A", "Black", corr_bw), ("B", "Hispanic", corr_hw)]:
        for label, (r, n) in corrs.items():
            results.append({
                "state": st, "panel": f"White vs. {ycol}",
                "subsample": label[4:], "pearson_r": r, "n_schools": n,
            })

    line_a = _format_corr_lines("Panel A", "Black", corr_bw)
    line_b = _format_corr_lines("Panel B", "Hispanic", corr_hw)

    vals = pd.concat([sub_a[["White", "Black"]].melt()["value"],
                      sub_b[["White", "Hispanic"]].melt()["value"]])
    lim = float(min(105, vals.max() + 5))

    def _scatter(ax: plt.Axes, sub: pd.DataFrame, ycol: str, letter: str) -> None:
        ax.plot([0, lim], [0, lim], "--", color="#888888", linewidth=1, zorder=1)
        for bucket, color, z, label in [
            ("other", COLOR_OTHER, 2, "Other"),
            ("urban", COLOR_URBAN, 3, u_label),
            ("college", COLOR_COLLEGE, 4, c_label),
        ]:
            pts = sub[sub["bucket"] == bucket]
            ax.scatter(pts["White"], pts[ycol], s=28, alpha=0.55, color=color,
                       edgecolors="white", linewidth=0.35, zorder=z,
                       label=f"{label} (n={len(pts):,})")
        ax.set_xlabel("White student proficiency (ELA, %, pooled)", fontsize=10)
        ax.set_ylabel(f"{ycol} student proficiency (ELA, %, pooled)", fontsize=10)
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.set_title(f"({letter}) School-level: White vs. {ycol}",
                     fontsize=11, fontweight="bold")
        ax.legend(fontsize=8, loc="lower right", framealpha=0.92)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6), sharey=False)
    _scatter(axes[0], sub_a, "Black", "A")
    _scatter(axes[1], sub_b, "Hispanic", "B")

    fig.suptitle(
        f"School-Level ELA Proficiency: White vs. Black and White vs. Hispanic\n"
        f"{cfg['name']} — {cfg['test']}, {cfg['years_note']}",
        fontsize=11, fontweight="bold", y=1.02,
    )
    note_base = (
        "Note: Each point is one school. Proficiency is pooled across grades 3–8 and years "
        "(weighted by tested counts where the state publishes them). A school appears in a panel "
        "only if both rates are non-suppressed under the state's masking rules. "
        "Dashed line = parity. Proficiency levels are NOT comparable across states."
    )
    fig.text(0.5, -0.02, note_base, ha="center", fontsize=8, color="#555555")
    fig.text(0.5, -0.12, line_a, ha="center", fontsize=7.5, color="#555555")
    fig.text(0.5, -0.20, line_b, ha="center", fontsize=7.5, color="#555555")
    plt.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT_FIGS / f"fig12_{st.lower()}_school_scatter.{ext}",
                    dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [{st}] saved fig12_{st.lower()}_school_scatter.pdf / .png  "
          f"(A n={len(sub_a):,}, B n={len(sub_b):,})")


def main() -> None:
    print("=" * 65)
    print("15_multistate_school_scatter.py — Fig 12 across states")
    print("=" * 65)

    multi = pd.read_parquet(PANEL_MULTI)
    multi = multi[multi["subject"] == "ELA"]
    wi = load_wi()

    results: list[dict] = []
    for st in STATE_CONFIG:
        df = wi if st == "WI" else multi[multi["state"] == st]
        if df.empty:
            print(f"  [{st}] no data; skipping")
            continue
        pooled = pool_schools(df)
        fig_state_scatter(st, pooled, results)

    res = pd.DataFrame(results)
    out_csv = OUT_TABLES / "multistate_school_correlations.csv"
    res.to_csv(out_csv, index=False)
    print(f"\nSaved {out_csv.relative_to(ROOT)}  ({len(res)} rows)")
    print("Done.")


if __name__ == "__main__":
    main()
