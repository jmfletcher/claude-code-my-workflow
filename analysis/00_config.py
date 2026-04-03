"""
Shared constants for the Panel Conditioning analysis pipeline.

Cohort design:
  - Three UK birth cohort studies each selected one week of births.
  - The ONS data cover 9 adjacent birth weeks per cohort cluster and
    5 birth years per cluster (one treated, four controls).
  - Death years: 1970–2013.

Week-in-year coding (CHRONOLOGICAL, 1–9):
  Group 1 (NSHD, Feb/March cluster):
    1="3-9 Feb"  2="10-16 Feb"  3="17-23 Feb"  4="24-x Feb/Mar"
    5="3-9 Mar"  6="10-16 Mar"  7="17-23 Mar"  8="24-30 Mar"
    9="31-x Mar/Apr"
  Group 2 (NCDS, same cluster structure, birth years 1956-1960):
    identical week labels, treated week = "3-9 March 1958"
  Group 3 (BCS70, Mar/April/May cluster):
    1="8-14 Mar"  2="15-21 Mar"  3="22-28 Mar"  4="29-x Mar/Apr"
    5="5-11 Apr"  6="12-18 Apr"  7="19-25 Apr"  8="26-x Apr/May"
    9="3-9 May"

TREATED_WIY = 5  (chronological position, symmetric: 4 control weeks each side)
"""

from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]

DATA_DIR     = ROOT / "Data"
ANALYSIS_DIR = ROOT / "analysis"
OUTPUT_DIR   = ROOT / "output"
TABLES_DIR   = OUTPUT_DIR / "tables"
FIGURES_DIR  = OUTPUT_DIR / "figures"

# Source data
ONS_CAUSE_XLS = DATA_DIR / "deathsregisteredbycauseofdeathicdchapterbyselectedweekofbirthenglandandwales1970to2013_tcm77-419405.xls"
ONS_MONTH_XLS = DATA_DIR / "deathsregisteredbymonthbyselectedweekofbirthenglandandwales1970to2013_tcm77-419401.xls"
HMD_PATH      = DATA_DIR / "HMD" / "Mx_1x1.txt"

# Legacy processed CSV (produced by original Stata/R pipeline; used as ground-truth rates)
LEGACY_CSV = ROOT / "Old Attempts and Results" / "Terrence" / "mortality age final.csv"

# ── Study design ──────────────────────────────────────────────────────────────
# Cohort groups
GROUPS = {
    1: dict(name="NSHD", year=1946, study="NSHD 1946",
             birth_years=[1944, 1945, 1946, 1947, 1948]),
    2: dict(name="NCDS", year=1958, study="NCDS 1958",
             birth_years=[1956, 1957, 1958, 1959, 1960]),
    3: dict(name="BCS70", year=1970, study="BCS70 1970",
             birth_years=[1968, 1969, 1970, 1971, 1972]),
}

# Treated weeks (birth_week string → group)
TREATED_WEEKS = {
    "3-9 March 1946":   1,
    "3-9 March 1958":   2,
    "5-11 April 1970":  3,
}

# Chronological position of the treated week within each 9-week cluster
TREATED_WIY = 5

# Implied birth-cohort size per week (legacy denominator, deaths per 1,000)
# Back-calculated from observed death counts; mean 15,334 across birth weeks.
LEGACY_N_PER_WEEK = 15_334  # used only for reference; actual rates loaded from LEGACY_CSV

# HMD population code for England & Wales (combined)
HMD_POPNAME = "GBRTENW"

# Death-year range
DEATH_YEAR_MIN = 1970
DEATH_YEAR_MAX = 2013

# Age intervals for sub-group analysis
AGE_INTERVALS = [
    (0,  9,  "Age 0–9"),
    (10, 19, "Age 10–19"),
    (20, 29, "Age 20–29"),
    (30, 39, "Age 30–39"),
    (40, 49, "Age 40–49"),
    (50, 59, "Age 50–59"),
    (60, 69, "Age 60–69"),
]

# Robustness: narrow-window week ranges (uses chronological week_in_year 1-9)
# With treated at position 5 the baseline is fully symmetric (4 before, 4 after).
ROBUSTNESS_WINDOWS = {
    "R1: Symmetric narrow (weeks 2–8)":  (2, 8),   # 3 before + treated + 3 after
    "R2: Tightest symmetric (weeks 3–7)": (3, 7),   # 2 before + treated + 2 after
}

# Cause-of-death harmonisation (ICD-8/9/10 → 5 broad groups)
CAUSE_COLS_ICD8  = {
    "cancer":        ["140\xad239"],
    "cardiovascular": ["390\xad458", "460\xad474", "476\xad489"],
    "respiratory":   ["460\xad519"],   # approximate
    "external":      ["800\xad999"],
    "other":         [],               # remainder
}
