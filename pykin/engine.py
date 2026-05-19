"""Time-varying two-sex matrix kinship engine - parent block only.

Compact Python port of DemoKin's `kin_time_variant_2sex` (Williams,
Alburez-Gutierrez, Song & Hal, v1.0.3) restricted to the parent kin block
`m`, which is all we need for parental orphanhood under 18.

State vector (length 4 * ages):
    [ live-f (ages 0..ω) , live-m (ages 0..ω) ,
      dead-f (ages 0..ω) , dead-m (ages 0..ω) ]

Notation matches `explorations/kinship_math.md`.

API:
    rates_to_arrays(pop_df, mort_df, fert_df, ages, years)
        -> dict of (ages, len(years)) arrays per role (pf, pm, ff, fm, nf, nm)
    initial_parents(year, arrays)                    -> π_t  (4*ages,)
    project_parents(year_birth, focal_ages, arrays)  -> (4*ages, len(focal_ages))
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import AGES, BIRTH_FEMALE


# ---------------------------------------------------------------------------
# Rate ingestion helpers
# ---------------------------------------------------------------------------

@dataclass
class Rates:
    """Dense per-year arrays needed by the engine.

    Each array has shape (ages, n_years). `years` is the calendar year index.
    """
    years: np.ndarray   # int 1-d
    ages:  np.ndarray   # int 1-d, 0 .. ages-1
    pf: np.ndarray      # survival prob, female (= 1 - q)
    pm: np.ndarray      # survival prob, male
    ff: np.ndarray      # age-specific fertility, female parent
    fm: np.ndarray      # age-specific fertility, male parent
    nf: np.ndarray      # population, female (for π_t)
    nm: np.ndarray      # population, male


def rates_to_arrays(
    pop_df: pd.DataFrame,
    mort_df: pd.DataFrame,
    fert_df: pd.DataFrame,
    *,
    race_eth: str = "All",
    years: range = range(1983, 2022),
    ages: int = AGES,
) -> Rates:
    """Pivot the long parquet tables into dense (ages, years) NumPy arrays.

    Years outside the source coverage (e.g. 1983-1989 when CDC bridged-race
    population starts in 1990) are back-filled using the earliest available
    year as a proxy, then forward-filled across any internal gaps. This
    matches the convention used by Villaveces et al. and similar US
    kinship-orphanhood pipelines.
    """
    yrs = np.array(list(years), dtype=int)
    ag = np.arange(ages, dtype=int)

    def _pivot(df, value_col, sex, fill_value=0.0):
        sub = df[(df["race_eth"] == race_eth) & (df["sex"] == sex)].copy()
        wide = (sub.pivot_table(index="age", columns="year", values=value_col,
                                aggfunc="sum", fill_value=fill_value)
                   .reindex(index=ag, fill_value=fill_value))
        # Backfill and forward-fill missing years.
        source_years = sorted(wide.columns.tolist())
        if not source_years:
            return np.full((ages, len(yrs)), fill_value, dtype=float)
        wide = wide.reindex(columns=yrs)
        wide = wide.bfill(axis=1).ffill(axis=1)
        wide = wide.fillna(fill_value)
        return wide.to_numpy(dtype=float)

    qf = _pivot(mort_df, "q", "f")
    qm = _pivot(mort_df, "q", "m")
    pf = np.clip(1.0 - qf, 0.0, 1.0)
    pm = np.clip(1.0 - qm, 0.0, 1.0)

    ff = _pivot(fert_df, "f_rate", "f")
    fm = _pivot(fert_df, "f_rate", "m")

    nf = _pivot(pop_df, "pop", "f")
    nm = _pivot(pop_df, "pop", "m")

    return Rates(years=yrs, ages=ag, pf=pf, pm=pm, ff=ff, fm=fm, nf=nf, nm=nm)


# ---------------------------------------------------------------------------
# Block matrix construction
# ---------------------------------------------------------------------------

def build_U(pf_t: np.ndarray, pm_t: np.ndarray) -> np.ndarray:
    """Build the 4n x 4n transition matrix for year t.

    Differs from DemoKin's `kin_time_variant_2sex` by making the dead blocks
    **absorbing** (bottom-right = identity, top-right = zero): once a parent
    is dead they stay tracked there. This makes the bottom blocks of the
    state vector represent CUMULATIVE probability of parent death, which is
    exactly the quantity needed for prevalent-orphanhood readouts.

    Aging happens via subdiagonal of U^s_t. The bottom-left block records
    new deaths in the period (diag(1 - p^s_a)). Dead kin are aged forward
    as well so we can read the age distribution at death later.

    Shape: (4 * ages, 4 * ages).
    """
    n = pf_t.shape[0]
    Uf = np.zeros((n, n))
    Um = np.zeros((n, n))
    for a in range(n - 1):
        Uf[a + 1, a] = pf_t[a]
        Um[a + 1, a] = pm_t[a]
    Uf[n - 1, n - 1] = pf_t[n - 1]   # open class survives in place
    Um[n - 1, n - 1] = pm_t[n - 1]

    Mf = np.diag(1.0 - pf_t)
    Mm = np.diag(1.0 - pm_t)

    # Age the already-dead block forward (so cumulative-dead mass is preserved
    # across the diagonal). G is the same age-shift used for the live blocks.
    G = np.zeros((n, n))
    for a in range(n - 1):
        G[a + 1, a] = 1.0
    G[n - 1, n - 1] = 1.0

    Z = np.zeros((n, n))
    top    = np.block([[Uf, Z, Z, Z],
                       [Z, Um, Z, Z]])
    bottom = np.block([[Mf, Z, G, Z],
                       [Z, Mm, Z, G]])
    U_block = np.vstack([top, bottom])
    return U_block


def initial_parents(rates: Rates, t_index: int) -> np.ndarray:
    """π_t  -- age distribution of mothers and fathers when focal is born.

    Computed from the population age distribution × age-specific fertility:
        π^s_t[a] = (n^s_{a,t} * f^s_{a,t}) / Σ_a (n^s_{a,t} * f^s_{a,t})
    matching DemoKin's `nf * ff` formulation.
    """
    n = rates.ages.size
    pi_f = rates.nf[:, t_index] * rates.ff[:, t_index]
    pi_m = rates.nm[:, t_index] * rates.fm[:, t_index]

    s_f = pi_f.sum()
    s_m = pi_m.sum()
    if s_f > 0:
        pi_f = pi_f / s_f
    if s_m > 0:
        pi_m = pi_m / s_m

    state = np.zeros(4 * n)
    state[0:n] = pi_f                # live female parents
    state[n:2 * n] = pi_m            # live male parents
    return state


def project_parents(
    rates: Rates,
    birth_year: int,
    *,
    max_focal_age: int = 17,
) -> np.ndarray:
    """Project the parent kin block forward across focal ages 0..max_focal_age.

    If the rates table does not cover all needed years (birth_year through
    birth_year + max_focal_age), the trajectory is projected as far as
    possible and remaining columns are filled with NaN. The
    `rates_to_arrays` helper already backfills missing years so this branch
    is rarely hit in practice.

    Returns array of shape (4 * ages, max_focal_age + 1):
        state[:, x] = m_x(t = birth_year + x)
    """
    n = rates.ages.size
    if birth_year < rates.years[0]:
        raise ValueError(
            f"birth_year {birth_year} < earliest rate year {rates.years[0]}"
        )

    out = np.full((4 * n, max_focal_age + 1), np.nan)
    t0_idx = int(np.where(rates.years == birth_year)[0][0])
    out[:, 0] = initial_parents(rates, t0_idx)

    last_t_idx = rates.years.size - 1
    for x in range(max_focal_age):
        t_idx = t0_idx + x
        if t_idx > last_t_idx:
            break
        U_t = build_U(rates.pf[:, t_idx], rates.pm[:, t_idx])
        out[:, x + 1] = U_t @ out[:, x]
    return out


# ---------------------------------------------------------------------------
# Helpers for orphanhood readout
# ---------------------------------------------------------------------------

def split_state(state_col: np.ndarray, ages: int) -> dict[str, np.ndarray]:
    """Split a column of the state vector into the four blocks."""
    n = ages
    return {
        "live_f": state_col[0:n],
        "live_m": state_col[n:2 * n],
        "dead_f": state_col[2 * n:3 * n],
        "dead_m": state_col[3 * n:4 * n],
    }


def prob_parent_dead(state_col: np.ndarray, ages: int) -> dict[str, float]:
    """Probabilities that mother / father / either is dead, given state_col."""
    parts = split_state(state_col, ages)
    p_mom_dead = parts["dead_f"].sum()
    p_dad_dead = parts["dead_m"].sum()
    # P(at least one dead) under independence assumption between maternal &
    # paternal mortality (the matrix kinship default).
    p_either = 1.0 - (1.0 - p_mom_dead) * (1.0 - p_dad_dead)
    return {"mom": p_mom_dead, "dad": p_dad_dead, "either": p_either}
