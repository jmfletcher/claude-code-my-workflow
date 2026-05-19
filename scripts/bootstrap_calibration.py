"""Cluster-bootstrap the NHIS-derived kappa_c calibration factors.

Resamples NHIS primary sampling units (PSUs) with replacement within strata,
producing B replicate kappa tables. Each replicate's kappa is then plugged
into the kinship engine and applied across all race groups + the pooled
"All" run; we collect prevalent orphan counts per year per race and report
the 2.5 / 50 / 97.5 percentile across replicates.

Outputs
    results/py/kappa_bootstrap/by_cell_b{NNN}.csv    -- B kappa CSVs
    results/py/kappa_bootstrap/singleyear_b{NNN}.csv -- B single-year tables
    results/kinship/calibrated_villaveces/bootstrap_summary.csv
        -- one row per (race_eth, focal_year) with baseline, calibrated
        point estimate, and 2.5/50/97.5 bootstrap percentiles of the
        calibrated count.

Speed
    Uses a cluster-level sufficient-statistic precomputation so each
    bootstrap pass is O(num_clusters x num_cells) rather than O(rows).
    B=200 takes about 90 seconds for kappa, then ~3 s per race per
    bootstrap for the engine, for ~6 races * 200 = ~60 minutes worst case.
    Engine runs reuse the same Rates structure; only the kappa array
    changes per replicate. Use --B 50 for a smoke test (~10 minutes).

Usage
    python scripts/bootstrap_calibration.py --B 200 --seed 7
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pykin import AGES
from pykin.calibrate import RACETH5_TO_KIN
from pykin.engine import rates_to_arrays
from pykin.ingest import load_cache
from pykin.orphanhood import annual_summaries, parental_loss_grid_cached
from scripts.export_nhis_calibration import (
    AGE_BANDS,
    RACETH5_LABEL,
    build_cells,
)


PARQUET = PROJECT_ROOT / "nhis_with_coresident_minors.parquet"
BOOT_DIR = PROJECT_ROOT / "results" / "py" / "kappa_bootstrap"
SUMMARY_PATH = (PROJECT_ROOT / "results" / "kinship"
                / "calibrated_villaveces" / "bootstrap_summary.csv")

DECADE_TO_YEARS = {
    1: list(range(1986, 1990)),
    2: list(range(1990, 2000)),
    3: list(range(2000, 2010)),
    4: list(range(2010, 2019)),
}
BAND_TO_AGES = {f"{lo}-{hi}": list(range(lo, hi + 1)) for (lo, hi) in AGE_BANDS}


# ---------------------------------------------------------------------------
# Sufficient statistics per (cluster, cell, died)
# ---------------------------------------------------------------------------

def build_cluster_stats(df: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    """Pre-aggregate cluster-level sufficient stats for fast bootstrap.

    df  -- analytic frame from build_cells (has died, nk_under18, mortwtsa,
           cells), but missing strata / psu.
    raw -- the original parquet with strata, psu, nhispid, mortwtsa.

    We assume rows in `df` are a subset of rows in `raw` and use a
    deterministic merge on the row index (build_cells preserves index).
    Returns DataFrame indexed by (cluster_id, sex, raceth5, age_band,
    yeardec, died) with sum_w_nk and sum_w columns.
    """
    # Attach strata, psu to df via index
    df = df.copy()
    df["strata"] = raw.loc[df.index, "strata"].astype("Int32").to_numpy()
    df["psu"]    = raw.loc[df.index, "psu"].astype("Int32").to_numpy()
    df = df.dropna(subset=["strata", "psu"]).copy()
    df["cluster_id"] = (df["strata"].astype(int).astype(str) + "_"
                        + df["psu"].astype(int).astype(str))

    df["w_nk"] = df["mortwtsa"] * df["nk_under18"]
    df["n"] = 1.0
    stats = (df.groupby(["cluster_id", "strata", "sex", "raceth5",
                         "age_band", "yeardec", "died"], observed=True)
               .agg(sum_w_nk=("w_nk", "sum"),
                    sum_w=("mortwtsa", "sum"),
                    n_unw=("n", "sum"))
               .reset_index())
    return stats


def list_clusters_by_stratum(stats: pd.DataFrame) -> dict[int, np.ndarray]:
    """Return {stratum: array of cluster_ids} for the bootstrap."""
    sub = stats[["strata", "cluster_id"]].drop_duplicates()
    return {int(s): g["cluster_id"].to_numpy()
            for s, g in sub.groupby("strata", observed=True)}


# ---------------------------------------------------------------------------
# One bootstrap replicate: cluster multiplicities -> kappa CSVs
# ---------------------------------------------------------------------------

def cell_means_from_stats(stats: pd.DataFrame,
                          mult: pd.Series | None = None) -> pd.DataFrame:
    """Aggregate cluster-level sufficient stats to cell-level kappa.

    If mult is not None, it should be a Series indexed by cluster_id giving
    the bootstrap multiplicity (the number of times each cluster appears in
    the resample). When None, returns the original point estimate.
    """
    if mult is None:
        s = stats.copy()
    else:
        s = stats.merge(mult.rename("m"), left_on="cluster_id",
                        right_index=True, how="left")
        s["m"] = s["m"].fillna(0.0)
        s = s.assign(sum_w_nk=lambda d: d["sum_w_nk"] * d["m"],
                     sum_w   =lambda d: d["sum_w"]    * d["m"],
                     n_unw   =lambda d: d["n_unw"]    * d["m"])

    cell = (s.groupby(["sex", "raceth5", "age_band", "yeardec", "died"],
                       observed=True)
              .agg(sum_w_nk=("sum_w_nk", "sum"),
                   sum_w=("sum_w", "sum"),
                   n_unw=("n_unw", "sum"))
              .reset_index())
    cell["mean_nk"] = np.where(cell["sum_w"] > 0,
                                cell["sum_w_nk"] / cell["sum_w"], np.nan)
    wide = cell.pivot_table(index=["sex", "raceth5", "age_band", "yeardec"],
                             columns="died",
                             values=["sum_w", "sum_w_nk", "mean_nk", "n_unw"])
    wide.columns = [f"{a}_{int(b)}" for a, b in wide.columns]
    wide = wide.reset_index()

    wide["kappa"] = np.where((wide.get("mean_nk_0", np.nan) > 0),
                              wide["mean_nk_1"] / wide["mean_nk_0"], np.nan)
    return wide


def smooth_kappa_b(cell_df: pd.DataFrame, min_dead_unw: int = 25) -> pd.DataFrame:
    """Pool sparse cells toward the (sex, raceth5, decade) mean.

    The sparseness test uses unweighted death-row count (n_unw_1) and the
    same threshold as scripts/export_nhis_calibration.py so the bootstrap's
    point estimate matches the canonical kappa table.
    """
    out = cell_df.copy()
    out["kappa_smooth"] = out["kappa"]
    grp = (out.assign(num=out["kappa"] * out["sum_w_1"])
              .groupby(["sex", "raceth5", "yeardec"], observed=True)
              .agg(num=("num", "sum"), den=("sum_w_1", "sum"))
              .reset_index())
    grp["kappa_pool"] = np.where(grp["den"] > 0, grp["num"] / grp["den"], 1.0)
    out = out.merge(grp[["sex", "raceth5", "yeardec", "kappa_pool"]],
                    on=["sex", "raceth5", "yeardec"], how="left")
    sparse = out["n_unw_1"].fillna(0) < min_dead_unw
    out.loc[sparse, "kappa_smooth"] = out.loc[sparse, "kappa_pool"]
    out["kappa_smooth"] = out["kappa_smooth"].fillna(out["kappa_pool"]).fillna(1.0)
    return out


def expand_singleyear_b(cells: pd.DataFrame) -> pd.DataFrame:
    """Project (sex, raceth5, age_band, yeardec) -> (sex, raceth5, age, year)."""
    rows = []
    for _, r in cells.iterrows():
        if r["age_band"] not in BAND_TO_AGES or r["yeardec"] not in DECADE_TO_YEARS:
            continue
        for age in BAND_TO_AGES[r["age_band"]]:
            for year in DECADE_TO_YEARS[r["yeardec"]]:
                rows.append({
                    "sex": r["sex"],
                    "raceth5": int(r["raceth5"]),
                    "age": age,
                    "year": year,
                    "kappa": float(r["kappa_smooth"]),
                })
    df = pd.DataFrame(rows)

    # Pad to 1983-2021
    out_rows = []
    for (sex, raceth5, age), g in df.groupby(["sex", "raceth5", "age"], observed=True):
        g = g.sort_values("year")
        first_kappa = g["kappa"].iloc[0]
        first_year  = int(g["year"].min())
        for y in range(1983, first_year):
            out_rows.append({"sex": sex, "raceth5": int(raceth5),
                             "age": int(age), "year": y, "kappa": first_kappa})
        out_rows.extend(g.to_dict("records"))
        last_kappa = g["kappa"].iloc[-1]
        last_year  = int(g["year"].max())
        for y in range(last_year + 1, 2022):
            out_rows.append({"sex": sex, "raceth5": int(raceth5),
                             "age": int(age), "year": y, "kappa": last_kappa})
    return pd.DataFrame(out_rows)


# ---------------------------------------------------------------------------
# Kappa array (sex -> (ages, years)) from single-year table, picking either
# "All" pooled or a specific race_eth label
# ---------------------------------------------------------------------------

def kappa_array_from(single: pd.DataFrame, *, race_eth: str,
                     years: range, ages: int) -> dict[str, np.ndarray]:
    """Like pykin.calibrate.kappa_array_for, but consumes an in-memory
    bootstrap single-year DataFrame (skips disk IO).
    """
    yrs = np.array(list(years), dtype=int)
    n = ages

    sub = single[(single["year"].isin(yrs)) & (single["age"] < n)].copy()
    if race_eth == "All":
        sub_grp = (sub.groupby(["sex", "age", "year"], as_index=False)["kappa"]
                      .mean())
    else:
        target = None
        for raceth5_id, lbl in RACETH5_TO_KIN.items():
            if lbl == race_eth:
                target = raceth5_id
                break
        if target is None:
            raise ValueError(f"race_eth {race_eth!r} not in RACETH5 map")
        sub_grp = sub[sub["raceth5"] == target]

    out = {}
    for sex in ("f", "m"):
        arr = np.ones((n, yrs.size))
        s = sub_grp[sub_grp["sex"] == sex]
        if not s.empty:
            ages_arr = s["age"].to_numpy(int)
            year_idx = np.searchsorted(yrs, s["year"].to_numpy(int))
            mask = (year_idx >= 0) & (year_idx < yrs.size)
            arr[ages_arr[mask], year_idx[mask]] = s["kappa"].to_numpy()[mask]
        out[sex] = arr
    return out


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def main(B: int, seed: int, races: list[str]) -> None:
    BOOT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[boot] loading NHIS parquet ...")
    raw = pd.read_parquet(PARQUET)
    df = build_cells(raw)
    print(f"[boot] analytic rows: {len(df):,}")

    print(f"[boot] building cluster-level sufficient stats ...")
    stats = build_cluster_stats(df, raw)
    clusters_by_stratum = list_clusters_by_stratum(stats)
    n_strata = len(clusters_by_stratum)
    n_clusters = sum(len(v) for v in clusters_by_stratum.values())
    print(f"[boot]   strata={n_strata}  clusters={n_clusters}")

    print(f"[boot] loading kinship caches and engine rates ...")
    pop, mort, fert = load_cache()
    rates_by_race: dict[str, object] = {}
    for r in races:
        rates_by_race[r] = rates_to_arrays(pop, mort, fert,
                                            race_eth=r,
                                            years=range(1983, 2022),
                                            ages=AGES)

    # Baseline + point-estimate calibrated runs (b = -1 for the point)
    rng = np.random.default_rng(seed)

    # Pre-compute baseline grids per race (no kappa).
    print(f"[boot] computing baselines ...")
    baseline_summaries: dict[str, pd.DataFrame] = {}
    for r in races:
        g = parental_loss_grid_cached(rates_by_race[r],
                                       year_min=2000, year_max=2021,
                                       max_focal_age=17)
        baseline_summaries[r] = annual_summaries(g, pop, race_eth=r)

    # Build the point-estimate kappa from stats (no resampling)
    print(f"[boot] computing point-estimate kappa ...")
    cells0 = cell_means_from_stats(stats)
    cells0_sm = smooth_kappa_b(cells0)
    single0 = expand_singleyear_b(cells0_sm)
    point_summaries: dict[str, pd.DataFrame] = {}
    for r in races:
        k = kappa_array_from(single0, race_eth=r, years=range(1983, 2022),
                              ages=AGES)
        g = parental_loss_grid_cached(rates_by_race[r],
                                       year_min=2000, year_max=2021,
                                       max_focal_age=17,
                                       kappa_f=k["f"], kappa_m=k["m"],
                                       kappa_years=np.arange(1983, 2022))
        point_summaries[r] = annual_summaries(g, pop, race_eth=r)

    # Bootstrap loop
    print(f"[boot] running B={B} bootstrap replicates ...")
    bootstrap_records: list[dict] = []   # one row per (b, race, focal_year)
    cluster_ids_per_stratum = {s: np.asarray(v)
                                for s, v in clusters_by_stratum.items()}

    for b in range(B):
        # Cluster multiplicities by stratum (sample with replacement, fixed
        # number per stratum).
        mult = {}
        for s, cs in cluster_ids_per_stratum.items():
            sampled = rng.choice(cs, size=len(cs), replace=True)
            uniq, counts = np.unique(sampled, return_counts=True)
            for u, c in zip(uniq, counts):
                mult[u] = mult.get(u, 0) + int(c)
        mult_series = pd.Series(mult, dtype=float)

        cells_b = cell_means_from_stats(stats, mult=mult_series)
        cells_b_sm = smooth_kappa_b(cells_b)
        single_b = expand_singleyear_b(cells_b_sm)

        for r in races:
            k = kappa_array_from(single_b, race_eth=r,
                                  years=range(1983, 2022), ages=AGES)
            g = parental_loss_grid_cached(rates_by_race[r],
                                           year_min=2000, year_max=2021,
                                           max_focal_age=17,
                                           kappa_f=k["f"], kappa_m=k["m"],
                                           kappa_years=np.arange(1983, 2022))
            s_b = annual_summaries(g, pop, race_eth=r)
            for _, row in s_b.iterrows():
                bootstrap_records.append({
                    "b": b,
                    "race_eth": r,
                    "focal_year": int(row["focal_year"]),
                    "prevalent": float(row["prevalent"]),
                    "incident": float(row["incident"])
                                if pd.notna(row["incident"]) else np.nan,
                })

        if (b + 1) % 10 == 0:
            print(f"[boot]   {b+1}/{B} done")

    bdf = pd.DataFrame(bootstrap_records)

    # Aggregate: 2.5 / 50 / 97.5 percentiles per (race, focal_year)
    print(f"[boot] aggregating ...")
    agg = (bdf.groupby(["race_eth", "focal_year"], as_index=False)["prevalent"]
              .agg(lo=lambda s: float(np.percentile(s, 2.5)),
                   med=lambda s: float(np.percentile(s, 50.0)),
                   hi=lambda s: float(np.percentile(s, 97.5)),
                   B=("count")))

    # Add baseline (no calibration) and point-estimate calibrated
    base_rows = pd.concat([d[["focal_year", "prevalent"]].assign(race_eth=r)
                            for r, d in baseline_summaries.items()],
                           ignore_index=True).rename(columns={"prevalent": "baseline"})
    point_rows = pd.concat([d[["focal_year", "prevalent"]].assign(race_eth=r)
                             for r, d in point_summaries.items()],
                            ignore_index=True).rename(columns={"prevalent": "calibrated_point"})
    summary = (base_rows.merge(point_rows, on=["race_eth", "focal_year"])
                        .merge(agg, on=["race_eth", "focal_year"]))
    summary["delta_point_abs"] = summary["calibrated_point"] - summary["baseline"]
    summary["delta_point_pct"] = 100.0 * summary["delta_point_abs"] / summary["baseline"]
    summary["delta_lo_pct"] = 100.0 * (summary["lo"] - summary["baseline"]) / summary["baseline"]
    summary["delta_hi_pct"] = 100.0 * (summary["hi"] - summary["baseline"]) / summary["baseline"]
    summary = summary[[
        "race_eth", "focal_year", "B",
        "baseline", "calibrated_point", "med", "lo", "hi",
        "delta_point_pct", "delta_lo_pct", "delta_hi_pct",
    ]]

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_PATH, index=False)
    print(f"[boot] wrote {SUMMARY_PATH.relative_to(PROJECT_ROOT)}")

    # Print headline rows (2021)
    head = summary[summary["focal_year"] == 2021].copy()
    print()
    print("=== 2021 bootstrap summary ===")
    cols = ["race_eth", "baseline", "calibrated_point",
            "lo", "hi", "delta_point_pct", "delta_lo_pct", "delta_hi_pct"]
    print(head[cols].to_string(index=False, formatters={
        "baseline":         "{:>13,.0f}".format,
        "calibrated_point": "{:>13,.0f}".format,
        "lo":               "{:>13,.0f}".format,
        "hi":               "{:>13,.0f}".format,
        "delta_point_pct":  "{:>+7.1f}".format,
        "delta_lo_pct":     "{:>+7.1f}".format,
        "delta_hi_pct":     "{:>+7.1f}".format,
    }))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--races", nargs="*", default=[
        "All",
        "Non-Hispanic White",
        "Non-Hispanic Black",
        "Hispanic",
        "Non-Hispanic Asian or Pacific Islander",
        "Non-Hispanic American Indian or Alaska Native",
    ])
    args = ap.parse_args()
    main(B=args.B, seed=args.seed, races=args.races)
