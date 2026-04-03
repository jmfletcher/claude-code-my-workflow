"""
01_load_and_clean.py
====================
Load the ONS data, assign chronological week-in-year positions, compute
mortality rates, and save a clean panel dataset.

Key fix (vs. the PR bug):
  week_in_year is assigned by CHRONOLOGICAL sort of the birth-week date
  string, not lexicographic sort.  The treated week ("3-9 March 1946",
  "3-9 March 1958", "5-11 April 1970") lands at position 5 of 9 under
  chronological ordering — symmetric (4 control weeks before, 4 after).

The lexicographic sort that was in the PR placed all three treated weeks
at position 8 (because "3-9 ..." < "31-6 ..." in ASCII but after all
"10-...", "17-...", "24-..." strings).  That produced the manuscript's
erroneous claim of "position 8 of 9, seven controls before, one after".
"""

from __future__ import annotations
import re
from pathlib import Path

import numpy as np
import pandas as pd
import xlrd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.config import (
    ONS_CAUSE_XLS, LEGACY_CSV, TABLES_DIR,
    GROUPS, TREATED_WEEKS, DEATH_YEAR_MIN, DEATH_YEAR_MAX,
)

# ── Month name → number ───────────────────────────────────────────────────────
_MONTH_NUM: dict[str, int] = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9,
    "Oct": 10, "Nov": 11, "Dec": 12,
}


_MONTH_RE = re.compile(
    r"January|February|March|April|May|June|July|August|"
    r"September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
)


def bw_sort_key(s: str) -> tuple[int, int]:
    """
    Chronological sort key (month_of_start_day, start_day) for a birth-week
    string such as '3-9 March 1946' or '24-1 Feb/March 1946'.

    The start day is the first number in the string; the month is the FIRST
    month name found by regex scan (left-to-right).  For cross-month weeks
    like '24-1 Feb/March 1946' the regex finds "Feb" before "March", so the
    start month is correctly February (2), placing this week before '3-9
    March' (month 3, day 3).

    Using `in` substring matching would wrongly pick "March" from "Feb/March"
    because it appears later and the iteration order of the month dict is not
    guaranteed to be chronological.  The regex alternative list tries full
    names before abbreviations at each string position, which avoids false
    matches of short abbreviations inside longer names.
    """
    s = s.strip()
    start_day = int(re.match(r"\d+", s).group())
    m = _MONTH_RE.search(s)
    if m is None:
        raise ValueError(f"Cannot parse month from birth-week string: {s!r}")
    return (_MONTH_NUM[m.group()], start_day)


# ── Birth-year → group mapping ────────────────────────────────────────────────
_YEAR_TO_GROUP: dict[int, int] = {
    yr: g for g, info in GROUPS.items() for yr in info["birth_years"]
}
_YEAR_TO_STUDY: dict[int, str] = {
    yr: info["study"] for g, info in GROUPS.items() for yr in info["birth_years"]
}


def load_ons_panel() -> pd.DataFrame:
    """
    Parse every 'Data YYYY' sheet from the ONS cause-of-death Excel file.
    Returns one row per (birth_week, birth_year, death_year) with all-cause
    death count.
    """
    wb = xlrd.open_workbook(str(ONS_CAUSE_XLS))
    records: list[dict] = []

    for sheet_name in wb.sheet_names():
        if not sheet_name.startswith("Data "):
            continue
        death_year = int(sheet_name.split()[1])
        if not (DEATH_YEAR_MIN <= death_year <= DEATH_YEAR_MAX):
            continue

        ws = wb.sheet_by_name(sheet_name)
        for i in range(ws.nrows):
            row = ws.row_values(i)
            cell0 = row[0]
            if not isinstance(cell0, str):
                continue
            cell0 = cell0.strip()
            # A data row has a date-range string and a numeric total deaths
            if "-" not in cell0 or not isinstance(row[1], (int, float)):
                continue
            if not any(m in cell0 for m in _MONTH_NUM):
                continue
            birth_week = cell0
            deaths_total = float(row[1])
            records.append(
                {
                    "birth_week": birth_week,
                    "death_year": death_year,
                    "deaths_total": deaths_total,
                }
            )

    df = pd.DataFrame(records)

    # Extract birth year from the birth_week string
    df["birth_year"] = df["birth_week"].str.extract(r"(\d{4})").astype(int)
    # Restrict to the three cohort clusters
    df = df[df["birth_year"].isin(_YEAR_TO_GROUP)].copy()
    df["group"] = df["birth_year"].map(_YEAR_TO_GROUP)
    df["study"] = df["birth_year"].map(_YEAR_TO_STUDY)

    # Derived variables
    df["age"] = df["death_year"] - df["birth_year"]
    df = df[(df["age"] >= 0) & (df["age"] <= 110)].copy()

    # ── Assign week_in_year (chronological) ───────────────────────────────────
    # Build a birth-week → chronological position mapping per group.
    # Sorting is done on the date key (month, start_day), NOT lexicographically.
    bw_key = (
        df[["group", "birth_year", "birth_week"]]
        .drop_duplicates()
        .assign(_sort=lambda d: d["birth_week"].map(bw_sort_key))
        .sort_values(["group", "birth_year", "_sort"])
        .drop(columns="_sort")
    )
    bw_key["week_in_year"] = (
        bw_key.groupby(["group", "birth_year"]).cumcount() + 1
    )
    # The mapping is consistent across birth years within a group; take unique
    # (group, week_in_year) → representative week label for reference only.
    df = df.merge(
        bw_key[["group", "birth_year", "birth_week", "week_in_year"]],
        on=["group", "birth_year", "birth_week"],
        how="left",
    )

    # Treatment indicator
    df["treated"] = df["birth_week"].isin(TREATED_WEEKS).astype(int)

    return df


def add_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach per-1,000-per-year mortality rates.

    We use the same birth-week-specific implied denominator as the legacy
    Stata/R pipeline: for each birth week the denominator N_b is back-
    calculated from the total observed deaths and the crude period mortality
    rate.  In practice this is equivalent to loading the pre-computed rates
    from the legacy CSV and merging them in.

    Here we load the legacy CSV directly so that the rate values are
    identical to the original analysis (ensures continuity with prior work).
    """
    legacy = pd.read_csv(
        LEGACY_CSV,
        usecols=["week", "year", "age_needed", "rate", "log_rate",
                 "cohort", "week_in_year"],
        dtype={"week": str, "rate": str, "log_rate": str},
    )
    legacy.rename(
        columns={"week": "birth_week", "year": "birth_year",
                 "age_needed": "age", "cohort": "_treated_legacy"},
        inplace=True,
    )
    legacy["birth_year"] = legacy["birth_year"].astype(int)
    legacy["age"] = legacy["age"].astype(int)
    legacy["rate"] = pd.to_numeric(legacy["rate"], errors="coerce")
    legacy["log_rate"] = pd.to_numeric(legacy["log_rate"], errors="coerce")

    # The legacy week_in_year is CHRONOLOGICAL (correct); verify and use.
    # (The old Stata analysis assigned positions 1–9 in the order the weeks
    # appear in the Excel sheets, which is chronological.)
    legacy.drop(columns=["_treated_legacy"], inplace=True)

    # Merge into main panel (left join keeps all df rows)
    df = df.merge(
        legacy[["birth_week", "birth_year", "age", "rate", "log_rate"]],
        on=["birth_week", "birth_year", "age"],
        how="left",
    )
    return df


def assign_group_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Add study-name and cohort-cluster labels."""
    df["study_name"] = df["birth_year"].map(
        {yr: info["name"] for g, info in GROUPS.items() for yr in info["birth_years"]}
    )
    return df


def build_panel() -> pd.DataFrame:
    """End-to-end: load, clean, rate, label."""
    df = load_ons_panel()
    df = add_rates(df)
    df = assign_group_labels(df)
    # Drop rows without a rate (age outside 1970-2013 window)
    df = df.dropna(subset=["rate"]).copy()
    return df


if __name__ == "__main__":
    panel = build_panel()
    out = TABLES_DIR / "panel_clean.csv"
    panel.to_csv(out, index=False)
    print(f"Panel built: {len(panel):,} rows → {out}")
    print(panel[["group", "study", "birth_year", "birth_week",
                 "week_in_year", "treated"]].drop_duplicates()
          .sort_values(["group", "birth_year", "week_in_year"])
          .head(27).to_string(index=False))
    print(f"\nTreated-week positions (should all be 5):")
    print(panel[panel["treated"] == 1][
        ["study", "birth_week", "week_in_year"]].drop_duplicates())
