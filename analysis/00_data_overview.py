"""
00_data_overview.py
===================
Panel Conditioning (UK cohorts) — data inspection pass.

Purpose: Print shapes, column names, and sample rows for all raw data files.
         Identify header structure of ONS XLS files before cleaning.
         Confirm legacy CSV structure matches expectations.

Requires: pandas, numpy
Optional: xlrd (for .xls inspection; skipped if not installed)

Run from repo root:
    python3 analysis/00_data_overview.py
"""

from pathlib import Path

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"
LEGACY = ROOT / "Old Attempts and Results" / "Terrence"

ONS_WOB   = DATA / "deathsregisteredbymonthbyselectedweekofbirthenglandandwales1970to2013_tcm77-419401.xls"
ONS_CAUSE = DATA / "deathsregisteredbycauseofdeathicdchapterbyselectedweekofbirthenglandandwales1970to2013_tcm77-419405.xls"
ONS_MONTH = DATA / "bymonthofdeath.xls"
LEGACY_FINAL = LEGACY / "final.csv"
LEGACY_AGE   = LEGACY / "mortality age final.csv"


def section(title: str) -> None:
    print(f"\n{'='*70}\n  {title}\n{'='*70}")


def inspect_csv(path: Path, name: str, nrows: int = 5) -> pd.DataFrame:
    section(f"CSV: {name}")
    if not path.exists():
        print(f"  [NOT FOUND] {path}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  dtypes:\n{df.dtypes.to_string()}")
    print(f"\n  Head ({nrows} rows):\n{df.head(nrows).to_string(index=False)}")
    for col in ("cohort", "group", "week_in_year"):
        if col in df.columns:
            vc = df[col].value_counts().sort_index()
            print(f"\n  '{col}' value counts:\n{vc.to_string()}")
    return df


def inspect_xls(path: Path, name: str) -> None:
    section(f"XLS: {name}")
    if not path.exists():
        print(f"  [NOT FOUND] {path}")
        return
    try:
        import xlrd  # noqa: F401
        engine = "xlrd"
    except ImportError:
        print(f"  [xlrd not installed — skipping XLS inspection for {path.name}]")
        print(f"  Run: pip install xlrd   then re-run this script.")
        return
    xl = pd.ExcelFile(path, engine=engine)
    print(f"  Sheets: {xl.sheet_names}")
    for sheet in xl.sheet_names[:3]:
        print(f"\n  --- Sheet: {sheet!r} ---")
        for header_row in range(5):
            try:
                df = pd.read_excel(path, sheet_name=sheet, header=header_row,
                                   nrows=4, engine=engine)
                if df.shape[1] > 1:
                    print(f"    header_row={header_row} → shape {df.shape}, "
                          f"cols[:8]: {list(df.columns)[:8]}")
                    break
            except Exception:
                continue


if __name__ == "__main__":
    print("Panel Conditioning (UK) — Data Overview")
    print(f"Repo root: {ROOT}")

    df_final = inspect_csv(LEGACY_FINAL, "final.csv  (aggregated, 136 rows)")
    df_age   = inspect_csv(LEGACY_AGE,   "mortality age final.csv  (age-resolved)")

    inspect_xls(ONS_WOB,   "ONS deaths by week of birth  (main)")
    inspect_xls(ONS_CAUSE, "ONS deaths by cause of death")
    inspect_xls(ONS_MONTH, "ONS deaths by month of death")

    # --- Denominator investigation ---
    section("Denominator check")
    if not df_final.empty:
        rate = pd.to_numeric(df_final["rate"], errors="coerce")
        total = pd.to_numeric(df_final["total"], errors="coerce")
        print(f"  'rate' stats:\n{rate.describe().to_string()}")
        print(f"\n  'total' (deaths) stats:\n{total.describe().to_string()}")
        # Check ratio rate/total: should equal 1/N if rate = deaths/N * scale
        ratio = rate / total
        print(f"\n  rate/total (should be ~constant if rate = total/N * scale):\n"
              f"  min={ratio.min():.4f}  max={ratio.max():.4f}  "
              f"mean={ratio.mean():.4f}  std={ratio.std():.4f}")
        if ratio.std() < 0.05:
            print("  → rate/total is roughly constant: rate ≈ total * constant")
            print(f"    Implied scale factor: 1/mean(total/rate) ≈ "
                  f"{(total/rate).mean():.1f}")
        else:
            print("  → rate/total varies: denominator differs across cells.")

    # --- Age data quick look ---
    if not df_age.empty:
        section("Age-resolved data quick look")
        age = pd.to_numeric(df_age["age_needed"], errors="coerce")
        print(f"  age_needed range: {age.min():.0f} – {age.max():.0f}")
        print(f"  Unique ages: {sorted(age.dropna().astype(int).unique())[:15]} ...")
        rate_age = pd.to_numeric(df_age["rate"], errors="coerce")
        na_frac = rate_age.isna().mean()
        print(f"  Missing rate: {na_frac:.1%} of rows "
              f"({rate_age.isna().sum()} / {len(df_age)})")

    print("\n\nDone. Check denominator note above before running 02_replicate_stata.py.")
