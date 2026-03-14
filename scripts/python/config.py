"""
Project configuration: paths, palette, constants, and shared utilities.

All other scripts import from this module for consistent settings.
"""

import math
import os
from pathlib import Path

# --- Paths ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
INPUT_DIR = PROJECT_ROOT / "data" / "input"
FIGURE_DIR = PROJECT_ROOT / "Figures"
OUTPUT_DIR = PROJECT_ROOT / "output"

# --- Figure palette (publication-ready, do not change without reason) ---
RACE_COLORS = {"White": "#2171b5", "Black": "#b2182b"}
FIGURE_DPI = 300
TITLE_CI_SUFFIX = " (95% CI, Poisson-based)"
FIGURE_SIZE = (10, 5)

# --- Geographies ---
GEOGRAPHIES = ["state", "milwaukee", "dane", "rest_of_wisconsin"]
CSV_FILES = {
    "state": "state_infant_mortality_by_race.csv",
    "milwaukee": "milwaukee_infant_mortality_by_race.csv",
    "dane": "dane_infant_mortality_by_race.csv",
    "rest_of_wisconsin": "rest_of_wisconsin_infant_mortality_by_race.csv",
}
GEO_LABELS = {
    "state": "State of Wisconsin",
    "milwaukee": "Milwaukee County",
    "dane": "Dane County",
    "rest_of_wisconsin": "Rest of Wisconsin\n(State − Milwaukee − Dane)",
}

# --- Policy constants ---
NFP_COST_PER_LIFE_M = 3.2  # $3.2M per infant death averted (Miller, 2015)
NFP_LIVES_PER_1M = 0.31    # 0.31 lives saved per $1M
REPORT_PERIOD = (2019, 2023)  # 5-year average period for Tables 1-3

# --- Benchmark reductions (from literature) ---
DENMARK_REDUCTION = 0.17  # 17.2% from Altindag et al.
KMC_REDUCTION = 0.32      # 32% from KMC meta-analysis


def ensure_dirs() -> None:
    """Create output directories if they don't exist."""
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ci_95_poisson(deaths: int, births: int) -> tuple[float, float]:
    """
    Approximate 95% CI for infant mortality rate per 1,000.

    Uses Poisson assumption: rate ± 1.96 × (1000 × √D) / B
    Returns (lower, upper) bounds; lower clamped to 0.
    """
    if births is None or births == 0 or deaths is None:
        return (0.0, 0.0)
    rate = 1000.0 * deaths / births
    if deaths <= 0:
        return (0.0, 0.0)
    se = 1000.0 * math.sqrt(deaths) / births
    half = 1.96 * se
    return (max(0.0, rate - half), rate + half)


def min_detectable_deaths(annual_deaths: float) -> int:
    """
    Minimum deaths averted to be detectable in one year (Poisson).

    The post-intervention count must fall below the lower bound of the
    95% CI: D - 1.96√D. So min averted = ceil(1.96 × √D).
    """
    if annual_deaths <= 0:
        return 0
    return math.ceil(1.96 * math.sqrt(annual_deaths))
