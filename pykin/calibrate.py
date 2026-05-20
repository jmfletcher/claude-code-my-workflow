"""Load NHIS-derived fertility-by-mortality calibration factors and apply
them to the kinship-engine orphanhood readout.

The cell index in the NHIS table is (sex, raceth5, age, year). We convert to
an (ages, n_years) NumPy array per sex, indexed by *parent age at focal
birth* and *year-of-focal-birth* (= cohort year). The runner picks the right
columns at projection time.

NHIS raceth5 numeric codes map to the kinship engine race_eth labels as:
    1 Hispanic        -> "Hispanic"
    2 NH White        -> "Non-Hispanic White"
    3 NH Black        -> "Non-Hispanic Black"
    4 NH Asian or PI  -> "Non-Hispanic Asian or Pacific Islander"
    5 NH AIAN/other   -> "Non-Hispanic American Indian or Alaska Native"
For the pooled "All" run we collapse the table to a single weighted-average
kappa per (sex, age, year) using the number of weighted decedents from the
NHIS file as weights.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import AGES

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CALIB_SINGLEYEAR = PROJECT_ROOT / "results" / "py" / "nhis_calibration_singleyear.csv"

RACETH5_TO_KIN = {
    1: "Hispanic",
    2: "Non-Hispanic White",
    3: "Non-Hispanic Black",
    4: "Non-Hispanic Asian or Pacific Islander",
    5: "Non-Hispanic American Indian or Alaska Native",
}


def load_kappa_table() -> pd.DataFrame:
    """Return the NHIS calibration table with sex, raceth5, age, year, kappa."""
    df = pd.read_csv(CALIB_SINGLEYEAR)
    df["raceth5"] = df["raceth5"].astype(int)
    df["age"] = df["age"].astype(int)
    df["year"] = df["year"].astype(int)
    df["sex"] = df["sex"].astype(str)
    return df


def kappa_array_for(
    table: pd.DataFrame,
    *,
    race_eth: str = "All",
    years: range = range(1983, 2022),
    ages: int = AGES,
    weights: pd.DataFrame | None = None,
) -> dict[str, np.ndarray]:
    """Pivot the long kappa table into dense (ages, n_years) arrays per sex.

    Years and ages outside the table's coverage default to 1.0 (no calibration).
    For race_eth="All", we collapse over raceth5 using the weighted-mean of
    kappa with weights = `n_dead_w` from the by-cell file (passed in via
    `weights`). If `weights` is None we use the simple unweighted mean across
    raceth5.

    Returns dict with keys 'f' and 'm', each shape (ages, len(years)).
    """
    yrs = np.array(list(years), dtype=int)
    n = ages

    sub = table[(table["year"].isin(yrs)) & (table["age"] < n)].copy()

    if race_eth == "All":
        if weights is None:
            sub_grp = (sub.groupby(["sex", "age", "year"], as_index=False)["kappa"]
                          .mean())
        else:
            w = weights[["sex", "raceth5", "yeardec", "n_dead_w"]].copy()
            # The kappa table varies by age/year within decade; rather than
            # decade-aggregate we just use the by-cell weight pooled to the
            # (sex, raceth5) level summed over decades.
            wgrp = (w.groupby(["sex", "raceth5"], as_index=False)["n_dead_w"].sum()
                     .rename(columns={"n_dead_w": "w"}))
            sub = sub.merge(wgrp, on=["sex", "raceth5"], how="left")
            sub["w"] = sub["w"].fillna(0.0)
            num = (sub.assign(num=sub["kappa"] * sub["w"])
                      .groupby(["sex", "age", "year"], as_index=False)["num"]
                      .sum())
            den = sub.groupby(["sex", "age", "year"], as_index=False)["w"].sum()
            sub_grp = num.merge(den, on=["sex", "age", "year"])
            sub_grp["kappa"] = np.where(sub_grp["w"] > 0,
                                        sub_grp["num"] / sub_grp["w"], 1.0)
    else:
        target = None
        for raceth5_id, lbl in RACETH5_TO_KIN.items():
            if lbl == race_eth:
                target = raceth5_id
                break
        if target is None:
            raise ValueError(f"race_eth {race_eth!r} not in NHIS raceth5 map")
        sub_grp = sub[sub["raceth5"] == target]

    out = {}
    for sex in ("f", "m"):
        arr = np.ones((n, yrs.size))
        s = sub_grp[sub_grp["sex"] == sex]
        for _, r in s.iterrows():
            a = int(r["age"])
            y = int(r["year"])
            j = int(np.where(yrs == y)[0][0])
            arr[a, j] = float(r["kappa"])
        out[sex] = arr
    return out


def apply_calibration(
    state_col: np.ndarray,
    ages: int,
    kappa_f: np.ndarray,
    kappa_m: np.ndarray,
) -> dict[str, float]:
    """Re-compute parent-loss probability with κ multipliers applied to the
    dead blocks. `kappa_f`/`kappa_m` are 1-D arrays of length `ages` indexed
    by the parent's age at focal birth (cohort year).

    The state vector's dead-block age axis indexes the parent's age at the
    focal year (= parent_age_at_birth + focal_age). Caller must pass the
    correct kappa column for cohort year c.

    Important: this scales the mass per cell; the resulting `dead_f.sum()`
    can exceed 1 if κ > 1 (interpretable as "average number of orphan
    events per child" rather than "probability of at least one dead
    parent"). For headline orphan counts we treat the scaled mass as
    multiplicative weight on the standard orphan-count expression.
    """
    n = ages
    dead_f = state_col[2 * n:3 * n]
    dead_m = state_col[3 * n:4 * n]
    weighted_f = float(np.sum(kappa_f * dead_f))
    weighted_m = float(np.sum(kappa_m * dead_m))
    p_either = 1.0 - max(0.0, 1.0 - weighted_f) * max(0.0, 1.0 - weighted_m)
    return {"mom": weighted_f, "dad": weighted_m, "either": p_either}
