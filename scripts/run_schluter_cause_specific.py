"""Schluter 2024 (JAMA) cause-specific replication: parental drug + firearm
deaths, 1999-2020, recast through NHIS-observed kids-per-decedent.

Approach
--------
The Schluter / Hillis style "cumulative children who experienced a parental
death from cause c during YYYY-YYYY" can be written without invoking a
matrix-kinship recurrence at all. For each year y and parent decedent cell
(age band a, sex s, race-eth r), define

    K_c(a, s, r, y)  = E[ co-resident under-18 children | dies, cell ]

and let D_c(a, s, r, y) be the number of parental deaths from cause c in
that cell from NCHS multiple-cause mortality. The cumulative children
losing a parent to cause c is

    N = sum over y, a, s, r of K_c(a, s, r, y) * D_c(a, s, r, y) .

Two scenarios produce the comparison:
- naive ("kinship-model" equivalent): K is the all-cell average over
  living adults (i.e. E[nk_under18 | alive, cell]) -- assumes a parent who
  dies of drugs or firearms has the same fertility profile as the
  population average.
- nhis: K is the NHIS-observed mean among decedents in that cell,
  E[nk_under18 | died, cell].

The ratio K_naive / K_nhis is essentially kappa_c, but applied here in
*absolute* terms so the cause-specific totals end up on the published
Schluter scale (1.19 M cumulative kids 1999-2020 for drugs+firearms).

Outputs
- results/kinship/schluter_drugs_firearms/cumulative_1999_2020.csv
- results/kinship/schluter_drugs_firearms/annual_by_cause.csv

Usage
    python scripts/run_schluter_cause_specific.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.export_nhis_calibration import (
    AGE_BANDS,
    RACETH5_LABEL,
    build_cells,
)


DEATHS_RDS = PROJECT_ROOT / ("data_kinship/data/NCHS/death/output/"
                              "Allcause_deaths_1983-2021.RDS")
OUT_DIR = PROJECT_ROOT / "results" / "kinship" / "schluter_drugs_firearms"
PARQUET = PROJECT_ROOT / "nhis_with_coresident_minors.parquet"


# ICD-10 prefixes
DRUG_RE = re.compile(r"^(X4[0-4]|X6[0-4]|X85|Y1[0-4])")        # poisoning by drugs
FIREARM_RE = re.compile(
    r"^(W3[2-4]|X7[2-4]|X9[3-5]|Y2[2-4]|Y35\.?0)"             # any intent
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def classify_cause(code: str) -> str:
    """Return 'drug', 'firearm', or 'other'."""
    if not isinstance(code, str) or not code:
        return "other"
    if DRUG_RE.match(code):
        return "drug"
    if FIREARM_RE.match(code):
        return "firearm"
    return "other"


def age_to_band(age: int) -> str | None:
    for lo, hi in AGE_BANDS:
        if lo <= age <= hi:
            return f"{lo}-{hi}"
    return None


# Map NCHS 5-year-band strings (e.g. "25-29") onto the broader NHIS
# calibration bands (e.g. "20-29"). NCHS strings come straight off the
# deaths RDS; bands outside the kappa universe map to None.
def nchs_band_to_kappa_band(s: str | None) -> str | None:
    if s is None or not isinstance(s, str):
        return None
    s = s.strip()
    if s == "15-19":
        return "18-29"
    if s in {"20-24", "25-29"}:
        return "18-29"
    if s in {"30-34", "35-39"}:
        return "30-39"
    if s in {"40-44", "45-49"}:
        return "40-49"
    if s in {"50-54", "55-59"}:
        return "50-59"
    if s in {"60-64", "65-69"}:
        return "60-69"
    if s in {"70-74", "75-79"}:
        return "70-100"
    return None


# Crude single-age proxy from an NCHS 5-year-band string. Used only to
# convert the band into an integer age range for filtering 15-79 adults.
def nchs_band_to_midpoint(s: str | None) -> int | None:
    if s is None or not isinstance(s, str):
        return None
    s = s.strip()
    if s in {"0-14"}:
        return 7
    if s in {"100+"}:
        return 100
    try:
        lo, hi = s.split("-")
        return (int(lo) + int(hi)) // 2
    except Exception:
        return None


def year_to_decade(year: int) -> int | None:
    """Map calendar year to the canonical NHIS calibration decade index.

    Years 2019-2020 are clamped to decade 4 (2010-2018) since that is the
    most recent decade with NHIS calibration support; this is a known
    extrapolation choice.
    """
    if 1986 <= year <= 1989:
        return 1
    if 1990 <= year <= 1999:
        return 2
    if 2000 <= year <= 2009:
        return 3
    if year >= 2010:
        return 4
    return None


RACE_ETH_TO_RACETH5 = {
    "Hispanic":           1,
    "Non-Hispanic White": 2,
    "Non-Hispanic Black": 3,
    "Non-Hispanic Asian": 4,
    "Non-Hispanic American Indian or Alaska Native": 5,
}


# ---------------------------------------------------------------------------
# Step 1: NHIS-observed kids-per-decedent and kids-per-living-adult by cell
# ---------------------------------------------------------------------------

def build_K_tables() -> pd.DataFrame:
    """Compute E[nk_under18 | died, cell] and E[nk_under18 | alive, cell]
    across (sex, raceth5, age_band, yeardec).
    """
    raw = pd.read_parquet(PARQUET)
    df = build_cells(raw)

    df["w_nk"] = df["mortwtsa"] * df["nk_under18"]
    grouped = (df.groupby(["sex", "raceth5", "age_band", "yeardec", "died"],
                          observed=True)
                 .agg(sum_w_nk=("w_nk", "sum"),
                      sum_w=("mortwtsa", "sum"),
                      n_rows=("nk_under18", "size"))
                 .reset_index())
    grouped["mean_nk"] = np.where(grouped["sum_w"] > 0,
                                   grouped["sum_w_nk"] / grouped["sum_w"], np.nan)

    wide = grouped.pivot_table(index=["sex", "raceth5", "age_band", "yeardec"],
                                columns="died",
                                values=["mean_nk", "n_rows"])
    wide.columns = [f"{a}_{int(b)}" for a, b in wide.columns]
    wide = wide.reset_index()

    # Smooth sparse death cells toward the (sex, raceth5, yeardec) mean.
    grp = (wide.groupby(["sex", "raceth5", "yeardec"], as_index=False)
                .agg(mean_died_grp=("mean_nk_1", "mean")))
    wide = wide.merge(grp, on=["sex", "raceth5", "yeardec"], how="left")
    sparse = wide["n_rows_1"].fillna(0) < 25
    wide["K_died"] = np.where(sparse,
                               wide["mean_died_grp"],
                               wide["mean_nk_1"])
    wide["K_died"] = wide["K_died"].fillna(wide["mean_died_grp"]).fillna(0.0)
    wide["K_alive"] = wide["mean_nk_0"].fillna(0.0)
    return wide[["sex", "raceth5", "age_band", "yeardec", "K_died", "K_alive"]]


# ---------------------------------------------------------------------------
# Step 2: cause-specific parental deaths from the NCHS file
# ---------------------------------------------------------------------------

def load_cause_specific_deaths() -> pd.DataFrame:
    """Return the deaths file filtered to ages 15-79 and 1999-2020 with a
    cause label attached.
    """
    print("[schluter] loading NCHS Allcause_deaths_1983-2021.RDS ...")
    d = pyreadr.read_r(str(DEATHS_RDS))
    df = list(d.values())[0]
    df = df[(df["year"] >= 1999) & (df["year"] <= 2020)].copy()
    df["age_mid"] = df["age"].apply(nchs_band_to_midpoint)
    df = df.dropna(subset=["age_mid"])
    df["age_mid"] = df["age_mid"].astype(int)
    df = df[(df["age_mid"] >= 15) & (df["age_mid"] <= 79)]
    df = df[df["race.eth"].isin(RACE_ETH_TO_RACETH5.keys())].copy()
    df["cause"] = df["single.code"].apply(classify_cause)
    df = df[df["cause"].isin(["drug", "firearm"])]
    df["raceth5"] = df["race.eth"].map(RACE_ETH_TO_RACETH5).astype(int)
    df["sex"] = df["sex"].map({"Female": "f", "Male": "m",
                                 "F": "f", "M": "m"})
    df["age_band"] = df["age"].apply(nchs_band_to_kappa_band)
    df["yeardec"] = df["year"].apply(year_to_decade)
    df = df.dropna(subset=["age_band", "yeardec", "sex"])
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").fillna(0)
    deaths_cell = (df.groupby(["cause", "year", "sex", "raceth5",
                                 "age_band", "yeardec"], observed=True)
                     ["deaths"].sum().reset_index())
    print(f"[schluter]   cause-specific cells (1999-2020): {len(deaths_cell):,}")
    return deaths_cell


# ---------------------------------------------------------------------------
# Step 3: combine
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    Ktab = build_K_tables()
    deaths = load_cause_specific_deaths()

    merged = deaths.merge(Ktab,
                           on=["sex", "raceth5", "age_band", "yeardec"],
                           how="left")
    miss = merged["K_died"].isna().sum()
    if miss:
        print(f"[schluter] WARN {miss} cause-specific cells have no NHIS K "
              f"value -- defaulting to 0")
    merged["K_died"] = merged["K_died"].fillna(0.0)
    merged["K_alive"] = merged["K_alive"].fillna(0.0)

    merged["children_nhis"]  = merged["deaths"] * merged["K_died"]
    merged["children_naive"] = merged["deaths"] * merged["K_alive"]

    # Annual aggregate by cause
    annual = (merged.groupby(["cause", "year"])[["deaths",
                                                   "children_nhis",
                                                   "children_naive"]]
                       .sum().reset_index())
    annual["delta_pct"] = 100.0 * ((annual["children_nhis"]
                                     - annual["children_naive"])
                                    / annual["children_naive"])
    annual.to_csv(OUT_DIR / "annual_by_cause.csv", index=False)
    print(f"[schluter] wrote {OUT_DIR.relative_to(PROJECT_ROOT)}/"
          f"annual_by_cause.csv")

    # Cumulative 1999-2020 totals by cause and race
    cum_race = (merged.groupby(["cause", "raceth5"])[["deaths",
                                                        "children_nhis",
                                                        "children_naive"]]
                         .sum().reset_index())
    cum_race["race_eth"] = cum_race["raceth5"].map(RACETH5_LABEL)
    cum_race = cum_race[["cause", "race_eth", "deaths",
                         "children_naive", "children_nhis"]]
    cum_race["delta_pct"] = 100.0 * ((cum_race["children_nhis"]
                                       - cum_race["children_naive"])
                                       / cum_race["children_naive"])
    cum_race.to_csv(OUT_DIR / "cumulative_1999_2020_by_race.csv", index=False)

    # Cumulative totals by cause across all groups
    cum_all = (merged.groupby("cause")[["deaths",
                                          "children_nhis",
                                          "children_naive"]]
                       .sum().reset_index())
    combined = pd.DataFrame({
        "cause":            ["drug+firearm combined"],
        "deaths":           [cum_all["deaths"].sum()],
        "children_naive":   [cum_all["children_naive"].sum()],
        "children_nhis":    [cum_all["children_nhis"].sum()],
    })
    cum_all = pd.concat([cum_all, combined], ignore_index=True)
    cum_all["delta_pct"] = 100.0 * ((cum_all["children_nhis"]
                                       - cum_all["children_naive"])
                                       / cum_all["children_naive"])
    cum_all.to_csv(OUT_DIR / "cumulative_1999_2020.csv", index=False)

    print()
    print("=== Cumulative 1999-2020, all races ===")
    print(cum_all.to_string(index=False, formatters={
        "deaths":          "{:>13,.0f}".format,
        "children_naive":  "{:>13,.0f}".format,
        "children_nhis":   "{:>13,.0f}".format,
        "delta_pct":       "{:>+7.1f}".format,
    }))
    print()
    print("Schluter 2024 (JAMA) published target: 1,190,000 cumulative US "
          "children losing a parent to drugs+firearms 1999-2020.")


if __name__ == "__main__":
    main()
