"""Schluter 2024 (JAMA) calibration using the detailed NHIS-LMF MORTUCOD
underlying-cause field (1986-2004 only) instead of the 10-category
MORTUCODLD recode.

Requires `mortucod` to be present in nhis_with_coresident_minors.parquet.
See IPUMS_EXTRACT_INSTRUCTIONS.md for how to add it. If `mortucod` is
absent the script exits with a friendly error.

Strategy
--------
1. Build NHIS-derived kids-per-decedent K's for two ICD eras separately
   (sensitivity check on the "effect is constant over time" assumption):

       ICD-10 era: NHIS-LMF 1999-2004 (NDI release allowed detail then)
       ICD-9  era: NHIS-LMF 1986-1998 (different code system, mapped
                   onto the E-code drug + firearm ranges)

   For each era we compute, at the (sex x raceth5 x age_band) cell level,

       K(cell, cause)   = E[nk_under18 | died, cell, cause = c]
       K_alive(cell)    = E[nk_under18 | alive, cell]

   where `cause` in {drug, firearm}. Cells with fewer than 25 raw
   death rows are pooled toward the (sex, raceth5, cause) mean.

2. Pull NCHS 1999-2020 deaths from drug or firearm causes via the same
   ICD-10 classifier used in `scripts/run_schluter_cause_specific.py`.

3. For each year 1999-2020 and each death cell apply the matching ICD-10
   era K (from step 1) and sum. We *do not* apply the ICD-9 era K to
   NCHS deaths -- ICD-9 K is reported only as a sensitivity check.

4. Report side by side:
     - naive (kids per living adult, cell-level)
     - all-cause kappa K  (from run_schluter_cause_specific.py)
     - intent-stratified K (from run_schluter_cause_stratified.py)
     - MORTUCOD ICD-10 era K (this script's headline)
     - MORTUCOD ICD-9  era K (sensitivity)

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
    nchs_band_to_kappa_band, nchs_band_to_midpoint, year_to_decade,
)

PARQUET = PROJECT_ROOT / "nhis_with_coresident_minors.parquet"
OUT_DIR = PROJECT_ROOT / "results" / "kinship" / "schluter_drugs_firearms"


# ---------------------------------------------------------------------------
# ICD code regexes
# ---------------------------------------------------------------------------

# IPUMS MORTUCOD is a 4-character string. For ICD-10 it is e.g. "X420"
# (with trailing 0 for the 4th digit when there is no subcategory).
# For ICD-9 external-cause codes the field begins with "E" e.g. "E850".

# ICD-10 (NHIS 1999-2004; NCHS 1999-2020)
ICD10_DRUG_RE = re.compile(r"^(X4[0-4]|X6[0-4]|X85|Y1[0-4])")
ICD10_FIRE_RE = re.compile(r"^(W3[2-4]|X7[2-4]|X9[3-5]|Y2[2-4]|Y350)")

# ICD-9 (NHIS 1986-1998)
# Accidental drug:           E850-E858
# Drug suicide:              E950.0-E950.5  -> as 4-digit: E9500-E9505
# Drug assault:              E962.0         -> as 4-digit: E9620
# Drug undetermined:         E980.0-E980.5  -> as 4-digit: E9800-E9805
# Firearm accidental:        E922(.x)
# Firearm suicide:           E955.0-E955.4
# Firearm assault:           E965.0-E965.4
# Firearm undetermined:      E985.0-E985.4
# Firearm legal:             E970
ICD9_DRUG_RE = re.compile(
    r"^(E85[0-8]|E950[0-5]|E9620|E980[0-5])"
)
ICD9_FIRE_RE = re.compile(
    r"^(E922|E955[0-4]|E965[0-4]|E985[0-4]|E970)"
)


def classify_cause(code: str, era: str) -> str | None:
    if not isinstance(code, str):
        return None
    if era == "icd10":
        if ICD10_DRUG_RE.match(code): return "drug"
        if ICD10_FIRE_RE.match(code): return "firearm"
    elif era == "icd9":
        if ICD9_DRUG_RE.match(code):  return "drug"
        if ICD9_FIRE_RE.match(code):  return "firearm"
    return None


# ---------------------------------------------------------------------------
# K tables from NHIS-LMF using mortucod
# ---------------------------------------------------------------------------

def build_K_mortucod(era: str) -> pd.DataFrame:
    """Compute K(cell, cause) for one ICD era.

    era in {"icd9", "icd10"}.
        icd10  -> NHIS deaths in 1999-2004 (mortdody)
        icd9   -> NHIS deaths in 1986-1998
    """
    raw = pd.read_parquet(PARQUET)
    if "mortucod" not in raw.columns:
        sys.exit(
            "[mortucod] mortucod column not found in parquet. "
            "Re-extract NHIS with MORTUCOD per IPUMS_EXTRACT_INSTRUCTIONS.md "
            "and rerun scripts/nhis_coresident_minors.py first."
        )
    df = build_cells(raw)
    df["mortucod"] = raw.loc[df.index, "mortucod"]
    df["mortdody"] = raw.loc[df.index, "mortdody"]

    if era == "icd10":
        year_window = (df["mortdody"] >= 1999) & (df["mortdody"] <= 2004)
    elif era == "icd9":
        year_window = (df["mortdody"] >= 1986) & (df["mortdody"] <= 1998)
    else:
        raise ValueError(era)

    df["died_in_era"] = (df["died"] == 1) & year_window
    df["cause"] = df.loc[df["died_in_era"], "mortucod"].apply(
        lambda c: classify_cause(c, era=era))
    # Living adults are reused across eras for the naive comparison.
    df["bucket"] = pd.NA
    df.loc[df["died"] == 0, "bucket"] = "alive"
    df.loc[df["cause"] == "drug",    "bucket"] = "drug"
    df.loc[df["cause"] == "firearm", "bucket"] = "firearm"
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

    # Smooth sparse drug/firearm cells toward (sex, raceth5, bucket) mean.
    pool = (cell.assign(num=cell["K"] * cell["sum_w"])
                 .groupby(["sex", "raceth5", "bucket"],
                           observed=True, as_index=False)
                 .agg(num=("num", "sum"), den=("sum_w", "sum")))
    pool["K_pool"] = np.where(pool["den"] > 0, pool["num"] / pool["den"],
                                np.nan)
    cell = cell.merge(pool[["sex", "raceth5", "bucket", "K_pool"]],
                       on=["sex", "raceth5", "bucket"], how="left")
    sparse = cell["n_rows"].fillna(0) < 25
    cell["K_smooth"] = np.where(sparse, cell["K_pool"], cell["K"])
    cell["K_smooth"] = (cell["K_smooth"].fillna(cell["K_pool"])
                                          .fillna(0.0))
    cell["era"] = era
    return cell[["era", "sex", "raceth5", "age_band", "bucket",
                  "K_smooth", "n_rows"]]


# ---------------------------------------------------------------------------
# NCHS cause-specific deaths (1999-2020 only -- ICD-10 era applicable)
# ---------------------------------------------------------------------------

def load_nchs_drug_firearm_deaths() -> pd.DataFrame:
    """Reuse the loader from run_schluter_cause_specific.py."""
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
    df["cause"]   = df["single.code"].apply(
        lambda c: classify_cause(c, era="icd10"))
    df = df.dropna(subset=["cause"])
    df["raceth5"] = df["race.eth"].map(RACE_ETH_TO_RACETH5).astype(int)
    df["sex"]     = df["sex"].map({"Female": "f", "Male": "m"})
    df["age_band"] = df["age"].apply(nchs_band_to_kappa_band)
    df["yeardec"]  = df["year"].apply(year_to_decade)
    df = df.dropna(subset=["age_band", "yeardec", "sex"])
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").fillna(0)
    cell = (df.groupby(["cause", "year", "sex", "raceth5",
                          "age_band"], observed=True)
                ["deaths"].sum().reset_index())
    print(f"[mortucod]   NCHS cause x cell rows: {len(cell):,}")
    return cell


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    K_icd10 = build_K_mortucod("icd10")
    K_icd9  = build_K_mortucod("icd9")
    K_tab = pd.concat([K_icd10, K_icd9], ignore_index=True)
    K_tab.to_csv(OUT_DIR / "mortucod_K_tables.csv", index=False)

    # National-pooled K by era and bucket
    def _pooled(era_K):
        # Weight by n_rows (raw counts) -- equivalent to the sum_w-weighted
        # mean across cells with raw N as a proxy.
        return (era_K.groupby("bucket")
                       .apply(lambda d: float(np.average(d["K_smooth"],
                                                          weights=d["n_rows"]
                                                                   .fillna(0)
                                                                   .clip(lower=1))),
                              include_groups=False))

    print()
    print("[mortucod] Pooled K by era and bucket:")
    print("  ICD-10 (NHIS 1999-2004):")
    print(_pooled(K_icd10).round(3))
    print()
    print("  ICD-9 (NHIS 1986-1998), sensitivity check:")
    print(_pooled(K_icd9).round(3))

    nchs = load_nchs_drug_firearm_deaths()

    # Apply ICD-10 era K to NCHS 1999-2020 deaths (the headline)
    K10_drug = (K_icd10[K_icd10["bucket"] == "drug"]
                  [["sex", "raceth5", "age_band", "K_smooth"]]
                  .rename(columns={"K_smooth": "K_drug"}))
    K10_fire = (K_icd10[K_icd10["bucket"] == "firearm"]
                  [["sex", "raceth5", "age_band", "K_smooth"]]
                  .rename(columns={"K_smooth": "K_firearm"}))
    K10_aliv = (K_icd10[K_icd10["bucket"] == "alive"]
                  [["sex", "raceth5", "age_band", "K_smooth"]]
                  .rename(columns={"K_smooth": "K_alive"}))

    merged = nchs.merge(K10_drug, on=["sex", "raceth5", "age_band"],
                          how="left")
    merged = merged.merge(K10_fire, on=["sex", "raceth5", "age_band"],
                            how="left")
    merged = merged.merge(K10_aliv, on=["sex", "raceth5", "age_band"],
                            how="left")
    for c in ["K_drug", "K_firearm", "K_alive"]:
        merged[c] = merged[c].fillna(0.0)
    merged["K_use"] = np.where(merged["cause"] == "drug",
                                 merged["K_drug"], merged["K_firearm"])
    merged["children_nhis_mortucod"] = merged["deaths"] * merged["K_use"]
    merged["children_naive"] = merged["deaths"] * merged["K_alive"]

    cum = (merged.groupby("cause")[["deaths",
                                        "children_naive",
                                        "children_nhis_mortucod"]]
                     .sum().reset_index())
    combined = pd.DataFrame({
        "cause": ["drug+firearm combined"],
        "deaths": [cum["deaths"].sum()],
        "children_naive": [cum["children_naive"].sum()],
        "children_nhis_mortucod": [cum["children_nhis_mortucod"].sum()],
    })
    cum = pd.concat([cum, combined], ignore_index=True)
    cum["delta_pct_vs_naive"] = (100.0
                                  * (cum["children_nhis_mortucod"]
                                       - cum["children_naive"])
                                  / cum["children_naive"])

    # Append the prior scenarios from the all-cause kappa and intent
    # stratified runs so the table is single-row-per-cause comparison.
    try:
        prior_all = (pd.read_csv(OUT_DIR / "cumulative_1999_2020.csv")
                        .set_index("cause")["children_nhis"])
        cum["children_nhis_allcause_kappa"] = (cum["cause"]
                                                 .map(prior_all).astype(float))
    except FileNotFoundError:
        pass
    try:
        prior_strat = (pd.read_csv(
            OUT_DIR / "cumulative_1999_2020_cause_stratified.csv")
                        .set_index("cause")["children_nhis_stratified"])
        cum["children_nhis_intent_stratified"] = (cum["cause"]
                                                    .map(prior_strat)
                                                    .astype(float))
    except FileNotFoundError:
        pass

    cum.to_csv(OUT_DIR / "mortucod_cumulative_1999_2020.csv", index=False)

    print()
    print("=== Cumulative 1999-2020, cause-specific MORTUCOD K (ICD-10 era) ===")
    print(cum.to_string(index=False, formatters={
        "deaths":                            "{:>13,.0f}".format,
        "children_naive":                    "{:>13,.0f}".format,
        "children_nhis_allcause_kappa":      "{:>13,.0f}".format,
        "children_nhis_intent_stratified":   "{:>13,.0f}".format,
        "children_nhis_mortucod":            "{:>13,.0f}".format,
        "delta_pct_vs_naive":                "{:>+7.1f}".format,
    }))
    print()
    print("Schluter 2024 (JAMA) published target: ~1,190,000 cumulative.")


if __name__ == "__main__":
    main()
