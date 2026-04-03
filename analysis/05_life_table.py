"""
05_life_table.py
================
Implied life-expectancy effects from the age-profile of treatment estimates.

Constructs cohort life tables using control-week mortality rates as baseline,
then adds the estimated age-interval coefficients for the treated group.
Reports excess deaths per 1,000 and implied reduction in life expectancy.
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from analysis.config import TABLES_DIR, AGE_INTERVALS


def build_life_table(
    ctrl_rates: dict[tuple[int,int], float],
    coefs: dict[tuple[int,int], float],
    max_obs_age: int = 69,
) -> pd.DataFrame:
    """
    ctrl_rates: dict (age_lo, age_hi) → mean control-week mortality rate
    coefs:      dict (age_lo, age_hi) → estimated treatment coefficient
    """
    rows = []
    l_ctrl = 1_000.0
    l_trt  = 1_000.0

    for lo, hi, label in AGE_INTERVALS:
        if (lo, hi) not in ctrl_rates:
            continue
        mx_ctrl = ctrl_rates[(lo, hi)] / 1_000  # per-person per-year rate
        beta    = coefs.get((lo, hi), 0.0)
        mx_trt  = (ctrl_rates[(lo, hi)] + beta) / 1_000
        mx_trt  = max(mx_trt, 0.0)

        n_years = hi - lo + 1
        # Fraction surviving the interval
        s_ctrl = np.exp(-mx_ctrl * n_years)
        s_trt  = np.exp(-mx_trt  * n_years)

        d_ctrl = l_ctrl * (1 - s_ctrl)
        d_trt  = l_trt  * (1 - s_trt)
        excess = d_trt - d_ctrl

        rows.append({
            "age_interval": label,
            "age_lo": lo, "age_hi": hi,
            "mx_ctrl": ctrl_rates[(lo, hi)],
            "beta": beta,
            "mx_trt": mx_trt * 1_000,
            "d_ctrl": d_ctrl,
            "d_trt": d_trt,
            "excess_deaths_per1000": excess,
            "l_ctrl_start": l_ctrl,
            "l_trt_start": l_trt,
        })

        l_ctrl *= s_ctrl
        l_trt  *= s_trt

    return pd.DataFrame(rows)


def le_from_life_table(df: pd.DataFrame, prefix: str) -> float:
    """Approximate life expectancy from a life table up to the last observed age."""
    total_ly = 0.0
    for _, r in df.iterrows():
        n_years = r.age_hi - r.age_lo + 1
        l_start = r[f"l_{prefix}_start"]
        mx = r[f"mx_{prefix}"] / 1_000
        # Integrate: L = l * (1 - e^{-mx*n}) / mx  (for constant mx)
        if mx > 0:
            ly = l_start * (1 - np.exp(-mx * n_years)) / mx
        else:
            ly = l_start * n_years
        total_ly += ly
    return total_ly / 1_000  # per person at birth


def main() -> None:
    panel   = pd.read_csv(TABLES_DIR / "panel_clean.csv")
    age_res = pd.read_csv(TABLES_DIR / "results_by_age.csv")

    # Control-week mean rates by age interval (pooled over all cohorts)
    ctrl = panel[panel["treated"] == 0]
    ctrl_rates: dict[tuple[int,int], float] = {}
    for lo, hi, label in AGE_INTERVALS:
        sub = ctrl[(ctrl["age"] >= lo) & (ctrl["age"] <= hi)]
        if len(sub) > 0:
            ctrl_rates[(lo, hi)] = sub["rate"].mean()

    # Treatment coefficients from by-age regression
    coefs: dict[tuple[int,int], float] = {}
    for _, r in age_res.iterrows():
        coefs[(int(r.age_lo), int(r.age_hi))] = r.coef

    lt = build_life_table(ctrl_rates, coefs)
    total_excess = lt["excess_deaths_per1000"].sum()

    le_ctrl = le_from_life_table(lt, "ctrl")
    le_trt  = le_from_life_table(lt, "trt")
    le_diff_months = (le_ctrl - le_trt) * 12

    print("=== Life-table implied effects ===")
    print(lt[["age_interval", "mx_ctrl", "beta", "excess_deaths_per1000"]].to_string(index=False))
    print(f"\nTotal excess deaths per 1,000: {total_excess:.2f}")
    print(f"Implied reduction in LE at birth: {le_ctrl - le_trt:.3f} years = {le_diff_months:.1f} months")

    lt.to_csv(TABLES_DIR / "results_life_table.csv", index=False)
    with open(TABLES_DIR / "results_life_table_summary.txt", "w") as f:
        f.write(f"total_excess_per1000={total_excess:.4f}\n")
        f.write(f"le_diff_years={le_ctrl-le_trt:.4f}\n")
        f.write(f"le_diff_months={le_diff_months:.2f}\n")
    print(f"Saved → {TABLES_DIR / 'results_life_table.csv'}")


if __name__ == "__main__":
    main()
