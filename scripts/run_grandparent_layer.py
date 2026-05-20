"""Additive grandparent-caregiver loss layer.

The parent-only kinship model produces ~2.27 M US children with a parent
who died (2021). Villaveces et al. (2025) report ~2.91 M when also
counting children whose custodial grandparent caregiver died -- this gap
(~640 K) is what we add here.

Method (simple flow-stock accounting, NOT matrix kinship)
---------------------------------------------------------
1. ACS S1002 (5-year estimates, US national) gives the annual count of
   *grandparents living with own grandchildren under 18 who are
   responsible for them* (the "skipped-generation" plus the broader
   "co-residing responsible" definitions). For 2010-2021 the broader
   number sits at ~2.5-2.9 M.
2. National adult mortality rates at ages 50-79 from
   data_kinship/cache/mortality_rates.parquet (built by pykin.ingest).
   We average male and female rates and pool ages by 1/(80-50)=1/30.
3. Annual caregiver deaths = caregivers(year) * pooled mort rate(year).
4. Children-per-caregiver multiplier `c_gp` (default 1.7, ACS national
   average across years) converts caregiver deaths to incident
   affected-child events.
5. Average remaining child duration `d_gp` (default 7 years, midpoint of
   the under-18 distribution among children in caregiver households)
   converts annual incident events to a prevalent stock.

Outputs
- results/kinship/grandparent_layer/annual_us.csv
  (year, caregivers, mort_50_79, deaths_per_year, incident_children,
   prevalent_stock)
- results/kinship/grandparent_layer/combined_target.csv
  (year, parental_calibrated, gp_layer, combined, villaveces_target)

This is an order-of-magnitude check, not a full kinship-recurrence
model. It does not use NHIS calibration; it stays at the Villaveces
fertility schedule because NHIS does not observe grandchildren counts
within multi-generation households.

Usage
    python scripts/run_grandparent_layer.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

GP_DIR = PROJECT_ROOT / "data_kinship/data/grandparents/raw"
MORT_PQT = PROJECT_ROOT / "data_kinship/cache/mortality_rates.parquet"
OUT_DIR = PROJECT_ROOT / "results/kinship/grandparent_layer"
CAL_PARENTAL = (PROJECT_ROOT
                / "results/kinship/calibrated_villaveces"
                / "annual_summary_All.csv")


CHILDREN_PER_CAREGIVER = 1.7   # ACS Table S1002 national average 2010-2021
AVG_RESIDUAL_DURATION_Y = 7    # midpoint of under-18 child distribution


# ---------------------------------------------------------------------------
# ACS S1002 parsing -- national-level totals only
# ---------------------------------------------------------------------------

ACS_YEAR_RE = re.compile(r"ACSST5Y(\d{4})\.S1002")


def _parse_acs_count(s: str) -> float | None:
    """Convert '7,239,762' or '12.4%' etc into a float."""
    if not isinstance(s, str):
        return None
    s = s.strip().replace(",", "")
    if s == "" or s == "N":
        return None
    if s.endswith("%"):
        try:
            return float(s[:-1]) / 100
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_acs_year(path: Path) -> dict:
    """Parse one ACS S1002 file. Extract two national counts:

    - total_living_with: grandparents living with own grandchildren under
      18 (row 2 of the "United States" block).
    - responsible_caregivers: grandparents *responsible* for their own
      grandchildren (row 5, inside the "Percent distribution of
      grandparents responsible for grandchildren" subsection).
    """
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    total_col = df.columns[1]
    total_living_with     = _parse_acs_count(df.iloc[2, 1])
    responsible_caregivers = _parse_acs_count(df.iloc[5, 1])
    year_match = ACS_YEAR_RE.search(path.name)
    year = int(year_match.group(1)) if year_match else None
    return {"year":                  year,
            "total_living_with":     total_living_with,
            "responsible_caregivers": responsible_caregivers}


def load_acs_table() -> pd.DataFrame:
    rows = []
    for p in sorted(GP_DIR.glob("ACSST5Y*.csv")):
        rows.append(parse_acs_year(p))
    df = (pd.DataFrame(rows)
             .dropna(subset=["year", "responsible_caregivers"]))
    df = df.sort_values("year").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# National adult mortality at ages 50-79
# ---------------------------------------------------------------------------

def load_pooled_mortality_50_79() -> pd.DataFrame:
    """Mean death rate across ages 50-79 (both sexes) by year."""
    m = pd.read_parquet(MORT_PQT)
    m = m[(m["race_eth"] == "All")
            & m["age"].between(50, 79)].copy()
    pooled = (m.groupby("year", as_index=False)["q"].mean()
                .rename(columns={"q": "mort_50_79"}))
    return pooled


# ---------------------------------------------------------------------------
# Combine
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    acs = load_acs_table()
    print("[gp] ACS years parsed:", acs["year"].tolist())
    print("[gp] ACS sample:")
    print(acs.head().to_string(index=False))

    mort = load_pooled_mortality_50_79()

    # Interpolate ACS caregivers across years 2000-2021 (the kinship engine
    # operates over 2000-2021). The earliest ACS S1002 5-year vintage is
    # 2010; we backfill 2000-2009 with the 2010 value (flat).
    yrs = np.arange(2000, 2022)
    cg = acs.set_index("year")["responsible_caregivers"].reindex(yrs)
    cg = cg.bfill().ffill()
    annual = pd.DataFrame({"year": yrs, "caregivers": cg.values})
    annual = annual.merge(mort, on="year", how="left")
    annual["deaths_per_year"] = annual["caregivers"] * annual["mort_50_79"]
    annual["incident_children"] = (annual["deaths_per_year"]
                                    * CHILDREN_PER_CAREGIVER)
    # Prevalent stock: sum of past incidents that still have residual under-18
    # exposure. Treat each incident as contributing AVG_RESIDUAL_DURATION_Y
    # child-years on average; an exposure of t years ago contributes
    # 1 - t/(2*AVG_RESIDUAL_DURATION_Y) (linear decay over ~2 * duration).
    # Equivalently, stock(y) = sum over s of incident(s) * w(y - s) where
    # w(k) = max(0, 1 - k/(2*AVG_RESIDUAL_DURATION_Y)).
    horizon = 2 * AVG_RESIDUAL_DURATION_Y
    stocks = []
    incident_vals = annual["incident_children"].to_numpy()
    for i, y in enumerate(annual["year"]):
        s = 0.0
        for k in range(min(i + 1, horizon)):
            w = max(0.0, 1.0 - k / horizon)
            s += incident_vals[i - k] * w
        stocks.append(s)
    annual["prevalent_stock"] = stocks
    annual.to_csv(OUT_DIR / "annual_us.csv", index=False)
    print()
    print("[gp] annual_us.csv:")
    print(annual.to_string(index=False, formatters={
        "caregivers":           "{:>14,.0f}".format,
        "mort_50_79":           "{:>10.4f}".format,
        "deaths_per_year":      "{:>14,.0f}".format,
        "incident_children":    "{:>14,.0f}".format,
        "prevalent_stock":      "{:>14,.0f}".format,
    }))

    # Combine with calibrated parental orphanhood
    parental = pd.read_csv(CAL_PARENTAL)
    parental = parental[["focal_year", "prevalent"]].rename(columns={
        "focal_year": "year",
        "prevalent":  "parental_calibrated",
    })
    combo = annual.merge(parental, on="year", how="left")
    combo["combined"] = combo["parental_calibrated"] + combo["prevalent_stock"]
    combo = combo[["year", "parental_calibrated",
                   "prevalent_stock", "combined"]].rename(columns={
        "prevalent_stock": "gp_layer",
    })
    combo["villaveces_target_2021"] = np.where(combo["year"] == 2021,
                                                 2_910_000, np.nan)
    combo.to_csv(OUT_DIR / "combined_target.csv", index=False)
    print()
    print("[gp] combined_target.csv (last 5 years):")
    print(combo.tail(5).to_string(index=False, formatters={
        "parental_calibrated":  "{:>14,.0f}".format,
        "gp_layer":             "{:>14,.0f}".format,
        "combined":             "{:>14,.0f}".format,
        "villaveces_target_2021": "{:>14,.0f}".format,
    }))
    print()
    headline = combo[combo["year"] == 2021].iloc[0]
    print(f"=== 2021 combined: {headline['combined']:,.0f}  "
          f"vs Villaveces target 2.91 M ===")


if __name__ == "__main__":
    main()
