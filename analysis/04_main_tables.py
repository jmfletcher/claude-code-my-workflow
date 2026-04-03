"""
04_main_tables.py
=================
Panel Conditioning (UK cohorts) — publication-ready coefficient tables.

Reads pre-computed regression results from 02_replicate_stata.py outputs and
formats them as:
  Table 1: Pooled OLS results (full coefficient table, condensed)
  Table 2: Age-interval cohort coefficients (the main result table)

Outputs:
  output/tables/04_table1_pooled.csv       — Table 1 as CSV
  output/tables/04_table1_pooled.tex       — Table 1 as LaTeX (manuscript-ready)
  output/tables/04_table2_age_intervals.csv
  output/tables/04_table2_age_intervals.tex
  output/tables/04_results_summary.json   — Machine-readable summary for manuscript

Run from repo root:
    python3 analysis/04_main_tables.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT     = Path(__file__).resolve().parent.parent
OUT_TAB  = ROOT / "output" / "tables"
OUT_TAB.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Load regression outputs from 02_replicate_stata.py
# ---------------------------------------------------------------------------

POOLED_CSV      = OUT_TAB / "02_spec1_pooled_full.csv"
INTERVALS_CSV   = OUT_TAB / "02_age_intervals_cohort_coef.csv"
BY_COHORT_CSV   = OUT_TAB / "02_by_cohort_coef.csv"


def load_pooled() -> pd.DataFrame:
    if not POOLED_CSV.exists():
        raise FileNotFoundError(f"Run 02_replicate_stata.py first: {POOLED_CSV}")
    df = pd.read_csv(POOLED_CSV, index_col=0)
    return df


def load_intervals() -> pd.DataFrame:
    if not INTERVALS_CSV.exists():
        raise FileNotFoundError(f"Run 02_replicate_stata.py first: {INTERVALS_CSV}")
    return pd.read_csv(INTERVALS_CSV)


def load_by_cohort() -> pd.DataFrame:
    if not BY_COHORT_CSV.exists():
        raise FileNotFoundError(f"Run 02_replicate_stata.py first: {BY_COHORT_CSV}")
    return pd.read_csv(BY_COHORT_CSV)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def stars(pval: float) -> str:
    if pval < 0.01:
        return "***"
    if pval < 0.05:
        return "**"
    if pval < 0.10:
        return "*"
    return ""


def fmt_coef(coef: float, se: float, pval: float, decimals: int = 3) -> tuple[str, str]:
    """Return (coef_str_with_stars, se_str_in_parens)."""
    coef_str = f"{coef:.{decimals}f}{stars(pval)}"
    se_str   = f"({se:.{decimals}f})"
    return coef_str, se_str


# ---------------------------------------------------------------------------
# Table 1: Pooled OLS — treatment coefficient only (condensed)
# ---------------------------------------------------------------------------

def make_table1(pooled: pd.DataFrame) -> pd.DataFrame:
    """Extract key rows for a concise pooled results panel."""
    cohort_row = pooled[pooled.index == "cohort"]
    if cohort_row.empty:
        # Try partial match (e.g., C(cohort)[T.1])
        cohort_row = pooled[pooled.index.str.contains("cohort")]

    rows = []
    for idx, row in cohort_row.iterrows():
        coef_s, se_s = fmt_coef(row["coef"], row["se"], row["pval"])
        rows.append({
            "Specification": "Pooled OLS (all ages, all cohorts)",
            "Dependent variable": "Mortality rate",
            "Cohort coefficient": coef_s,
            "(SE)": se_s,
            "p-value": f"{row['pval']:.3f}",
            "N": int(row.get("n", "")) if "n" in row.index else "",
            "R²": "",
        })

    # Also load session info for N and R²
    session_path = OUT_TAB / "02_session_info.json"
    if session_path.exists():
        pass  # R² not in current output; leave blank

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Table 2: Age-interval cohort coefficients
# ---------------------------------------------------------------------------

def make_table2(intervals: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in intervals.iterrows():
        coef_s, se_s = fmt_coef(row["coef"], row["se"], row["pval"])
        rows.append({
            "Age interval": row["age_bin"],
            "Cohort coef.": coef_s,
            "(SE)": se_s,
            "t": f"{row['t']:.3f}",
            "p-value": f"{row['pval']:.3f}",
            "N": f"{int(row['n']):,}",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# LaTeX rendering
# ---------------------------------------------------------------------------

LATEX_HEADER = r"""\begin{table}[htbp]
  \centering
  \small
"""

LATEX_FOOTER = r"""  \begin{tablenotes}
    \footnotesize
    \item \textit{Notes:} OLS with age, birth-year, and week-of-year fixed effects.
    Standard errors (in parentheses) clustered by birth week.
    $^{*}p<0.10$, $^{**}p<0.05$, $^{***}p<0.01$.
    Data: ONS deaths by week of birth, England and Wales 1970--2013.
  \end{tablenotes}
\end{table}
"""


def df_to_latex(df: pd.DataFrame, caption: str, label: str) -> str:
    cols = list(df.columns)
    n_cols = len(cols)
    col_spec = "l" + "c" * (n_cols - 1)

    lines = [LATEX_HEADER]
    lines.append(f"  \\caption{{{caption}}}\n  \\label{{{label}}}")
    lines.append(f"  \\begin{{tabular}}{{{col_spec}}}")
    lines.append("  \\toprule")

    # Header row
    header = " & ".join(f"\\textbf{{{c}}}" for c in cols) + " \\\\"
    lines.append("  " + header)
    lines.append("  \\midrule")

    # Data rows — pair (coef, SE) rows
    i = 0
    rows = df.values.tolist()
    while i < len(rows):
        row = rows[i]
        # Check if next row is a SE row (starts with empty label)
        if (i + 1 < len(rows) and str(rows[i + 1][0]).strip() == ""):
            # Two-line format: coef row + SE row
            coef_line = " & ".join(str(v) for v in row) + " \\\\"
            se_line = " & ".join(str(v) for v in rows[i + 1]) + " \\\\"
            lines.append("  " + coef_line)
            lines.append("  " + se_line)
            i += 2
        else:
            data_line = " & ".join(str(v) for v in row) + " \\\\"
            lines.append("  " + data_line)
            i += 1

    lines.append("  \\bottomrule")
    lines.append("  \\end{tabular}")
    lines.append(LATEX_FOOTER)
    return "\n".join(lines)


def table2_latex(df: pd.DataFrame) -> str:
    """Table 2 with stacked coef / (SE) rows."""
    lines = [LATEX_HEADER]
    lines.append(
        "  \\caption{Panel conditioning effect on mortality rate by age interval}\n"
        "  \\label{tab:age-intervals}"
    )
    lines.append("  \\begin{tabular}{lcccc}")
    lines.append("  \\toprule")
    lines.append(
        "  \\textbf{Age interval} & \\textbf{Cohort coef.} & "
        "\\textbf{t-stat} & \\textbf{p-value} & \\textbf{N} \\\\"
    )
    lines.append("  \\midrule")

    for _, row in df.iterrows():
        coef_col = str(row["Cohort coef."])
        se_col   = str(row["(SE)"])
        lines.append(
            f"  {row['Age interval']} & {coef_col} & "
            f"{row['t']} & {row['p-value']} & {row['N']} \\\\"
        )
        lines.append(f"  & {se_col} & & & \\\\")

    lines.append("  \\bottomrule")
    lines.append("  \\end{tabular}")
    lines.append(LATEX_FOOTER)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Results summary JSON (for manuscript inline references)
# ---------------------------------------------------------------------------

def make_table3(by_cohort: pd.DataFrame) -> pd.DataFrame:
    """Table 3: By-cohort pooled + age-interval coefficients."""
    rows = []
    for _, row in by_cohort.iterrows():
        coef_s, se_s = fmt_coef(row["coef"], row["se"], row["pval"])
        rows.append({
            "Study": row["study"],
            "Age interval": row["age_bin"],
            "Cohort coef.": coef_s,
            "(SE)": se_s,
            "p-value": f"{row['pval']:.3f}",
            "N": f"{int(row['n']):,}",
        })
    return pd.DataFrame(rows)


def make_results_summary(pooled: pd.DataFrame, intervals: pd.DataFrame,
                         by_cohort: pd.DataFrame | None = None) -> dict:
    cohort_row = pooled[pooled.index == "cohort"]
    if cohort_row.empty:
        cohort_row = pooled[pooled.index.str.contains("cohort")]

    summary = {"pooled": {}, "age_intervals": {}}
    if not cohort_row.empty:
        r = cohort_row.iloc[0]
        summary["pooled"] = {
            "coef":  round(float(r["coef"]), 4),
            "se":    round(float(r["se"]),   4),
            "pval":  round(float(r["pval"]), 4),
            "stars": stars(float(r["pval"])),
        }

    for _, row in intervals.iterrows():
        summary["age_intervals"][row["age_bin"]] = {
            "coef":  round(float(row["coef"]), 4),
            "se":    round(float(row["se"]),   4),
            "pval":  round(float(row["pval"]), 4),
            "n":     int(row["n"]),
            "stars": stars(float(row["pval"])),
        }

    if by_cohort is not None:
        summary["by_cohort"] = {}
        for study in by_cohort["study"].unique():
            sub = by_cohort[by_cohort["study"] == study]
            summary["by_cohort"][study] = {}
            for _, row in sub.iterrows():
                summary["by_cohort"][study][row["age_bin"]] = {
                    "coef":  round(float(row["coef"]), 4),
                    "se":    round(float(row["se"]),   4),
                    "pval":  round(float(row["pval"]), 4),
                    "n":     int(row["n"]),
                    "stars": stars(float(row["pval"])),
                }

    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("  04_main_tables.py — build publication tables")
    print("=" * 70)

    pooled     = load_pooled()
    intervals  = load_intervals()
    by_cohort  = load_by_cohort()

    # ---- Table 1 ----
    t1 = make_table1(pooled)
    t1.to_csv(OUT_TAB / "04_table1_pooled.csv", index=False)
    t1_tex = df_to_latex(t1,
                         caption="Pooled OLS estimate of panel conditioning effect on mortality",
                         label="tab:pooled")
    (OUT_TAB / "04_table1_pooled.tex").write_text(t1_tex)
    print(f"\nTable 1 (pooled):")
    print(t1.to_string(index=False))

    # ---- Table 2 ----
    t2 = make_table2(intervals)
    t2.to_csv(OUT_TAB / "04_table2_age_intervals.csv", index=False)
    t2_tex = table2_latex(t2)
    (OUT_TAB / "04_table2_age_intervals.tex").write_text(t2_tex)
    print(f"\nTable 2 (age intervals):")
    print(t2.to_string(index=False))

    # ---- Table 3 ----
    t3 = make_table3(by_cohort)
    t3.to_csv(OUT_TAB / "04_table3_by_cohort.csv", index=False)
    print(f"\nTable 3 (by cohort):")
    print(t3.to_string(index=False))

    # ---- Results summary JSON ----
    summary = make_results_summary(pooled, intervals, by_cohort)
    summary_path = OUT_TAB / "04_results_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\nResults summary → {summary_path.name}")
    print(json.dumps(summary["pooled"], indent=2))

    print("\nDone.")
