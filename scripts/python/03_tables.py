"""
Generate summary tables for the report (2019–2023 averages).

Table 1: Infant mortality rate and 95% CI by geography and race
Table 2: Detectability of rate reductions (17% and 32% benchmarks)
Table 3: Annual infant deaths, minimum detectable effect, and NFP spend

Inputs:  data/processed/*_infant_mortality_by_race.csv
Outputs: output/table1_rates.csv, output/table2_detectability.csv, output/table3_counts.csv
"""

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    CSV_FILES, DATA_DIR, OUTPUT_DIR, REPORT_PERIOD, GEOGRAPHIES, GEO_LABELS,
    NFP_COST_PER_LIFE_M, DENMARK_REDUCTION, KMC_REDUCTION,
    ci_95_poisson, min_detectable_deaths, ensure_dirs,
)


def load_period_averages() -> pd.DataFrame:
    """Compute 2019–2023 averages for each geography × race."""
    rows = []
    for geo in GEOGRAPHIES:
        df = pd.read_csv(DATA_DIR / CSV_FILES[geo])
        for col in ["rate_per_1000", "rate_lo", "rate_hi"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        period = df[(df["year"] >= REPORT_PERIOD[0]) &
                     (df["year"] <= REPORT_PERIOD[1])]

        for race in ["White", "Black"]:
            rdf = period[period["race"] == race]
            if rdf.empty:
                continue

            avg_births = rdf["births"].mean()
            avg_deaths = rdf["deaths"].mean()
            total_births = rdf["births"].sum()
            total_deaths = rdf["deaths"].sum()

            avg_rate = 1000.0 * total_deaths / total_births if total_births > 0 else 0
            rate_lo, rate_hi = ci_95_poisson(int(round(avg_deaths)), int(round(avg_births)))

            rows.append({
                "geography": GEO_LABELS[geo].replace("\n", " "),
                "race": race,
                "rate_per_1000": round(avg_rate, 2),
                "ci_lower": round(rate_lo, 1),
                "ci_upper": round(rate_hi, 1),
                "approx_annual_births": int(round(avg_births)),
                "approx_annual_deaths": int(round(avg_deaths)),
            })
    return pd.DataFrame(rows)


def build_table1(averages: pd.DataFrame) -> pd.DataFrame:
    """Table 1: rates and CIs."""
    t1 = averages[["geography", "race", "rate_per_1000",
                     "ci_lower", "ci_upper",
                     "approx_annual_births", "approx_annual_deaths"]].copy()
    t1["ci_95"] = t1.apply(lambda r: f"{r['ci_lower']}–{r['ci_upper']}", axis=1)
    return t1


def build_table2(averages: pd.DataFrame) -> pd.DataFrame:
    """Table 2: detectability of 17% and 32% rate reductions."""
    rows = []
    for _, r in averages.iterrows():
        rate = r["rate_per_1000"]
        lo = r["ci_lower"]
        margin = round(rate - lo, 2)
        red_17 = round(rate * DENMARK_REDUCTION, 2)
        red_32 = round(rate * KMC_REDUCTION, 2)
        det_17 = "Yes" if red_17 > margin else "No"
        det_32 = "Yes" if red_32 > margin else "No"

        rows.append({
            "geography": r["geography"],
            "race": r["race"],
            "avg_rate": rate,
            "ci_95": f"{lo}–{r['ci_upper']}",
            "margin_to_lower": margin,
            "reduction_17pct": red_17,
            "reduction_32pct": red_32,
            "detectable_17": det_17,
            "detectable_32": det_32,
        })
    return pd.DataFrame(rows)


def build_table3(averages: pd.DataFrame) -> pd.DataFrame:
    """Table 3: count-based detectability and NFP spend."""
    rows = []
    for _, r in averages.iterrows():
        deaths = r["approx_annual_deaths"]

        d_lo = deaths - 1.96 * math.sqrt(deaths) if deaths > 0 else 0
        d_hi = deaths + 1.96 * math.sqrt(deaths) if deaths > 0 else 0
        ci_deaths = f"{max(0, int(round(d_lo)))}–{int(round(d_hi))}"

        min_averted = min_detectable_deaths(deaths)
        nfp_spend = round(min_averted * NFP_COST_PER_LIFE_M)

        rows.append({
            "geography": r["geography"],
            "race": r["race"],
            "approx_annual_deaths": deaths,
            "ci_95_deaths": ci_deaths,
            "min_deaths_averted": min_averted,
            "est_spend_nfp_M": nfp_spend,
        })
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    averages = load_period_averages()

    t1 = build_table1(averages)
    t1_path = OUTPUT_DIR / "table1_rates.csv"
    t1.to_csv(t1_path, index=False)

    t2 = build_table2(averages)
    t2_path = OUTPUT_DIR / "table2_detectability.csv"
    t2.to_csv(t2_path, index=False)

    t3 = build_table3(averages)
    t3_path = OUTPUT_DIR / "table3_counts.csv"
    t3.to_csv(t3_path, index=False)

    print(f"Tables saved → {t1_path}, {t2_path}, {t3_path}")


if __name__ == "__main__":
    main()
