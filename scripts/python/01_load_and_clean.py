"""
Load and validate processed CSV data for all four geographies.

Reads CSVs from data/processed/, validates column structure and value ranges,
and prints summary statistics. This script is also importable by other scripts
via load_all_data().

Inputs:  data/processed/*_infant_mortality_by_race.csv
Outputs: Validation report to stdout
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_DIR, CSV_FILES, GEOGRAPHIES, GEO_LABELS, REPORT_PERIOD


EXPECTED_COLUMNS = ["year", "race", "births", "deaths",
                    "rate_per_1000", "rate_lo", "rate_hi"]


def load_geo(geo: str) -> pd.DataFrame:
    """Load one geography's CSV into a DataFrame with proper types."""
    path = DATA_DIR / CSV_FILES[geo]
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")
    df = pd.read_csv(path)
    for col in ["rate_per_1000", "rate_lo", "rate_hi"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["geography"] = geo
    return df


def load_all_data() -> pd.DataFrame:
    """Load all geographies into a single DataFrame."""
    frames = []
    for geo in GEOGRAPHIES:
        frames.append(load_geo(geo))
    return pd.concat(frames, ignore_index=True)


def validate(df: pd.DataFrame, geo: str) -> list[str]:
    """Run validation checks; return list of warnings."""
    warnings = []
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        warnings.extend(f"Missing column: {c}" for c in missing)
        return warnings

    if (df["births"] < 0).any():
        warnings.append("Negative birth counts found")
    if (df["deaths"] < 0).any():
        warnings.append("Negative death counts found")

    rate_valid = df["rate_per_1000"].dropna()
    if (rate_valid < 0).any():
        warnings.append("Negative rates found")
    if (rate_valid > 100).any():
        warnings.append("Implausibly high rate (>100 per 1,000)")

    races = set(df["race"].unique())
    if races != {"White", "Black"}:
        warnings.append(f"Unexpected race categories: {races}")

    return warnings


def main() -> None:
    all_ok = True
    for geo in GEOGRAPHIES:
        df = load_geo(geo)
        warns = validate(df, geo)
        if warns:
            all_ok = False
            label = GEO_LABELS[geo]
            for w in warns:
                print(f"  WARNING [{label}]: {w}")

    if all_ok:
        print("ALL GEOGRAPHIES PASSED VALIDATION")
    else:
        print("WARNINGS FOUND — review above")


if __name__ == "__main__":
    main()
