"""
00_data_loading.py
Load and parse all HMD data into clean analysis-ready DataFrames.
Saves intermediate parquet files for fast reloading.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from config import (
    POL_STATS, POL_CAUSE, HMD_CROSS, DATA_DIR,
    BASELINE_START, PROJECT_ROOT, PROCESSED_DIR, END_YEAR
)

OUTPUT_DIR = PROCESSED_DIR


def parse_hmd_txt(filepath, has_country_col=False):
    """Parse standard HMD fixed-width text files."""
    rows = []
    with open(filepath) as f:
        lines = f.readlines()

    header_found = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if not header_found:
            if "Year" in stripped and "Age" in stripped:
                header_found = True
            continue

        parts = stripped.split()
        if len(parts) < 4:
            continue

        try:
            if has_country_col:
                country = parts[0]
                year = int(parts[1])
                age_str = parts[2]
                values = parts[3:]
            else:
                country = None
                year = int(parts[0])
                age_str = parts[1]
                values = parts[2:]

            age = 110 if age_str == "110+" else int(age_str.replace("+", ""))

            parsed_vals = []
            for v in values:
                try:
                    parsed_vals.append(float(v))
                except ValueError:
                    parsed_vals.append(np.nan)

            row = {"Year": year, "Age": age}
            if has_country_col:
                row["Country"] = country

            col_names = ["Female", "Male", "Total"]
            for i, name in enumerate(col_names):
                if i < len(parsed_vals):
                    row[name] = parsed_vals[i]

            rows.append(row)
        except (ValueError, IndexError):
            continue

    df = pd.DataFrame(rows)
    return df


def parse_hmd_lifetable(filepath, has_country_col=False):
    """Parse HMD life table files (more columns than standard)."""
    rows = []
    with open(filepath) as f:
        lines = f.readlines()

    header_found = False
    col_names = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if not header_found:
            if "Year" in stripped and "Age" in stripped:
                parts = stripped.split()
                if has_country_col:
                    col_names = parts[3:]  # skip PopName, Year, Age
                else:
                    col_names = parts[2:]  # skip Year, Age
                header_found = True
            continue

        parts = stripped.split()
        if len(parts) < 4:
            continue

        try:
            if has_country_col:
                country = parts[0]
                year = int(parts[1])
                age_str = parts[2]
                values = parts[3:]
            else:
                country = None
                year = int(parts[0])
                age_str = parts[1]
                values = parts[2:]

            age = 110 if age_str == "110+" else int(age_str.replace("+", ""))

            row = {"Year": year, "Age": age}
            if has_country_col:
                row["Country"] = country

            for i, name in enumerate(col_names):
                if i < len(values):
                    try:
                        row[name] = float(values[i])
                    except ValueError:
                        row[name] = np.nan

            rows.append(row)
        except (ValueError, IndexError):
            continue

    return pd.DataFrame(rows)


def load_poland_mortality():
    """Load Poland death rates, deaths, exposures at 1x1 resolution."""
    print("Loading Poland mortality data...")

    mx = parse_hmd_txt(POL_STATS / "Mx_1x1.txt")
    mx = mx.rename(columns={"Female": "mx_female", "Male": "mx_male", "Total": "mx_total"})

    deaths = parse_hmd_txt(POL_STATS / "Deaths_1x1.txt")
    deaths = deaths.rename(columns={"Female": "deaths_female", "Male": "deaths_male", "Total": "deaths_total"})

    exposures = parse_hmd_txt(POL_STATS / "Exposures_1x1.txt")
    exposures = exposures.rename(columns={"Female": "exp_female", "Male": "exp_male", "Total": "exp_total"})

    df = mx.merge(deaths, on=["Year", "Age"], how="outer")
    df = df.merge(exposures, on=["Year", "Age"], how="outer")
    df = df[df["Year"] >= BASELINE_START].copy()
    if END_YEAR is not None:
        df = df[df["Year"] <= END_YEAR].copy()
    df = df.sort_values(["Year", "Age"]).reset_index(drop=True)

    print(f"  Poland: {len(df)} rows, years {df.Year.min()}-{df.Year.max()}, ages {df.Age.min()}-{df.Age.max()}")
    return df


def load_poland_cause_of_death():
    """Load Poland cause-specific death rates."""
    print("Loading Poland cause-of-death data...")
    filepath = POL_CAUSE / "POL_m_short_idr.csv"
    df = pd.read_csv(filepath)
    df = df.rename(columns={"country": "Country", "year": "Year", "sex": "Sex", "cause": "Cause"})
    df = df[df["Year"] >= BASELINE_START].copy()
    if END_YEAR is not None:
        df = df[df["Year"] <= END_YEAR].copy()

    age_cols = [c for c in df.columns if c.startswith("m")]
    age_cols = [c for c in age_cols if c != "m0" or True]

    print(f"  Cause-of-death: {len(df)} rows, {df.Cause.nunique()} causes, years {df.Year.min()}-{df.Year.max()}")
    return df


def load_cross_country_deaths():
    """Load cross-country deaths at 1x1 resolution."""
    print("Loading cross-country deaths...")
    filepath = HMD_CROSS / "deaths" / "Deaths_1x1" / "Deaths_1x1.txt"
    df = parse_hmd_txt(filepath, has_country_col=True)
    df = df.rename(columns={"Female": "deaths_female", "Male": "deaths_male", "Total": "deaths_total"})
    df = df[df["Year"] >= BASELINE_START].copy()
    if END_YEAR is not None:
        df = df[df["Year"] <= END_YEAR].copy()
    print(f"  Cross-country deaths: {len(df)} rows, {df.Country.nunique()} countries")
    return df


def load_cross_country_exposures():
    """Load cross-country exposures at 1x1 resolution."""
    print("Loading cross-country exposures...")
    filepath = HMD_CROSS / "exposures" / "Exposures_1x1" / "Exposures_1x1.txt"
    df = parse_hmd_txt(filepath, has_country_col=True)
    df = df.rename(columns={"Female": "exp_female", "Male": "exp_male", "Total": "exp_total"})
    df = df[df["Year"] >= BASELINE_START].copy()
    if END_YEAR is not None:
        df = df[df["Year"] <= END_YEAR].copy()
    print(f"  Cross-country exposures: {len(df)} rows, {df.Country.nunique()} countries")
    return df


def load_cross_country_rates():
    """Load cross-country death rates at 1x1 resolution."""
    print("Loading cross-country death rates...")
    filepath = HMD_CROSS / "death_rates" / "Mx_1x1" / "Mx_1x1.txt"
    if filepath.exists():
        df = parse_hmd_txt(filepath, has_country_col=True)
        df = df.rename(columns={"Female": "mx_female", "Male": "mx_male", "Total": "mx_total"})
        df = df[df["Year"] >= BASELINE_START].copy()
        if END_YEAR is not None:
            df = df[df["Year"] <= END_YEAR].copy()
        print(f"  Cross-country rates: {len(df)} rows, {df.Country.nunique()} countries")
        return df

    # Compute from deaths and exposures if rate file not available
    print("  Rate file not found, computing from deaths/exposures...")
    deaths = load_cross_country_deaths()
    exposures = load_cross_country_exposures()
    df = deaths.merge(exposures, on=["Country", "Year", "Age"], how="inner")
    for sex in ["female", "male", "total"]:
        df[f"mx_{sex}"] = df[f"deaths_{sex}"] / df[f"exp_{sex}"]
    print(f"  Computed rates: {len(df)} rows, {df.Country.nunique()} countries")
    return df


def load_cross_country_lifetables():
    """Load cross-country life tables (both sexes)."""
    print("Loading cross-country life tables...")
    filepath = DATA_DIR / "lt_both" / "bltper_1x1" / "bltper_1x1.txt"
    df = parse_hmd_lifetable(filepath, has_country_col=True)
    df = df[df["Year"] >= BASELINE_START].copy()
    if END_YEAR is not None:
        df = df[df["Year"] <= END_YEAR].copy()
    print(f"  Life tables: {len(df)} rows, {df.Country.nunique()} countries")
    return df


def build_age_group_panel(df, age_groups=None, country_col=None):
    """Aggregate single-year data into age group panels."""
    if age_groups is None:
        age_groups = {
            "60-64": (60, 64),
            "65-69": (65, 69),
            "70-74": (70, 74),
            "75-79": (75, 79),
            "80-84": (80, 84),
            "85-89": (85, 89),
            "90+": (90, 110),
        }

    panels = []
    group_keys = ["Year"] if country_col is None else ["Country", "Year"]

    for name, (lo, hi) in age_groups.items():
        sub = df[(df["Age"] >= lo) & (df["Age"] <= hi)].copy()
        agg = sub.groupby(group_keys, as_index=False).agg({
            c: "sum" for c in df.columns
            if c.startswith("deaths_") or c.startswith("exp_")
        })
        for sex in ["female", "male", "total"]:
            dc = f"deaths_{sex}"
            ec = f"exp_{sex}"
            if dc in agg.columns and ec in agg.columns:
                agg[f"mx_{sex}"] = agg[dc] / agg[ec]
        agg["AgeGroup"] = name
        agg["AgeMin"] = lo
        agg["AgeMax"] = hi
        panels.append(agg)

    return pd.concat(panels, ignore_index=True)


if __name__ == "__main__":
    print("=" * 60)
    print("HMD Data Loading Pipeline")
    print("=" * 60)

    pol = load_poland_mortality()
    pol.to_parquet(OUTPUT_DIR / "poland_mortality_1x1.parquet", index=False)

    pol_cause = load_poland_cause_of_death()
    pol_cause.to_parquet(OUTPUT_DIR / "poland_cause_of_death.parquet", index=False)

    cross_deaths = load_cross_country_deaths()
    cross_exp = load_cross_country_exposures()

    cross = cross_deaths.merge(cross_exp, on=["Country", "Year", "Age"], how="inner")
    for sex in ["female", "male", "total"]:
        cross[f"mx_{sex}"] = cross[f"deaths_{sex}"] / cross[f"exp_{sex}"]
    cross.to_parquet(OUTPUT_DIR / "cross_country_1x1.parquet", index=False)

    # Build age-group panels
    pol_ag = build_age_group_panel(pol)
    pol_ag.to_parquet(OUTPUT_DIR / "poland_age_groups.parquet", index=False)

    cross_ag = build_age_group_panel(cross, country_col="Country")
    cross_ag.to_parquet(OUTPUT_DIR / "cross_country_age_groups.parquet", index=False)

    # Life tables
    lt = load_cross_country_lifetables()
    lt.to_parquet(OUTPUT_DIR / "cross_country_lifetables.parquet", index=False)

    print("\n" + "=" * 60)
    print("All data saved to:", OUTPUT_DIR)
    print("Files:")
    for f in sorted(OUTPUT_DIR.glob("*.parquet")):
        size_mb = f.stat().st_size / 1e6
        print(f"  {f.name}: {size_mb:.1f} MB")
    print("=" * 60)
