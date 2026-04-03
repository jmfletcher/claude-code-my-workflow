"""
03_figures.py
=============
Panel Conditioning (UK cohorts) — publication-ready figures.

Data source: fresh ONS pipeline (output/tables/01_*.csv), not legacy CSVs.

Figures produced:
  fig01_age_interval_coefs.pdf/.png   Forest-style plot: cohort coef by age bin
  fig02_mortality_trajectories.pdf/.png  Treated vs control mortality rates by death year
  fig03_cohort_profiles.pdf/.png      Mortality by age, faceted by cohort group

Run from repo root:
    python3 analysis/03_figures.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend; works in all environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
OUT_FIG = ROOT / "output" / "figures"
OUT_TAB = ROOT / "output" / "tables"
FRESH_LONG    = OUT_TAB / "01_clean_long.csv"      # birth_week × death_year
FRESH_AGE_AGG = OUT_TAB / "01_age_aggregated.csv"  # birth_week × age
AGE_COEF_CSV  = OUT_TAB / "02_age_intervals_cohort_coef.csv"

OUT_FIG.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Shared theme
# ---------------------------------------------------------------------------
BLUE   = "#1a5276"   # treated / main series
RED    = "#922b21"   # control / comparison
GRAY   = "#5d6d7e"
LGRAY  = "#d5d8dc"

plt.rcParams.update({
    "font.family":      "sans-serif",
    "font.size":        11,
    "axes.spines.top":  False,
    "axes.spines.right": False,
    "axes.grid":        True,
    "grid.color":       LGRAY,
    "grid.linewidth":   0.6,
    "figure.dpi":       150,
})

FIGSIZE_WIDE   = (9, 4.5)
FIGSIZE_SQUARE = (7, 6)


def save(fig: plt.Figure, stem: str) -> None:
    for ext in ("pdf", "png"):
        path = OUT_FIG / f"{stem}.{ext}"
        fig.savefig(path, bbox_inches="tight", dpi=300)
        print(f"  Saved: {path.name}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 1 — Age-interval cohort coefficients (forest plot style)
# ---------------------------------------------------------------------------

def fig01_age_interval_coefs() -> None:
    print("\nFigure 1: Age-interval cohort coefficients")
    if not AGE_COEF_CSV.exists():
        print(f"  [MISSING] {AGE_COEF_CSV} — run 02_replicate_stata.py first")
        return
    df = pd.read_csv(AGE_COEF_CSV)

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)

    y = np.arange(len(df))
    colors = [BLUE if p < 0.05 else GRAY for p in df["pval"]]

    ax.hlines(y, df["ci_lo"], df["ci_hi"], colors=colors, linewidth=2.5)
    ax.scatter(df["coef"], y, color=colors, s=60, zorder=5)
    ax.axvline(0, color="black", linewidth=0.9, linestyle="--")

    ax.set_yticks(y)
    ax.set_yticklabels(df["age_bin"], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Cohort coefficient (mortality rate difference, treated − control)",
                  fontsize=10)
    ax.set_title("Panel conditioning effect on mortality rate by age interval\n"
                 "OLS with age, year, week-of-year FE; SE clustered by birth week",
                 fontsize=11)

    # Annotation: sample sizes
    for i, row in df.iterrows():
        ax.text(df["ci_hi"].max() + 0.02, i, f"N={int(row['n']):,}",
                va="center", fontsize=8, color=GRAY)

    fig.tight_layout()
    save(fig, "fig01_age_interval_coefs")


# ---------------------------------------------------------------------------
# Figure 2 — Mortality rate trajectories: treated vs control over time
# ---------------------------------------------------------------------------

def fig02_mortality_trajectories() -> None:
    """Mortality rate by death year, treated vs control, faceted by cohort group."""
    print("\nFigure 2: Mortality trajectories by cohort group")
    if not FRESH_LONG.exists():
        print(f"  [MISSING] {FRESH_LONG} — run 01_load_and_clean.py first")
        return

    df = pd.read_csv(FRESH_LONG)
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df = df[df["age"].between(1, 69)]  # exclude age=0 (infant, see denominator note)

    cohort_labels = {1: "NSHD 1946", 2: "NCDS 1958", 3: "BCS70 1970"}

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharey=False)

    for ax, (grp, label) in zip(axes, cohort_labels.items()):
        sub = df[df["group"] == grp].copy()

        treated = (sub[sub["cohort"] == 1]
                   .groupby("death_year")["rate"].mean()
                   .reset_index())
        ctrl_grp = sub[sub["cohort"] == 0].groupby("death_year")["rate"]
        control_mean = ctrl_grp.mean().reset_index()
        control_lo   = ctrl_grp.min()
        control_hi   = ctrl_grp.max()

        ax.fill_between(
            control_mean["death_year"],
            control_lo.values,
            control_hi.values,
            color=GRAY, alpha=0.12, label="Control range"
        )
        ax.plot(control_mean["death_year"], control_mean["rate"],
                color=GRAY, linewidth=1.2, linestyle="--", label="Control mean")
        ax.plot(treated["death_year"], treated["rate"],
                color=BLUE, linewidth=2.0, label="Treated week")

        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.set_xlabel("Death year")
        if grp == 1:
            ax.set_ylabel("Mortality rate (per 1,000 births)")
        ax.legend(fontsize=8, framealpha=0.5)
        ax.set_xlim(1970, 2013)

    fig.suptitle(
        "Annual mortality: selected (treated) vs adjacent (control) birth weeks\n"
        "England and Wales, 1970–2013  (ages 1–69 only)",
        fontsize=11, y=1.02
    )
    fig.tight_layout()
    save(fig, "fig02_mortality_trajectories")


# ---------------------------------------------------------------------------
# Figure 3 — Age profiles: mortality rate vs age, by cohort group
# ---------------------------------------------------------------------------

def fig03_cohort_age_profiles() -> None:
    """Mortality rate vs age, treated vs control, faceted by cohort group."""
    print("\nFigure 3: Age profiles by cohort group")
    if not FRESH_AGE_AGG.exists():
        print(f"  [MISSING] {FRESH_AGE_AGG} — run 01_load_and_clean.py first")
        return

    df = pd.read_csv(FRESH_AGE_AGG)
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df = df[df["age"].between(1, 69)]  # exclude age=0 (infant mortality)
    df = df.dropna(subset=["rate"])

    cohort_labels = {1: "NSHD 1946", 2: "NCDS 1958", 3: "BCS70 1970"}

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharey=False)

    for ax, (grp, label) in zip(axes, cohort_labels.items()):
        sub = df[df["group"] == grp]
        treated = sub[sub["cohort"] == 1]
        control = sub[sub["cohort"] == 0]

        t_age = treated.groupby("age")["rate"].mean()
        c_age = control.groupby("age")["rate"].mean()
        c_lo  = control.groupby("age")["rate"].quantile(0.10)
        c_hi  = control.groupby("age")["rate"].quantile(0.90)

        ax.fill_between(c_lo.index, c_lo, c_hi, color=GRAY, alpha=0.15,
                        label="Control 10–90th pctile")
        ax.plot(c_age.index, c_age, color=GRAY, linewidth=1.4,
                linestyle="--", label="Control mean")
        ax.plot(t_age.index, t_age, color=BLUE, linewidth=2.0,
                label="Treated week")

        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.set_xlabel("Age (years)")
        if grp == 1:
            ax.set_ylabel("Mortality rate (per 1,000 births)")
        ax.legend(fontsize=8, framealpha=0.5)

    fig.suptitle(
        "Mortality rate by age: selected (treated) vs adjacent (control) birth weeks\n"
        "(ages 1–69; excludes infant year)",
        fontsize=11, y=1.02
    )
    fig.tight_layout()
    save(fig, "fig03_cohort_age_profiles")


# ---------------------------------------------------------------------------
# Figure 4 — By-cohort age-interval coefficients (3-panel forest plot)
# ---------------------------------------------------------------------------

BY_COHORT_CSV = OUT_TAB / "02_by_cohort_coef.csv"
COHORT_COLORS = {
    "NSHD 1946": "#1a5276",
    "NCDS 1958": "#922b21",
    "BCS70 1970": "#1e8449",
}


def fig04_by_cohort_coefs() -> None:
    """Forest plot of cohort coefficient by age interval, one panel per study."""
    print("\nFigure 4: By-cohort age-interval coefficients")
    if not BY_COHORT_CSV.exists():
        print(f"  [MISSING] {BY_COHORT_CSV} — run 02_replicate_stata.py first")
        return

    df = pd.read_csv(BY_COHORT_CSV)
    # Exclude the pooled row for the age-interval subplots
    df_intervals = df[df["age_bin"] != "Pooled"].copy()
    df_pooled    = df[df["age_bin"] == "Pooled"].copy()

    studies = ["NSHD 1946", "NCDS 1958", "BCS70 1970"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=False)

    for ax, study in zip(axes, studies):
        sub = df_intervals[df_intervals["study"] == study].copy()
        pool = df_pooled[df_pooled["study"] == study]
        color = COHORT_COLORS[study]

        if sub.empty:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")
            ax.set_title(study)
            continue

        y = np.arange(len(sub))
        pt_colors = [color if p < 0.05 else GRAY for p in sub["pval"]]

        ax.hlines(y, sub["ci_lo"], sub["ci_hi"], colors=pt_colors, linewidth=2.5)
        ax.scatter(sub["coef"], y, color=pt_colors, s=60, zorder=5)
        ax.axvline(0, color="black", linewidth=0.9, linestyle="--")

        # Pooled estimate as vertical dashed line with label
        if not pool.empty:
            pv = pool.iloc[0]
            lbl = (f"Pooled β={pv['coef']:.3f}"
                   f"{'**' if pv['pval']<0.05 else ''}"
                   f" (p={pv['pval']:.3f})")
            ax.axvline(pv["coef"], color=color, linewidth=1.2,
                       linestyle=":", alpha=0.8)
            ax.text(pv["coef"], len(sub) - 0.3, lbl,
                    fontsize=7.5, color=color, rotation=90,
                    ha="right", va="top")

        ax.set_yticks(y)
        ax.set_yticklabels(sub["age_bin"], fontsize=9)
        ax.invert_yaxis()
        ax.set_title(study, fontsize=11, fontweight="bold", color=color)
        ax.set_xlabel("Cohort coef. (95% CI)", fontsize=9)
        if study == "NSHD 1946":
            ax.set_ylabel("Age interval")

        # Sample size annotation
        for i, row in sub.reset_index(drop=True).iterrows():
            ax.text(sub["ci_hi"].max() + 0.02, i,
                    f"N={int(row['n']):,}", va="center", fontsize=7.5, color=GRAY)

    fig.suptitle(
        "Panel conditioning effect by cohort study and age interval\n"
        "OLS with age, birth-year, week-of-year FE; SE clustered by birth week",
        fontsize=11, y=1.02
    )
    fig.tight_layout()
    save(fig, "fig04_by_cohort_coefs")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Panel Conditioning (UK) — Figures")
    print(f"Output: {OUT_FIG}")

    fig01_age_interval_coefs()
    fig02_mortality_trajectories()
    fig03_cohort_age_profiles()
    fig04_by_cohort_coefs()

    print("\nAll figures done.")
