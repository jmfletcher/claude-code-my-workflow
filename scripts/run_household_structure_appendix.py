"""Household-structure appendix for the NHIS calibration.

Motivation
----------
The NHIS-based K = E[co-resident minors | died, cell] measures children at
*the decedent's interview address*. This omits non-co-resident children
(a non-custodial father whose child lives elsewhere; an out-of-state
divorced parent; a parent in prison or hospitalized at survey).

Demographic-rate orphanhood papers sit at the other extreme: every birth
counts toward parental loss when the parent dies, regardless of whether
the parent was ever present in the child's life. The truth is between.

The asymmetry is **sex-specific**: mothers are co-resident with their
minor children in ~80-95 % of cases; fathers in 60-75 % depending on
race, era, and SES. So K_father systematically understates true paternal
exposure to children's bereavement, while K_mother is closer to right.

This script stratifies the calibration two ways:
1. By **sex of decedent**: pooled K_mother vs K_father, and how the
   sex-stratified K compares across race/ethnicity.
2. By **household structure** of the respondent at NHIS interview:
   - sole adult parent (single-parent family unit)
   - coupled adult parent (married / cohabiting two-adult family unit)
   - other (multi-adult extended family)

Together these two cuts let the reader see (a) how much of the
"K_died < K_alive" finding is driven by fathers whose children live
elsewhere and (b) whether single-parent decedents have systematically
different K and mortality rates than coupled-parent decedents.

Outputs
- results/py/appendix_household_structure_K.csv
- results/py/appendix_household_structure_mortality.csv
- results/py/appendix_K_by_sex.csv

Usage
    python scripts/run_household_structure_appendix.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.export_nhis_calibration import (AGE_BANDS, RACETH5_LABEL,
                                              ASIAN_CODES, AIAN_CODES)

PARQUET = PROJECT_ROOT / "nhis_with_coresident_minors.parquet"
OUT_DIR = PROJECT_ROOT / "results" / "py"

MARRIED_CODES   = {10, 11, 12, 13}           # any "married" marstat code
COHAB_CODES     = {1, 3, 4}                  # cohabiting codes in cohabmarst


def classify_hh_structure(df: pd.DataFrame) -> pd.Series:
    """Sole / coupled / multi_adult_other for adult parents.

    Operational definitions (NHIS family unit fmx):
        sole_adult   : exactly 1 adult (age >=18) in the family unit and
                       the adult is a parent (has minor child in family)
        coupled      : exactly 2 adults in family unit AND respondent is
                       married (any marstat in {10,11,12,13}) or
                       cohabiting (cohabmarst in {1,3,4})
        multi_adult_other:  3+ adults, OR exactly 2 adults but not
                              married/cohabiting (e.g. adult sibling pair
                              co-residing with the children).
    """
    df = df.copy()
    df["is_adult"] = (df["age"] >= 18).astype(int)
    adults_per_fmx = (df.groupby(["year", "serial", "fmx"])["is_adult"]
                          .sum().rename("n_adults_in_fmx").reset_index())
    df = df.merge(adults_per_fmx, on=["year", "serial", "fmx"], how="left")
    married_or_cohab = (df["marstat"].isin(MARRIED_CODES)
                         | df["cohabmarst"].isin(COHAB_CODES))
    s = pd.Series("multi_adult_other", index=df.index, dtype="object")
    s = s.mask(df["n_adults_in_fmx"].eq(1), "sole_adult")
    s = s.mask(df["n_adults_in_fmx"].eq(2) & married_or_cohab, "coupled")
    return s


def add_raceth5_died_band(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    elig = out["mortelig"].eq(1)
    out["died"] = pd.Series(np.nan, index=out.index, dtype="float64")
    out.loc[elig & out["mortstat"].eq(1), "died"] = 1.0
    out.loc[elig & out["mortstat"].eq(2), "died"] = 0.0

    hisp = out["hispeth"].between(20, 70, inclusive="both")
    racenew = out["racenew"]
    racea = out["racea"]

    nh = pd.Series(pd.NA, index=out.index, dtype="Int8")
    nh = nh.mask((~hisp) & racenew.eq(100), 2)
    nh = nh.mask((~hisp) & racenew.eq(200), 3)
    nh = nh.mask((~hisp) & racenew.eq(400), 4)
    nh = nh.mask((~hisp) & racenew.eq(300), 5)
    nh = nh.mask(nh.isna() & (~hisp) & racea.eq(100), 2)
    nh = nh.mask(nh.isna() & (~hisp) & racea.eq(200), 3)
    nh = nh.mask(nh.isna() & (~hisp) & racea.isin(ASIAN_CODES), 4)
    nh = nh.mask(nh.isna() & (~hisp) & racea.isin(AIAN_CODES), 5)
    raceth5 = pd.Series(pd.NA, index=out.index, dtype="Int8")
    raceth5 = raceth5.mask(hisp, 1)
    raceth5 = raceth5.where(hisp, nh)
    raceth5 = raceth5.fillna(5).astype("Int8")
    out["raceth5"] = raceth5

    out["nk_under18"] = (out["n_fam_childminor017"].astype("float64")
                          .fillna(0.0).clip(0, 8))
    out["sex_label"] = out["sex"].map({1: "m", 2: "f"})

    band_label = pd.Series(pd.NA, index=out.index, dtype="object")
    age = out["age"].astype("Int16")
    for lo, hi in AGE_BANDS:
        band_label = band_label.mask(age.between(lo, hi), f"{lo}-{hi}")
    out["age_band"] = band_label
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[hh] loading parquet ...")
    df = pd.read_parquet(PARQUET)

    df["hh_struct"] = classify_hh_structure(df)
    df = add_raceth5_died_band(df)

    elig = (df["died"].isin([0.0, 1.0])
              & df["mortwtsa"].notna() & (df["mortwtsa"] > 0)
              & df["sex_label"].isin(["f", "m"])
              & df["raceth5"].notna()
              & df["age_band"].notna()
              & (df["age"] >= 18))
    df = df.loc[elig].copy()

    # Parent sample: at least one minor child in the family unit.
    # This keeps survivors and decedents on the same footing -- both
    # were observed as adult parents at interview.
    parents = df[df["nk_under18"] > 0].copy()
    print(f"[hh] adult parent sample N = {len(parents):,}")
    print(f"[hh]   decedents: {int((parents['died']==1).sum()):,}")
    print(f"[hh]   survivors: {int((parents['died']==0).sum()):,}")
    print()
    print("[hh] HH structure distribution among adult parents:")
    print((parents.groupby("hh_struct").size()
              / len(parents) * 100).round(1).rename("share %"))
    print()

    # --- 1. Pooled K by sex (regardless of structure) ---------------
    parents["w_nk"] = parents["mortwtsa"] * parents["nk_under18"]

    sex_summary = (parents.groupby(["sex_label", "died"], observed=True)
                            .agg(K=("nk_under18",
                                     lambda x: np.average(
                                         x,
                                         weights=parents.loc[x.index,
                                                              "mortwtsa"])),
                                  n=("nk_under18", "size"))
                            .reset_index())
    sex_summary["died_label"] = sex_summary["died"].map(
        {0.0: "alive", 1.0: "died"})
    sex_pivot = sex_summary.pivot_table(index="sex_label",
                                          columns="died_label",
                                          values="K")
    sex_pivot["kappa"] = sex_pivot["died"] / sex_pivot["alive"]
    sex_pivot.to_csv(OUT_DIR / "appendix_K_by_sex.csv")
    print("[hh] K by sex of respondent (parents only, all years/races):")
    print(sex_pivot.round(3))
    print()

    # --- 2. K by sex x race x hh_struct -----------------------------
    def w_avg(g):
        w = g["mortwtsa"].to_numpy()
        v = g["nk_under18"].to_numpy()
        sw = w.sum()
        return float((v * w).sum() / sw) if sw > 0 else np.nan

    cell = (parents.groupby(["sex_label", "raceth5", "hh_struct", "died"],
                              observed=True)
                      .apply(lambda g: pd.Series({
                          "K": w_avg(g),
                          "n_rows": len(g),
                          "sum_w": float(g["mortwtsa"].sum()),
                      }), include_groups=False)
                      .reset_index())
    cell["died_label"] = cell["died"].map({0.0: "alive", 1.0: "died"})
    K_tab = cell.pivot_table(index=["sex_label", "raceth5", "hh_struct"],
                               columns="died_label",
                               values="K").reset_index()
    n_tab = cell.pivot_table(index=["sex_label", "raceth5", "hh_struct"],
                               columns="died_label",
                               values="n_rows").reset_index()
    K_tab = K_tab.merge(
        n_tab.rename(columns={"alive": "n_alive", "died": "n_died"}),
        on=["sex_label", "raceth5", "hh_struct"])
    K_tab["kappa"] = K_tab["died"] / K_tab["alive"]
    K_tab["raceth5_label"] = K_tab["raceth5"].map(RACETH5_LABEL)
    K_tab.to_csv(OUT_DIR / "appendix_household_structure_K.csv", index=False)
    print("[hh] K by sex x race x hh_struct (parents):")
    show = K_tab[["sex_label", "raceth5_label", "hh_struct",
                  "alive", "died", "kappa", "n_alive", "n_died"]].copy()
    show.columns = ["sex", "race/eth", "hh_struct", "K_alive",
                    "K_died", "kappa", "n_alive", "n_died"]
    print(show.to_string(index=False,
                          formatters={"K_alive": "{:>6.3f}".format,
                                       "K_died":  "{:>6.3f}".format,
                                       "kappa":   "{:>6.3f}".format,
                                       "n_alive": "{:>7,.0f}".format,
                                       "n_died":  "{:>6,.0f}".format}))
    print()

    # --- 3. Mortality probability by sex x race x hh_struct x band ---
    parents["w_died"] = parents["mortwtsa"] * (parents["died"] == 1.0)
    mort = (parents.groupby(["sex_label", "raceth5", "hh_struct",
                                "age_band"], observed=True)
                      .agg(sum_w=("mortwtsa", "sum"),
                           sum_w_died=("w_died", "sum"),
                           n_died=("died", lambda x: int((x == 1).sum())))
                      .reset_index())
    mort["p_died"] = mort["sum_w_died"] / mort["sum_w"]
    mort["raceth5_label"] = mort["raceth5"].map(RACETH5_LABEL)
    mort.to_csv(OUT_DIR / "appendix_household_structure_mortality.csv",
                  index=False)
    print("[hh] Mortality probability by sex x race x hh_struct (pooled "
          "across age bands; raw, not standardized):")
    pool = (mort.groupby(["sex_label", "raceth5", "hh_struct"],
                          observed=True)
                  .agg(sum_w=("sum_w", "sum"),
                       sum_w_died=("sum_w_died", "sum"))
                  .reset_index())
    pool["p_died"] = pool["sum_w_died"] / pool["sum_w"]
    pool["raceth5_label"] = pool["raceth5"].map(RACETH5_LABEL)
    pool_show = pool[["sex_label", "raceth5_label", "hh_struct",
                       "p_died"]].copy()
    print(pool_show.to_string(index=False,
                                formatters={"p_died": "{:>7.4f}".format}))
    print()

    # --- 4. Sex composition of decedents by race --------------------
    dec = parents[parents["died"] == 1.0].copy()
    dec_comp = (dec.groupby(["raceth5", "sex_label"], observed=True)
                       ["mortwtsa"].sum().reset_index())
    dec_total = (dec_comp.groupby("raceth5")["mortwtsa"].sum()
                            .rename("total"))
    dec_comp = dec_comp.merge(dec_total, on="raceth5")
    dec_comp["share"] = dec_comp["mortwtsa"] / dec_comp["total"]
    dec_comp["raceth5_label"] = dec_comp["raceth5"].map(RACETH5_LABEL)
    print("[hh] Sex composition of NHIS-LMF adult parent decedents by race:")
    print(dec_comp.pivot_table(index="raceth5_label", columns="sex_label",
                                  values="share").round(3))
    print()

    # --- 5. Hypothetical impact of non-resident-parent bias ---------
    # If we believe paternal non-residence rates vs ACS:
    #   NH White:    ~30 % of dads non-resident
    #   NH Black:    ~55 % of dads non-resident
    #   Hispanic:    ~35 % of dads non-resident
    #   NH Asian:    ~15 % of dads non-resident
    #   NH AIAN:     ~50 % of dads non-resident (high uncertainty)
    # and assume non-resident dads have, on average, 1 minor child
    # somewhere (their own), then K_father_true could be:
    #     K_father_true ≈ K_father_nhis + nonresident_rate * 1
    # This is a crude back-of-envelope but communicates the scale.
    rates = pd.DataFrame({
        "raceth5": [2, 3, 4, 5, 1],
        "nonres_father_rate": [0.30, 0.55, 0.15, 0.50, 0.35],
    })
    K_male = K_tab[(K_tab["sex_label"] == "m")
                     & (K_tab["hh_struct"] != "multi_adult_other")].copy()
    K_male_died = (K_male.groupby("raceth5", observed=True)
                          .apply(lambda d: float(np.average(
                              d["died"].fillna(0),
                              weights=d["n_died"].fillna(1))),
                                  include_groups=False)
                          .rename("K_father_died_nhis").reset_index())
    K_male_died = K_male_died.merge(rates, on="raceth5")
    K_male_died["K_father_died_adj"] = (K_male_died["K_father_died_nhis"]
                                          + K_male_died["nonres_father_rate"])
    K_male_died["raceth5_label"] = K_male_died["raceth5"].map(RACETH5_LABEL)
    print("[hh] Back-of-envelope: NHIS K_father_died augmented with "
          "non-resident-father rate (assumes 1 child per non-resident dad):")
    print(K_male_died[["raceth5_label", "K_father_died_nhis",
                         "nonres_father_rate", "K_father_died_adj"]]
              .to_string(index=False,
                          formatters={
                              "K_father_died_nhis": "{:>6.3f}".format,
                              "nonres_father_rate": "{:>6.2f}".format,
                              "K_father_died_adj":  "{:>6.3f}".format}))


if __name__ == "__main__":
    main()
