"""Schluter 2024 (JAMA) calibration using the detailed NHIS-LMF MORTUCOD
underlying-cause variable.

IPUMS publishes MORTUCOD as a 3-digit NCHS-style cause recode harmonized
across the ICD-9 (NHIS samples 1986-1998) and ICD-10 (NHIS samples
1999-2004) eras; coverage is the sample year, not the death year. The
relevant codes for the Schluter drug + firearm target are:

    119  Accidental discharge of firearms       (ICD-10 W32-W34)
    122  Accidental poisoning                   (ICD-10 X40-X49)*
    125  Suicide by discharge of firearms       (ICD-10 X72-X74)
    126  Suicide by other or means              (ICD-10 X60-X84)**
    128  Homicide by firearm discharge          (ICD-10 X93-X95)
    129  Homicide by other means                (ICD-10 X85-X92)**
    132  Firearm discharge, unknown intent      (ICD-10 Y22-Y24)
    130  Legal intervention                     (ICD-10 Y35-Y36)  (excluded)

    *  122 lumps drug overdose with other non-drug accidental poisoning
       (e.g. carbon monoxide). Most of the bucket is drug-overdose.
    ** Drug suicide and drug homicide hide inside 126 and 129 with the
       non-drug methods. We use 126 / 129 K only as a noisy proxy for
       the drug-suicide / drug-homicide subset in the BROAD scenario.

NHIS sample
-----------
Pooled across all NHIS-LMF death events with non-NIU MORTUCOD. The
harmonized integer recode lets us pool the ICD-9 and ICD-10 era sample
respondents into a single K estimate. Sample size: ~700 decedents in
the drug bucket and ~1,500 in the firearm bucket.

NCHS scope -- two scenarios
---------------------------
NARROW (apples-to-apples with NHIS bucket definitions):
    drug    = NCHS single.code in X40-X49           (~803 K deaths)
    firearm = NCHS single.code in W32-W34, X72-X74, X93-X95, Y22-Y24
                                                    (~683 K deaths)

BROAD (matches Schluter's 1.19 M target denominator):
    drug    = X40-X44 (accidental, NHIS K_122)
            + Y10-Y14 (undetermined, NHIS K_122)
            + X60-X64 (suicide, NHIS K_126, noisy proxy)
            + X85     (homicide, NHIS K_129, noisy proxy)
    firearm = same as NARROW (Y35.0 legal intervention excluded
                                because it is not in our NHIS firearm
                                bucket).

Outputs
- results/kinship/schluter_drugs_firearms/mortucod_K_tables.csv
- results/kinship/schluter_drugs_firearms/mortucod_cumulative_1999_2020.csv

Usage
    python scripts/run_schluter_mortucod.py
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

from scripts.export_nhis_calibration import (AGE_BANDS, RACETH5_LABEL,
                                              build_cells)
from scripts.run_schluter_cause_specific import (
    DEATHS_RDS, RACE_ETH_TO_RACETH5,
    nchs_band_to_kappa_band, nchs_band_to_midpoint,
)

PARQUET = PROJECT_ROOT / "nhis_with_coresident_minors.parquet"
OUT_DIR = PROJECT_ROOT / "results" / "kinship" / "schluter_drugs_firearms"


# NHIS MORTUCOD integer codes used to define K buckets.
NHIS_BUCKETS = {
    "drug":          {122},
    "firearm":       {119, 125, 128, 132},
    "suicide_other": {126},
    "homicide_other": {129},
}

# ICD-10 -> (NCHS scope label, NHIS K bucket to apply) for the BROAD
# Schluter-style mapping.
ICD10_BROAD = [
    (re.compile(r"^X4[0-4]"),                  "drug",    "drug"),
    (re.compile(r"^Y1[0-4]"),                  "drug",    "drug"),
    (re.compile(r"^X6[0-4]"),                  "drug",    "suicide_other"),
    (re.compile(r"^X85"),                      "drug",    "homicide_other"),
    (re.compile(r"^(W3[2-4])"),                "firearm", "firearm"),
    (re.compile(r"^(X7[2-4])"),                "firearm", "firearm"),
    (re.compile(r"^(X9[3-5])"),                "firearm", "firearm"),
    (re.compile(r"^(Y2[2-4])"),                "firearm", "firearm"),
]

# NARROW: NHIS bucket definitions verbatim.
ICD10_NARROW = [
    (re.compile(r"^X4[0-9]"),                  "drug",    "drug"),
    (re.compile(r"^(W3[2-4])"),                "firearm", "firearm"),
    (re.compile(r"^(X7[2-4])"),                "firearm", "firearm"),
    (re.compile(r"^(X9[3-5])"),                "firearm", "firearm"),
    (re.compile(r"^(Y2[2-4])"),                "firearm", "firearm"),
]


def classify_icd10(code: str, table) -> tuple[str | None, str | None]:
    """Return (scope_label, K_bucket) or (None, None) if no match."""
    if not isinstance(code, str):
        return (None, None)
    for rx, scope, bucket in table:
        if rx.match(code):
            return (scope, bucket)
    return (None, None)


# ---------------------------------------------------------------------------
# K tables from NHIS-LMF using MORTUCOD (pooled across all eras)
# ---------------------------------------------------------------------------

def build_K_pooled() -> pd.DataFrame:
    """Compute K(cell, bucket) pooled across all NHIS-LMF decedents with
    a non-NIU MORTUCOD value.
    """
    raw = pd.read_parquet(PARQUET)
    if "mortucod" not in raw.columns:
        sys.exit(
            "[mortucod] mortucod column not found in parquet. "
            "Re-extract NHIS with MORTUCOD per IPUMS_EXTRACT_INSTRUCTIONS.md "
            "and rerun scripts/nhis_coresident_minors.py first."
        )
    df = build_cells(raw)
    df["mortucod"] = raw.loc[df.index, "mortucod"].astype("Int16")

    df["bucket"] = pd.NA
    df.loc[df["died"] == 0, "bucket"] = "alive"
    for name, codes in NHIS_BUCKETS.items():
        df.loc[(df["died"] == 1) & (df["mortucod"].isin(codes)),
                 "bucket"] = name
    df = df.dropna(subset=["bucket"]).copy()
    df["w_nk"] = df["mortwtsa"] * df["nk_under18"]

    cell = (df.groupby(["sex", "raceth5", "age_band", "bucket"],
                         observed=True)
                 .agg(sum_w_nk=("w_nk", "sum"),
                      sum_w=("mortwtsa", "sum"),
                      n_rows=("nk_under18", "size"))
                 .reset_index())
    cell["K"] = np.where(cell["sum_w"] > 0,
                          cell["sum_w_nk"] / cell["sum_w"], np.nan)

    # Smooth: sparse cells (< 25 raw rows) -> (sex, raceth5, bucket) mean
    # -> overall bucket mean.
    pool = (cell.assign(num=cell["K"] * cell["sum_w"])
                 .groupby(["sex", "raceth5", "bucket"],
                           observed=True, as_index=False)
                 .agg(num=("num", "sum"), den=("sum_w", "sum")))
    pool["K_pool"] = np.where(pool["den"] > 0, pool["num"] / pool["den"],
                                np.nan)
    cell = cell.merge(pool[["sex", "raceth5", "bucket", "K_pool"]],
                       on=["sex", "raceth5", "bucket"], how="left")

    bucket_mean = (cell.assign(num=cell["K"] * cell["sum_w"])
                          .groupby("bucket", observed=True, as_index=False)
                          .agg(num=("num", "sum"), den=("sum_w", "sum")))
    bucket_mean["K_bucket"] = np.where(bucket_mean["den"] > 0,
                                         bucket_mean["num"]
                                         / bucket_mean["den"], 0.0)
    cell = cell.merge(bucket_mean[["bucket", "K_bucket"]],
                       on="bucket", how="left")
    sparse = cell["n_rows"].fillna(0) < 25
    cell["K_smooth"] = np.where(sparse, cell["K_pool"], cell["K"])
    cell["K_smooth"] = (cell["K_smooth"].fillna(cell["K_pool"])
                                          .fillna(cell["K_bucket"]))
    return cell[["sex", "raceth5", "age_band", "bucket",
                  "K_smooth", "n_rows"]]


# ---------------------------------------------------------------------------
# NCHS deaths split by scope and K bucket
# ---------------------------------------------------------------------------

def load_nchs_deaths(table) -> pd.DataFrame:
    import pyreadr
    print("[mortucod] loading NCHS deaths 1999-2020 ...")
    d = pyreadr.read_r(str(DEATHS_RDS))
    df = list(d.values())[0]
    df = df[(df["year"] >= 1999) & (df["year"] <= 2020)].copy()
    df["age_mid"] = df["age"].apply(nchs_band_to_midpoint)
    df = df.dropna(subset=["age_mid"])
    df["age_mid"] = df["age_mid"].astype(int)
    df = df[(df["age_mid"] >= 15) & (df["age_mid"] <= 79)]
    df = df[df["race.eth"].isin(RACE_ETH_TO_RACETH5.keys())].copy()
    cls = df["single.code"].apply(lambda c: classify_icd10(c, table))
    df["scope"]  = cls.apply(lambda t: t[0])
    df["bucket"] = cls.apply(lambda t: t[1])
    df = df.dropna(subset=["scope"])
    df["raceth5"]  = df["race.eth"].map(RACE_ETH_TO_RACETH5).astype(int)
    df["sex"]      = df["sex"].map({"Female": "f", "Male": "m"})
    df["age_band"] = df["age"].apply(nchs_band_to_kappa_band)
    df = df.dropna(subset=["age_band", "sex"])
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").fillna(0)
    cell = (df.groupby(["scope", "bucket", "year", "sex", "raceth5",
                          "age_band"], observed=True)
                ["deaths"].sum().reset_index())
    return cell


# ---------------------------------------------------------------------------
# Combine NCHS deaths with NHIS K and total
# ---------------------------------------------------------------------------

def apply_K(nchs: pd.DataFrame, K: pd.DataFrame) -> pd.DataFrame:
    """Merge each NCHS-death cell with the matching NHIS K (by bucket)
    and the alive K_naive."""
    K_b = K.copy()
    K_alive = (K_b[K_b["bucket"] == "alive"]
                  [["sex", "raceth5", "age_band", "K_smooth"]]
                  .rename(columns={"K_smooth": "K_alive"}))
    K_use = K_b[K_b["bucket"] != "alive"][[
                 "sex", "raceth5", "age_band", "bucket", "K_smooth"]]
    m = nchs.merge(K_use, on=["sex", "raceth5", "age_band", "bucket"],
                     how="left")
    m = m.merge(K_alive, on=["sex", "raceth5", "age_band"], how="left")
    for c in ["K_smooth", "K_alive"]:
        m[c] = m[c].fillna(0.0)
    m["children_nhis"]  = m["deaths"] * m["K_smooth"]
    m["children_naive"] = m["deaths"] * m["K_alive"]
    return m


def cum_table(m: pd.DataFrame, scenario_label: str) -> pd.DataFrame:
    s = (m.groupby("scope")[["deaths", "children_naive", "children_nhis"]]
           .sum().reset_index().rename(columns={
               "scope": "cause", "children_nhis": f"children_{scenario_label}"
           }))
    total = pd.DataFrame({
        "cause": ["drug+firearm combined"],
        "deaths": [s["deaths"].sum()],
        "children_naive": [s["children_naive"].sum()],
        f"children_{scenario_label}": [s[f"children_{scenario_label}"].sum()],
    })
    return pd.concat([s, total], ignore_index=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _pooled_K(K: pd.DataFrame) -> pd.Series:
    return (K.groupby("bucket")
              .apply(lambda d: float(np.average(d["K_smooth"],
                                                  weights=d["n_rows"]
                                                           .fillna(0)
                                                           .clip(lower=1))),
                      include_groups=False))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    K = build_K_pooled()
    K.to_csv(OUT_DIR / "mortucod_K_tables.csv", index=False)

    print()
    print("[mortucod] Pooled K by bucket (NHIS 1986-2004 sample, all years):")
    print(_pooled_K(K).round(3))

    nchs_narrow = load_nchs_deaths(ICD10_NARROW)
    nchs_broad  = load_nchs_deaths(ICD10_BROAD)
    print(f"[mortucod]   NCHS rows narrow: {len(nchs_narrow):,}")
    print(f"[mortucod]   NCHS rows broad:  {len(nchs_broad):,}")

    m_narrow = apply_K(nchs_narrow, K)
    m_broad  = apply_K(nchs_broad,  K)

    cum_n = cum_table(m_narrow, "narrow")
    cum_b = cum_table(m_broad,  "broad")
    cum = cum_n.merge(cum_b[["cause", "children_broad"]],
                       on="cause", how="left")
    cum = cum.rename(columns={
        "deaths": "deaths_narrow",
        "children_naive": "naive_narrow",
    })
    cum["deaths_broad"] = cum["cause"].map(
        cum_b.set_index("cause")["deaths"])
    cum["naive_broad"]  = cum["cause"].map(
        cum_b.set_index("cause")["children_naive"])

    cum["delta_pct_narrow"] = (100.0
                                 * (cum["children_narrow"]
                                      - cum["naive_narrow"])
                                 / cum["naive_narrow"])
    cum["delta_pct_broad"]  = (100.0
                                 * (cum["children_broad"]
                                      - cum["naive_broad"])
                                 / cum["naive_broad"])

    # Append prior scenarios for comparison
    try:
        prior_all = (pd.read_csv(OUT_DIR / "cumulative_1999_2020.csv")
                       .set_index("cause")["children_nhis"])
        cum["children_prior_allcause_kappa"] = (cum["cause"]
                                                  .map(prior_all)
                                                  .astype(float))
    except FileNotFoundError:
        pass
    try:
        prior_strat = (pd.read_csv(
                         OUT_DIR / "cumulative_1999_2020_cause_stratified.csv")
                       .set_index("cause")["children_nhis_stratified"])
        cum["children_prior_intent_stratified"] = (cum["cause"]
                                                     .map(prior_strat)
                                                     .astype(float))
    except FileNotFoundError:
        pass

    cum.to_csv(OUT_DIR / "mortucod_cumulative_1999_2020.csv", index=False)

    print()
    print("=== NARROW scope (NCHS bucket = NHIS bucket; apples-to-apples) ===")
    show_n = cum[["cause", "deaths_narrow", "naive_narrow",
                  "children_narrow", "delta_pct_narrow"]].copy()
    print(show_n.to_string(index=False, formatters={
        "deaths_narrow":      "{:>13,.0f}".format,
        "naive_narrow":       "{:>13,.0f}".format,
        "children_narrow":    "{:>13,.0f}".format,
        "delta_pct_narrow":   "{:>+7.1f}".format,
    }))
    print()
    print("=== BROAD scope (matches Schluter 1.19 M denominator) ===")
    show_b = cum[["cause", "deaths_broad", "naive_broad",
                  "children_broad", "delta_pct_broad"]].copy()
    print(show_b.to_string(index=False, formatters={
        "deaths_broad":       "{:>13,.0f}".format,
        "naive_broad":        "{:>13,.0f}".format,
        "children_broad":     "{:>13,.0f}".format,
        "delta_pct_broad":    "{:>+7.1f}".format,
    }))
    print()
    print("Schluter 2024 (JAMA) published target: ~1,190,000 cumulative.")
    print()
    print("BROAD applies NHIS K_122 (accidental poisoning) to X40-X44 and "
          "Y10-Y14 NCHS deaths, K_126 to X60-X64 (drug suicide), and K_129 "
          "to X85 (drug homicide). The 126/129 buckets pool drug- and "
          "non-drug methods so the BROAD drug K is a noisy proxy.")


if __name__ == "__main__":
    main()
