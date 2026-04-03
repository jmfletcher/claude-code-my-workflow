"""
03_hmd_comparison.py
====================
Appendix Table A1: ONS control-week rates vs. HMD period rates.

The HMD file (Data/HMD/Mx_1x1.txt) is the multi-country aggregate file
with 6 columns: PopName, Year, Age, Female, Male, Total.
We filter to GBRTENW (England & Wales combined).

HMD death rates are period mx (deaths per person per year).  We multiply
by 1,000 to match our ONS units, then match each ONS control-week
observation to the HMD cell at the same age AND calendar year of death.
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from analysis.config import HMD_PATH, TABLES_DIR, AGE_INTERVALS, HMD_POPNAME


def load_hmd() -> pd.DataFrame:
    """
    Parse the multi-country HMD Mx_1x1.txt.

    Format (after 2-row header):
        PopName  Year  Age  Female  Male  Total
    The 'Total' column is mx (deaths per person per year); we convert to
    deaths per 1,000 per year by multiplying by 1,000.
    """
    hmd = pd.read_csv(
        HMD_PATH,
        sep=r"\s+",
        skiprows=2,
        names=["PopName", "Year", "Age", "Female", "Male", "Total"],
    )
    hmd = hmd[hmd["PopName"] == HMD_POPNAME].copy()
    hmd["Year"]  = pd.to_numeric(hmd["Year"],  errors="coerce")
    hmd["Age"]   = pd.to_numeric(
        hmd["Age"].astype(str).str.replace("+", "", regex=False),
        errors="coerce",
    )
    hmd["Total"] = pd.to_numeric(hmd["Total"], errors="coerce")
    hmd["mx_per1000"] = hmd["Total"] * 1_000
    return hmd.dropna(subset=["Year", "Age", "mx_per1000"])


def build_comparison(panel: pd.DataFrame, hmd: pd.DataFrame) -> pd.DataFrame:
    """
    For each (study, age interval) compute:
      - ONS mean/SD from control-week observations
      - HMD mean/SD from matched (age, calendar_year_of_death) cells
      - ratio ONS/HMD
    """
    panel = panel.copy()
    panel["death_year"] = panel["birth_year"] + panel["age"]

    hmd_lookup = hmd.set_index(["Age", "Year"])["mx_per1000"]
    panel["hmd_rate"] = [
        hmd_lookup.get((int(r.age), int(r.death_year)), np.nan)
        for r in panel.itertuples()
    ]

    rows = []
    for study, grp in panel.groupby("study"):
        ctrl = grp[grp["treated"] == 0]
        for lo, hi, label in AGE_INTERVALS:
            sub = ctrl[(ctrl["age"] >= lo) & (ctrl["age"] <= hi)]
            sub_hmd = sub.dropna(subset=["hmd_rate"])
            if len(sub) == 0:
                continue
            ons_mean = sub["rate"].mean()
            ons_sd   = sub["rate"].std()
            hmd_mean = sub_hmd["hmd_rate"].mean() if len(sub_hmd) > 0 else np.nan
            hmd_sd   = sub_hmd["hmd_rate"].std()  if len(sub_hmd) > 0 else np.nan
            ratio    = ons_mean / hmd_mean if hmd_mean and hmd_mean > 0 else np.nan
            rows.append({
                "study": study,
                "age_interval": label,
                "ons_mean": ons_mean,
                "ons_sd": ons_sd,
                "hmd_mean": hmd_mean,
                "hmd_sd": hmd_sd,
                "ratio": ratio,
            })
    return pd.DataFrame(rows)


def main() -> None:
    panel = pd.read_csv(TABLES_DIR / "panel_clean.csv")

    print("Loading HMD data …")
    hmd = load_hmd()
    print(f"  HMD rows (GBRTENW): {len(hmd):,}")

    comp = build_comparison(panel, hmd)
    comp = comp.dropna(subset=["hmd_mean"])

    fmt = comp.copy()
    fmt["ons_mean_fmt"] = fmt.apply(
        lambda r: f"{r.ons_mean:.3f} ({r.ons_sd:.3f})", axis=1
    )
    fmt["hmd_mean_fmt"] = fmt.apply(
        lambda r: f"{r.hmd_mean:.3f} ({r.hmd_sd:.3f})", axis=1
    )
    fmt["ratio_fmt"] = fmt["ratio"].map(lambda x: f"{x:.2f}")

    print("\n=== Appendix Table A1: ONS vs HMD ===")
    print(fmt[["study", "age_interval", "ons_mean_fmt",
               "hmd_mean_fmt", "ratio_fmt"]].to_string(index=False))

    comp.to_csv(TABLES_DIR / "results_hmd_comparison.csv", index=False)
    print(f"\nSaved → {TABLES_DIR / 'results_hmd_comparison.csv'}")


if __name__ == "__main__":
    main()
