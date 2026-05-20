"""Export NHIS-based fertility-by-mortality calibration factors kappa_c.

For each cell c = (sex, raceth5, age_band, decade) we compute
    kappa_c = E[nk_under18 | died=1, c] / E[nk_under18 | died=0, c]
using NHIS person weights. Cells with too few deaths are pooled across age.

Inputs:
    nhis_with_coresident_minors.parquet (top-level)

Outputs:
    results/py/nhis_calibration_by_cell.csv      -- compact cell-level table
    results/py/nhis_calibration_singleyear.csv   -- expanded to
        (sex, raceth5, age, year) -> kappa for direct use by the kinship engine

The cell schema:
    sex       in {f, m}
    raceth5   in {1 Hispanic, 2 NH White, 3 NH Black, 4 NH Asian-PI,
                  5 NH AIAN+other+multiracial}
    age_band  in {18-29, 30-39, 40-49, 50-59, 60-69, 70+}
    decade    in {1: 1986-1989, 2: 1990-1999, 3: 2000-2009, 4: 2010-2018}
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARQUET = PROJECT_ROOT / "nhis_with_coresident_minors.parquet"
OUT_DIR = PROJECT_ROOT / "results" / "py"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ASIAN_CODES = [400, 410, 411, 412, 413, 414, 415, 416, 417, 419,
               420, 430, 431, 432, 433, 434]
AIAN_CODES  = [300, 310, 320, 330, 340, 350]

RACETH5_LABEL = {
    1: "Hispanic",
    2: "Non-Hispanic White",
    3: "Non-Hispanic Black",
    4: "Non-Hispanic Asian or Pacific Islander",
    5: "Non-Hispanic American Indian or Alaska Native",
}

AGE_BANDS = [(18, 29), (30, 39), (40, 49), (50, 59), (60, 69), (70, 100)]


def build_cells(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # died outcome, mortelig==1 only
    elig = out["mortelig"].eq(1)
    out["died"] = pd.Series(np.nan, index=out.index, dtype="float64")
    out.loc[elig & out["mortstat"].eq(1), "died"] = 1.0
    out.loc[elig & out["mortstat"].eq(2), "died"] = 0.0

    # raceth5 -- matches nhis_svy_mortality_logit.py
    hisp = out["hispeth"].between(20, 70, inclusive="both")
    race_nhx = pd.Series(pd.NA, index=out.index, dtype="Int8")
    racenew = out["racenew"]
    race_nhx = race_nhx.mask((~hisp) & racenew.eq(100), 1)
    race_nhx = race_nhx.mask((~hisp) & racenew.eq(200), 2)
    race_nhx = race_nhx.mask((~hisp) & racenew.eq(400), 3)
    race_nhx = race_nhx.mask((~hisp) & racenew.eq(300), 4)
    racea = out["racea"]
    race_nhx = race_nhx.mask(race_nhx.isna() & (~hisp) & racea.eq(100), 1)
    race_nhx = race_nhx.mask(race_nhx.isna() & (~hisp) & racea.eq(200), 2)
    race_nhx = race_nhx.mask(race_nhx.isna() & (~hisp) & racea.isin(ASIAN_CODES), 3)
    race_nhx = race_nhx.mask(race_nhx.isna() & (~hisp) & racea.isin(AIAN_CODES), 4)
    race_nhx = race_nhx.where(~(race_nhx.isna() & ~hisp), 5)

    raceth5 = pd.Series(pd.NA, index=out.index, dtype="Int8")
    raceth5 = raceth5.mask(hisp, 1)
    raceth5 = raceth5.mask((~hisp) & race_nhx.eq(1), 2)
    raceth5 = raceth5.mask((~hisp) & race_nhx.eq(2), 3)
    raceth5 = raceth5.mask((~hisp) & race_nhx.eq(3), 4)
    raceth5 = raceth5.mask((~hisp) & race_nhx.isin([4, 5]), 5)
    raceth5 = raceth5.fillna(5).astype("Int8")
    out["raceth5"] = raceth5

    # nk_under18
    nk = out["n_fam_childminor017"].astype("float64").fillna(0.0)
    out["nk_under18"] = nk.clip(0, 8)

    # decade FE
    yeardec = pd.Series(pd.NA, index=out.index, dtype="Int8")
    yeardec = yeardec.mask(out["year"].between(1986, 1989), 1)
    yeardec = yeardec.mask(out["year"].between(1990, 1999), 2)
    yeardec = yeardec.mask(out["year"].between(2000, 2009), 3)
    yeardec = yeardec.mask(out["year"].between(2010, 2018), 4)
    out["yeardec"] = yeardec

    # age band
    band_label = pd.Series(pd.NA, index=out.index, dtype="object")
    age = out["age"].astype("Int16")
    for lo, hi in AGE_BANDS:
        band_label = band_label.mask(age.between(lo, hi), f"{lo}-{hi}")
    out["age_band"] = band_label

    # sex -> 'f' / 'm' (NHIS coding: 1=male, 2=female)
    out["sex_label"] = out["sex"].map({1: "m", 2: "f"})

    # filter to analytic sample: mortelig==1, died observed, adult age band
    valid = (
        out["died"].isin([0.0, 1.0])
        & out["mortwtsa"].notna() & (out["mortwtsa"] > 0)
        & out["age_band"].notna()
        & out["yeardec"].notna()
        & out["raceth5"].notna()
        & out["sex_label"].isin(["f", "m"])
    )
    out = out.loc[valid, [
        "sex_label", "raceth5", "age_band", "yeardec",
        "died", "nk_under18", "mortwtsa",
    ]].rename(columns={"sex_label": "sex"}).copy()
    return out


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    w_sum = weights.sum()
    if w_sum <= 0:
        return np.nan
    return float((values * weights).sum() / w_sum)


def collapse_cells(rows: pd.DataFrame) -> pd.DataFrame:
    """Compute weighted means of nk_under18 by cell x died status."""
    out_rows = []
    grp_cols = ["sex", "raceth5", "age_band", "yeardec"]
    for keys, g in rows.groupby(grp_cols, observed=True):
        alive = g[g["died"] == 0.0]
        dead  = g[g["died"] == 1.0]

        n_alive = float(alive["mortwtsa"].sum())
        n_dead  = float(dead["mortwtsa"].sum())

        m_alive = weighted_mean(alive["nk_under18"].to_numpy(),
                                alive["mortwtsa"].to_numpy())
        m_dead  = weighted_mean(dead["nk_under18"].to_numpy(),
                                dead["mortwtsa"].to_numpy())

        out_rows.append({
            **dict(zip(grp_cols, keys)),
            "n_alive_w": n_alive,
            "n_dead_w":  n_dead,
            "n_alive_unw": len(alive),
            "n_dead_unw":  len(dead),
            "mean_nk_alive": m_alive,
            "mean_nk_dead":  m_dead,
            "kappa": (m_dead / m_alive) if (m_alive and m_alive > 0) else np.nan,
        })
    return pd.DataFrame(out_rows)


def smooth_kappa(cells: pd.DataFrame, min_dead_unw: int = 25) -> pd.DataFrame:
    """Where the dead cell is sparse, pool kappa within (sex, raceth5, decade)
    using a weighted average across age bands.

    Returns a copy of `cells` with a `kappa_smooth` column added.
    """
    out = cells.copy()
    out["kappa_smooth"] = out["kappa"]

    grp_cols = ["sex", "raceth5", "yeardec"]
    pooled = (
        out.groupby(grp_cols, observed=True)
           .apply(lambda g: weighted_mean(
               g["kappa"].to_numpy(),
               g["n_dead_w"].to_numpy(),
           ), include_groups=False)
           .rename("kappa_pool")
           .reset_index()
    )
    out = out.merge(pooled, on=grp_cols, how="left")
    sparse = out["n_dead_unw"] < min_dead_unw
    out.loc[sparse, "kappa_smooth"] = out.loc[sparse, "kappa_pool"]
    out["kappa_smooth"] = out["kappa_smooth"].fillna(out["kappa_pool"])
    out["kappa_smooth"] = out["kappa_smooth"].fillna(1.0)  # last resort
    return out


def expand_to_singleyear(cells_smoothed: pd.DataFrame) -> pd.DataFrame:
    """Project (sex, raceth5, age_band, yeardec) -> (sex, raceth5, age, year).

    age 0..17 are not parents in this regression; we assign kappa=1.0.
    age 18+ uses the band lookup with constant within the band.
    """
    rows = []
    band_to_ages = {f"{lo}-{hi}": list(range(lo, hi + 1)) for (lo, hi) in AGE_BANDS}
    decade_to_years = {
        1: list(range(1986, 1990)),
        2: list(range(1990, 2000)),
        3: list(range(2000, 2010)),
        4: list(range(2010, 2019)),  # last NHIS-LMF closeout 2019Q4
    }

    for _, r in cells_smoothed.iterrows():
        if r["age_band"] not in band_to_ages or r["yeardec"] not in decade_to_years:
            continue
        for age in band_to_ages[r["age_band"]]:
            for year in decade_to_years[r["yeardec"]]:
                rows.append({
                    "sex": r["sex"],
                    "raceth5": int(r["raceth5"]),
                    "age": age,
                    "year": year,
                    "kappa": float(r["kappa_smooth"]),
                })

    df = pd.DataFrame(rows)
    # Extend coverage years to 1983-2021 by holding kappa flat at the nearest
    # observed year (the kinship engine asks for kappa for 1983-2021).
    full_years = list(range(1983, 2022))
    out_rows = []
    for (sex, raceth5, age), g in df.groupby(["sex", "raceth5", "age"], observed=True):
        g = g.sort_values("year")
        # extend backward
        first_kappa = g["kappa"].iloc[0]
        first_year  = int(g["year"].min())
        for y in range(1983, first_year):
            out_rows.append({"sex": sex, "raceth5": int(raceth5),
                             "age": int(age), "year": y, "kappa": first_kappa})
        # observed years
        out_rows.extend(g.to_dict("records"))
        # extend forward
        last_kappa = g["kappa"].iloc[-1]
        last_year  = int(g["year"].max())
        for y in range(last_year + 1, 2022):
            out_rows.append({"sex": sex, "raceth5": int(raceth5),
                             "age": int(age), "year": y, "kappa": last_kappa})
    out_df = pd.DataFrame(out_rows)
    out_df["raceth5_label"] = out_df["raceth5"].map(RACETH5_LABEL)
    return out_df


def main():
    print(f"[calib] loading {PARQUET.name}")
    df = pd.read_parquet(PARQUET)
    df = build_cells(df)
    print(f"[calib] analytic rows: {len(df):,}")

    cells = collapse_cells(df)
    cells_sm = smooth_kappa(cells, min_dead_unw=25)

    cells_path = OUT_DIR / "nhis_calibration_by_cell.csv"
    cells_sm.to_csv(cells_path, index=False)
    print(f"[calib] wrote {cells_path.relative_to(PROJECT_ROOT)} rows={len(cells_sm)}")

    single = expand_to_singleyear(cells_sm)
    single_path = OUT_DIR / "nhis_calibration_singleyear.csv"
    single.to_csv(single_path, index=False)
    print(f"[calib] wrote {single_path.relative_to(PROJECT_ROOT)} rows={len(single):,}")

    # Show a short summary table
    print()
    print("=== kappa summary (smoothed) by (sex, raceth5, decade), pooled across age ===")
    summary = (cells_sm
               .groupby(["sex", "raceth5", "yeardec"], observed=True)
               .apply(lambda g: weighted_mean(
                   g["kappa_smooth"].to_numpy(),
                   g["n_dead_w"].to_numpy(),
               ), include_groups=False)
               .rename("kappa")
               .reset_index())
    summary["raceth5"] = summary["raceth5"].map(RACETH5_LABEL).fillna(summary["raceth5"].astype(str))
    print(summary.to_string(index=False, float_format=lambda x: f"{x:6.3f}"))


if __name__ == "__main__":
    main()
