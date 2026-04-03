"""
03_load_wkce.py — Load and clean WKCE Scale Score Summary (SSS) data (2003-04 to 2013-14).

DATA ERA: WKCE (Wisconsin Knowledge and Concepts Exam) — pre-Forward Exam era.
DO NOT mix outputs from this script with Forward Exam panels (panel_school_race.parquet,
panel_district_race.parquet). This is a SEPARATE, NON-BRIDGED analysis era.

Source files: Data/raw/wkce_sss/  (tab-delimited TXT files from Keo SSS archive)
Codebook:     Data/archive/keo_compiled/layout_EXW_IAS_SPS_SSS (1).xls

Student Group codes used in this script:
  Org Level 1 = statewide, 2 = district, 3 = school, 4 = CESA
  14 = American Indian/Alaska Native
  15 = Asian/Pacific Islander  (pre-2010-11; split into separate codes after 2010-11)
  16 = Black (Not of Hispanic Origin)
  17 = Hispanic
  18 = White (Not of Hispanic Origin)
  19 = Race/Eth Code Missing or Invalid  (excluded)
  20 = Combined Race/Eth Groups (suppression stand-in, excluded)

Race category change at 2010-11 boundary:
  Pre-2010-11:  codes 14–18 (5 categories; no "Two or More")
  2010-11+:     same codes plus additional split codes for Asian/Pacific Islander subcategories
                and new "Two or More Races" code. Check layout file to confirm post-2010-11 additions.

Outputs:
  output/data/panel_wkce_district_race.parquet   — district × year × grade × subject × race
  output/tables/wkce_qc_summary.txt              — coverage, suppression, and era notes
"""

from pathlib import Path
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "Data" / "raw" / "wkce_sss"
OUT_DATA = ROOT / "output" / "data"
OUT_TABLES = ROOT / "output" / "tables"

OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_TABLES.mkdir(parents=True, exist_ok=True)

# Race/ethnicity codes → canonical label mapping.
# NOTE: codes may expand after 2010-11; update if additional codes are discovered.
RACE_CODE_MAP = {
    "14": "Amer Indian",
    "15": "Asian/PI",        # pre-2010-11 combined; flag as pre-split
    "16": "Black",
    "17": "Hispanic",
    "18": "White",
    # Post-2010-11 codes (to confirm against layout when loading those years):
    # "XX": "Asian",
    # "YY": "Pacific Isle",
    # "ZZ": "Two or More",
}

# Exclude: missing/invalid race, combined suppression groups, non-race groups
EXCLUDE_CODES = {"19", "20"}

# Org levels to keep
ORG_LEVEL_DISTRICT = "2"   # district-level rows
ORG_LEVEL_STATE    = "1"   # statewide rows (useful for reference)
ORG_LEVEL_SCHOOL   = "3"   # school-level (very high suppression; skip for now)

# Year boundary for race category change
RACE_CATEGORY_CHANGE_YEAR = 2011  # 2010-11 school year → numeric year label in file = 2011

# Subjects: each subject has an N, mean, SD, and percentile columns
SUBJECTS = ["Reading", "Language Arts", "Math", "Science", "Social Studies"]

# Peer districts for MMSD comparison analysis (Forward Exam era validated).
# District names in WKCE files are ABBREVIATED (e.g., "MADISON" not "Madison Metropolitan").
# Confirm exact strings by running 00_inspect_wkce.py (TODO).
PEER_DISTRICTS = {
    # Tier 1 — major urban
    "MILWAUKEE",
    "RACINE",
    "KENOSHA",
    "GREEN BAY",
    "BELOIT",
    # Tier 2 — mid-size
    "SUN PRAIRIE",
    "APPLETON",
    "WAUKESHA",
    "JANESVILLE",
    "W ALLIS",           # West Allis-West Milwaukee — confirm abbreviation
    # Madison region
    "VERONA",
    "MIDDLETON",
    # MMSD itself
    "MADISON",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    print(msg, flush=True)


def parse_numeric(series: pd.Series) -> pd.Series:
    """Convert a string column to float; suppress/missing → NaN."""
    return pd.to_numeric(series.astype(str).str.strip(), errors="coerce")


def extract_subject_cols(df: pd.DataFrame, subject: str) -> dict:
    """
    Return a dict of canonical column names → Series for a given subject.
    Column naming in SSS files: '<Subject> Scale Scores Mean', etc.
    """
    prefix = subject
    col_map = {
        "n_tested":   f"{prefix} N Tested WKCE SSS",
        "pct_tested": f"{prefix} % Tested WKCE SSS",
        "mean_ss":    f"{prefix} Scale Scores Mean",
        "sd_ss":      f"{prefix} Scale Scores Standard Deviation",
        "p10":        f"{prefix} Scale Scores 10th Percentile",
        "p25":        f"{prefix} Scale Scores 25% Percentile",
        "median_ss":  f"{prefix} Scale Scores Median",
        "p75":        f"{prefix} Scale Scores 75% Percentile",
        "p90":        f"{prefix} Scale Scores 90th Percentile",
    }
    return {k: df[v] if v in df.columns else pd.Series(np.nan, index=df.index)
            for k, v in col_map.items()}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_year_dir(year_dir: Path) -> pd.DataFrame:
    """
    Load all TXT files in a year directory and concatenate.
    Each file corresponds to a grade (e.g., SSS_Grade05_Fall2010.txt).
    Returns a raw, un-cleaned concatenation with a 'source_file' column.
    """
    frames = []
    for txt_file in sorted(year_dir.glob("*.txt")):
        try:
            df = pd.read_csv(txt_file, sep="\t", dtype=str, encoding="latin-1")
            df["source_file"] = txt_file.name
            frames.append(df)
            log(f"  Loaded {txt_file.name}: {len(df):,} rows × {len(df.columns)} cols")
        except Exception as e:
            log(f"  ERROR loading {txt_file.name}: {e}")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def clean_and_reshape(raw: pd.DataFrame, year_label: str) -> pd.DataFrame:
    """
    Filter to race groups at the district level, extract subject stats, and
    reshape to long format: one row per district × grade × subject × race.

    Parameters
    ----------
    raw        : raw concatenation from load_year_dir()
    year_label : string like "2009-10" (constructed from folder name)

    Returns
    -------
    Long DataFrame with columns:
      year, district_name, district_code, grade, subject, race, race_code,
      n_tested, pct_tested, mean_ss, sd_ss, p10, p25, median_ss, p75, p90,
      org_level, pre_race_split, suppressed
    """
    if raw.empty:
        return pd.DataFrame()

    # Standardize column names: strip extra spaces
    raw.columns = [c.strip() for c in raw.columns]

    # Required columns
    org_col   = "Org Level"
    grade_col = "Grade"
    dist_name = "District Name"
    dist_num  = "District Number"
    sg_col    = "Student Group"

    for col in [org_col, grade_col, sg_col]:
        if col not in raw.columns:
            log(f"  WARNING: column '{col}' not found — skipping year {year_label}")
            log(f"  (2003-2005 files use a different layout; TODO: handle separately)")
            return pd.DataFrame()

    # Keep district-level rows only (Org Level == 2)
    df = raw[raw[org_col].astype(str).str.strip() == ORG_LEVEL_DISTRICT].copy()
    log(f"  District-level rows: {len(df):,} of {len(raw):,} total")

    # Filter to race codes of interest
    df["_sg"] = df[sg_col].astype(str).str.strip()
    race_df = df[df["_sg"].isin(RACE_CODE_MAP.keys()) & ~df["_sg"].isin(EXCLUDE_CODES)].copy()
    log(f"  Race-group rows after filter: {len(race_df):,}")

    if race_df.empty:
        return pd.DataFrame()

    # Map race codes to canonical labels
    race_df["race"] = race_df["_sg"].map(RACE_CODE_MAP)
    race_df["race_code"] = race_df["_sg"]

    # Flag pre-split era (Asian/Pacific Islander combined)
    numeric_year = int(year_label.split("-")[0]) + 1  # "2009-10" → 2010
    pre_split = numeric_year < RACE_CATEGORY_CHANGE_YEAR
    race_df["pre_race_split"] = pre_split

    # Canonicalize identifiers
    race_df["year"] = year_label
    race_df["district_name"] = race_df[dist_name].str.strip() if dist_name in race_df.columns else np.nan
    race_df["district_code"] = parse_numeric(race_df[dist_num]) if dist_num in race_df.columns else np.nan
    # Normalize grade to zero-padded 2-digit string (some files use '3', others '03')
    race_df["grade"] = race_df[grade_col].str.strip().str.zfill(2)

    # Extract each subject and reshape to long
    long_frames = []
    for subject in SUBJECTS:
        sub_cols = extract_subject_cols(race_df, subject)
        sub_df = race_df[["year", "district_name", "district_code", "grade",
                           "race", "race_code", "pre_race_split"]].copy()
        for stat_name, series in sub_cols.items():
            sub_df[stat_name] = parse_numeric(series)
        sub_df["subject"] = subject
        long_frames.append(sub_df)

    out = pd.concat(long_frames, ignore_index=True)

    # Suppression flag: no N tested or N tested < 10
    out["suppressed"] = out["n_tested"].isna() | (out["n_tested"] < 10)

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_year_label(folder_name: str) -> str:
    """
    Convert folder name like '2010 raw' or '2013-14 raw' to a canonical
    school-year label like '2009-10' or '2013-14'.

    The 'Year' column in the file records the CALENDAR year of the fall test
    (e.g., 2010 for the 2010-11 school year). We convert to school-year format.
    """
    # Try to extract first 4-digit number
    import re
    m = re.search(r"(\d{4})-(\d{2})", folder_name)
    if m:
        return f"{m.group(1)}-{m.group(2)}"   # already "2013-14"
    m = re.search(r"(\d{4})", folder_name)
    if m:
        year = int(m.group(1))
        return f"{year}-{str(year + 1)[2:]}"   # "2010" → "2010-11"
    return folder_name


def main() -> None:
    log("=" * 70)
    log("03_load_wkce.py — Loading WKCE Scale Score Summary data")
    log("=" * 70)

    if not DATA_DIR.exists():
        log(f"ERROR: Data directory not found: {DATA_DIR}")
        log("Run `python3 analysis/00_download_data.py --era wkce` or place")
        log("Keo SSS TXT files in Data/raw/wkce_sss/<year>/ directories.")
        return

    year_dirs = sorted([d for d in DATA_DIR.iterdir() if d.is_dir()])
    log(f"Found {len(year_dirs)} year directories: {[d.name for d in year_dirs]}")

    all_frames = []
    coverage = []

    for year_dir in year_dirs:
        year_label = build_year_label(year_dir.name)
        log(f"\n--- {year_label} ({year_dir.name}) ---")

        raw = load_year_dir(year_dir)
        if raw.empty:
            log(f"  No data loaded for {year_label}")
            continue

        cleaned = clean_and_reshape(raw, year_label)
        if cleaned.empty:
            log(f"  No usable rows after cleaning for {year_label}")
            continue

        n_suppressed = cleaned["suppressed"].sum()
        n_total = len(cleaned)
        pct_supp = 100 * n_suppressed / n_total if n_total > 0 else float("nan")
        log(f"  Output rows: {n_total:,}  |  Suppressed: {n_suppressed:,} ({pct_supp:.1f}%)")

        coverage.append({
            "year": year_label,
            "n_rows": n_total,
            "n_suppressed": n_suppressed,
            "pct_suppressed": round(pct_supp, 1),
            "pre_race_split": cleaned["pre_race_split"].iloc[0] if n_total > 0 else None,
        })
        all_frames.append(cleaned)

    if not all_frames:
        log("\nNo data loaded. Exiting.")
        return

    panel = pd.concat(all_frames, ignore_index=True)
    log(f"\n{'=' * 70}")
    log(f"Total panel rows: {len(panel):,}")
    log(f"Years covered: {sorted(panel['year'].unique())}")
    log(f"Races: {sorted(panel['race'].dropna().unique())}")
    log(f"Subjects: {sorted(panel['subject'].unique())}")
    log(f"Grades: {sorted(panel['grade'].dropna().unique())}")

    # Save panel
    out_path = OUT_DATA / "panel_wkce_district_race.parquet"
    panel.to_parquet(out_path, index=False)
    log(f"\nSaved: {out_path}")

    # Save QC summary
    cov_df = pd.DataFrame(coverage)
    qc_path = OUT_TABLES / "wkce_qc_summary.txt"
    with open(qc_path, "w") as f:
        f.write("WKCE Scale Score Summary — QC Report\n")
        f.write("=" * 60 + "\n\n")
        f.write("ERA NOTE: WKCE era is NON-BRIDGED with Forward Exam era.\n")
        f.write("Do not trend WKCE scale scores with Forward Exam proficiency rates.\n\n")
        f.write("RACE CATEGORY NOTE: Pre-2010-11 uses 5 categories (Asian/PI combined).\n")
        f.write("Post-2010-11 uses 7+ categories. Flag pre_race_split==True for caution.\n\n")
        f.write("Coverage by year:\n")
        f.write(cov_df.to_string(index=False))
        f.write("\n\nColumn definitions:\n")
        f.write("  mean_ss    = Mean WKCE scale score\n")
        f.write("  sd_ss      = Standard deviation of scale score\n")
        f.write("  p10/p25/median_ss/p75/p90 = Scale score percentiles\n")
        f.write("  n_tested   = Number of students tested\n")
        f.write("  suppressed = True if n_tested < 10 or missing\n")
        f.write("  pre_race_split = True if year < 2010-11 (Asian/PI not yet split)\n")
    log(f"Saved QC: {qc_path}")

    # Quick MMSD check
    mmsd = panel[panel["district_name"].str.contains("MADISON", na=False, case=False)]
    log(f"\nMMSD rows in panel: {len(mmsd):,}")
    if not mmsd.empty:
        log(mmsd.groupby(["year", "race"])["mean_ss"].mean().unstack("race").to_string())

    log("\nDone.")


if __name__ == "__main__":
    main()
