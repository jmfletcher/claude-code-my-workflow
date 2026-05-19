"""Ingest Villaveces / NCHS / CDC-WONDER inputs into tidy national
single-year-of-age tables for the kinship engine.

Outputs (all under data_kinship/cache/):
    population_national.parquet  -- year, age, sex, race_eth, pop
    mortality_rates.parquet      -- year, age, sex, race_eth, q
    fertility_rates.parquet      -- year, age, sex (parent), race_eth, f_rate

National scope only; years 1990-2021 (CDC WONDER bridged-race coverage).

Race/eth = "All" or one of:
    Non-Hispanic White, Non-Hispanic Black, Non-Hispanic Asian or Pacific Islander,
    Non-Hispanic American Indian or Alaska Native, Hispanic.

Run as a script to materialise the parquet caches:
    python -m pykin.ingest [--force] [--pooled-only]
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr

from . import AGES

DATA_ROOT = Path(__file__).resolve().parents[1] / "data_kinship"
CACHE_DIR = DATA_ROOT / "cache"
DEATH_ADULT = DATA_ROOT / "data/NCHS/death/output/Allcause_deaths_1983-2021.RDS"
DEATH_CHILD = DATA_ROOT / "data/NCHS/death_child/output/NCHS_deaths_children_1983-2021.RDS"
BIRTHS_FILE = DATA_ROOT / "data/NCHS/births/output/births_1968-2021.RDS"
POP_DIR     = DATA_ROOT / "data/data/pop/raw"

YEAR_MIN = 1990
YEAR_MAX = 2021

CACHE_DIR.mkdir(parents=True, exist_ok=True)

SEX_MAP = {"Female": "f", "Male": "m", "F": "f", "M": "m"}

# Map CDC WONDER (Race, Ethnicity) -> our race_eth label, sticking to the
# nine bridged-race published groups.
RACE_BRIDGE = {
    ("White", "Not Hispanic or Latino"):
        "Non-Hispanic White",
    ("Black or African American", "Not Hispanic or Latino"):
        "Non-Hispanic Black",
    ("Asian or Pacific Islander", "Not Hispanic or Latino"):
        "Non-Hispanic Asian or Pacific Islander",
    ("American Indian or Alaska Native", "Not Hispanic or Latino"):
        "Non-Hispanic American Indian or Alaska Native",
    # Hispanic is collapsed across race per the standard bridged-race
    # presentation used by Villaveces et al.
    ("White", "Hispanic or Latino"): "Hispanic",
    ("Black or African American", "Hispanic or Latino"): "Hispanic",
    ("Asian or Pacific Islander", "Hispanic or Latino"): "Hispanic",
    ("American Indian or Alaska Native", "Hispanic or Latino"): "Hispanic",
}

RACE_ETH = [
    "All",
    "Non-Hispanic White",
    "Non-Hispanic Black",
    "Non-Hispanic Asian or Pacific Islander",
    "Non-Hispanic American Indian or Alaska Native",
    "Hispanic",
]

# Map NCHS race.eth labels (in deaths and births files) -> our labels.
NCHS_RACE_MAP = {
    "Non-Hispanic White": "Non-Hispanic White",
    "Non-Hispanic Black": "Non-Hispanic Black",
    "Non-Hispanic Asian": "Non-Hispanic Asian or Pacific Islander",
    "Non-Hispanic American Indian or Alaska Native":
        "Non-Hispanic American Indian or Alaska Native",
    "Hispanic": "Hispanic",
    "All": "All",
}


# ---------------------------------------------------------------------------
# Population (CDC WONDER bridged-race + children single-year)
# ---------------------------------------------------------------------------

# CDC WONDER 5-year age groups, in order. The "< 1 year" category and "1-4
# years" are exceptions to the 5-year rule.
WONDER_BAND_AGES = {
    "< 1 year":  [0],
    "1-4 years": [1, 2, 3, 4],
    "85+ years": list(range(85, AGES)),   # open class spread to 100
    # All others handled programmatically below.
}


def _band_to_ages(label: str) -> list[int]:
    label = label.strip()
    if label in WONDER_BAND_AGES:
        return WONDER_BAND_AGES[label]
    if label.endswith(" years"):
        lo, hi = (int(x) for x in label.replace(" years", "").strip().split("-"))
        return list(range(lo, hi + 1))
    raise ValueError(f"Unknown age band: {label!r}")


COLUMN_RENAME = {
    "Age":                       "age",
    "Age Code":                  "age_code",
    "Single-Year Ages":          "age",
    "Single-Year Ages Code":     "age_code",
    "Age Group":                 "band",
    "Age Group Code":            "band_code",
    "Five-Year Age Groups":      "band",
    "Five-Year Age Groups Code": "band_code",
    "Gender":                    "sex_name",
    "Gender Code":               "sex",
    "Race":                      "Race",
    "Ethnicity":                 "Ethnicity",
    "Yearly July 1st Estimates": "year_name",
    "Yearly July 1st Estimates Code": "year",
    "Population":                "pop",
}


def _read_wonder_tsv(path: Path) -> pd.DataFrame:
    """Read a CDC WONDER tab-delimited extract and harmonise column names."""
    df = pd.read_csv(path, sep="\t", dtype=str,
                     na_values=["", "Not Applicable", "Missing"])
    df = df.loc[df["Notes"].isna() | (df["Notes"] == "")].copy()
    df = df.rename(columns=COLUMN_RENAME)
    return df


def build_population_national(pooled_only: bool = False) -> pd.DataFrame:
    """Build population by year × single-year-age × sex × race_eth.

    Combines:
        adults (5-year bands) from CDC WONDER bridged-race files
        children (single-year, 0-17) from the CDC WONDER children single-year files
    """
    # ---- Children single-year, pooled and race-stratified ----
    p_child_pooled_19 = POP_DIR / "national_level_single_year_children_1990-2020.txt"
    p_child_pooled_21 = POP_DIR / "national_level_single_year_children_2021.txt"
    p_child_race_19   = POP_DIR / "national_race_level_single_year_children_1990-2020.txt"
    p_child_race_21   = POP_DIR / "national_race_level_single_year_children_2021.txt"

    def _children_pooled(p):
        d = _read_wonder_tsv(p)
        # Prefer the *_code columns for numeric parsing.
        if "age_code" in d.columns:
            d["age"] = d["age_code"]
        d = d[d["age"].notna() & d["year"].notna() & d["pop"].notna()]
        d["age"] = d["age"].astype(int)
        d["year"] = d["year"].astype(int)
        d["pop"] = pd.to_numeric(d["pop"], errors="coerce")
        d["race_eth"] = "All"
        # Children single-year file has no sex split; split 51/49 m/f.
        out = []
        for s, share in [("m", 0.512), ("f", 0.488)]:
            sub = d[["year", "age", "race_eth", "pop"]].copy()
            sub["sex"] = s
            sub["pop"] *= share
            out.append(sub)
        return pd.concat(out, ignore_index=True)

    children_all = pd.concat(
        [_children_pooled(p_child_pooled_19), _children_pooled(p_child_pooled_21)],
        ignore_index=True,
    )

    if not pooled_only:
        def _children_race(p):
            d = _read_wonder_tsv(p)
            if "age_code" in d.columns:
                d["age"] = d["age_code"]
            d = d[d["age"].notna() & d["year"].notna() & d["pop"].notna()]
            d["age"] = d["age"].astype(int)
            d["year"] = d["year"].astype(int)
            d["pop"] = pd.to_numeric(d["pop"], errors="coerce")
            d["race_eth"] = d.apply(
                lambda r: RACE_BRIDGE.get((r["Race"], r["Ethnicity"]), "Others"),
                axis=1,
            )
            d = d[d["race_eth"].isin(RACE_ETH)]
            # Hispanic collapse: sum across child races within Hispanic.
            d = (d.groupby(["year", "age", "race_eth"], as_index=False)["pop"]
                  .sum())
            # No sex; split 51/49.
            out = []
            for s, share in [("m", 0.512), ("f", 0.488)]:
                sub = d.copy()
                sub["sex"] = s
                sub["pop"] *= share
                out.append(sub)
            return pd.concat(out, ignore_index=True)

        children_race = pd.concat(
            [_children_race(p_child_race_19), _children_race(p_child_race_21)],
            ignore_index=True,
        )
        children = pd.concat([children_all, children_race], ignore_index=True)
    else:
        children = children_all

    children = children[(children["year"] >= YEAR_MIN) &
                        (children["year"] <= YEAR_MAX) &
                        (children["age"] <= 17)]

    # ---- Adults: 5-year bands from CDC WONDER bridged-race ----
    p_adult_19 = POP_DIR / "National Bridged-Race Population Estimates 1990-2019.txt"
    p_adult_21 = POP_DIR / "National Bridged-Race Population Estimates 2020-2021.txt"

    def _adults(p):
        d = _read_wonder_tsv(p)
        d = d.dropna(subset=["band", "year", "pop"])
        d = d[["band", "sex", "Race", "Ethnicity", "year", "pop"]].copy()
        d["year"] = d["year"].astype(int)
        d["pop"] = pd.to_numeric(d["pop"], errors="coerce")
        d["sex"] = d["sex"].map(SEX_MAP)
        d["race_eth"] = d.apply(
            lambda r: RACE_BRIDGE.get((r["Race"], r["Ethnicity"]), "Others"),
            axis=1,
        )
        d = d[d["race_eth"].isin(RACE_ETH[1:])]
        d = (d.groupby(["year", "band", "sex", "race_eth"], as_index=False)["pop"]
              .sum())
        return d

    adults = pd.concat([_adults(p_adult_19), _adults(p_adult_21)],
                       ignore_index=True)
    adults = adults[(adults["year"] >= YEAR_MIN) & (adults["year"] <= YEAR_MAX)]

    # Race='All' = sum across race_eth at the same (year, band, sex)
    adults_all = (adults.groupby(["year", "band", "sex"], as_index=False)["pop"]
                        .sum()
                        .assign(race_eth="All"))
    adults_full = pd.concat([adults_all, adults], ignore_index=True)
    if pooled_only:
        adults_full = adults_full[adults_full["race_eth"] == "All"].copy()

    # Expand 5-year bands to single year (uniform within band, ages 18-100).
    rows = []
    for band, grp in adults_full.groupby("band", sort=False):
        ages_in_band = _band_to_ages(band)
        ages_in_band = [a for a in ages_in_band if 18 <= a < AGES]
        if not ages_in_band:
            continue
        for a in ages_in_band:
            sub = grp[["year", "sex", "race_eth", "pop"]].copy()
            sub["age"] = a
            sub["pop"] = sub["pop"] / len(ages_in_band)
            rows.append(sub)
    adults_single = pd.concat(rows, ignore_index=True)

    # Children (ages 0-17) already single year.
    children = children.rename(columns={"age": "age"})
    children["age"] = children["age"].astype(int)
    adults_single["age"] = adults_single["age"].astype(int)

    pop = pd.concat([children[["year", "age", "sex", "race_eth", "pop"]],
                     adults_single[["year", "age", "sex", "race_eth", "pop"]]],
                    ignore_index=True)
    pop = pop.groupby(["year", "age", "sex", "race_eth"], as_index=False)["pop"].sum()
    pop["age"] = pop["age"].astype("int16")
    pop["pop"] = pop["pop"].astype("float64")
    return pop


# ---------------------------------------------------------------------------
# Mortality from NCHS RDS deaths + CDC pop
# ---------------------------------------------------------------------------

ADULT_BAND_TO_AGES = {
    "0-14":   list(range(0, 15)),
    "100+":   [100],
}


def _adult_band_to_ages(band: str) -> list[int]:
    if band in ADULT_BAND_TO_AGES:
        return ADULT_BAND_TO_AGES[band]
    lo, hi = (int(x) for x in band.split("-"))
    return list(range(lo, hi + 1))


def build_mortality_rates(pop_long: pd.DataFrame, pooled_only: bool = False) -> pd.DataFrame:
    print("[ingest] Loading adult deaths RDS...")
    d_adult_raw = list(pyreadr.read_r(str(DEATH_ADULT)).values())[0]
    print("[ingest] Loading child deaths RDS...")
    d_child_raw = list(pyreadr.read_r(str(DEATH_CHILD)).values())[0]

    # Race='All' is only present in 1983 in the deaths file. For 1990+ we
    # construct it as the sum across the five NHIS-style race/eth groups
    # (excluding 'Others').
    five_re = [k for k in NCHS_RACE_MAP if k not in ("All", "Others")]

    # Adult deaths
    da = d_adult_raw.loc[d_adult_raw["race.eth"].isin(five_re)].copy()
    da["sex"] = da["sex"].map(SEX_MAP)
    da["race_eth"] = da["race.eth"].map(NCHS_RACE_MAP)
    da = da[(da["year"] >= YEAR_MIN) & (da["year"] <= YEAR_MAX)]
    da = (da.groupby(["age", "sex", "year", "race_eth"], as_index=False, observed=True)["deaths"]
            .sum())
    da_all = (da.groupby(["age", "sex", "year"], as_index=False)["deaths"].sum()
                .assign(race_eth="All"))
    da = pd.concat([da_all, da], ignore_index=True)
    if pooled_only:
        da = da[da["race_eth"] == "All"]
    # Expand age bands to single year (uniform spread; ages 18+ here, since
    # child deaths come from a separate single-year file).
    rows = []
    for band, grp in da.groupby("age", sort=False):
        ages_in_band = [a for a in _adult_band_to_ages(band) if 18 <= a < AGES]
        if not ages_in_band:
            continue
        for a in ages_in_band:
            sub = grp[["year", "sex", "race_eth", "deaths"]].copy()
            sub["age"] = a
            sub["deaths"] = sub["deaths"] / len(ages_in_band)
            rows.append(sub)
    da_single = pd.concat(rows, ignore_index=True)

    # Child deaths (single year already)
    dc = d_child_raw.loc[d_child_raw["race.eth"].isin(five_re)].copy()
    dc["race_eth"] = dc["race.eth"].map(NCHS_RACE_MAP)
    dc = dc[(dc["year"] >= YEAR_MIN) & (dc["year"] <= YEAR_MAX)]
    dc = (dc.groupby(["age", "year", "race_eth"], as_index=False, observed=True)["deaths"]
            .sum())
    dc["age"] = dc["age"].astype(int)
    dc_all = (dc.groupby(["age", "year"], as_index=False)["deaths"].sum()
                .assign(race_eth="All"))
    dc = pd.concat([dc_all, dc], ignore_index=True)
    if pooled_only:
        dc = dc[dc["race_eth"] == "All"]
    dc_long = []
    for s, share in [("m", 0.512), ("f", 0.488)]:
        sub = dc.copy()
        sub["sex"] = s
        sub["deaths"] = sub["deaths"] * share
        dc_long.append(sub)
    dc_long = pd.concat(dc_long, ignore_index=True)
    dc_long = dc_long[dc_long["age"] <= 17]

    deaths = pd.concat([dc_long[["year", "age", "sex", "race_eth", "deaths"]],
                        da_single[["year", "age", "sex", "race_eth", "deaths"]]],
                       ignore_index=True)
    deaths["age"] = deaths["age"].astype("int16")

    pop_long = pop_long.copy()
    pop_long["age"] = pop_long["age"].astype("int16")
    merged = deaths.merge(pop_long, on=["year", "age", "sex", "race_eth"], how="left")
    merged["pop"] = merged["pop"].fillna(0.0)
    merged["q"] = np.where(merged["pop"] > 0,
                           merged["deaths"] / merged["pop"], 0.0)
    merged["q"] = np.clip(merged["q"], 0.0, 0.999)
    return merged[["year", "age", "sex", "race_eth", "q"]]


# ---------------------------------------------------------------------------
# Fertility from NCHS RDS births + CDC pop
# ---------------------------------------------------------------------------

def build_fertility_rates(pop_long: pd.DataFrame, pooled_only: bool = False) -> pd.DataFrame:
    print("[ingest] Loading births RDS...")
    df = list(pyreadr.read_r(str(BIRTHS_FILE)).values())[0]
    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()

    def _normalise(s: pd.Series) -> pd.Series:
        return s.astype(str).str.replace("Unknown-hispanic ", "", regex=False)

    df["mother.race.eth"] = _normalise(df["mother.race.eth"]).map(NCHS_RACE_MAP)
    df["father.race.eth"] = _normalise(df["father.race.eth"]).map(NCHS_RACE_MAP)

    keep_re = [v for v in NCHS_RACE_MAP.values() if v not in ("All", "Others")]

    # Mother schedule
    mom = (df.loc[df["mother.race.eth"].isin(keep_re),
                  ["year", "mother.age", "mother.race.eth", "births"]]
             .groupby(["year", "mother.age", "mother.race.eth"], as_index=False, observed=True)["births"]
             .sum()
             .rename(columns={"mother.age": "age", "mother.race.eth": "race_eth"}))
    mom_all = mom.groupby(["year", "age"], as_index=False)["births"].sum().assign(race_eth="All")
    mom = pd.concat([mom_all, mom], ignore_index=True)
    mom["sex"] = "f"

    # Father schedule (drop NaN father.age)
    dad = (df.loc[df["father.race.eth"].isin(keep_re) & df["father.age"].notna(),
                  ["year", "father.age", "father.race.eth", "births"]]
             .groupby(["year", "father.age", "father.race.eth"], as_index=False, observed=True)["births"]
             .sum()
             .rename(columns={"father.age": "age", "father.race.eth": "race_eth"}))
    dad_all = dad.groupby(["year", "age"], as_index=False)["births"].sum().assign(race_eth="All")
    dad = pd.concat([dad_all, dad], ignore_index=True)
    dad["sex"] = "m"

    parents = pd.concat([mom, dad], ignore_index=True)
    parents["age"] = parents["age"].astype("int16")
    if pooled_only:
        parents = parents[parents["race_eth"] == "All"]

    pop = pop_long.copy()
    pop["age"] = pop["age"].astype("int16")
    merged = parents.merge(pop, on=["year", "age", "sex", "race_eth"], how="left")
    merged["pop"] = merged["pop"].fillna(0.0)
    merged["f_rate"] = np.where(merged["pop"] > 0,
                                merged["births"] / merged["pop"], 0.0)
    return merged[["year", "age", "sex", "race_eth", "f_rate"]]


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------

def build_all(force: bool = False, pooled_only: bool = False) -> None:
    targets = {
        "population_national": CACHE_DIR / "population_national.parquet",
        "mortality_rates":     CACHE_DIR / "mortality_rates.parquet",
        "fertility_rates":     CACHE_DIR / "fertility_rates.parquet",
    }

    if force or not targets["population_national"].exists():
        print("[ingest] Building national population from CDC WONDER ...")
        pop = build_population_national(pooled_only=pooled_only)
        pop.to_parquet(targets["population_national"], index=False)
        print(f"[ingest]   wrote {targets['population_national'].name} rows={len(pop):,}")
    else:
        print("[ingest] population_national.parquet exists; skipping.")

    pop = pd.read_parquet(targets["population_national"])

    if force or not targets["mortality_rates"].exists():
        mort = build_mortality_rates(pop, pooled_only=pooled_only)
        mort.to_parquet(targets["mortality_rates"], index=False)
        print(f"[ingest]   wrote {targets['mortality_rates'].name} rows={len(mort):,}")
    else:
        print("[ingest] mortality_rates.parquet exists; skipping.")

    if force or not targets["fertility_rates"].exists():
        fert = build_fertility_rates(pop, pooled_only=pooled_only)
        fert.to_parquet(targets["fertility_rates"], index=False)
        print(f"[ingest]   wrote {targets['fertility_rates'].name} rows={len(fert):,}")
    else:
        print("[ingest] fertility_rates.parquet exists; skipping.")

    print("[ingest] Done.")


def load_cache():
    pop  = pd.read_parquet(CACHE_DIR / "population_national.parquet")
    mort = pd.read_parquet(CACHE_DIR / "mortality_rates.parquet")
    fert = pd.read_parquet(CACHE_DIR / "fertility_rates.parquet")
    return pop, mort, fert


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--pooled-only", action="store_true",
                    help="Build only race_eth='All' tables (fast).")
    args = ap.parse_args()
    build_all(force=args.force, pooled_only=args.pooled_only)
