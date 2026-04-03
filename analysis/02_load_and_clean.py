"""
Load, filter, and clean all Forward Exam years into a single analysis-ready panel.

Inputs:  Data/raw/forward/forward_certified_*.zip
Outputs:
  output/data/panel_school_race.parquet    — school-level, by race
  output/data/panel_district_race.parquet  — district-level, by race (DPI pre-computed)
  output/tables/02_qc_summary.txt          — suppression rates, counts, MMSD check

Run from repo root:
  python3 analysis/02_load_and_clean.py

Design decisions:
  - Filter TEST_GROUP == "Forward" (exclude DLM alternate assessment)
  - Filter GROUP_BY == "Race/Ethnicity" (main analysis group)
  - Filter TEST_SUBJECT in ("ELA", "Mathematics"), GRADE_LEVEL in (3..8)
  - Proficiency = PERCENT_OF_GROUP where TEST_RESULT in ("Proficient", "Advanced")
    → pct_proficient = sum of both levels (0–100 scale)
  - Suppression: PERCENT_OF_GROUP == "*" → NaN; if any level is suppressed,
    combined proficiency rate is NaN (conservative — do not impute)
  - n_tested = GROUP_COUNT for a group (same across all result-level rows)
  - Exclude 2020-21 from the primary panel (COVID disruption); saved separately
  - 2023-24 and 2024-25 each have two CSVs per zip — concatenate both
  - ELL Status (2015-18) harmonized to EL Status (2020+)
"""

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FORWARD_DIR = ROOT / "Data" / "raw" / "forward"
OUTPUT_DATA = ROOT / "output" / "data"
OUTPUT_TABLES = ROOT / "output" / "tables"
OUTPUT_DATA.mkdir(parents=True, exist_ok=True)
OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ANALYSIS_SUBJECTS = ("ELA", "Mathematics")
ANALYSIS_GRADES = (3, 4, 5, 6, 7, 8)
PROFICIENCY_LEVELS = ("Proficient", "Advanced")  # at-or-above proficiency
SUPPRESSION_SYMBOL = "*"
COVID_YEAR = "2020-21"
NEW_STANDARD_YEARS = ("2023-24", "2024-25")

# School-year analysis windows (for reference in report)
PRIMARY_YEARS = (
    "2015-16", "2016-17", "2017-18", "2018-19",
    "2021-22", "2022-23",
)  # excludes 2019-20 (no data) and 2020-21 (COVID)

# DPI race label → our canonical label (for readability in outputs)
RACE_RENAME = {
    "Amer Indian": "American Indian",
    "Pacific Isle": "Pacific Islander",
    "Two or More": "Two or More Races",
    "[Data Suppressed]": "Unknown/Suppressed",
}


# ---------------------------------------------------------------------------
# File reader
# ---------------------------------------------------------------------------

def read_forward_zip(zip_path: Path) -> pd.DataFrame:
    """
    Read all data CSVs from a Forward Exam zip file and return a single DataFrame.

    Handles:
    - 2015-16 to 2022-23: one CSV per zip
    - 2023-24 to 2024-25: two CSVs per zip (ELA_RDG_WRT and MTH_SCN_SOC)
    """
    with zipfile.ZipFile(zip_path) as zf:
        csv_names = [n for n in zf.namelist()
                     if n.lower().endswith(".csv") and "layout" not in n.lower()]
        if not csv_names:
            raise ValueError(f"No data CSV in {zip_path.name}")

        frames = []
        for csv_name in csv_names:
            with zf.open(csv_name) as f:
                raw = f.read()
                for enc in ("utf-8", "latin-1", "cp1252"):
                    try:
                        df = pd.read_csv(io.BytesIO(raw), encoding=enc, dtype=str, low_memory=False)
                        frames.append(df)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError(f"Could not decode {csv_name} in {zip_path.name}")

    result = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    return result


# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------

def clean_raw(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply standard cleaning to a raw DPI Forward Exam DataFrame.

    - Harmonize ELL Status → EL Status
    - Convert suppressed (*) values to NaN
    - Cast numeric columns
    """
    # Harmonize ELL → EL
    df["GROUP_BY"] = df["GROUP_BY"].str.replace("ELL Status", "EL Status", regex=False)

    # Convert suppression symbols to NaN
    for col in ("STUDENT_COUNT", "PERCENT_OF_GROUP", "GROUP_COUNT",
                "FORWARD_AVERAGE_SCALE_SCORE"):
        if col in df.columns:
            df[col] = df[col].replace(SUPPRESSION_SYMBOL, np.nan)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # TEST_RESULT and TEST_RESULT_CODE: keep as string but note suppressed rows
    df["suppressed"] = df["TEST_RESULT"] == SUPPRESSION_SYMBOL

    # Cast grade to int where possible
    df["GRADE_LEVEL"] = pd.to_numeric(df["GRADE_LEVEL"], errors="coerce")

    return df


# ---------------------------------------------------------------------------
# Core reshape: long (one row per result level) → wide (one row per group)
# ---------------------------------------------------------------------------

def reshape_to_proficiency(df: pd.DataFrame) -> pd.DataFrame:
    """
    From a cleaned, filtered DataFrame (one row per school×grade×subject×race×result),
    compute pct_proficient (= pct_proficient + pct_advanced) for each
    school×grade×subject×race combination.

    Returns one row per school × grade × subject × race × year.
    """
    GROUP_COLS = [
        "SCHOOL_YEAR", "AGENCY_TYPE", "CESA", "COUNTY",
        "DISTRICT_CODE", "DISTRICT_NAME", "SCHOOL_CODE", "SCHOOL_NAME",
        "CHARTER_IND", "TEST_SUBJECT", "GRADE_LEVEL", "TEST_GROUP",
        "GROUP_BY", "GROUP_BY_VALUE",
    ]

    # Fill NaN in key group columns so pandas groupby does not silently drop rows
    # (district-level rows have SCHOOL_CODE = NaN; statewide rows have multiple NaNs)
    df = df.copy()
    for col in ("SCHOOL_CODE", "SCHOOL_NAME", "COUNTY", "CESA", "CHARTER_IND"):
        if col in df.columns:
            df[col] = df[col].fillna("[missing]")

    # n_tested is constant within a group (same GROUP_COUNT for all result levels)
    # Take the first non-null value per group
    n_tested = (
        df.groupby(GROUP_COLS, sort=False, dropna=False)["GROUP_COUNT"]
        .first()
        .rename("n_tested")
        .reset_index()
    )

    # Average scale score (same for all result levels within a group)
    scale_score = (
        df.groupby(GROUP_COLS, sort=False, dropna=False)["FORWARD_AVERAGE_SCALE_SCORE"]
        .first()
        .rename("avg_scale_score")
        .reset_index()
    )

    # Proficiency: sum pct for Proficient + Advanced rows.
    # IMPORTANT: use n_tested as the LEFT side of the merge so that
    # fully-suppressed groups (zero Proficient/Advanced rows) appear as NaN,
    # not dropped entirely.
    prof_df = df[df["TEST_RESULT"].isin(PROFICIENCY_LEVELS)].copy()

    pct_prof = (
        prof_df.groupby(GROUP_COLS, sort=False, dropna=False)["PERCENT_OF_GROUP"]
        .sum(min_count=1)  # NaN only if all contributing rows are NaN
        .rename("pct_proficient")
        .reset_index()
    )

    n_prof = (
        prof_df.groupby(GROUP_COLS, sort=False, dropna=False)["STUDENT_COUNT"]
        .sum(min_count=1)
        .rename("n_at_or_above_proficient")
        .reset_index()
    )

    # Start from n_tested (all groups) → left-join proficiency data.
    # Groups with no Proficient/Advanced rows become NaN in pct_proficient.
    out = (
        n_tested
        .merge(pct_prof, on=GROUP_COLS, how="left")
        .merge(n_prof, on=GROUP_COLS, how="left")
        .merge(scale_score, on=GROUP_COLS, how="left")
    )

    # Flag suppressed: pct_proficient is NaN (no valid Proficient/Advanced data)
    # OR n_tested is NaN (group count itself is suppressed)
    out["suppressed"] = out["pct_proficient"].isna() | out["n_tested"].isna()

    return out


# ---------------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------------

def load_all_years(verbose: bool = True) -> pd.DataFrame:
    """
    Load, clean, and stack all Forward Exam years.
    Returns a combined DataFrame (long, one row per school×grade×subject×race×year).
    """
    zips = sorted(FORWARD_DIR.glob("forward_certified_*.zip"))
    if not zips:
        print(f"ERROR: No zip files found in {FORWARD_DIR}")
        print("Run: python3 analysis/00_download_data.py --era forward")
        sys.exit(1)

    all_frames = []
    for zip_path in zips:
        year = zip_path.stem.replace("forward_certified_", "")

        if verbose:
            flags = []
            if year == COVID_YEAR:
                flags.append("COVID")
            if year in NEW_STANDARD_YEARS:
                flags.append("NEW-STD")
            flag_str = f" [{','.join(flags)}]" if flags else ""
            print(f"  Loading {year}{flag_str}...", end="", flush=True)

        raw = read_forward_zip(zip_path)
        raw = clean_raw(raw)

        # Core filters
        raw = raw[
            (raw["TEST_GROUP"] == "Forward") &
            (raw["GROUP_BY"] == "Race/Ethnicity") &
            (raw["TEST_SUBJECT"].isin(ANALYSIS_SUBJECTS)) &
            (raw["GRADE_LEVEL"].isin(ANALYSIS_GRADES))
        ]

        if verbose:
            print(f" {len(raw):,} rows")

        all_frames.append(raw)

    combined = pd.concat(all_frames, ignore_index=True)
    return combined


# ---------------------------------------------------------------------------
# Post-processing
# ---------------------------------------------------------------------------

def add_analysis_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add year-level flags for COVID disruption and standards change."""
    df = df.copy()
    df["covid_year"] = df["SCHOOL_YEAR"] == COVID_YEAR
    df["new_standards"] = df["SCHOOL_YEAR"].isin(NEW_STANDARD_YEARS)
    df["primary_analysis"] = df["SCHOOL_YEAR"].isin(PRIMARY_YEARS)
    return df


def rename_race_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Expand DPI abbreviated race labels to full names."""
    df = df.copy()
    df["race"] = df["GROUP_BY_VALUE"].replace(RACE_RENAME)
    return df


# AGENCY_TYPE values in the Forward Exam DPI files (full strings, not codes):
#   NaN                                → Statewide rows (DISTRICT_NAME == "[Statewide]")
#   "School District"                  → District-level aggregate rows
#   "Public school"                    → Individual public school rows
#   "Non District Charter Schools"     → Non-district charters (individual schools)
#   "Public Schools-Multidistrict Charters" → Multi-district charters
#   "ICS Governance Board/Legal Entity"    → Independent charter schools
SCHOOL_AGENCY_TYPES = {
    "Public school",
    "Non District Charter Schools",
    "Public Schools-Multidistrict Charters",
    "ICS Governance Board/Legal Entity",
}
DISTRICT_AGENCY_TYPE = "School District"
STATEWIDE_AGENCY_TYPE = None  # NaN rows


RENAME_COLS = {
    "SCHOOL_YEAR": "year",
    "AGENCY_TYPE": "agency_type",
    "CESA": "cesa",
    "COUNTY": "county",
    "DISTRICT_CODE": "district_code",
    "DISTRICT_NAME": "district_name",
    "SCHOOL_CODE": "school_code",
    "SCHOOL_NAME": "school_name",
    "CHARTER_IND": "charter",
    "TEST_SUBJECT": "subject",
    "GRADE_LEVEL": "grade",
    "TEST_GROUP": "test_group",
    "GROUP_BY": "group_by",
    "GROUP_BY_VALUE": "group_by_value",
}


def make_school_panel(combined: pd.DataFrame) -> pd.DataFrame:
    """
    Build school-level panel: one row per school × grade × subject × race × year.
    Includes public schools and all charter school types.
    """
    school = combined[combined["AGENCY_TYPE"].isin(SCHOOL_AGENCY_TYPES)].copy()
    panel = reshape_to_proficiency(school)
    panel = add_analysis_flags(panel)
    panel = rename_race_labels(panel)
    panel = panel.rename(columns=RENAME_COLS)
    return panel


def make_district_panel(combined: pd.DataFrame) -> pd.DataFrame:
    """
    Build district-level panel using DPI pre-computed district rows.
    Aggregate all schools in a district; AGENCY_TYPE == "School District".
    """
    district = combined[combined["AGENCY_TYPE"] == DISTRICT_AGENCY_TYPE].copy()
    panel = reshape_to_proficiency(district)
    panel = add_analysis_flags(panel)
    panel = rename_race_labels(panel)
    panel = panel.rename(columns=RENAME_COLS)
    return panel


# ---------------------------------------------------------------------------
# QC report
# ---------------------------------------------------------------------------

def qc_report(school_panel: pd.DataFrame, district_panel: pd.DataFrame) -> str:
    """Generate a QC summary report as a string."""
    lines = []

    def log(s=""):
        lines.append(s)
        print(s)

    log("=" * 70)
    log("QC Report: Forward Exam Panel (02_load_and_clean.py)")
    log("=" * 70)
    log()

    # ---- School panel overview ----
    log("SCHOOL PANEL")
    log(f"  Total rows:      {len(school_panel):>10,}")
    log(f"  Primary years:   {len(school_panel[school_panel['primary_analysis']]):>10,}")
    log(f"  COVID year:      {len(school_panel[school_panel['covid_year']]):>10,}")
    log(f"  New-std years:   {len(school_panel[school_panel['new_standards']]):>10,}")
    log()

    # ---- Rows by year ----
    log("Rows per year (school panel):")
    year_counts = school_panel.groupby("year").agg(
        rows=("pct_proficient", "count"),
        n_suppressed=("suppressed", "sum"),
        pct_suppressed=("suppressed", "mean"),
        unique_schools=("school_code", "nunique"),
    ).reset_index()
    for _, r in year_counts.iterrows():
        flag = ""
        if r["year"] == COVID_YEAR:
            flag = "  ← COVID"
        if r["year"] in NEW_STANDARD_YEARS:
            flag = "  ← new standards"
        log(f"  {r['year']:<10}  {r['rows']:>7,} rows  "
            f"{r['unique_schools']:>5} schools  "
            f"suppressed: {r['pct_suppressed']:.1%}{flag}")
    log()

    # ---- Suppression by race (primary years only) ----
    primary = school_panel[school_panel["primary_analysis"]]
    log("Suppression rate by race (primary years, school panel):")
    race_sup = primary.groupby("race")["suppressed"].mean().sort_values(ascending=False)
    for race, rate in race_sup.items():
        log(f"  {race:<25} {rate:.1%}")
    log()

    # ---- MMSD verification ----
    mmsd = school_panel[school_panel["district_name"] == "Madison Metropolitan"]
    log("MMSD (Madison Metropolitan) school panel:")
    log(f"  Total rows:      {len(mmsd):,}")
    log(f"  Unique schools:  {mmsd['school_name'].nunique()}")
    log(f"  Years present:   {sorted(mmsd['year'].unique())}")
    log()

    mmsd_primary = mmsd[mmsd["primary_analysis"]]
    if len(mmsd_primary) > 0:
        log("MMSD proficiency by race (ELA, grade 5, primary years — spot check):")
        spot = mmsd_primary[
            (mmsd_primary["subject"] == "ELA") &
            (mmsd_primary["grade"] == 5)
        ]
        # District-level aggregate
        mmsd_dist = district_panel[
            (district_panel["district_name"] == "Madison Metropolitan") &
            (district_panel["primary_analysis"]) &
            (district_panel["subject"] == "ELA") &
            (district_panel["grade"] == 5)
        ]
        if len(mmsd_dist) > 0:
            log("  (District-level rows from DPI pre-computed district data)")
            log(f"  {'Race':<25} {'Year':<10} {'pct_prof':>9}  {'n_tested':>8}")
            for _, r in mmsd_dist.sort_values(["race", "year"]).iterrows():
                sup = " *" if r["suppressed"] else ""
                pct = f"{r['pct_proficient']:.1f}" if not r["suppressed"] else "  suppressed"
                log(f"  {r['race']:<25} {r['year']:<10} {pct:>9}  {r['n_tested']:>8.0f}{sup}")
        log()

    # ---- State-level gap (primary years, ELA grade 5) ----
    log("State-level Black–White ELA gap (grade 5, district panel, primary years):")
    state_dist = district_panel[
        (district_panel["district_code"].astype(str) == "0")  # state-level rows if present
        | (district_panel["district_name"].str.contains("State", case=False, na=False))
    ]
    if len(state_dist) == 0:
        # Fall back to statewide from school panel
        log("  (No explicit state-level rows; computing from school panel by year)")
        statewide = (
            school_panel[
                (school_panel["primary_analysis"]) &
                (school_panel["subject"] == "ELA") &
                (school_panel["grade"] == 5) &
                (school_panel["race"].isin(["Black", "White"])) &
                (~school_panel["suppressed"])
            ]
            .groupby(["year", "race"])
            .apply(lambda x: np.average(x["pct_proficient"],
                                        weights=x["n_tested"].fillna(1)), include_groups=False)
            .unstack("race")
        )
        if "White" in statewide and "Black" in statewide:
            statewide["gap"] = statewide["White"] - statewide["Black"]
            log(f"  {'Year':<10} {'White':>8} {'Black':>8} {'Gap':>8}")
            for yr, row in statewide.iterrows():
                log(f"  {yr:<10} {row.get('White', float('nan')):>8.1f} {row.get('Black', float('nan')):>8.1f} {row.get('gap', float('nan')):>8.1f}")
    log()

    log("OUTPUT FILES:")
    log(f"  {OUTPUT_DATA / 'panel_school_race.parquet'}")
    log(f"  {OUTPUT_DATA / 'panel_district_race.parquet'}")
    log()
    log("NEXT STEP:")
    log("  python3 analysis/03_state_gaps.py")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("Wisconsin Forward Exam — Load & Clean")
    print("=" * 70)
    print(f"\nForward Exam data: {FORWARD_DIR}")
    print(f"Output:            {OUTPUT_DATA}\n")

    # 1. Load all years
    print("Loading raw files...")
    combined = load_all_years(verbose=True)
    print(f"\nTotal filtered rows (all years): {len(combined):,}")

    # 2. Build school and district panels
    print("\nBuilding school-level panel...")
    school_panel = make_school_panel(combined)
    print(f"  School panel: {len(school_panel):,} rows")

    print("Building district-level panel...")
    district_panel = make_district_panel(combined)
    print(f"  District panel: {len(district_panel):,} rows")

    # 3. Save
    print("\nSaving...")
    school_panel.to_parquet(OUTPUT_DATA / "panel_school_race.parquet", index=False)
    district_panel.to_parquet(OUTPUT_DATA / "panel_district_race.parquet", index=False)
    print(f"  Saved: panel_school_race.parquet  ({(OUTPUT_DATA / 'panel_school_race.parquet').stat().st_size / 1e6:.1f} MB)")
    print(f"  Saved: panel_district_race.parquet ({(OUTPUT_DATA / 'panel_district_race.parquet').stat().st_size / 1e6:.1f} MB)")

    # 4. QC report
    print("\n" + "=" * 70)
    report = qc_report(school_panel, district_panel)
    qc_path = OUTPUT_TABLES / "02_qc_summary.txt"
    qc_path.write_text(report, encoding="utf-8")
    print(f"\nQC report saved to {qc_path}")
