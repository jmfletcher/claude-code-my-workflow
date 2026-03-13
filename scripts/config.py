"""
Project configuration: paths, constants, and policy parameters.
"""
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "Data" / "HMD"

# Optional: run with data through END_YEAR and write to a separate folder (e.g. pre-COVID)
# Set env: OUTPUT_SUBDIR=results_pre2020 END_YEAR=2019
OUTPUT_SUBDIR = os.environ.get("OUTPUT_SUBDIR", "").strip()
END_YEAR = int(os.environ.get("END_YEAR", 0)) if os.environ.get("END_YEAR") else None  # None = use all years

if OUTPUT_SUBDIR:
    _subroot = PROJECT_ROOT / OUTPUT_SUBDIR
    FIGURES_DIR = _subroot / "Figures"
    TABLES_DIR = _subroot / "Paper" / "tables"
    PROCESSED_DIR = _subroot / "Data" / "processed"
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
else:
    FIGURES_DIR = PROJECT_ROOT / "Figures"
    TABLES_DIR = PROJECT_ROOT / "Paper" / "tables"
    PROCESSED_DIR = PROJECT_ROOT / "Data" / "processed"
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Poland-specific HMD paths
POL_STATS = DATA_DIR / "POL" / "STATS"
POL_CAUSE = DATA_DIR / "POL" / "Cause"

# Cross-country HMD paths
HMD_CROSS = DATA_DIR / "hmd_statistics_20251211"
HMD_LT_BOTH = DATA_DIR / "lt_both"
HMD_LT_FEMALE = DATA_DIR / "lt_female"
HMD_LT_MALE = DATA_DIR / "lt_male"

# Policy parameters
POLICY_YEAR_75 = 2016   # Sep 2016: Drugs 75+ introduced
POLICY_YEAR_65 = 2023   # Sep 2023: expanded to 65+
FIRST_FULL_TREATMENT_YEAR = 2017  # first full calendar year of treatment

TREATED_AGE_MIN_75 = 75
TREATED_AGE_MIN_65 = 65
CONTROL_AGE_MIN = 60
CONTROL_AGE_MAX = 74  # for pre-2023 analysis

BASELINE_START = 2000
BASELINE_END = 2015

# Comparator country sets
VISEGRAD = ["CZE", "SVK", "HUN"]
CEE_BROAD = VISEGRAD + ["EST", "LTU", "LVA", "HRV", "SVN", "BGR"]
EU_MIXED = CEE_BROAD + ["AUT", "DEU", "ESP", "ITA"]

ALL_COMPARATORS = {
    "Visegrad": VISEGRAD,
    "CEE-broad": CEE_BROAD,
    "EU-mixed": EU_MIXED,
}

# HMD cause-of-death codes (short list)
CAUSE_CODES = {
    "S000": "All causes",
    "S001": "Infectious & parasitic",
    "S002": "Neoplasms",
    "S003": "Endocrine, nutritional, metabolic",
    "S004": "Blood diseases",
    "S005": "Mental & behavioural",
    "S006": "Nervous system",
    "S007": "Circulatory system",
    "S008": "Respiratory system",
    "S009": "Digestive system",
    "S010": "Perinatal conditions",
    "S011": "Genitourinary system",
    "S012": "Ill-defined causes",
    "S013": "Musculoskeletal",
    "S014": "Other",
    "S015": "Congenital anomalies",
    "S016": "External causes",
}

# Drug-relevant cause categories for supplementary analysis
DRUG_RELEVANT_CAUSES = ["S007", "S008", "S003", "S002"]

# Figure style
FIGURE_DPI = 300
FIGURE_FORMAT = "pdf"

# Matplotlib configuration for publication-quality figures
# Use a project-local, writable MPL config directory to avoid ~/.matplotlib issues
MPL_CONFIG_DIR = PROJECT_ROOT / ".mpl_config"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPL_CONFIG_DIR)

import matplotlib as mpl
mpl.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": FIGURE_DPI,
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.figsize": (8, 5),
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 1.5,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})
