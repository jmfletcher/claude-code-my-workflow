"""Run the kinship matrix engine with NHIS-derived fertility-by-mortality
calibration applied to the parent-loss probabilities.

Outputs (under results/kinship/calibrated_villaveces/):
    annual_summary_<race>.csv            -- year-level totals (calibrated)
    parental_loss_grid_<race>.parquet    -- (focal_year, focal_age) probs
And under results/kinship/baseline_villaveces/ for the side-by-side:
    delta_<race>.csv                     -- baseline, calibrated, delta
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pykin import AGES
from pykin.calibrate import kappa_array_for, load_kappa_table
from pykin.engine import rates_to_arrays
from pykin.ingest import load_cache
from pykin.orphanhood import annual_summaries, parental_loss_grid_cached


CAL_DIR  = PROJECT_ROOT / "results" / "kinship" / "calibrated_villaveces"
BASE_DIR = PROJECT_ROOT / "results" / "kinship" / "baseline_villaveces"


def run_one(race_eth: str = "All"):
    pop, mort, fert = load_cache()
    rates = rates_to_arrays(pop, mort, fert,
                            race_eth=race_eth,
                            years=range(1983, 2022),
                            ages=AGES)

    # Baseline (no calibration)
    print(f"[run] race={race_eth}: baseline ...")
    grid_base = parental_loss_grid_cached(
        rates, year_min=2000, year_max=2021, max_focal_age=17,
    )
    summary_base = annual_summaries(grid_base, pop, race_eth=race_eth)

    # Calibrated
    print(f"[run] race={race_eth}: loading kappa and running calibrated ...")
    ktab = load_kappa_table()
    kappa_yrs = np.arange(1983, 2022)
    kappa = kappa_array_for(ktab, race_eth=race_eth, years=range(1983, 2022),
                            ages=AGES)
    grid_cal = parental_loss_grid_cached(
        rates, year_min=2000, year_max=2021, max_focal_age=17,
        kappa_f=kappa["f"], kappa_m=kappa["m"], kappa_years=kappa_yrs,
    )
    summary_cal = annual_summaries(grid_cal, pop, race_eth=race_eth)

    CAL_DIR.mkdir(parents=True, exist_ok=True)
    suffix = race_eth.replace(" ", "_").replace("/", "-").replace(",", "")
    grid_cal_path = CAL_DIR / f"parental_loss_grid_{suffix}.parquet"
    sum_cal_path  = CAL_DIR / f"annual_summary_{suffix}.csv"
    grid_cal.to_parquet(grid_cal_path, index=False)
    summary_cal.to_csv(sum_cal_path, index=False)
    print(f"[run] wrote {grid_cal_path.relative_to(PROJECT_ROOT)}")
    print(f"[run] wrote {sum_cal_path.relative_to(PROJECT_ROOT)}")

    # Side-by-side
    delta = summary_base.merge(
        summary_cal[["focal_year", "prevalent", "incident"]],
        on="focal_year", suffixes=("_base", "_cal"),
    )
    delta["delta_prevalent_abs"] = delta["prevalent_cal"] - delta["prevalent_base"]
    delta["delta_prevalent_pct"] = 100.0 * delta["delta_prevalent_abs"] / delta["prevalent_base"]
    delta["delta_incident_abs"]  = delta["incident_cal"]  - delta["incident_base"]
    delta["delta_incident_pct"]  = np.where(
        delta["incident_base"].notna() & (delta["incident_base"] != 0),
        100.0 * delta["delta_incident_abs"] / delta["incident_base"],
        np.nan,
    )
    delta_path = BASE_DIR / f"delta_{suffix}.csv"
    delta.to_csv(delta_path, index=False)
    print(f"[run] wrote {delta_path.relative_to(PROJECT_ROOT)}")

    return summary_base, summary_cal, delta


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--race", default="All")
    args = ap.parse_args()

    base, cal, delta = run_one(args.race)
    print()
    print(f"=== Baseline vs calibrated for race_eth={args.race!r} ===")
    cols = ["focal_year", "prevalent_base", "prevalent_cal",
            "delta_prevalent_abs", "delta_prevalent_pct"]
    print(delta[cols].to_string(index=False, formatters={
        "prevalent_base": "{:>14,.0f}".format,
        "prevalent_cal":  "{:>14,.0f}".format,
        "delta_prevalent_abs": "{:>+14,.0f}".format,
        "delta_prevalent_pct": "{:>+8,.1f}".format,
    }))
