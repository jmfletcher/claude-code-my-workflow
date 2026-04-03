"""
02_regressions.py
=================
Run all OLS regressions and export coefficient tables.

Specification:
  rate_{b,y,a} = α + β·treated_{b,y} + γ_a + δ_y + η_w + ε_{b,y,a}

  where η_w are week-in-year fixed effects (position 1–9, chronological),
  γ_a are age fixed effects (single year of age), δ_y are birth-year FEs.
  Standard errors clustered by birth_week.

Outputs:
  tables/results_pooled.csv
  tables/results_by_age.csv
  tables/results_by_cohort.csv
  tables/results_by_cohort_age.csv
  tables/results_robustness.csv
  tables/results_cause.csv
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analysis.config import (
    TABLES_DIR, AGE_INTERVALS, TREATED_WIY, ROBUSTNESS_WINDOWS, GROUPS,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _formula(outcome: str = "rate") -> str:
    return (
        f"{outcome} ~ treated "
        "+ C(age) + C(birth_year) + C(week_in_year)"
    )


def _fit(df: pd.DataFrame, formula: str = None) -> dict:
    """Return a dict with coef, se, pval, n for the 'treated' term."""
    if formula is None:
        formula = _formula()
    model = smf.ols(formula, data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["birth_week"]}
    )
    coef = model.params["treated"]
    se   = model.bse["treated"]
    pval = model.pvalues["treated"]
    n    = int(model.nobs)
    return {"coef": coef, "se": se, "pval": pval, "n": n}


def stars(p: float) -> str:
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.10: return "*"
    return ""


# ── Load panel ────────────────────────────────────────────────────────────────

def load_panel() -> pd.DataFrame:
    path = TABLES_DIR / "panel_clean.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run 01_load_and_clean.py first."
        )
    df = pd.read_csv(path)
    df["birth_week"] = df["birth_week"].astype(str)
    return df


# ── Regressions ───────────────────────────────────────────────────────────────

def pooled(df: pd.DataFrame) -> pd.DataFrame:
    r = _fit(df)
    row = {
        "spec": "Pooled (all ages, all cohorts)",
        "coef": r["coef"], "se": r["se"], "pval": r["pval"], "n": r["n"],
        "stars": stars(r["pval"]),
    }
    return pd.DataFrame([row])


def by_age(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for lo, hi, label in AGE_INTERVALS:
        sub = df[(df["age"] >= lo) & (df["age"] <= hi)]
        if sub["treated"].sum() == 0:
            continue
        r = _fit(sub)
        rows.append({
            "age_interval": label, "age_lo": lo, "age_hi": hi,
            **r, "stars": stars(r["pval"]),
        })
    return pd.DataFrame(rows)


def by_cohort(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for g, info in GROUPS.items():
        sub = df[df["group"] == g]
        r = _fit(sub)
        rows.append({
            "study": info["study"], "group": g, "spec": "Pooled",
            **r, "stars": stars(r["pval"]),
        })
    return pd.DataFrame(rows)


def by_cohort_age(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for g, info in GROUPS.items():
        gsub = df[df["group"] == g]
        r = _fit(gsub)
        rows.append({
            "study": info["study"], "age_interval": "Pooled",
            **r, "stars": stars(r["pval"]),
        })
        for lo, hi, label in AGE_INTERVALS:
            sub = gsub[(gsub["age"] >= lo) & (gsub["age"] <= hi)]
            if sub["treated"].sum() == 0 or len(sub) < 10:
                continue
            r = _fit(sub)
            rows.append({
                "study": info["study"], "age_interval": label,
                "age_lo": lo, "age_hi": hi,
                **r, "stars": stars(r["pval"]),
            })
    return pd.DataFrame(rows)


def robustness(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Baseline
    r = _fit(df)
    rows.append({"spec": "B: Baseline (all weeks, level rate)", **r,
                 "stars": stars(r["pval"])})

    # Narrow windows (chronological week_in_year positions)
    for label, (lo, hi) in ROBUSTNESS_WINDOWS.items():
        sub = df[(df["week_in_year"] >= lo) & (df["week_in_year"] <= hi)]
        r = _fit(sub)
        rows.append({"spec": label, **r, "stars": stars(r["pval"])})

    # Log outcome — exclude -inf (zero death counts)
    sub_log = df[df["log_rate"].notna() & np.isfinite(df["log_rate"])].copy()
    r = _fit(sub_log, _formula("log_rate"))
    rows.append({"spec": "R3: Log outcome (log rate)", **r,
                 "stars": stars(r["pval"])})

    # Leave-one-out cohort
    for drop_g, info in GROUPS.items():
        sub = df[df["group"] != drop_g]
        others = [v["name"] for k, v in GROUPS.items() if k != drop_g]
        label = f"R{3 + drop_g}: Drop {info['name']} ({' + '.join(others)})"
        r = _fit(sub)
        rows.append({"spec": label, **r, "stars": stars(r["pval"])})

    return pd.DataFrame(rows)


def cause_of_death(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run pooled regression on each cause-of-death category.
    Requires the cause columns to be present (loaded from 08_cause_of_death.py).
    If not present, skip.
    """
    cause_cols = [c for c in df.columns if c.startswith("cause_")]
    if not cause_cols:
        print("  No cause columns found; skipping cause decomposition.")
        return pd.DataFrame()
    rows = []
    for col in cause_cols:
        label = col.replace("cause_", "").replace("_", " ")
        sub = df[df[col].notna()].copy()
        sub = sub.rename(columns={col: "rate_cause"})
        r = _fit(sub, _formula("rate_cause"))
        rows.append({"cause": label, **r, "stars": stars(r["pval"])})
    return pd.DataFrame(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    df = load_panel()
    print(f"Panel loaded: {len(df):,} rows, treated={df['treated'].sum()} obs")

    print("\n=== Pooled estimate ===")
    t_pooled = pooled(df)
    print(t_pooled.to_string(index=False))
    t_pooled.to_csv(TABLES_DIR / "results_pooled.csv", index=False)

    print("\n=== By age interval ===")
    t_age = by_age(df)
    print(t_age[["age_interval", "coef", "se", "pval", "n", "stars"]].to_string(index=False))
    t_age.to_csv(TABLES_DIR / "results_by_age.csv", index=False)

    print("\n=== By cohort (pooled) ===")
    t_cohort = by_cohort(df)
    print(t_cohort[["study", "coef", "se", "pval", "n", "stars"]].to_string(index=False))
    t_cohort.to_csv(TABLES_DIR / "results_by_cohort.csv", index=False)

    print("\n=== By cohort × age interval ===")
    t_ca = by_cohort_age(df)
    print(t_ca[["study", "age_interval", "coef", "se", "pval", "n", "stars"]].to_string(index=False))
    t_ca.to_csv(TABLES_DIR / "results_by_cohort_age.csv", index=False)

    print("\n=== Robustness ===")
    t_rob = robustness(df)
    print(t_rob[["spec", "coef", "se", "pval", "n", "stars"]].to_string(index=False))
    t_rob.to_csv(TABLES_DIR / "results_robustness.csv", index=False)

    print("\nAll regression tables saved to", TABLES_DIR)


if __name__ == "__main__":
    main()
