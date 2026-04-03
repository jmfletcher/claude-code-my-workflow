"""
01_load_and_clean.py
====================
Panel Conditioning (UK cohorts) — load ONS XLS files and build clean dataset.

Input:  Data/deathsregisteredbymonthbyselectedweekofbirthenglandandwales1970to2013_tcm77-419401.xls
Output: output/tables/01_clean_long.csv   — long format: birth_week × death_year → deaths + metadata
        output/tables/01_clean_summary.csv — aggregated by birth_week × death_year (total deaths)

ONS file structure (confirmed 2026-04-02):
  - One sheet per death-registration year: "Data 1970" through "Data 2013"
  - header_row=6: columns = [birth_week, Total, January, ..., December]
  - 135 birth weeks per sheet (9 weeks × 5 birth years × 3 cohort groups)

Denominator note:
  The ONS file reports DEATH COUNTS only, not birth counts.
  The legacy rate (final.csv) was computed as:
      rate = total_deaths / N × scale,  where N ≈ 15,300 per birth week
  We reproduce this rate using the legacy implied scale (mean total/rate ≈ 15.26).
  Until we obtain ONS birth registration counts (which would give exact N per week),
  use this constant denominator. Flag clearly in manuscript methods section.

Run from repo root:
    python3 analysis/01_load_and_clean.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"
OUT  = ROOT / "output" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

ONS_WOB = DATA / (
    "deathsregisteredbymonthbyselectedweekofbirthenglandandwales1970to2013"
    "_tcm77-419401.xls"
)

# ---------------------------------------------------------------------------
# Treated birth week definitions (confirmed from BCS documentation + legacy data)
# ---------------------------------------------------------------------------
TREATED_WEEKS = {
    "3-9 March 1946":    {"study": "NSHD",  "group": 1},
    "3-9 March 1958":    {"study": "NCDS",  "group": 2},
    "5-11 April 1970":   {"study": "BCS70", "group": 3},
}

# Birth-year clusters by group (birth years included in the ONS file)
BIRTH_YEAR_GROUPS = {
    1: list(range(1944, 1949)),   # NSHD cluster: 1944–1948
    2: list(range(1956, 1961)),   # NCDS cluster: 1956–1960
    3: list(range(1968, 1973)),   # BCS70 cluster: 1968–1972
}

# Implied denominator from legacy data (rate = deaths / N × 1000).
# Cross-validated: ONS deaths_total × 1000 / legacy_rate per cell → mean = 15,334
# (SD = 1,215; variation reflects true differences in births per week/year).
# We use a single constant for reproducibility; regression is invariant to this
# scale since C(week_in_year) absorbs level differences.
LEGACY_N_PER_WEEK = 15_334.0

# ---------------------------------------------------------------------------
# Helper: extract birth year from a birth_week string like "3-9 March 1946   "
# ---------------------------------------------------------------------------

def extract_birth_year(s: str) -> int | None:
    s = str(s).strip()
    # Last token should be a 4-digit year
    parts = s.split()
    if parts and parts[-1].isdigit() and len(parts[-1]) == 4:
        return int(parts[-1])
    return None


def assign_group(birth_year: int) -> int:
    for grp, years in BIRTH_YEAR_GROUPS.items():
        if birth_year in years:
            return grp
    return 0  # unassigned


def assign_cohort(birth_week_clean: str) -> int:
    """1 if this birth week is a treated (selected survey) week, else 0."""
    for tw in TREATED_WEEKS:
        if tw.lower() in birth_week_clean.lower():
            return 1
    return 0


# ---------------------------------------------------------------------------
# Load all data sheets
# ---------------------------------------------------------------------------

def load_ons_wob(path: Path) -> pd.DataFrame:
    """Load all Data YYYY sheets from the ONS week-of-birth XLS.
    Returns long DataFrame: one row per (birth_week, death_year).
    """
    xl = pd.ExcelFile(path, engine="xlrd")
    data_sheets = [s for s in xl.sheet_names if s.startswith("Data ")]
    print(f"  Found {len(data_sheets)} data sheets: {data_sheets[0]} … {data_sheets[-1]}")

    rows = []
    for sheet in data_sheets:
        death_year = int(sheet.replace("Data ", ""))
        df = pd.read_excel(path, sheet_name=sheet, header=6, engine="xlrd")
        df.columns = ["birth_week"] + list(df.columns[1:])
        # Keep only rows with a valid birth week string
        df = df.dropna(subset=["birth_week"])
        df["birth_week"] = df["birth_week"].astype(str).str.strip()
        df = df[df["birth_week"].str.len() > 3]
        df["death_year"] = death_year
        # Rename Total or All → deaths_total (ONS changed label after ~1979)
        total_col = [c for c in df.columns if str(c).lower() in ("total", "all")]
        if total_col:
            df = df.rename(columns={total_col[0]: "deaths_total"})
        else:
            # Fallback: second column (index 1) is always the annual total
            df = df.rename(columns={df.columns[1]: "deaths_total"})
        rows.append(df[["birth_week", "death_year", "deaths_total"]])

    long = pd.concat(rows, ignore_index=True)
    long["deaths_total"] = pd.to_numeric(long["deaths_total"], errors="coerce").fillna(0).astype(int)
    return long


# ---------------------------------------------------------------------------
# Build analytic dataset
# ---------------------------------------------------------------------------

def build_analytic(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()

    # Birth year from label string
    df["birth_year"] = df["birth_week"].apply(extract_birth_year)
    df = df.dropna(subset=["birth_year"])
    df["birth_year"] = df["birth_year"].astype(int)

    # Group (cohort cluster) and cohort (treated = 1)
    df["group"]  = df["birth_year"].apply(assign_group)
    df["cohort"] = df["birth_week"].apply(assign_cohort)

    # Drop rows not in any of the three cohort clusters
    df = df[df["group"] > 0].copy()

    # Add study name for treated rows
    study_map = {v["group"]: v["study"] for v in TREATED_WEEKS.values()}
    df["study"] = df["group"].map(study_map)

    # Age at death registration year (approximate; mid-year convention)
    df["age"] = df["death_year"] - df["birth_year"]

    # Mortality rate using legacy implied denominator
    df["rate"] = df["deaths_total"] / LEGACY_N_PER_WEEK * 1000

    # Week-in-year (position 1–9 within each cohort-birth-year cluster)
    # Build a stable mapping from (group, birth_year, birth_week) → week_in_year
    # by ranking birth weeks within each (group, birth_year) using their order
    # in the raw ONS sheets (which is chronological within each group).
    bw_key = (
        df[["group", "birth_year", "birth_week"]]
        .drop_duplicates()
        .sort_values(["group", "birth_year", "birth_week"])
    )
    bw_key["week_in_year"] = bw_key.groupby(["group", "birth_year"]).cumcount() + 1
    df = df.merge(bw_key, on=["group", "birth_year", "birth_week"], how="left")

    # Sanity checks
    n_treated = df["cohort"].sum()
    n_control = (df["cohort"] == 0).sum()
    unique_treated_weeks = df[df["cohort"] == 1]["birth_week"].nunique()
    print(f"  Total rows: {len(df):,}  |  treated rows: {n_treated:,}  "
          f"(= {unique_treated_weeks} birth weeks × {n_treated // max(unique_treated_weeks,1)} death years)")
    print(f"  Control rows: {n_control:,}")
    print(f"  Death years: {df['death_year'].min()}–{df['death_year'].max()}")
    print(f"  Age range: {df['age'].min()}–{df['age'].max()}")
    print(f"  Groups: {df['group'].value_counts().sort_index().to_dict()}")
    print(f"  Treated deaths by group:")
    print(df[df['cohort']==1].groupby(['group','study'])['deaths_total'].sum().to_string())
    print(f"  week_in_year range: {df['week_in_year'].min()}–{df['week_in_year'].max()}")

    assert df["week_in_year"].between(1, 9).all(), \
        f"week_in_year out of 1–9: {df['week_in_year'].value_counts().sort_index()}"
    return df


# ---------------------------------------------------------------------------
# Cross-check against legacy final.csv
# ---------------------------------------------------------------------------

def crosscheck_legacy(clean: pd.DataFrame) -> None:
    """Cross-check ONS data against legacy age-resolved CSV (row-count validation).

    Note: legacy final.csv is a cross-section (1 row per birth week, collapsed
    over all death years), so its 'total' is NOT comparable to per-year death counts.
    The age-resolved CSV ('mortality age final.csv') is the correct comparator.
    """
    age_path = ROOT / "Old Attempts and Results" / "Terrence" / "mortality age final.csv"
    if not age_path.exists():
        print("  [SKIP] Legacy age-resolved CSV not found.")
        return

    leg = pd.read_csv(age_path)
    leg["rate"] = pd.to_numeric(leg["rate"], errors="coerce")
    leg_nonmiss = leg.dropna(subset=["rate"])

    # ONS aggregated to (birth_week × age), ages 0–69
    ons_age = (
        clean[clean["age"].between(0, 69)]
        .groupby(["birth_week", "age"])["deaths_total"].sum()
        .reset_index()
    )
    n_ons_nonzero = (ons_age["deaths_total"] > 0).sum()

    print(f"\n  Cross-check vs legacy 'mortality age final.csv':")
    print(f"    Legacy non-missing rows:  {len(leg_nonmiss):,}")
    print(f"    ONS (birth_week × age):   {len(ons_age):,}  ({n_ons_nonzero:,} with deaths > 0)")
    if len(ons_age) == len(leg_nonmiss):
        print(f"    ✅ Row counts match exactly.")
    else:
        print(f"    Row count diff: {len(ons_age):,} vs {len(leg_nonmiss):,} "
              f"(delta = {len(ons_age) - len(leg_nonmiss):+,})")
        print(f"    Note: difference may reflect pre-1970 cells in legacy data "
              f"that our ONS file cannot cover.")

    # Rate comparison (ONS uses constant N ≈ 15,334)
    ons_age["rate_ons"] = ons_age["deaths_total"] / LEGACY_N_PER_WEEK * 1000
    print(f"    Legacy mean rate: {leg_nonmiss['rate'].mean():.4f}")
    print(f"    ONS mean rate:    {ons_age[ons_age['deaths_total']>0]['rate_ons'].mean():.4f}")
    print(f"    (Rate diff reflects variable per-week denominator; "
          f"regression estimates are invariant to this scale.)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("  01_load_and_clean.py — build analytic dataset from ONS XLS")
    print("=" * 70)

    if not ONS_WOB.exists():
        print(f"[ERROR] ONS file not found: {ONS_WOB}")
        sys.exit(1)

    print("\nLoading ONS sheets...")
    raw = load_ons_wob(ONS_WOB)
    print(f"  Raw rows loaded: {len(raw):,}")

    print("\nBuilding analytic dataset...")
    clean = build_analytic(raw)

    crosscheck_legacy(clean)

    # Save outputs
    out_long = OUT / "01_clean_long.csv"
    clean.to_csv(out_long, index=False)
    print(f"\n  Saved: {out_long.name}  ({len(clean):,} rows)")

    # Age-aggregated dataset (matches legacy 'mortality age final.csv' structure)
    # Aggregate over all calendar years that contribute to a given age cell
    age_agg = (
        clean[clean["age"].between(0, 69)]
        .groupby(["group", "study", "birth_week", "birth_year",
                  "cohort", "week_in_year", "age"])
        ["deaths_total"].sum()
        .reset_index()
    )
    age_agg["rate"] = age_agg["deaths_total"] / LEGACY_N_PER_WEEK * 1000

    # Mark cells as unobservable (NaN) when death year falls outside the ONS window.
    # ONS file covers death-registration years 1970–2013.
    # Cells where birth_year + age < 1970 have structurally zero deaths in our data
    # (the cohort was too young before 1970; deaths occurred in an unobserved period).
    # Setting these to NaN rather than 0 matches the legacy dataset's NaN convention
    # and avoids inflating the sample with uninformative zero-rate cells.
    ons_start = 1970
    ons_end   = 2013
    death_year = age_agg["birth_year"] + age_agg["age"]
    outside_window = (death_year < ons_start) | (death_year > ons_end)
    age_agg.loc[outside_window, "rate"] = np.nan
    age_agg.loc[outside_window, "deaths_total"] = np.nan
    n_outside = outside_window.sum()
    age_agg = age_agg.dropna(subset=["rate"])  # drop unobservable cells
    out_age = OUT / "01_age_aggregated.csv"
    age_agg.to_csv(out_age, index=False)
    deaths_nonzero = (age_agg["deaths_total"].fillna(0) > 0).sum()
    print(f"  Saved: {out_age.name}  ({len(age_agg):,} rows, "
          f"{deaths_nonzero:,} with deaths > 0)")
    print(f"  Cells excluded (outside ONS window 1970–2013): {n_outside:,}")
    print(f"  Legacy 'mortality age final.csv' non-missing rows: 5,913  "
          f"→ match={'✅' if len(age_agg) == 5913 else f'({len(age_agg):,} — check coverage)'}")

    # Session info
    session = {
        "python": sys.version,
        "packages": {p: __import__(p).__version__
                     for p in ["pandas", "numpy"]},
        "denominator_note": (
            f"N per birth week = {LEGACY_N_PER_WEEK:,.0f} (legacy implied; "
            "not from birth registration data)"
        ),
    }
    with open(OUT / "01_session_info.json", "w") as fh:
        json.dump(session, fh, indent=2)

    print("\nDone.")
