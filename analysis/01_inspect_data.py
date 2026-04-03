"""
Inspect downloaded Forward Exam zip files: print column names, unique race labels,
unique district names, row counts, suppression symbols, and year coverage.

Run after 00_download_data.py:
    python3 analysis/01_inspect_data.py

Outputs a report to output/tables/00_data_inspection.txt
"""

import io
import zipfile
import textwrap
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FORWARD_DIR = ROOT / "Data" / "raw" / "forward"
OUTPUT_DIR = ROOT / "output" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# COVID and standard-change flags (for annotation)
COVID_YEARS = {"2020-21"}
NEW_STANDARD_YEARS = {"2023-24", "2024-25"}
EXCLUDED_YEARS = {"2019-20"}  # no data at all

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_zip_csv(zip_path: Path) -> tuple[pd.DataFrame | None, list[str]]:
    """
    Open a Forward Exam zip and read the first CSV found inside.
    Returns (DataFrame, list_of_csv_names_in_zip).
    """
    try:
        with zipfile.ZipFile(zip_path) as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                return None, zf.namelist()
            # Read first CSV (usually only one)
            with zf.open(csv_names[0]) as f:
                # Try UTF-8 then latin-1
                raw = f.read()
                for enc in ("utf-8", "latin-1", "cp1252"):
                    try:
                        df = pd.read_csv(io.BytesIO(raw), encoding=enc, low_memory=False)
                        return df, csv_names
                    except UnicodeDecodeError:
                        continue
                return None, csv_names
    except zipfile.BadZipFile:
        return None, []


def suppression_symbols(df: pd.DataFrame) -> dict:
    """Find common DPI suppression symbols across all columns."""
    symbols = {}
    for col in df.columns:
        if df[col].dtype == object:
            vals = df[col].unique()
            for sym in ["*", "--", "N/A", "NA", "n/a", "s", "DS"]:
                if sym in vals:
                    count = (df[col] == sym).sum()
                    symbols.setdefault(col, {})[sym] = int(count)
    return symbols


# ---------------------------------------------------------------------------
# Main inspection
# ---------------------------------------------------------------------------

def inspect_all() -> str:
    """Run inspection and return report as string."""
    lines = []

    def log(s=""):
        lines.append(s)
        print(s)

    log("=" * 70)
    log("Wisconsin Forward Exam — Data Inspection Report")
    log("=" * 70)
    log()

    zips = sorted(FORWARD_DIR.glob("forward_certified_*.zip"))
    if not zips:
        log(f"ERROR: No zip files found in {FORWARD_DIR}")
        log("Run: python3 analysis/00_download_data.py --era forward")
        return "\n".join(lines)

    log(f"Found {len(zips)} zip files in {FORWARD_DIR}")
    log()

    # Track column names and race labels across years for consistency check
    all_columns: dict[str, list[str]] = {}
    all_race_labels: dict[str, list] = {}
    race_col_candidate = None  # will be set on first file

    for zip_path in zips:
        year = zip_path.stem.replace("forward_certified_", "")
        flags = []
        if year in COVID_YEARS:
            flags.append("COVID-DISRUPTED")
        if year in NEW_STANDARD_YEARS:
            flags.append("NEW-STANDARDS")
        flag_str = f" [{', '.join(flags)}]" if flags else ""

        log(f"--- {year}{flag_str} ---")

        df, csv_names = read_zip_csv(zip_path)
        log(f"  CSV files in zip: {csv_names}")

        if df is None:
            log("  ERROR: Could not read CSV")
            log()
            continue

        log(f"  Rows: {len(df):,}   Columns: {len(df.columns)}")
        log(f"  Columns: {list(df.columns)}")
        all_columns[year] = list(df.columns)

        # Detect GROUP_BY and GROUP_BY_VALUE columns; extract race labels
        if "GROUP_BY" in df.columns and "GROUP_BY_VALUE" in df.columns:
            group_by_vals = sorted(df["GROUP_BY"].dropna().unique().tolist())
            log(f"  GROUP_BY categories: {group_by_vals}")
            race_rows = df[df["GROUP_BY"] == "Race/Ethnicity"]
            race_labels = sorted(race_rows["GROUP_BY_VALUE"].dropna().unique().tolist())
            log(f"  Race/Ethnicity labels: {race_labels}")
            all_race_labels[year] = race_labels
        else:
            # Fallback for unexpected layouts
            race_candidates = [c for c in df.columns
                               if ("race" in c.lower() or "ethnicity" in c.lower())
                               and "group_by" not in c.lower()]
            if race_candidates:
                for rc in race_candidates:
                    unique_vals = sorted(df[rc].dropna().unique().tolist())
                    log(f"  Unique values in '{rc}': {unique_vals}")
                    all_race_labels[year] = unique_vals

        # Suppression
        sup = suppression_symbols(df)
        if sup:
            log(f"  Suppression symbols found:")
            for col, syms in list(sup.items())[:5]:
                log(f"    {col}: {syms}")
        else:
            log("  No obvious suppression symbols found in string columns")

        # Detect district/school columns
        id_cols = [c for c in df.columns if any(k in c.lower() for k in ["district", "school", "agency", "lea"])]
        log(f"  District/School ID columns: {id_cols}")

        # Check for MMSD
        for id_col in id_cols:
            if "name" in id_col.lower():
                mmsd_check = df[df[id_col].str.contains("Madison", case=False, na=False)]
                if len(mmsd_check) > 0:
                    log(f"  MMSD rows in '{id_col}': {len(mmsd_check)}")
                    district_name_sample = mmsd_check[id_col].unique()[:3]
                    log(f"    Sample MMSD names: {list(district_name_sample)}")

        # Proficiency-related columns
        pct_cols = [c for c in df.columns if any(k in c.lower() for k in ["pct", "percent", "proficien", "rate"])]
        log(f"  Proficiency-related columns: {pct_cols}")

        # Grade column
        grade_cols = [c for c in df.columns if "grade" in c.lower()]
        if grade_cols:
            for gc in grade_cols:
                log(f"  Unique values in '{gc}': {sorted(df[gc].dropna().unique().tolist())}")

        # Subject column
        subj_cols = [c for c in df.columns if any(k in c.lower() for k in ["subject", "test", "content"])]
        if subj_cols:
            for sc in subj_cols:
                log(f"  Unique values in '{sc}': {sorted(df[sc].dropna().unique().tolist())}")

        log()

    # Cross-year column consistency check
    log("=" * 70)
    log("CROSS-YEAR COLUMN CONSISTENCY")
    log("=" * 70)
    all_col_sets = {y: set(c) for y, c in all_columns.items()}
    if all_col_sets:
        # Columns present in ALL years
        common = set.intersection(*all_col_sets.values()) if all_col_sets else set()
        log(f"\nColumns present in ALL years ({len(common)}):")
        log(f"  {sorted(common)}")

        # Columns that appear in some but not all
        union = set.union(*all_col_sets.values()) if all_col_sets else set()
        missing_somewhere = union - common
        if missing_somewhere:
            log(f"\nColumns NOT present in all years ({len(missing_somewhere)}):")
            for col in sorted(missing_somewhere):
                present_in = [y for y, s in all_col_sets.items() if col in s]
                log(f"  '{col}': present in {present_in}")

    # Cross-year race label consistency
    log()
    log("=" * 70)
    log("CROSS-YEAR RACE LABEL CONSISTENCY (Race/Ethnicity GROUP_BY_VALUE)")
    log("=" * 70)
    if all_race_labels:
        all_labels = set()
        for labels in all_race_labels.values():
            all_labels.update(labels)
        log(f"\nAll unique Race/Ethnicity labels across all years:")
        for label in sorted(all_labels):
            years_present = [y for y, labels in all_race_labels.items() if label in labels]
            in_all = "ALL YEARS" if len(years_present) == len(all_race_labels) else f"only: {years_present}"
            log(f"  '{label}': {in_all}")

    # Summary table
    log()
    log("=" * 70)
    log("RECOMMENDED ANALYSIS FLAGS")
    log("=" * 70)
    log()
    log(f"  {'Year':<10} {'Status':<20} {'Recommendation'}")
    log(f"  {'-'*10} {'-'*20} {'-'*40}")
    log(f"  {'2019-20':<10} {'MISSING':<20} Exclude — no state testing (COVID waiver)")
    for zip_path in zips:
        year = zip_path.stem.replace("forward_certified_", "")
        if year in COVID_YEARS:
            status = "COVID-DISRUPTED"
            rec = "Exclude from trends; flag if included"
        elif year in NEW_STANDARD_YEARS:
            status = "NEW STANDARDS"
            rec = "Do not compare to 2015-22 without caveats"
        else:
            status = "Clean"
            rec = "Include in main analysis"
        log(f"  {year:<10} {status:<20} {rec}")

    log()
    log("NEXT STEPS:")
    log("  1. Fill in .claude/rules/knowledge-base-template.md with confirmed column names")
    log("  2. Run: python3 analysis/01_load_and_clean.py")

    return "\n".join(lines)


if __name__ == "__main__":
    report = inspect_all()
    out_path = OUTPUT_DIR / "00_data_inspection.txt"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to {out_path}")
