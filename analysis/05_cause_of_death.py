"""
05_cause_of_death.py
====================
Panel Conditioning (UK cohorts) — cause-of-death breakdown.

Reads the ONS cause-of-death XLS and maps ICD chapters (ICD-8, ICD-9, ICD-10)
to five harmonised cause categories:
  cancer        — neoplasms
  cardiovascular — circulatory system diseases
  respiratory   — respiratory system diseases
  external      — accidents, injury, suicide, homicide
  other         — all remaining chapters

For each cause category, runs the main regression:
  rate ~ cohort + C(age) + C(birth_year) + C(week_in_year)
pooled and by cohort group, to identify which causes drive the treatment effect.

Outputs:
  output/tables/05_cause_long.csv         — long format: birth_week × death_year × cause
  output/tables/05_cause_age_agg.csv      — aggregated to birth_week × age × cause
  output/tables/05_cause_coef_pooled.csv  — pooled cohort coef by cause category
  output/tables/05_cause_coef_by_cohort.csv — by cohort × cause
  output/figures/fig05_cause_coefs.pdf/.png

Run from repo root:
    python3 analysis/05_cause_of_death.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT       = Path(__file__).resolve().parent.parent
DATA       = ROOT / "Data"
OUT_TAB    = ROOT / "output" / "tables"
OUT_FIG    = ROOT / "output" / "figures"
OUT_TAB.mkdir(parents=True, exist_ok=True)
OUT_FIG.mkdir(parents=True, exist_ok=True)

COD_XLS = DATA / (
    "deathsregisteredbycauseofdeathicdchapterbyselectedweekofbirthenglandandwales"
    "1970to2013_tcm77-419405.xls"
)

# Metadata from the main clean dataset
CLEAN_LONG = OUT_TAB / "01_clean_long.csv"

N_PER_WEEK = 15_334.0  # same denominator as main analysis

# ---------------------------------------------------------------------------
# ICD → cause category mapping
# The ONS XLS uses soft-hyphens (\xad) in column labels; we strip all
# non-ASCII dashes/hyphens before matching.
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    """Normalise a column name: strip whitespace, replace soft-hyphen with '-'."""
    return str(s).replace("\xad", "-").replace("\u2012", "-").strip()


# Map normalised ICD range prefix → harmonised cause category
# Patterns match start of the normalised column label (or full label).
ICD8_MAP = {
    "000-136": "other",        # Infectious & parasitic
    "140-239": "cancer",       # Neoplasms
    "240-279": "other",        # Endocrine/nutritional
    "280-289": "other",        # Blood diseases
    "290-315": "other",        # Mental disorders
    "320-389": "other",        # Nervous system
    "390-458": "cardiovascular",
    "460-519": "respiratory",
    "520-577": "other",        # Digestive
    "580-629": "other",        # Genitourinary
    "630-678": "other",        # Obstetric
    "680-709": "other",        # Skin
    "710-738": "other",        # Musculoskeletal
    "740-759": "other",        # Congenital
    "760-779": "other",        # Perinatal
    "780-796": "other",        # Ill-defined
    "E800-E999": "external",
}

ICD9_MAP = {
    "001-139": "other",
    "140-239": "cancer",
    "240-279": "other",
    "280-289": "other",
    "290-319": "other",
    "320-389": "other",
    "390-459": "cardiovascular",
    "460-519": "respiratory",
    "520-579": "other",
    "580-629": "other",
    "630-676": "other",
    "680-709": "other",
    "710-739": "other",
    "740-759": "other",
    "760-779": "other",
    "780-799": "other",
    "E800-E999": "external",
}

ICD10_MAP = {
    "A00-B99": "other",        # Infectious
    "C00-D48": "cancer",       # Neoplasms
    "D50-D89": "other",        # Blood
    "E00-E90": "other",        # Endocrine
    "F00-F99": "other",        # Mental
    "G00-G99": "other",        # Nervous
    "H00-H59": "other",
    "H60-H95": "other",
    "I00-I99": "cardiovascular",
    "J00-J99": "respiratory",
    "K00-K93": "other",        # Digestive
    "L00-L99": "other",
    "M00-M99": "other",
    "N00-N99": "other",
    "O00-O99": "other",
    "P00-P96": "other",
    "Q00-Q99": "other",
    "R00-R99": "other",        # Ill-defined
    "U509": "external",        # Covid/misc (ICD-10 late addition)
    "V01-Y89": "external",
}


def detect_icd_version(cols: list[str]) -> dict:
    """Detect ICD version from column names and return the appropriate mapping."""
    col_str = " ".join(_norm(c) for c in cols)
    if "A00-B99" in col_str or "I00-I99" in col_str:
        return ICD10_MAP
    if "001-139" in col_str or "390-459" in col_str:
        return ICD9_MAP
    return ICD8_MAP


def map_columns(df: pd.DataFrame, icd_map: dict) -> pd.DataFrame:
    """Add a 'cause' column by melting ICD columns and mapping to categories."""
    # Rename first col to birth_week; col 1 = All Causes; rest = ICD chapters
    df = df.copy()
    df.columns = ["birth_week"] + [_norm(c) for c in df.columns[1:]]

    # Identify chapter columns (not 'birth_week' or 'All Causes' or 'All causes')
    chapter_cols = [c for c in df.columns if c not in ("birth_week",)
                    and not c.lower().startswith("all")]

    # Melt to long format: birth_week, icd_range, deaths
    melted = df[["birth_week"] + chapter_cols].melt(
        id_vars="birth_week",
        var_name="icd_range",
        value_name="deaths",
    )
    melted["deaths"] = pd.to_numeric(melted["deaths"], errors="coerce").fillna(0)

    # Map ICD range → cause category
    def get_cause(icd_range: str) -> str:
        norm = _norm(icd_range)
        # Try direct match first
        if norm in icd_map:
            return icd_map[norm]
        # Try prefix match (for ICD-10 combined columns like "U509‚V01-Y89")
        for key, cat in icd_map.items():
            if key in norm or norm.startswith(key[:3]):
                return cat
        return "other"

    melted["cause"] = melted["icd_range"].apply(get_cause)
    return melted.groupby(["birth_week", "cause"])["deaths"].sum().reset_index()


# ---------------------------------------------------------------------------
# Load ONS cause-of-death data
# ---------------------------------------------------------------------------

def load_cod(path: Path) -> pd.DataFrame:
    xl = pd.ExcelFile(path, engine="xlrd")
    data_sheets = [s for s in xl.sheet_names if s.startswith("Data ")]
    print(f"  Found {len(data_sheets)} sheets: {data_sheets[0]} … {data_sheets[-1]}")

    rows = []
    for sheet in data_sheets:
        death_year = int(sheet.replace("Data ", ""))
        df = pd.read_excel(path, sheet_name=sheet, header=6, engine="xlrd")
        df = df.dropna(subset=[df.columns[0]])
        df[df.columns[0]] = df[df.columns[0]].astype(str).str.strip()
        df = df[df[df.columns[0]].str.len() > 3]

        icd_map = detect_icd_version(list(df.columns))
        melted  = map_columns(df, icd_map)
        melted["death_year"] = death_year
        rows.append(melted)

    cod_long = pd.concat(rows, ignore_index=True)
    return cod_long


# ---------------------------------------------------------------------------
# Merge with cohort metadata
# ---------------------------------------------------------------------------

def build_cod_analytic(cod: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Join cause-of-death long data with birth_week metadata."""
    # meta = 01_clean_long.csv with columns: birth_week, death_year, birth_year,
    #        group, cohort, study, age, week_in_year
    meta_key = meta[["birth_week", "death_year", "birth_year",
                      "group", "cohort", "study", "age", "week_in_year"]].copy()
    merged = cod.merge(meta_key, on=["birth_week", "death_year"], how="inner")
    merged["rate"] = merged["deaths"] / N_PER_WEEK * 1000
    return merged


# ---------------------------------------------------------------------------
# Regression helpers (same as 02_replicate_stata.py)
# ---------------------------------------------------------------------------

def run_ols(formula: str, data: pd.DataFrame, cluster_col: str) -> dict | None:
    if len(data) < 20 or data["cohort"].nunique() < 2:
        return None
    try:
        result = smf.ols(formula, data=data).fit(
            cov_type="cluster",
            cov_kwds={"groups": data[cluster_col]},
        )
        cohort_idx = [i for i in result.params.index if i == "cohort"]
        if not cohort_idx:
            cohort_idx = [i for i in result.params.index if "cohort" in i]
        if not cohort_idx:
            return None
        idx = cohort_idx[0]
        return {
            "coef": result.params[idx],
            "se":   result.bse[idx],
            "t":    result.tvalues[idx],
            "pval": result.pvalues[idx],
            "ci_lo": result.conf_int().loc[idx, 0],
            "ci_hi": result.conf_int().loc[idx, 1],
            "n":    int(result.nobs),
        }
    except Exception as e:
        print(f"    [WARN] regression failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

CAUSES = ["cancer", "cardiovascular", "respiratory", "external", "other"]
FORMULA = "rate ~ cohort + C(age) + C(birth_year) + C(week_in_year)"
COHORT_NAMES = {1: "NSHD 1946", 2: "NCDS 1958", 3: "BCS70 1970"}


def run_cause_regressions(df_age: pd.DataFrame) -> tuple[list, list]:
    """Return (pooled_results, by_cohort_results) lists of dicts."""
    pooled_rows = []
    by_cohort_rows = []

    for cause in CAUSES:
        sub = df_age[df_age["cause"] == cause].copy()
        # Convert FE variables to string for Patsy; drop originals to avoid
        # duplicate column names that break statsmodels C() encoding
        sub["birth_year"] = sub["birth_year"].astype(str)
        sub["age"]        = sub["age"].astype(str)
        sub["week_in_year"] = sub["week_in_year"].astype(str)
        sub = sub.rename(columns={"birth_week": "week"})

        print(f"\n  Cause: {cause}  ({len(sub):,} rows)")

        # Pooled
        r = run_ols(FORMULA, sub, "week")
        if r:
            r["cause"] = cause
            r["study"] = "All"
            pooled_rows.append(r)
            print(f"    Pooled: β={r['coef']:.4f}  SE={r['se']:.4f}  p={r['pval']:.3f}")

        # By cohort
        for grp, name in COHORT_NAMES.items():
            grp_sub = sub[sub["group"] == grp]
            r2 = run_ols(FORMULA, grp_sub, "week")
            if r2:
                r2["cause"] = cause
                r2["study"] = name
                by_cohort_rows.append(r2)

    return pooled_rows, by_cohort_rows


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

CAUSE_LABELS = {
    "cancer":         "Cancer",
    "cardiovascular": "Cardiovascular",
    "respiratory":    "Respiratory",
    "external":       "External causes",
    "other":          "Other",
}
BLUE  = "#1a5276"
GRAY  = "#5d6d7e"
LGRAY = "#d5d8dc"

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": LGRAY, "grid.linewidth": 0.6,
    "figure.dpi": 150,
})


def make_cause_figure(pooled: pd.DataFrame, by_cohort: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left: pooled by cause
    ax = axes[0]
    sub = pooled.set_index("cause").reindex(CAUSES)
    sub["label"] = [CAUSE_LABELS[c] for c in CAUSES]
    y = np.arange(len(sub))
    colors = [BLUE if p < 0.05 else GRAY for p in sub["pval"]]
    ax.hlines(y, sub["ci_lo"], sub["ci_hi"], colors=colors, linewidth=2.5)
    ax.scatter(sub["coef"], y, color=colors, s=60, zorder=5)
    ax.axvline(0, color="black", linewidth=0.9, linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels(sub["label"], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Cohort coef. (95% CI)")
    ax.set_title("Pooled (all cohorts)", fontsize=11, fontweight="bold")
    for i, row in sub.reset_index(drop=True).iterrows():
        ax.text(sub["ci_hi"].max() + 0.005, i,
                f"N={int(row['n']):,}", va="center", fontsize=8, color=GRAY)

    # Right: by cohort × cause (dot plot)
    ax2 = axes[1]
    study_colors = {"NSHD 1946": "#1a5276", "NCDS 1958": "#922b21", "BCS70 1970": "#1e8449"}
    markers = {"NSHD 1946": "o", "NCDS 1958": "s", "BCS70 1970": "^"}
    offset = {"NSHD 1946": -0.18, "NCDS 1958": 0, "BCS70 1970": 0.18}

    for study, grp in by_cohort.groupby("study"):
        grp = grp.set_index("cause").reindex(CAUSES).dropna(subset=["coef"])
        y_pos = [CAUSES.index(c) + offset[study] for c in grp.index]
        col = [study_colors[study] if p < 0.05 else "#aaaaaa" for p in grp["pval"]]
        ax2.hlines(y_pos, grp["ci_lo"], grp["ci_hi"],
                   colors=[study_colors[study]] * len(grp), linewidth=1.2, alpha=0.5)
        ax2.scatter(grp["coef"], y_pos, color=col, s=55,
                    marker=markers[study], zorder=5, label=study)

    ax2.axvline(0, color="black", linewidth=0.9, linestyle="--")
    ax2.set_yticks(range(len(CAUSES)))
    ax2.set_yticklabels([CAUSE_LABELS[c] for c in CAUSES], fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel("Cohort coef. (95% CI)")
    ax2.set_title("By cohort study", fontsize=11, fontweight="bold")
    ax2.legend(fontsize=8, framealpha=0.5)

    fig.suptitle(
        "Panel conditioning effect by cause of death\n"
        "OLS with age, birth-year, week-of-year FE; SE clustered by birth week",
        fontsize=11, y=1.02
    )
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT_FIG / f"fig05_cause_coefs.{ext}", bbox_inches="tight", dpi=300)
        print(f"  Saved: fig05_cause_coefs.{ext}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("  05_cause_of_death.py — cause-specific mortality analysis")
    print("=" * 70)

    if not COD_XLS.exists():
        print(f"[ERROR] ONS cause-of-death file not found: {COD_XLS}")
        sys.exit(1)
    if not CLEAN_LONG.exists():
        print(f"[ERROR] Run 01_load_and_clean.py first: {CLEAN_LONG}")
        sys.exit(1)

    print("\nLoading cause-of-death ONS data...")
    cod_long = load_cod(COD_XLS)
    print(f"  Loaded: {len(cod_long):,} rows  |  causes: {cod_long['cause'].unique()}")

    print("\nLoading metadata from 01_clean_long.csv...")
    meta = pd.read_csv(CLEAN_LONG)

    print("\nBuilding analytic dataset...")
    analytic = build_cod_analytic(cod_long, meta)
    print(f"  Analytic rows: {len(analytic):,}")
    print(f"  Cause distribution:\n{analytic.groupby('cause')['deaths'].sum().sort_values(ascending=False).to_string()}")
    analytic.to_csv(OUT_TAB / "05_cause_long.csv", index=False)

    # Aggregate to birth_week × age × cause (for regression)
    age_agg = (
        analytic[analytic["age"].between(1, 69)]
        .groupby(["birth_week", "birth_year", "group", "cohort",
                  "study", "week_in_year", "age", "cause"])
        ["deaths"].sum()
        .reset_index()
    )
    age_agg["rate"] = age_agg["deaths"] / N_PER_WEEK * 1000
    age_agg.to_csv(OUT_TAB / "05_cause_age_agg.csv", index=False)
    print(f"\n  Age-aggregated rows: {len(age_agg):,}")

    print("\nRunning cause-specific regressions...")
    pooled_rows, by_cohort_rows = run_cause_regressions(age_agg)

    # Save results
    df_pooled = pd.DataFrame(pooled_rows)
    df_by_cohort = pd.DataFrame(by_cohort_rows)
    df_pooled.to_csv(OUT_TAB / "05_cause_coef_pooled.csv", index=False)
    df_by_cohort.to_csv(OUT_TAB / "05_cause_coef_by_cohort.csv", index=False)

    print("\n\nPooled cause-specific cohort coefficients:")
    print(df_pooled[["cause", "coef", "se", "pval", "n"]].to_string(index=False))

    print("\nBy-cohort cause-specific cohort coefficients:")
    print(df_by_cohort[["study", "cause", "coef", "se", "pval", "n"]].to_string(index=False))

    print("\nGenerating figure...")
    make_cause_figure(df_pooled, df_by_cohort)

    print("\nDone.")
