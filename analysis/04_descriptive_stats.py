"""
04_descriptive_stats.py
=======================
Table 1: Mean mortality rates by cohort cluster and age interval,
split by treated vs. control birth weeks.
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from analysis.config import TABLES_DIR, AGE_INTERVALS


def build_table1(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for study, grp in panel.groupby("study"):
        for lo, hi, label in AGE_INTERVALS:
            sub = grp[(grp["age"] >= lo) & (grp["age"] <= hi)]
            if len(sub) == 0:
                continue
            ctrl = sub[sub["treated"] == 0]
            trt  = sub[sub["treated"] == 1]
            if len(ctrl) == 0 and len(trt) == 0:
                continue
            rows.append({
                "study":          study,
                "age_interval":   label,
                "ctrl_mean":      ctrl["rate"].mean() if len(ctrl) > 0 else float("nan"),
                "ctrl_sd":        ctrl["rate"].std()  if len(ctrl) > 0 else float("nan"),
                "ctrl_n":         len(ctrl),
                "trt_mean":       trt["rate"].mean()  if len(trt) > 0 else float("nan"),
                "trt_sd":         trt["rate"].std()   if len(trt) > 0 else float("nan"),
                "trt_n":          len(trt),
            })
    return pd.DataFrame(rows)


def main() -> None:
    panel = pd.read_csv(TABLES_DIR / "panel_clean.csv")
    t1 = build_table1(panel)

    fmt = t1.copy()
    fmt["ctrl_mean_fmt"] = fmt.apply(
        lambda r: f"{r.ctrl_mean:.3f} ({r.ctrl_sd:.3f})", axis=1
    )
    fmt["trt_mean_fmt"] = fmt.apply(
        lambda r: f"{r.trt_mean:.3f} ({r.trt_sd:.3f})", axis=1
    )
    print("=== Table 1: Sample characteristics ===")
    print(fmt[["study", "age_interval", "ctrl_mean_fmt", "ctrl_n",
               "trt_mean_fmt", "trt_n"]].to_string(index=False))

    t1.to_csv(TABLES_DIR / "results_descriptive.csv", index=False)
    print(f"\nSaved → {TABLES_DIR / 'results_descriptive.csv'}")


if __name__ == "__main__":
    main()
