"""
07_figures.py
=============
Generate all manuscript figures and save to output/figures/.

Figure files (names must match HTML references):
  fig01_age_interval_coefs.png   — Figure 1: age-interval forest plot
  fig07_survival_curves.png      — Figure 2: survival curves + excess deaths
  fig02_mortality_trajectories.png — Figure 3: annual rate trajectories
  fig03_cohort_age_profiles.png  — Figure 4: rate by age, by cohort
  fig04_by_cohort_coefs.png      — Figure 5: by-cohort × age forest plot
  fig06_robustness.png           — Figure 6: robustness coefficient plot
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats as scipy_stats

from analysis.config import TABLES_DIR, FIGURES_DIR, AGE_INTERVALS, GROUPS

# ── Style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 180,
    "font.family": "serif",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "axes.grid": False,
    "lines.linewidth": 1.4,
    "legend.frameon": False,
    "legend.fontsize": 9,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
})

BLUE   = "#2563EB"
RED    = "#DC2626"
GREY   = "#6B7280"
GREEN  = "#16A34A"
ORANGE = "#EA580C"

STUDY_COLORS = {
    "NSHD 1946": "#1D4ED8",
    "NCDS 1958": "#059669",
    "BCS70 1970": "#DC2626",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def ci95(coef, se):
    return coef - 1.96 * se, coef + 1.96 * se


def save(fig, name: str):
    path = FIGURES_DIR / name
    fig.savefig(path, bbox_inches="tight", dpi=180)
    plt.close(fig)
    print(f"  Saved {name} ({path.stat().st_size // 1024} KB)")


# ── Figure 1: Age-interval forest plot ───────────────────────────────────────

def fig01_age_interval_coefs():
    df = pd.read_csv(TABLES_DIR / "results_by_age.csv")

    fig, ax = plt.subplots(figsize=(6, 4.5))

    labels = df["age_interval"].tolist()
    y = np.arange(len(labels))
    coefs = df["coef"].values
    ses   = df["se"].values
    pvals = df["pval"].values
    lo    = coefs - 1.96 * ses
    hi    = coefs + 1.96 * ses

    for i, (c, l, h, p) in enumerate(zip(coefs, lo, hi, pvals)):
        color = BLUE if p < 0.05 else GREY
        marker = "o" if p < 0.05 else "o"
        mfc = color if p < 0.05 else "white"
        ax.plot([l, h], [y[i], y[i]], color=color, lw=1.2, zorder=2)
        ax.plot(c, y[i], marker=marker, color=color, mfc=mfc,
                mec=color, ms=7, zorder=3)

    ax.axvline(0, color="black", lw=0.8, ls="--", alpha=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Cohort coefficient (deaths per 1,000 per year)")
    ax.set_title("Figure 1: Treatment effect by age interval")

    filled = mpatches.Patch(color=BLUE, label=r"$p < 0.05$")
    empty  = mpatches.Patch(facecolor="white", edgecolor=GREY, label=r"$p \geq 0.05$")
    ax.legend(handles=[filled, empty], loc="lower right")

    ax.invert_yaxis()
    fig.tight_layout()
    save(fig, "fig01_age_interval_coefs.png")


# ── Figure 2: Survival curves + cumulative excess deaths ─────────────────────

def fig07_survival_curves():
    lt = pd.read_csv(TABLES_DIR / "results_life_table.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))

    # Build cumulative survival
    l_ctrl = [1_000.0]
    l_trt  = [1_000.0]
    ages   = [0]
    excess_cum = [0.0]

    for _, r in lt.iterrows():
        ages.append(r.age_hi + 1)
        mx_c = r.mx_ctrl / 1_000
        mx_t = r.mx_trt  / 1_000
        n = r.age_hi - r.age_lo + 1
        l_ctrl.append(l_ctrl[-1] * np.exp(-mx_c * n))
        l_trt.append( l_trt[-1]  * np.exp(-mx_t  * n))
        excess_cum.append(excess_cum[-1] + r.excess_deaths_per1000)

    # Panel A: survival
    ax1.plot(ages, l_ctrl, color=GREY,  ls="--", label="Control weeks")
    ax1.plot(ages, l_trt,  color=BLUE,  ls="-",  label="Treated week")
    ax1.axvline(ages[-1], color="black", lw=0.6, ls=":", alpha=0.6)
    ax1.set_xlabel("Age")
    ax1.set_ylabel("Survivors per 1,000 births")
    ax1.set_title("Panel A: Cohort survival")
    ax1.legend()

    # Panel B: cumulative excess deaths
    ax2.fill_between(ages, 0, excess_cum, where=[e >= 0 for e in excess_cum],
                     alpha=0.25, color=RED)
    ax2.fill_between(ages, 0, excess_cum, where=[e < 0 for e in excess_cum],
                     alpha=0.25, color=GREEN)
    ax2.plot(ages, excess_cum, color=RED, lw=1.5)
    ax2.axhline(0, color="black", lw=0.6, ls="--", alpha=0.5)
    ax2.axvline(ages[-1], color="black", lw=0.6, ls=":", alpha=0.6)
    ax2.set_xlabel("Age")
    ax2.set_ylabel("Cumulative excess deaths per 1,000")
    ax2.set_title("Panel B: Cumulative excess deaths (treated − control)")

    fig.suptitle("Figure 2: Implied cohort life table", fontsize=11)
    fig.tight_layout()
    save(fig, "fig07_survival_curves.png")


# ── Figure 3: Annual mortality trajectories ───────────────────────────────────

def fig02_mortality_trajectories():
    panel = pd.read_csv(TABLES_DIR / "panel_clean.csv")
    panel["death_year"] = panel["birth_year"] + panel["age"]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=False)

    for ax, (g, info) in zip(axes, GROUPS.items()):
        grp = panel[panel["group"] == g]
        ctrl = grp[grp["treated"] == 0]
        trt  = grp[grp["treated"] == 1]

        ctrl_yr = ctrl.groupby("death_year")["rate"].mean().reset_index()
        trt_yr  = trt.groupby("death_year")["rate"].mean().reset_index()
        ctrl_lo = ctrl.groupby("death_year")["rate"].quantile(0.10).reset_index()
        ctrl_hi = ctrl.groupby("death_year")["rate"].quantile(0.90).reset_index()

        ax.fill_between(ctrl_lo["death_year"], ctrl_lo["rate"], ctrl_hi["rate"],
                        alpha=0.15, color=GREY, label="Control 10–90th pct")
        ax.plot(ctrl_yr["death_year"], ctrl_yr["rate"],
                color=GREY, ls="--", lw=1.2, label="Control mean")
        ax.plot(trt_yr["death_year"], trt_yr["rate"],
                color=STUDY_COLORS[info["study"]], lw=1.6,
                label=f"Treated ({info['name']})")

        ax.set_title(f"{info['study']}")
        ax.set_xlabel("Year of death")
        if g == 1:
            ax.set_ylabel("Mortality rate (per 1,000 per year)")
        ax.legend(fontsize=7.5)

    fig.suptitle("Figure 3: Annual mortality rate for treated vs. control birth weeks", fontsize=11)
    fig.tight_layout()
    save(fig, "fig02_mortality_trajectories.png")


# ── Figure 4: Mortality by age, treated vs. control ──────────────────────────

def fig03_cohort_age_profiles():
    panel = pd.read_csv(TABLES_DIR / "panel_clean.csv")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=False)

    for ax, (g, info) in zip(axes, GROUPS.items()):
        grp = panel[panel["group"] == g]
        ctrl = grp[grp["treated"] == 0]
        trt  = grp[grp["treated"] == 1]

        ctrl_age = ctrl.groupby("age")["rate"].mean().reset_index()
        trt_age  = trt.groupby("age")["rate"].mean().reset_index()
        ctrl_lo  = ctrl.groupby("age")["rate"].quantile(0.10).reset_index()
        ctrl_hi  = ctrl.groupby("age")["rate"].quantile(0.90).reset_index()

        ax.fill_between(ctrl_lo["age"], ctrl_lo["rate"], ctrl_hi["rate"],
                        alpha=0.15, color=GREY)
        ax.plot(ctrl_age["age"], ctrl_age["rate"],
                color=GREY, ls="--", lw=1.2, label="Control mean")
        ax.plot(trt_age["age"], trt_age["rate"],
                color=STUDY_COLORS[info["study"]], lw=1.6,
                label=f"Treated ({info['name']})")

        ax.set_title(f"{info['study']}")
        ax.set_xlabel("Age")
        if g == 1:
            ax.set_ylabel("Mortality rate (per 1,000 per year)")
        ax.legend(fontsize=7.5)

    fig.suptitle("Figure 4: Mortality rate by age, treated vs. control birth weeks", fontsize=11)
    fig.tight_layout()
    save(fig, "fig03_cohort_age_profiles.png")


# ── Figure 5: By-cohort × age interval forest plot ───────────────────────────

def fig04_by_cohort_coefs():
    df = pd.read_csv(TABLES_DIR / "results_by_cohort_age.csv")
    # Drop "Pooled" rows — show only age-interval rows
    df_age = df[df["age_interval"] != "Pooled"].copy()

    studies = ["NSHD 1946", "NCDS 1958", "BCS70 1970"]
    n_studies = len(studies)

    fig, axes = plt.subplots(1, n_studies, figsize=(12, 5), sharey=True)

    for ax, study in zip(axes, studies):
        sub = df_age[df_age["study"] == study].copy()
        labels = sub["age_interval"].tolist()
        y = np.arange(len(labels))

        pooled_row = df[(df["study"] == study) & (df["age_interval"] == "Pooled")]
        pooled_est = pooled_row["coef"].values[0] if len(pooled_row) else None

        for i, (_, r) in enumerate(sub.iterrows()):
            lo, hi = ci95(r.coef, r.se)
            color = STUDY_COLORS[study] if r.pval < 0.05 else GREY
            mfc   = color if r.pval < 0.05 else "white"
            ax.plot([lo, hi], [y[i], y[i]], color=color, lw=1.2)
            ax.plot(r.coef, y[i], "o", color=color, mfc=mfc,
                    mec=color, ms=6)

        ax.axvline(0, color="black", lw=0.7, ls="--", alpha=0.5)
        if pooled_est is not None:
            ax.axvline(pooled_est, color=STUDY_COLORS[study],
                       lw=1.0, ls=":", alpha=0.7,
                       label=f"Pooled = {pooled_est:.3f}")
            ax.legend(fontsize=7.5)

        ax.set_yticks(y)
        ax.set_yticklabels(labels if study == studies[0] else [])
        ax.set_title(study)
        ax.set_xlabel("Coefficient")
        ax.invert_yaxis()

    fig.suptitle("Figure 5: Panel conditioning effect by cohort and age interval", fontsize=11)
    fig.tight_layout()
    save(fig, "fig04_by_cohort_coefs.png")


# ── Figure 6: Robustness checks ───────────────────────────────────────────────

def fig06_robustness():
    df = pd.read_csv(TABLES_DIR / "results_robustness.csv")

    fig, ax = plt.subplots(figsize=(8, 5))

    labels = df["spec"].tolist()
    y = np.arange(len(labels))
    coefs = df["coef"].values
    ses   = df["se"].values
    pvals = df["pval"].values

    baseline = coefs[0]

    for i, (c, s, p, lab) in enumerate(zip(coefs, ses, pvals, labels)):
        if np.isnan(c):
            ax.plot(0, y[i], "x", color=GREY, ms=8)
            continue
        lo, hi = ci95(c, s)
        color = GREEN if p < 0.05 else GREY
        mfc   = color if p < 0.05 else "white"
        ax.plot([lo, hi], [y[i], y[i]], color=color, lw=1.3)
        ax.plot(c, y[i], "o", color=color, mfc=mfc, mec=color, ms=7)

    ax.axvline(0, color="black", lw=0.8, ls="--", alpha=0.5)
    ax.axvline(baseline, color=BLUE, lw=1.0, ls="--", alpha=0.7,
               label=f"Baseline = {baseline:.3f}")

    ax.set_yticks(y)
    ax.set_yticklabels([l[:45] for l in labels], fontsize=8.5)
    ax.set_xlabel("Cohort coefficient (deaths per 1,000 per year)")
    ax.set_title("Figure 6: Robustness checks", fontsize=11)
    ax.legend(fontsize=8.5)
    ax.invert_yaxis()

    green_p = mpatches.Patch(color=GREEN, label=r"$p < 0.05$")
    grey_p  = mpatches.Patch(facecolor="white", edgecolor=GREY, label=r"$p \geq 0.05$")
    ax.legend(handles=[
        mpatches.Patch(color=BLUE, alpha=0.5, label=f"Baseline = {baseline:.3f}"),
        green_p, grey_p
    ], fontsize=8.5, loc="lower right")

    fig.tight_layout()
    save(fig, "fig06_robustness.png")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating figures → {FIGURES_DIR}")
    fig01_age_interval_coefs()
    fig07_survival_curves()
    fig02_mortality_trajectories()
    fig03_cohort_age_profiles()
    fig04_by_cohort_coefs()
    fig06_robustness()
    print("Done.")


if __name__ == "__main__":
    main()
