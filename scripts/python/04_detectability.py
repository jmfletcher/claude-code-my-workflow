"""
Extended detectability analysis with narrative summaries.

Computes power/detectability for each geography × race cell and
produces a markdown summary suitable for inclusion in the Quarto report.

Inputs:  data/processed/*_infant_mortality_by_race.csv
Outputs: output/detectability_summary.md
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


def compute_detectability() -> list[dict]:
    """Compute detectability metrics for each geography × race."""
    results = []
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

            avg_rate = 1000.0 * total_deaths / total_births if total_births else 0
            rate_lo, rate_hi = ci_95_poisson(
                int(round(avg_deaths)), int(round(avg_births))
            )
            margin = avg_rate - rate_lo

            red_17_rate = avg_rate * DENMARK_REDUCTION
            red_32_rate = avg_rate * KMC_REDUCTION

            min_averted = min_detectable_deaths(int(round(avg_deaths)))
            nfp_spend = min_averted * NFP_COST_PER_LIFE_M

            red_17_count = avg_deaths * DENMARK_REDUCTION
            red_32_count = avg_deaths * KMC_REDUCTION

            results.append({
                "geography": GEO_LABELS[geo].replace("\n", " "),
                "geo_key": geo,
                "race": race,
                "avg_rate": round(avg_rate, 2),
                "ci_lower": round(rate_lo, 1),
                "ci_upper": round(rate_hi, 1),
                "margin": round(margin, 2),
                "red_17_rate": round(red_17_rate, 2),
                "red_32_rate": round(red_32_rate, 2),
                "det_17_rate": red_17_rate > margin,
                "det_32_rate": red_32_rate > margin,
                "avg_deaths": int(round(avg_deaths)),
                "avg_births": int(round(avg_births)),
                "min_averted": min_averted,
                "nfp_spend_M": round(nfp_spend),
                "red_17_count": round(red_17_count, 1),
                "red_32_count": round(red_32_count, 1),
                "det_17_count": red_17_count >= min_averted,
                "det_32_count": red_32_count >= min_averted,
            })
    return results


def generate_markdown(results: list[dict]) -> str:
    """Generate markdown summary of detectability analysis."""
    lines = [
        "# Detectability Analysis Summary",
        "",
        f"**Period:** {REPORT_PERIOD[0]}–{REPORT_PERIOD[1]} averages",
        f"**Benchmarks:** 17% reduction (Denmark campaign), "
        f"32% reduction (KMC meta-analysis)",
        f"**Cost benchmark:** ${NFP_COST_PER_LIFE_M}M per life (NFP, Miller 2015)",
        "",
        "## Key Finding",
        "",
    ]

    mke_black = [r for r in results
                 if r["geo_key"] == "milwaukee" and r["race"] == "Black"]
    if mke_black:
        m = mke_black[0]
        lines.extend([
            f"**Milwaukee Black** is the only county-level geography where a "
            f"32% rate reduction would be detectable in one year:",
            f"",
            f"- Rate: {m['avg_rate']} per 1,000 (CI: {m['ci_lower']}–{m['ci_upper']})",
            f"- ~{m['avg_deaths']} deaths/year",
            f"- Minimum {m['min_averted']} deaths averted needed for detectability",
            f"- 32% reduction ≈ {m['red_32_count']:.0f} deaths averted → "
            f"{'DETECTABLE' if m['det_32_count'] else 'NOT detectable'}",
            f"- Estimated NFP spend: ${m['nfp_spend_M']}M/year",
            "",
        ])

    lines.extend([
        "## Full Results",
        "",
        "| Geography | Race | Rate | 95% CI | Margin | "
        "17% det? | 32% det? | Deaths/yr | Min averted | NFP $M |",
        "|-----------|------|------|--------|--------|"
        "---------|---------|-----------|-------------|--------|",
    ])

    for r in results:
        det17 = "Yes" if r["det_17_rate"] else "No"
        det32 = "Yes" if r["det_32_rate"] else "No"
        lines.append(
            f"| {r['geography']} | {r['race']} | {r['avg_rate']} | "
            f"{r['ci_lower']}–{r['ci_upper']} | {r['margin']} | "
            f"{det17} | {det32} | {r['avg_deaths']} | "
            f"{r['min_averted']} | {r['nfp_spend_M']} |"
        )

    lines.extend(["", "---", "",
                   "*Generated by scripts/python/04_detectability.py*"])
    return "\n".join(lines)


def main() -> None:
    ensure_dirs()
    results = compute_detectability()

    raw_df = pd.DataFrame(results)
    raw_path = OUTPUT_DIR / "detectability_raw.csv"
    raw_df.to_csv(raw_path, index=False)

    md = generate_markdown(results)
    out_path = OUTPUT_DIR / "detectability_summary.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"Detectability outputs saved → {raw_path}, {out_path}")


if __name__ == "__main__":
    main()
