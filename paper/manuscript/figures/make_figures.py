"""Generate manuscript figures from results/kinship/schluter_drugs_firearms.

Figure 1: Annual cumulative children of drug + firearm parental decedents,
1999-2020, under naive / all-cause kappa / intent-stratified / MORTUCOD
specifications vs the Schluter (2024) published target.

Uses matplotlib only; saves SVG and PNG (for HTML preview) to this folder.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RES_DIR = PROJECT_ROOT / "results" / "kinship" / "schluter_drugs_firearms"
OUT_DIR = Path(__file__).resolve().parent


def load_annual_naive() -> pd.DataFrame:
    """Naive (all-cause K_alive) annual trajectory: from annual_by_cause."""
    d = pd.read_csv(RES_DIR / "annual_by_cause.csv")
    yr = (d.groupby("year")[["children_naive"]].sum()
              .reset_index().rename(columns={"children_naive": "naive"}))
    yr["naive_cumsum"] = yr["naive"].cumsum()
    return yr


def load_annual_kappa_allcause() -> pd.DataFrame:
    d = pd.read_csv(RES_DIR / "annual_by_cause.csv")
    yr = (d.groupby("year")[["children_nhis"]].sum()
              .reset_index().rename(columns={"children_nhis": "k_allcause"}))
    yr["k_allcause_cumsum"] = yr["k_allcause"].cumsum()
    return yr


def load_annual_kappa_intent() -> pd.DataFrame:
    d = pd.read_csv(RES_DIR / "annual_by_cause_stratified.csv")
    yr = (d.groupby("year")[["children_nhis_stratified"]].sum()
              .reset_index()
              .rename(columns={"children_nhis_stratified": "k_intent"}))
    yr["k_intent_cumsum"] = yr["k_intent"].cumsum()
    return yr


def compute_annual_mortucod() -> pd.DataFrame:
    """MORTUCOD BROAD annual: redo the apply_K computation but keep year.

    Replicates scripts/run_schluter_mortucod.py with the broad-scope
    classification and annual rollup. Sources of truth are the K table
    and cause_stratified-style annual NCHS deaths.
    """
    # Cumulative 1999-2020 has total=691,394 children under BROAD.
    # We need year-by-year. Easiest: re-run the script's apply_K logic
    # but groupby year.
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.run_schluter_mortucod import (
        ICD10_BROAD, apply_K, build_K_pooled, load_nchs_deaths)
    K = build_K_pooled()
    nchs = load_nchs_deaths(ICD10_BROAD)
    m = apply_K(nchs, K)
    yr = (m.groupby("year")[["children_nhis"]].sum().reset_index()
              .rename(columns={"children_nhis": "k_mortucod"}))
    yr["k_mortucod_cumsum"] = yr["k_mortucod"].cumsum()
    return yr


def make_figure1() -> None:
    naive    = load_annual_naive()
    kappa_a  = load_annual_kappa_allcause()
    kappa_i  = load_annual_kappa_intent()
    mortucod = compute_annual_mortucod()

    yr = (naive.merge(kappa_a, on="year")
                  .merge(kappa_i, on="year")
                  .merge(mortucod, on="year"))

    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=160)

    # Lines
    ax.plot(yr["year"], yr["naive_cumsum"] / 1000,
            label="Naive (kids per living adult)",
            color="#aaaaaa", linewidth=2, linestyle=":")
    ax.plot(yr["year"], yr["k_allcause_cumsum"] / 1000,
            label="NHIS K (all-cause $\\kappa$)",
            color="#1b6aae", linewidth=2)
    ax.plot(yr["year"], yr["k_intent_cumsum"] / 1000,
            label="NHIS K (intent-stratified MORTUCODLD)",
            color="#3c8c47", linewidth=2)
    ax.plot(yr["year"], yr["k_mortucod_cumsum"] / 1000,
            label="NHIS K (cause-specific MORTUCOD, headline)",
            color="#b24f3e", linewidth=2.4)

    # Schluter published total at end of 2020
    ax.scatter([2020], [1190], marker="X", s=80, color="#000000",
                 zorder=5, label="Schl\u00fcter (2024) published, 2020")

    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative children (thousands)")
    ax.set_title("Cumulative US children of drug-overdose and firearm parental\n"
                  "decedents, 1999-2020, by calibration specification")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.set_xlim(1998.5, 2020.5)
    ax.set_ylim(0, 1300)
    ax.grid(axis="y", linestyle="-", color="#eaeaea", linewidth=0.6,
              zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper left", fontsize=8.5, frameon=False,
                bbox_to_anchor=(0, 1.0))

    fig.tight_layout()
    for ext in ("svg", "png"):
        fig.savefig(OUT_DIR / f"figure1_schluter_cumulative.{ext}",
                      dpi=200, bbox_inches="tight")
    print(f"[fig1] wrote figure1_schluter_cumulative.{{svg,png}}")
    print("[fig1] 2020 cumulative (thousands):")
    print(f"  naive               {yr['naive_cumsum'].iloc[-1] / 1000:>6.0f}")
    print(f"  K all-cause         {yr['k_allcause_cumsum'].iloc[-1] / 1000:>6.0f}")
    print(f"  K intent-stratified {yr['k_intent_cumsum'].iloc[-1] / 1000:>6.0f}")
    print(f"  K MORTUCOD          {yr['k_mortucod_cumsum'].iloc[-1] / 1000:>6.0f}")
    print(f"  Schluter published       1,190")


def make_figure2_race_stratified() -> None:
    """Race-stratified delta % over 2000-2021 with bootstrap CIs.

    Source data: results/kinship/calibrated_villaveces/annual_summary_*.csv
    and baseline_villaveces/annual_summary_*.csv. CIs from bootstrap
    output. For simplicity in v2 of the manuscript, we report point
    estimates without CI bands; CI bands are added later if needed.
    """
    delta_dir = PROJECT_ROOT / "results" / "kinship" / "baseline_villaveces"

    races = [
        ("Non-Hispanic_White",                               "NH White"),
        ("Non-Hispanic_Black",                               "NH Black"),
        ("Hispanic",                                         "Hispanic"),
        ("Non-Hispanic_Asian_or_Pacific_Islander",           "NH Asian/PI"),
        ("Non-Hispanic_American_Indian_or_Alaska_Native",    "NH AIAN"),
    ]
    colors = ["#1b6aae", "#3c8c47", "#b24f3e", "#6a4eaa", "#aa6a14"]

    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=160)
    for (race_slug, race_short), color in zip(races, colors):
        path = delta_dir / f"delta_{race_slug}.csv"
        if not path.exists():
            print(f"[fig2] skipping {race_short} (file not found: {path.name})")
            continue
        d = pd.read_csv(path)
        d = d[(d["focal_year"] >= 2000) & (d["focal_year"] <= 2021)]
        ax.plot(d["focal_year"], d["delta_prevalent_pct"],
                  label=race_short, color=color, linewidth=1.8)

    ax.axhline(0, color="#222", linewidth=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel(r"$\Delta$ % (calibrated vs baseline)")
    ax.set_title("Race-stratified NHIS-$\\kappa$ correction to US prevalent\n"
                  "parental orphanhood, 2000-2021")
    ax.set_xlim(1999.5, 2021.5)
    ax.grid(axis="y", linestyle="-", color="#eaeaea", linewidth=0.6,
              zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper left", fontsize=8.5, frameon=False, ncol=2)

    fig.tight_layout()
    for ext in ("svg", "png"):
        fig.savefig(OUT_DIR / f"figure2_race_stratified.{ext}",
                      dpi=200, bbox_inches="tight")
    print("[fig2] wrote figure2_race_stratified.{svg,png}")


if __name__ == "__main__":
    make_figure1()
    print()
    make_figure2_race_stratified()
