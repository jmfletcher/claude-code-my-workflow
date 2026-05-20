"""Schluter 2024 calibration with NHIS *cause-stratified* kids-per-decedent.

The earlier scripts/run_schluter_cause_specific.py used K = E[nk_under18 |
died, cell] computed over all decedents. That is wrong for cause-specific
targets because cause of death is strongly correlated with parental age
and therefore with the number of co-resident minors: accident decedents
have ~2.3x more co-resident minors than the average decedent.

NHIS-LMF records the 10-category leading-cause recode MORTUCODLD. We
collapse it to two buckets that line up with the ICD-10 intents:

  external_accident  = MORTUCODLD == 4
      (Accidents (unintentional injuries) -- includes accidental drug
       poisoning X40-X44 and accidental firearm W32-W34.)

  external_other     = MORTUCODLD == 10
      (All other causes residual -- absorbs suicide, homicide, and
       undetermined drug overdose and firearm deaths.)

We then weight the bucket-specific K's by the actual NCHS intent share
within drug and firearm deaths:

  drug deaths (X40-X44 + X60-X64 + X85 + Y10-Y14)
      ~75 % accidental (X40-X44 + Y10-Y14 -> Accidents bucket)
      ~25 % suicide / assault (X60-X64 + X85 -> Other bucket)

  firearm deaths (W32-W34 + X72-X74 + X93-X95 + Y22-Y24 + Y35.0)
      ~ 1 % accidental (W32-W34 -> Accidents bucket)
      ~99 % suicide / assault (everything else -> Other bucket)

For each ICD-10 death event we look at its single.code and assign it to
Accidents (X40-X44, Y10-Y14, W32-W34) or Other (X60-X64, X85, X72-X74,
X93-X95, Y22-Y24, Y35.0) and apply the corresponding NHIS K.

Outputs
- results/kinship/schluter_drugs_firearms/
      cumulative_1999_2020_cause_stratified.csv
      cumulative_1999_2020_cause_stratified_by_race.csv
      cause_stratified_K_tables.csv
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

from scripts.export_nhis_calibration import (AGE_BANDS, RACETH5_LABEL,
                                              build_cells)
from scripts.run_schluter_cause_specific import (
    DEATHS_RDS, RACE_ETH_TO_RACETH5,
    nchs_band_to_kappa_band, nchs_band_to_midpoint, year_to_decade,
)

OUT_DIR = PROJECT_ROOT / "results" / "kinship" / "schluter_drugs_firearms"
PARQUET = PROJECT_ROOT / "nhis_with_coresident_minors.parquet"


# ---------------------------------------------------------------------------
# ICD-10 -> NHIS intent bucket
# ---------------------------------------------------------------------------

ACCIDENT_RE = re.compile(r"^(X4[0-4]|Y1[0-4]|W3[2-4])")          # drug accidental + firearm accidental + undetermined drugs
OTHER_RE    = re.compile(r"^(X6[0-4]|X85|X7[2-4]|X9[3-5]|Y2[2-4]|Y35\.?0)")  # suicide/assault drug & firearm

DRUG_RE = re.compile(r"^(X4[0-4]|X6[0-4]|X85|Y1[0-4])")
FIRE_RE = re.compile(r"^(W3[2-4]|X7[2-4]|X9[3-5]|Y2[2-4]|Y35\.?0)")


def classify_intent(code: str) -> str | None:
    if not isinstance(code, str):
        return None
    if ACCIDENT_RE.match(code):
        return "accident"
    if OTHER_RE.match(code):
        return "other"
    return None


def classify_cause(code: str) -> str | None:
    if not isinstance(code, str):
        return None
    if DRUG_RE.match(code):
        return "drug"
    if FIRE_RE.match(code):
        return "firearm"
    return None


# ---------------------------------------------------------------------------
# Cause-stratified K tables from NHIS
# ---------------------------------------------------------------------------

def build_K_cause_stratified() -> pd.DataFrame:
    """Return one row per (sex, raceth5, age_band, yeardec, intent_bucket)
    with K_died = E[nk_under18 | died, cell, intent].

    intent_bucket in {accident, other, alive} where 'alive' is the
    living-adult comparison used by the naive Schluter estimate.

    Cells with fewer than 25 raw death rows in a given intent are
    pooled toward the (sex, raceth5, yeardec, intent) mean.
    """
    raw = pd.read_parquet(PARQUET)
    df = build_cells(raw)
    df["mortucodld"] = raw.loc[df.index, "mortucodld"].astype("Int8")

    df["intent"] = pd.NA
    df.loc[df["died"] == 0, "intent"] = "alive"
    df.loc[(df["died"] == 1) & (df["mortucodld"] == 4),  "intent"] = "accident"
    df.loc[(df["died"] == 1) & (df["mortucodld"] == 10), "intent"] = "other"
    df = df.dropna(subset=["intent"])

    df["w_nk"] = df["mortwtsa"] * df["nk_under18"]
    grouped = (df.groupby(["sex", "raceth5", "age_band", "yeardec", "intent"],
                            observed=True)
                 .agg(sum_w_nk=("w_nk", "sum"),
                      sum_w=("mortwtsa", "sum"),
                      n_rows=("nk_under18", "size"))
                 .reset_index())
    grouped["K"] = np.where(grouped["sum_w"] > 0,
                              grouped["sum_w_nk"] / grouped["sum_w"], np.nan)

    # Smooth sparse death buckets toward (sex, raceth5, yeardec, intent)
    # weighted mean (using sum_w as the weight for pooling).
    pool = (grouped.assign(num=grouped["K"] * grouped["sum_w"])
                    .groupby(["sex", "raceth5", "yeardec", "intent"],
                             observed=True, as_index=False)
                    .agg(num=("num", "sum"), den=("sum_w", "sum")))
    pool["K_pool"] = np.where(pool["den"] > 0, pool["num"] / pool["den"],
                                np.nan)
    grouped = grouped.merge(pool[["sex", "raceth5", "yeardec",
                                    "intent", "K_pool"]],
                              on=["sex", "raceth5", "yeardec", "intent"],
                              how="left")
    sparse = grouped["n_rows"].fillna(0) < 25
    grouped["K_smooth"] = np.where(sparse, grouped["K_pool"], grouped["K"])
    grouped["K_smooth"] = (grouped["K_smooth"].fillna(grouped["K_pool"])
                                                .fillna(0.0))
    return grouped[["sex", "raceth5", "age_band", "yeardec",
                    "intent", "K_smooth", "n_rows"]]


# ---------------------------------------------------------------------------
# NCHS cause-specific deaths labeled with cause AND intent
# ---------------------------------------------------------------------------

def load_deaths_with_intent() -> pd.DataFrame:
    print("[stratified] loading NCHS deaths ...")
    d = pyreadr.read_r(str(DEATHS_RDS))
    df = list(d.values())[0]
    df = df[(df["year"] >= 1999) & (df["year"] <= 2020)].copy()
    df["age_mid"] = df["age"].apply(nchs_band_to_midpoint)
    df = df.dropna(subset=["age_mid"])
    df["age_mid"] = df["age_mid"].astype(int)
    df = df[(df["age_mid"] >= 15) & (df["age_mid"] <= 79)]
    df = df[df["race.eth"].isin(RACE_ETH_TO_RACETH5.keys())].copy()
    df["cause"]  = df["single.code"].apply(classify_cause)
    df["intent"] = df["single.code"].apply(classify_intent)
    df = df[df["cause"].isin(["drug", "firearm"])]
    df = df.dropna(subset=["intent"])
    df["raceth5"]  = df["race.eth"].map(RACE_ETH_TO_RACETH5).astype(int)
    df["sex"]      = df["sex"].map({"Female": "f", "Male": "m"})
    df["age_band"] = df["age"].apply(nchs_band_to_kappa_band)
    df["yeardec"]  = df["year"].apply(year_to_decade)
    df = df.dropna(subset=["age_band", "yeardec", "sex"])
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").fillna(0)
    cell = (df.groupby(["cause", "intent", "year", "sex", "raceth5",
                          "age_band", "yeardec"], observed=True)
                ["deaths"].sum().reset_index())
    print(f"[stratified]   cause x intent x cell rows: {len(cell):,}")
    return cell


# ---------------------------------------------------------------------------
# Combine
# ---------------------------------------------------------------------------

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    K = build_K_cause_stratified()
    K.to_csv(OUT_DIR / "cause_stratified_K_tables.csv", index=False)

    # Quick national summary of K by intent
    print()
    print("[stratified] National-pooled K by intent (sum_w weighted):")
    weighted = (K.groupby("intent")
                  .apply(lambda d: np.average(d["K_smooth"],
                                                weights=d["n_rows"]
                                                          .fillna(0)),
                          include_groups=False))
    print(weighted)

    deaths = load_deaths_with_intent()

    # Two K tables to compare: alive (naive) and intent-specific
    K_alive    = (K[K["intent"] == "alive"]
                    [["sex", "raceth5", "age_band", "yeardec", "K_smooth"]]
                    .rename(columns={"K_smooth": "K_alive"}))
    K_accident = (K[K["intent"] == "accident"]
                    [["sex", "raceth5", "age_band", "yeardec", "K_smooth"]]
                    .rename(columns={"K_smooth": "K_accident"}))
    K_other    = (K[K["intent"] == "other"]
                    [["sex", "raceth5", "age_band", "yeardec", "K_smooth"]]
                    .rename(columns={"K_smooth": "K_other"}))

    merged = (deaths.merge(K_alive,
                              on=["sex", "raceth5", "age_band", "yeardec"],
                              how="left")
                       .merge(K_accident,
                              on=["sex", "raceth5", "age_band", "yeardec"],
                              how="left")
                       .merge(K_other,
                              on=["sex", "raceth5", "age_band", "yeardec"],
                              how="left"))
    for col in ["K_alive", "K_accident", "K_other"]:
        merged[col] = merged[col].fillna(0.0)

    merged["children_naive"] = merged["deaths"] * merged["K_alive"]
    merged["K_used"] = np.where(merged["intent"] == "accident",
                                  merged["K_accident"], merged["K_other"])
    merged["children_nhis_stratified"] = merged["deaths"] * merged["K_used"]

    # Also keep the old all-cause-kappa estimate for side-by-side comparison
    # (load it back from disk if available, otherwise compute again via the
    # build_K_tables that the original Schluter script uses).
    try:
        old = pd.read_csv(OUT_DIR / "cumulative_1999_2020.csv")
        old = old[old["cause"] != "drug+firearm combined"]
        old_by_cause = old.set_index("cause")["children_nhis"]
    except FileNotFoundError:
        old_by_cause = None

    annual = (merged.groupby(["cause", "year"])
                       [["deaths", "children_naive",
                          "children_nhis_stratified"]]
                       .sum().reset_index())
    annual["delta_pct"] = 100.0 * ((annual["children_nhis_stratified"]
                                      - annual["children_naive"])
                                     / annual["children_naive"])
    annual.to_csv(OUT_DIR / "annual_by_cause_stratified.csv", index=False)

    cum = (merged.groupby("cause")[["deaths", "children_naive",
                                        "children_nhis_stratified"]]
                      .sum().reset_index())
    combined = pd.DataFrame({
        "cause":            ["drug+firearm combined"],
        "deaths":           [cum["deaths"].sum()],
        "children_naive":   [cum["children_naive"].sum()],
        "children_nhis_stratified": [cum["children_nhis_stratified"].sum()],
    })
    cum = pd.concat([cum, combined], ignore_index=True)
    cum["delta_pct_vs_naive"] = (100.0
                                  * (cum["children_nhis_stratified"]
                                       - cum["children_naive"])
                                  / cum["children_naive"])
    if old_by_cause is not None:
        cum["children_nhis_allcause_kappa"] = (cum["cause"]
                                                 .map(old_by_cause)
                                                 .astype(float))
        cum["delta_pct_vs_allcause_kappa"] = (
            100.0 * (cum["children_nhis_stratified"]
                       - cum["children_nhis_allcause_kappa"])
                   / cum["children_nhis_allcause_kappa"])
    cum.to_csv(OUT_DIR / "cumulative_1999_2020_cause_stratified.csv",
                index=False)

    # By race
    cum_race = (merged.groupby(["cause", "raceth5"])
                         [["deaths", "children_naive",
                            "children_nhis_stratified"]]
                         .sum().reset_index())
    cum_race["race_eth"] = cum_race["raceth5"].map(RACETH5_LABEL)
    cum_race = cum_race[["cause", "race_eth", "deaths",
                          "children_naive", "children_nhis_stratified"]]
    cum_race["delta_pct"] = (100.0
                              * (cum_race["children_nhis_stratified"]
                                   - cum_race["children_naive"])
                              / cum_race["children_naive"])
    cum_race.to_csv(OUT_DIR
                      / "cumulative_1999_2020_cause_stratified_by_race.csv",
                      index=False)

    print()
    print("=== Cumulative 1999-2020, cause-stratified NHIS K ===")
    cols = ["cause", "deaths", "children_naive",
            "children_nhis_stratified"]
    if "children_nhis_allcause_kappa" in cum.columns:
        cols.append("children_nhis_allcause_kappa")
    cols += ["delta_pct_vs_naive"]
    print(cum[cols].to_string(index=False, formatters={
        "deaths":                       "{:>13,.0f}".format,
        "children_naive":               "{:>13,.0f}".format,
        "children_nhis_stratified":     "{:>13,.0f}".format,
        "children_nhis_allcause_kappa": "{:>13,.0f}".format,
        "delta_pct_vs_naive":           "{:>+7.1f}".format,
    }))
    print()
    print("Schluter 2024 (JAMA) published target: 1,190,000 cumulative")


if __name__ == "__main__":
    main()
