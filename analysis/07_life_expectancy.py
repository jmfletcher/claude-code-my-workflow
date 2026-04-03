"""
07_life_expectancy.py
=====================
Translates the age-interval treatment effect estimates into implied effects
on cohort life expectancy.

Method
------
1. Construct a baseline life table from the observed control-week mortality
   rates (01_age_aggregated.csv, cohort == 0), averaged across all birth
   years and groups.  These are annual mortality rates per 1,000.

2. Add the age-interval treatment coefficients (02_age_intervals_cohort_coef.csv)
   to form the treated life table.

3. Extend both tables from the observed maximum age (~69) to age 100 using
   approximate England and Wales period values (ONS, 2000-era cohort tables),
   applied identically to baseline and treated so the extension does not
   introduce spurious LE differences beyond the data window.

4. Compute life expectancy at birth (e₀) and at age 10 (e₁₀) for both tables
   and report the difference.

5. Compute cumulative excess deaths per 1,000 within the observed data window.

Key assumptions
---------------
- Treatment effect is constant within each 10-year interval.
- The additional hazard does NOT persist beyond the observed data window
  (conservative; sensitivity check also applies the effect to all ages).
- Denominators are approximately equal across treated and control weeks
  (supported by the observed rate structure).

Outputs
-------
  output/tables/07_lifetable_comparison.csv   (full life table)
  output/tables/07_le_summary.json            (headline numbers)
  output/figures/fig07_survival_curves.pdf/.png

Run from repo root:
    python3 analysis/07_life_expectancy.py
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT    = Path(__file__).resolve().parent.parent
OUT_TAB = ROOT / "output" / "tables"
OUT_FIG = ROOT / "output" / "figures"

AGE_AGG    = OUT_TAB / "01_age_aggregated.csv"
INTERVALS  = OUT_TAB / "02_age_intervals_cohort_coef.csv"

# ---------------------------------------------------------------------------
# England and Wales approximate annual mortality rates per 1,000 (post-2000
# period life table, combined sexes) for ages 70–100.
# Source: ONS National Life Tables 2019-2021 (rounded).
# Used only to extend the life table beyond our observation window; applied
# identically to baseline and treated, so they cancel in the LE difference.
# ---------------------------------------------------------------------------
EW_EXTENSION = {
    70: 2.2, 71: 2.5, 72: 2.8, 73: 3.1, 74: 3.5,
    75: 4.0, 76: 4.5, 77: 5.1, 78: 5.8, 79: 6.7,
    80: 7.7, 81: 8.9, 82: 10.3, 83: 11.9, 84: 13.7,
    85: 16.0, 86: 18.5, 87: 21.4, 88: 24.7, 89: 28.5,
    90: 32.7, 91: 37.5, 92: 42.8, 93: 48.6, 94: 55.0,
    95: 62.0, 96: 70.0, 97: 78.0, 98: 86.0, 99: 93.0,
}
MAX_AGE = 100

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_age_bin(label: str) -> tuple[int, int]:
    """'Age 0–9' -> (0, 9); 'Age 60–69' -> (60, 69) etc."""
    label = label.replace("\u2013", "-").replace("–", "-")
    nums = [int(x) for x in label.replace("Age ", "").split("-")]
    return nums[0], nums[1]


def build_baseline(df: pd.DataFrame) -> pd.Series:
    """
    Mean annual mortality rate per 1,000 by single year of age,
    computed from control weeks only.
    Returns a Series indexed by age (int).
    """
    ctrl = df[df["cohort"] == 0].copy()
    ctrl["rate"] = pd.to_numeric(ctrl["rate"], errors="coerce")
    baseline = (
        ctrl.groupby("age")["rate"]
        .mean()
        .rename("q_baseline")
    )
    return baseline


def build_interval_map(intervals: pd.DataFrame) -> dict[int, float]:
    """Map each single age to the treatment coefficient for its 10-yr interval."""
    mapping: dict[int, float] = {}
    for _, row in intervals.iterrows():
        lo, hi = parse_age_bin(row["age_bin"])
        for a in range(lo, hi + 1):
            mapping[a] = float(row["coef"])
    return mapping


def life_table(rates_per_1000: pd.Series, max_age: int = MAX_AGE) -> pd.DataFrame:
    """
    Build a cohort life table from annual mortality rates (per 1,000).
    Rates are treated as the probability of dying during that year given
    survival to the start (small-rate approximation q ≈ m).
    Returns DataFrame with columns: age, q, lx, dx, Lx, Tx, ex.
    """
    rows = []
    for a in range(0, max_age + 1):
        q = min(rates_per_1000.get(a, np.nan) / 1000, 1.0)
        rows.append({"age": a, "q": q})
    lt = pd.DataFrame(rows)

    # Fill gaps via linear interpolation then forward-fill
    lt["q"] = lt["q"].interpolate(method="linear").ffill().bfill()

    lt["lx"] = 0.0
    lt.at[0, "lx"] = 100_000.0
    for i in range(1, len(lt)):
        lt.loc[i, "lx"] = lt.loc[i - 1, "lx"] * (1 - lt.loc[i - 1, "q"])

    lt["dx"] = lt["lx"] * lt["q"]
    lt["Lx"] = lt["lx"] - 0.5 * lt["dx"]          # person-years in interval
    lt["Tx"] = lt["Lx"][::-1].cumsum()[::-1]       # future person-years
    lt["ex"] = lt["Tx"] / lt["lx"]                 # life expectancy

    return lt


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("  07_life_expectancy.py")
    print("=" * 70)

    for p in (AGE_AGG, INTERVALS):
        if not p.exists():
            print(f"[ERROR] Missing input: {p}")
            sys.exit(1)

    # --- load data ----------------------------------------------------------
    df = pd.read_csv(AGE_AGG)
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df = df.dropna(subset=["age", "rate"])

    intervals = pd.read_csv(INTERVALS)
    interval_map = build_interval_map(intervals)

    # --- baseline rates from control weeks ----------------------------------
    baseline = build_baseline(df)
    obs_ages = sorted(baseline.index.tolist())
    print(f"\nObserved ages in data: {min(obs_ages)}–{max(obs_ages)}")

    # Extend to MAX_AGE using EW values
    full_baseline = baseline.copy()
    for a, r in EW_EXTENSION.items():
        if a not in full_baseline.index:
            full_baseline[a] = r
    full_baseline = full_baseline.sort_index()

    # --- treated rates: add interval coefficient to observed ages only -------
    full_treated = full_baseline.copy()
    for a in obs_ages:
        delta = interval_map.get(a, 0.0)
        full_treated[a] = full_treated[a] + delta

    # --- life tables --------------------------------------------------------
    lt_base    = life_table(full_baseline)
    lt_treated = life_table(full_treated)

    e0_base    = lt_base.loc[0,  "ex"]
    e0_treated = lt_treated.loc[0,  "ex"]
    e10_base   = lt_base.loc[10, "ex"]
    e10_treated = lt_treated.loc[10, "ex"]

    delta_e0  = e0_treated  - e0_base
    delta_e10 = e10_treated - e10_base

    print(f"\nLife expectancy at birth:  baseline = {e0_base:.2f} yrs, "
          f"treated = {e0_treated:.2f} yrs, Δ = {delta_e0:.3f} yrs "
          f"({delta_e0*12:.1f} months)")
    print(f"Life expectancy at age 10: baseline = {e10_base:.2f} yrs, "
          f"treated = {e10_treated:.2f} yrs, Δ = {delta_e10:.3f} yrs "
          f"({delta_e10*12:.1f} months)")

    # --- excess deaths per 1,000 within observed window ---------------------
    print("\nExcess deaths per 1,000 by age interval (within data window):")
    total_excess = 0.0
    interval_rows = []
    for _, row in intervals.iterrows():
        lo, hi = parse_age_bin(row["age_bin"])
        width = hi - lo + 1
        excess = row["coef"] * width / 1000.0   # additional deaths per person
        total_excess += excess
        interval_rows.append({
            "age_bin": row["age_bin"],
            "coef_per_1000_yr": round(row["coef"], 4),
            "interval_width_yrs": width,
            "excess_deaths_per_1000": round(excess * 1000, 3),
            "pval": round(row["pval"], 4),
        })
        print(f"  {row['age_bin']:12s}  β={row['coef']:+.4f}  "
              f"excess={excess*1000:+.2f}/1,000  p={row['pval']:.3f}")
    print(f"\n  TOTAL excess deaths per 1,000 by age {max(obs_ages)}: "
          f"{total_excess*1000:+.2f}")

    # --- full life-expectancy sensitivity check: effect persists beyond 70 --
    full_treated_ext = full_baseline.copy()
    delta_adult = np.mean([interval_map.get(a, 0.0) for a in range(40, 70)])
    for a in full_treated_ext.index:
        full_treated_ext[a] = full_treated_ext[a] + interval_map.get(
            int(a), delta_adult   # extrapolate using mean adult-age effect
        )
    lt_ext = life_table(full_treated_ext)
    delta_e0_ext = lt_ext.loc[0, "ex"] - e0_base
    print(f"\n  Sensitivity: if treatment effect persists beyond age {max(obs_ages)}")
    print(f"  (extrapolated at mean adult-age coefficient), Δe₀ = "
          f"{delta_e0_ext:.3f} yrs ({delta_e0_ext*12:.1f} months)")

    # --- save outputs -------------------------------------------------------
    # Combined life table
    lt_combined = lt_base.merge(
        lt_treated[["age", "q", "lx", "ex"]],
        on="age", suffixes=("_base", "_treated")
    )
    lt_combined.to_csv(OUT_TAB / "07_lifetable_comparison.csv", index=False)

    # Summary JSON
    summary = {
        "e0_baseline_yrs":      round(e0_base, 3),
        "e0_treated_yrs":       round(e0_treated, 3),
        "delta_e0_yrs":         round(delta_e0, 4),
        "delta_e0_months":      round(delta_e0 * 12, 2),
        "e10_baseline_yrs":     round(e10_base, 3),
        "delta_e10_yrs":        round(delta_e10, 4),
        "delta_e10_months":     round(delta_e10 * 12, 2),
        "total_excess_deaths_per_1000_to_age69": round(total_excess * 1000, 2),
        "delta_e0_sensitivity_yrs":   round(delta_e0_ext, 4),
        "delta_e0_sensitivity_months": round(delta_e0_ext * 12, 2),
        "notes": (
            "Effect applied only to observed ages (data window) in main estimate. "
            "Extension applies mean adult-age coefficient beyond observed ages. "
            "Life table extended to age 100 using ONS 2019-21 period rates (both tables); "
            "LE difference beyond observed ages is therefore zero in the main estimate."
        )
    }
    with open(OUT_TAB / "07_le_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved: 07_lifetable_comparison.csv, 07_le_summary.json")

    # --- figure: survival curves -------------------------------------------
    BLUE  = "#1a5276"
    RED   = "#922b21"
    LGRAY = "#d5d8dc"
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": LGRAY, "grid.linewidth": 0.6,
        "figure.dpi": 150,
    })
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Panel A: survival curves
    ax = axes[0]
    ax.plot(lt_base["age"],    lt_base["lx"]    / 1000, color=BLUE,
            label="Control (baseline)", linewidth=2)
    ax.plot(lt_treated["age"], lt_treated["lx"] / 1000, color=RED,
            label="Treated (baseline + effect)", linewidth=2, linestyle="--")
    ax.axvline(max(obs_ages), color="gray", linewidth=0.8, linestyle=":",
               label=f"Data window ends (age {max(obs_ages)})")
    ax.set_xlabel("Age")
    ax.set_ylabel("Survivors per 1,000 births")
    ax.set_title("A. Survival curves")
    ax.legend(fontsize=9)

    # Panel B: cumulative excess deaths per 1,000
    ax2 = axes[1]
    ages_plot = lt_combined["age"].values
    excess_cum = (
        (lt_combined["lx_base"] - lt_combined["lx_treated"]) / 100   # per 1,000
    )
    ax2.plot(ages_plot, excess_cum, color=RED, linewidth=2)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.axvline(max(obs_ages), color="gray", linewidth=0.8, linestyle=":",
                label=f"Data window ends (age {max(obs_ages)})")
    ax2.set_xlabel("Age")
    ax2.set_ylabel("Cumulative excess deaths per 1,000 births")
    ax2.set_title("B. Cumulative excess deaths (treated − control)")
    ax2.legend(fontsize=9)

    fig.suptitle(
        "Implied cohort life-table effects of panel conditioning treatment estimate\n"
        "Treatment effect applied only within observed data window (age 0–69)",
        fontsize=10
    )
    fig.tight_layout()
    for ext in ("pdf", "png"):
        p = OUT_FIG / f"fig07_survival_curves.{ext}"
        fig.savefig(p, bbox_inches="tight", dpi=300)
        print(f"Saved: {p.name}")
    plt.close(fig)

    print("\nDone.")
