"""Orphanhood readout from kinship-engine output.

The engine produces, for each (birth_year c, focal_age x) pair, the column
m_x(t = c + x) describing the joint age × vital-status distribution of the
focal child's mother and father. We convert this to:

    P_either(c, x) = 1 - (1 - p_mom_dead) * (1 - p_dad_dead)

and then multiply by the population of focal age x in year t to get the
**prevalent orphan count** (current children under 18 who have at least one
deceased parent).

Two summary measures (matching the Villaveces 2025 paper):
    prevalent(t)  = Σ_{x=0..17} N_{x, t}^{children} * P_either(t - x, x)
    incident(t)   = Σ_{x=0..17} N_{x, t}^{children} *
                        [ P_either(t - x, x) - P_either(t - x, x - 1) ]
                  i.e. new orphan events in year t (approximately).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import AGES
from .calibrate import apply_calibration
from .engine import Rates, project_parents, prob_parent_dead


def parental_loss_grid(rates: Rates, *, year_min: int, year_max: int,
                       max_focal_age: int = 17) -> pd.DataFrame:
    """Produce a long DataFrame with one row per (focal_year, focal_age).

    Columns:
        focal_year, focal_age, birth_year,
        p_mom_dead, p_dad_dead, p_either_dead.
    """
    rows = []
    # Need rates years to cover birth_year through birth_year + 17 for every
    # focal_age x and focal_year t = birth_year + x.
    for t in range(year_min, year_max + 1):
        for x in range(max_focal_age + 1):
            c = t - x
            if c < rates.years[0] or c + max_focal_age > rates.years[-1]:
                continue
            # We re-project the parent block from c through c+17 just once
            # per cohort to amortise (handled by caching outside this loop in
            # practice). For clarity we re-call here; the runner script
            # caches.
            state = project_parents(rates, c, max_focal_age=max_focal_age)
            probs = prob_parent_dead(state[:, x], rates.ages.size)
            rows.append((t, x, c, probs["mom"], probs["dad"], probs["either"]))
    df = pd.DataFrame(rows, columns=["focal_year", "focal_age", "birth_year",
                                     "p_mom_dead", "p_dad_dead",
                                     "p_either_dead"])
    return df


def parental_loss_grid_cached(rates: Rates, *, year_min: int, year_max: int,
                              max_focal_age: int = 17,
                              kappa_f: np.ndarray | None = None,
                              kappa_m: np.ndarray | None = None,
                              kappa_years: np.ndarray | None = None) -> pd.DataFrame:
    """Faster variant: project each cohort once and slice for all focal ages.

    Only requires that the cohort's birth_year is within the rates window;
    `project_parents` projects as far as data allows. NaN slots are dropped.

    If `kappa_f` / `kappa_m` are provided (shape (ages, n_kappa_years), with
    column years given by `kappa_years`), the dead-block probabilities are
    weighted by the cohort-year column of κ before forming P_either. κ is
    indexed by the *parent's age at focal birth* and the *focal cohort year*.
    """
    rows = []
    cohorts_needed = set()
    for t in range(year_min, year_max + 1):
        for x in range(max_focal_age + 1):
            c = t - x
            if c < rates.years[0] or c > rates.years[-1]:
                continue
            cohorts_needed.add(c)

    cache: dict[int, np.ndarray] = {}
    for c in sorted(cohorts_needed):
        cache[c] = project_parents(rates, c, max_focal_age=max_focal_age)

    n = rates.ages.size

    use_kappa = (kappa_f is not None) and (kappa_m is not None) and (kappa_years is not None)
    if use_kappa:
        kappa_years_arr = np.asarray(kappa_years)

    for t in range(year_min, year_max + 1):
        for x in range(max_focal_age + 1):
            c = t - x
            if c not in cache:
                continue
            col = cache[c][:, x]
            if np.isnan(col).any():
                continue

            if use_kappa:
                if c < kappa_years_arr.min() or c > kappa_years_arr.max():
                    kf = np.ones(n)
                    km = np.ones(n)
                else:
                    j = int(np.where(kappa_years_arr == c)[0][0])
                    # Build per-age kappa vectors indexed by parent age at
                    # focal birth = age - x where 'age' indexes the dead block
                    # at year t (= parent age at year t). For x>0 we need to
                    # shift; the m block's age axis is "parent age at year t".
                    kf = np.ones(n)
                    km = np.ones(n)
                    for a in range(n):
                        a_at_birth = a - x
                        if 0 <= a_at_birth < n:
                            kf[a] = kappa_f[a_at_birth, j]
                            km[a] = kappa_m[a_at_birth, j]
                probs = apply_calibration(col, n, kf, km)
            else:
                probs = prob_parent_dead(col, n)

            rows.append((t, x, c, probs["mom"], probs["dad"], probs["either"]))

    return pd.DataFrame(rows, columns=["focal_year", "focal_age",
                                       "birth_year", "p_mom_dead",
                                       "p_dad_dead", "p_either_dead"])


def annual_summaries(
    grid: pd.DataFrame,
    pop_children: pd.DataFrame,
    *,
    race_eth: str = "All",
) -> pd.DataFrame:
    """Combine the parental-loss grid with child population to produce
    prevalent and incident orphan counts by year.

    Args:
        pop_children: long DF with columns year, age, sex, race_eth, pop.
            (Same shape as the cached `population_national.parquet`.)
    """
    pc = pop_children[(pop_children["race_eth"] == race_eth) &
                      (pop_children["age"] <= 17)].copy()
    pc_tot = (pc.groupby(["year", "age"], as_index=False)["pop"]
                .sum()
                .rename(columns={"year": "focal_year", "age": "focal_age",
                                 "pop": "N_child"}))

    df = grid.merge(pc_tot, on=["focal_year", "focal_age"], how="left")
    df["N_child"] = df["N_child"].fillna(0.0)
    df["orphans_prevalent"] = df["p_either_dead"] * df["N_child"]

    # Incidence is the within-cohort year-on-year increase in P(either dead),
    # so it represents *new* orphan events occurring in year t. For focal age
    # 0 this is the probability of a parent dying around the focal's birth.
    # We set incidence to NaN where the cohort's age-(x-1) observation is not
    # in our window (so the difference would be ill-defined), then back-fill
    # those with NaN; downstream aggregators sum only non-NaN values.
    df = df.sort_values(["birth_year", "focal_age"]).reset_index(drop=True)
    df["p_either_prev"] = df.groupby("birth_year")["p_either_dead"].shift(1)
    # Mark "first appearance of cohort" rows where focal_age > 0 as missing
    # rather than zero, to avoid double-counting against age 0 incidence.
    first_rows = df["p_either_prev"].isna() & (df["focal_age"] > 0)
    df.loc[first_rows, "p_either_prev"] = np.nan
    df["p_either_prev"] = df["p_either_prev"].fillna(0.0)
    df["orphans_incident"] = (df["p_either_dead"] - df["p_either_prev"]) * df["N_child"]
    df.loc[first_rows, "orphans_incident"] = np.nan

    # Aggregate to annual. For the incidence column we sum only rows where
    # the cohort previously appeared (so missing values are propagated to
    # NaN rather than treated as zero).
    inc_complete = df.groupby("focal_year")["orphans_incident"].apply(
        lambda s: float(s.sum(skipna=False))
    )
    out = (df.groupby("focal_year", as_index=False)
             .agg(prevalent=("orphans_prevalent", "sum"),
                  N_children_under18=("N_child", "sum"))
             .assign(race_eth=race_eth))
    out["incident"] = out["focal_year"].map(inc_complete)
    out = out[["focal_year", "race_eth", "prevalent", "incident",
               "N_children_under18"]]
    out["prevalence_rate_per_100k"] = (
        100000.0 * out["prevalent"] / out["N_children_under18"].where(out["N_children_under18"] > 0, np.nan)
    )
    return out[["focal_year", "race_eth", "prevalent", "incident",
                "N_children_under18", "prevalence_rate_per_100k"]].copy()
