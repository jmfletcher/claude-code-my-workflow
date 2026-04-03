"""
08_descriptive_stats.py
=======================
Two outputs:

  TABLE A  Descriptive statistics: mean mortality rates (per 1,000/yr) by
           age interval and cohort cluster, separately for treated and
           control birth weeks.  Includes number of birth-week × age cells
           and the standard deviation across cells.

  TABLE B  Appendix — validation against HMD: our observed control-week
           mortality rates by age interval, compared with the Human
           Mortality Database (HMD) period death rates for England and
           Wales (GBRTENW) for the same calendar-year windows.
           HMD rates (deaths per person per year) are multiplied by 1,000
           to match our units.

Outputs
-------
  output/tables/08_descriptive_stats.csv        (Table A)
  output/tables/08_hmd_comparison.csv           (Table B)
  output/tables/08_descriptive_stats.tex        (LaTeX version of Table A)
  output/tables/08_hmd_comparison.tex           (LaTeX version of Table B)

Run from repo root:
    python3 analysis/08_descriptive_stats.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT     = Path(__file__).resolve().parent.parent
OUT_TAB  = ROOT / "output" / "tables"
AGE_AGG  = OUT_TAB / "01_age_aggregated.csv"
HMD_FILE = ROOT / "Data" / "HMD" / "Mx_1x1.txt"
OUT_TAB.mkdir(parents=True, exist_ok=True)

AGE_BINS   = [(0, 9), (10, 19), (20, 29), (30, 39),
              (40, 49), (50, 59), (60, 69)]
STUDY_MAP  = {1: "NSHD 1946", 2: "NCDS 1958", 3: "BCS70 1970"}

# Calendar-year windows each cohort cluster is observed in our data
# (birth_year range × age range → death_year range)
COHORT_WINDOWS = {
    1: (1970, 2013),   # NSHD: birth years 1944-1948, ages 22-69
    2: (1970, 2013),   # NCDS: birth years 1956-1960, ages 10-57
    3: (1970, 2013),   # BCS70: birth years 1968-1972, ages 0-45
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def age_bin_label(lo: int, hi: int) -> str:
    return f"{lo}–{hi}"


def assign_bin(age: int) -> str | None:
    for lo, hi in AGE_BINS:
        if lo <= age <= hi:
            return age_bin_label(lo, hi)
    return None


def stars(p: float) -> str:
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


# ---------------------------------------------------------------------------
# TABLE A — descriptive statistics
# ---------------------------------------------------------------------------

def make_table_a(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["age_bin"] = df["age"].apply(assign_bin)
    df = df.dropna(subset=["age_bin", "rate"])

    rows = []
    for grp, study in STUDY_MAP.items():
        sub = df[df["group"] == grp]
        for lo, hi in AGE_BINS:
            label = age_bin_label(lo, hi)
            cells = sub[sub["age_bin"] == label]
            if cells.empty:
                continue

            ctrl = cells[cells["cohort"] == 0]["rate"]
            trt  = cells[cells["cohort"] == 1]["rate"]

            rows.append({
                "Study":             study,
                "Age interval":      label,
                "Control mean":      ctrl.mean() if len(ctrl) else np.nan,
                "Control SD":        ctrl.std()  if len(ctrl) else np.nan,
                "Control N cells":   len(ctrl),
                "Treated mean":      trt.mean()  if len(trt) else np.nan,
                "Treated SD":        trt.std()   if len(trt) else np.nan,
                "Treated N cells":   len(trt),
            })

    tbl = pd.DataFrame(rows)
    return tbl


def format_table_a(tbl: pd.DataFrame) -> pd.DataFrame:
    out = tbl.copy()
    out["Control mean (SD)"] = out.apply(
        lambda r: f"{r['Control mean']:.3f} ({r['Control SD']:.3f})"
        if not pd.isna(r["Control mean"]) else "—", axis=1)
    out["Treated mean (SD)"] = out.apply(
        lambda r: f"{r['Treated mean']:.3f} ({r['Treated SD']:.3f})"
        if not pd.isna(r["Treated mean"]) else "—", axis=1)
    out["N (control cells)"] = out["Control N cells"].astype(int)
    out["N (treated cells)"] = out["Treated N cells"].astype(int)
    return out[["Study", "Age interval",
                "Control mean (SD)", "N (control cells)",
                "Treated mean (SD)", "N (treated cells)"]]


# ---------------------------------------------------------------------------
# TABLE B — HMD comparison
# ---------------------------------------------------------------------------

def load_hmd(path: Path) -> pd.DataFrame:
    hmd = pd.read_csv(
        path, sep=r"\s+", skiprows=2,
        names=["PopName", "Year", "Age", "Female", "Male", "Total"],
    )
    hmd = hmd[hmd["PopName"] == "GBRTENW"].copy()
    hmd["Year"] = pd.to_numeric(hmd["Year"], errors="coerce")
    hmd["Age"]  = pd.to_numeric(hmd["Age"].astype(str).str.replace("+", "", regex=False),
                                errors="coerce")
    hmd["Total"] = pd.to_numeric(hmd["Total"], errors="coerce")
    # Convert to per 1,000 per year
    hmd["mx_per1000"] = hmd["Total"] * 1000
    return hmd.dropna(subset=["Year", "Age", "mx_per1000"])


def make_table_b(df: pd.DataFrame, hmd: pd.DataFrame) -> pd.DataFrame:
    """
    Match HMD period rates to the exact (age, death_year) cells in our data,
    then aggregate by study and age interval.  This ensures the comparison
    uses the same calendar-year × age combinations in both series, rather
    than averaging HMD over the full 1970-2013 window.
    """
    df = df.copy()
    df["age_bin"]    = df["age"].apply(assign_bin)
    df["death_year"] = df["birth_year"] + df["age"]
    df = df.dropna(subset=["age_bin", "rate", "death_year"])
    df["death_year"] = df["death_year"].astype(int)
    df["age"]        = df["age"].astype(int)

    # Build HMD lookup: (Year, Age) -> mx_per1000
    hmd_lookup = hmd.set_index(
        [hmd["Year"].astype(int), hmd["Age"].astype(int)]
    )["mx_per1000"]

    # Attach matched HMD rate to each ONS row
    def match_hmd(row):
        key = (int(row["death_year"]), int(row["age"]))
        return hmd_lookup.get(key, np.nan)

    df["hmd_rate"] = df.apply(match_hmd, axis=1)

    rows = []
    for grp, study in STUDY_MAP.items():
        sub = df[(df["group"] == grp) & (df["cohort"] == 0)].copy()

        for lo, hi in AGE_BINS:
            label = age_bin_label(lo, hi)
            cells = sub[sub["age_bin"] == label]
            ons   = cells["rate"].dropna()
            hmds  = cells["hmd_rate"].dropna()

            if ons.empty:
                continue

            rows.append({
                "Study":          study,
                "Age interval":   label,
                "ONS mean":       ons.mean(),
                "ONS SD":         ons.std(),
                "ONS N":          len(ons),
                "HMD mean":       hmds.mean() if len(hmds) else np.nan,
                "HMD SD":         hmds.std()  if len(hmds) else np.nan,
                "HMD N":          len(hmds),
                "Ratio ONS/HMD":  (ons.mean() / hmds.mean())
                                  if (len(hmds) and hmds.mean() > 0) else np.nan,
            })

    return pd.DataFrame(rows)


def format_table_b(tbl: pd.DataFrame) -> pd.DataFrame:
    out = tbl.copy()
    out["ONS mean (SD)"] = out.apply(
        lambda r: f"{r['ONS mean']:.3f} ({r['ONS SD']:.3f})"
        if not pd.isna(r["ONS mean"]) else "—", axis=1)
    out["HMD mean (SD)"] = out.apply(
        lambda r: f"{r['HMD mean']:.3f} ({r['HMD SD']:.3f})"
        if not pd.isna(r["HMD mean"]) else "—", axis=1)
    out["ONS/HMD ratio"] = out["Ratio ONS/HMD"].apply(
        lambda x: f"{x:.2f}" if not pd.isna(x) else "—")
    return out[["Study", "Age interval",
                "ONS mean (SD)", "HMD mean (SD)", "ONS/HMD ratio"]]


# ---------------------------------------------------------------------------
# LaTeX rendering
# ---------------------------------------------------------------------------

def to_latex(display: pd.DataFrame, caption: str, label: str) -> str:
    col_fmt = "ll" + "r" * (len(display.columns) - 2)
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\small",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{{col_fmt}}}",
        r"\toprule",
    ]
    # Header
    lines.append(" & ".join(display.columns) + r" \\")
    lines.append(r"\midrule")

    prev_study = None
    for _, row in display.iterrows():
        if row.iloc[0] != prev_study:
            if prev_study is not None:
                lines.append(r"\midrule")
            prev_study = row.iloc[0]
        lines.append(" & ".join(str(v) for v in row.values) + r" \\")

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("  08_descriptive_stats.py")
    print("=" * 70)

    for p in (AGE_AGG, HMD_FILE):
        if not p.exists():
            print(f"[ERROR] Missing: {p}")
            sys.exit(1)

    df = pd.read_csv(AGE_AGG)
    df["rate"]       = pd.to_numeric(df["rate"],       errors="coerce")
    df["age"]        = pd.to_numeric(df["age"],        errors="coerce")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce")
    df = df.dropna(subset=["rate", "age"])

    hmd = load_hmd(HMD_FILE)
    print(f"HMD England & Wales: {len(hmd):,} rows, "
          f"years {int(hmd['Year'].min())}–{int(hmd['Year'].max())}")

    # --- Table A
    print("\nBuilding Table A (descriptive statistics)...")
    tbl_a_raw = make_table_a(df)
    tbl_a_raw.to_csv(OUT_TAB / "08_descriptive_stats.csv", index=False)
    tbl_a_fmt = format_table_a(tbl_a_raw)
    print(tbl_a_fmt.to_string(index=False))
    with open(OUT_TAB / "08_descriptive_stats.tex", "w") as f:
        f.write(to_latex(
            tbl_a_fmt,
            caption=(
                "Mean mortality rates (deaths per 1,000 per year) by age interval "
                "and cohort cluster. SD across birth-week $\\times$ age cells. "
                "Treated = the cohort-selected birth week; Control = the eight "
                "adjacent birth weeks."
            ),
            label="tab:descriptive",
        ))
    print("  Saved: 08_descriptive_stats.csv/.tex")

    # --- Table B
    print("\nBuilding Table B (HMD comparison)...")
    tbl_b_raw = make_table_b(df, hmd)
    tbl_b_raw.to_csv(OUT_TAB / "08_hmd_comparison.csv", index=False)
    tbl_b_fmt = format_table_b(tbl_b_raw)
    print(tbl_b_fmt.to_string(index=False))
    with open(OUT_TAB / "08_hmd_comparison.tex", "w") as f:
        f.write(to_latex(
            tbl_b_fmt,
            caption=(
                "Comparison of ONS control-week mortality rates with HMD period "
                "death rates for England and Wales (GBRTENW), by cohort cluster and "
                "age interval. Both series in deaths per 1,000 per year. HMD rates "
                "are period rates averaged over the same calendar-year window as "
                "the ONS observations. Ratio $>1$ indicates ONS rates exceed HMD "
                "national average; ratio $<1$ indicates they are below."
            ),
            label="tab:hmd_comparison",
        ))
    print("  Saved: 08_hmd_comparison.csv/.tex")
    print("\nDone.")
