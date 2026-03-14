"""
Generate publication-ready infant mortality rate figures by race for all geographies.

Produces 4 PNG figures (300 DPI) in Figures/:
  - state_infant_mortality_by_race.png
  - milwaukee_infant_mortality_by_race.png
  - dane_infant_mortality_by_race.png
  - rest_of_wisconsin_infant_mortality_by_race.png

Inputs:  data/processed/*_infant_mortality_by_race.csv
Outputs: Figures/*.png
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    CSV_FILES, DATA_DIR, FIGURE_DIR, FIGURE_DPI, FIGURE_SIZE,
    GEO_LABELS, GEOGRAPHIES, RACE_COLORS, TITLE_CI_SUFFIX, ensure_dirs,
)


def plot_geo(geo: str) -> Path:
    """Generate rate-by-race figure for one geography. Returns output path."""
    df = pd.read_csv(DATA_DIR / CSV_FILES[geo])
    for col in ["rate_per_1000", "rate_lo", "rate_hi"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    label = GEO_LABELS[geo]
    years = sorted(df["year"].unique())

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    for race in ("White", "Black"):
        rdf = df[df["race"] == race].dropna(subset=["rate_per_1000"]).sort_values("year")
        if rdf.empty:
            continue
        color = RACE_COLORS[race]
        ax.plot(rdf["year"], rdf["rate_per_1000"], "o-",
                label=race, color=color, markersize=5)
        ax.fill_between(rdf["year"], rdf["rate_lo"], rdf["rate_hi"],
                        color=color, alpha=0.25)

    ax.set_xlabel("Year")
    ax.set_ylabel("Infant mortality rate (per 1,000 live births)")
    ax.set_title(f"{label} infant mortality rate by race{TITLE_CI_SUFFIX}")
    ax.legend()
    ax.grid(True, alpha=0.25)
    ax.set_xlim(min(years) - 0.5, max(years) + 0.5)

    fig.tight_layout()
    out_path = FIGURE_DIR / f"{geo}_infant_mortality_by_race.png"
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> None:
    ensure_dirs()
    for geo in GEOGRAPHIES:
        csv_path = DATA_DIR / CSV_FILES[geo]
        if not csv_path.exists():
            print(f"SKIP {geo}: {csv_path} not found")
            continue
        plot_geo(geo)

    print(f"Figures saved to {FIGURE_DIR}")


if __name__ == "__main__":
    main()
