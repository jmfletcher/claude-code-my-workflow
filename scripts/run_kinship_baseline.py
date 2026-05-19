"""Run the kinship matrix engine on US all-cause inputs and produce
baseline orphanhood numbers for the Villaveces 2025 comparison.

Outputs (under results/kinship/baseline_villaveces/):
    annual_summary_All.csv         -- year-level totals
    parental_loss_grid_All.parquet -- (focal_year, focal_age) probabilities
    SUMMARY.md                     -- side-by-side comparison
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pykin import AGES
from pykin.engine import rates_to_arrays
from pykin.ingest import load_cache
from pykin.orphanhood import annual_summaries, parental_loss_grid_cached


OUT_DIR = PROJECT_ROOT / "results" / "kinship" / "baseline_villaveces"


def run_baseline(race_eth: str = "All"):
    pop, mort, fert = load_cache()
    rates = rates_to_arrays(pop, mort, fert,
                            race_eth=race_eth,
                            years=range(1983, 2022),
                            ages=AGES)

    print(f"[run] race={race_eth}: projecting cohorts and reading parental loss ...")
    grid = parental_loss_grid_cached(
        rates, year_min=2000, year_max=2021, max_focal_age=17,
    )

    summary = annual_summaries(grid, pop, race_eth=race_eth)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = race_eth.replace(" ", "_").replace("/", "-").replace(",", "")
    grid_path = OUT_DIR / f"parental_loss_grid_{suffix}.parquet"
    sum_path  = OUT_DIR / f"annual_summary_{suffix}.csv"
    grid.to_parquet(grid_path, index=False)
    summary.to_csv(sum_path, index=False)
    print(f"[run] wrote {grid_path.name} rows={len(grid):,}")
    print(f"[run] wrote {sum_path.name} rows={len(summary):,}")
    return summary


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--race", default="All", help="race_eth filter")
    args = ap.parse_args()

    s = run_baseline(args.race)
    print()
    print(f"=== Annual summary for race_eth='{args.race}' ===")
    print(s.to_string(index=False, formatters={
        "prevalent": "{:>14,.0f}".format,
        "incident":  "{:>13,.0f}".format,
        "N_children_under18": "{:>14,.0f}".format,
        "prevalence_rate_per_100k": "{:>10,.1f}".format,
    }))

    target_2021 = s.loc[s["focal_year"] == 2021, "prevalent"].iloc[0]
    print()
    print(f"== Headline ==")
    print(f"2021 prevalent parental orphanhood: {target_2021:>12,.0f}")
    print(f"Villaveces 2025 (prevalent orphanhood + caregiver loss, ALL): "
          f"~2,910,000")
    print(f"Note: matrix-kinship parental-only is expected to be lower than "
          f"the Villaveces combined target because we omit grandparent caregiver "
          f"loss.")
