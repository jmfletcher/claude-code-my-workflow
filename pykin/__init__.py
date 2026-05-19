"""pykin: a minimal Python port of the Caswell & Song (2021) time-varying
matrix kinship model, scoped to parental orphanhood under 18.

Modules:
    ingest    -- Read NCHS/Villaveces RDS files and produce national
                 single-year-of-age fertility, mortality, and population
                 tables (parquet cache).
    engine    -- Build the U and F block matrices and project the parent
                 kin block forward in time. Two-sex.
    orphanhood -- Convert engine output into orphanhood prevalence and
                 incidence among focal children under 18.
    calibrate -- Apply NHIS-derived kappa_c multipliers to the fertility
                 inputs.

Conventions:
    AGES = 0 .. 100 (open at 100+).
    Sexes f, m.
    Race/eth = "All" or one of the five NHIS-style buckets.
    All flows are annual.
"""

AGES = 101
BIRTH_FEMALE = 1.0 / 2.04  # Female share at birth, per DemoKin default.

RACE_ETH_CATEGORIES = (
    "All",
    "Non-Hispanic White",
    "Non-Hispanic Black",
    "Non-Hispanic Asian",
    "Non-Hispanic American Indian or Alaska Native",
    "Hispanic",
)

__all__ = ["AGES", "BIRTH_FEMALE", "RACE_ETH_CATEGORIES"]
