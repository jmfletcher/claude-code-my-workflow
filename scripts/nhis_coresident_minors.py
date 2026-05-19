"""Build roster-derived co-resident minor counts from the IPUMS NHIS fixed-width
extract (nhis_00002.dat, 1986-2018) and save a tidy parquet for downstream
survey-weighted mortality regressions.

Mirrors scripts/nhis_coresident_minors.do but uses pandas + pyarrow.

Outputs (project root):
    nhis_with_coresident_minors.parquet     analytic frame keyed on year+serial+pernum

Caveats:
    - RELATE is to the householder, NOT to each adult; household-level
      attribution of minors to non-parent adults is noisy.
    - Co-residence != completed parity; nonresident minors invisible.
    - Pre-1997 NHIS does not have a usable FMX in this extract, so family-unit
      counts fall back to household-level counts in those years.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


def _colspecs() -> tuple[list[tuple[int, int]], list[str], dict[str, str]]:
    """Column specs derived from nhis_00002.do (1-indexed Stata ranges).

    Returns
    -------
    colspecs : list of (start, end) 0-indexed half-open intervals
    names    : column names in order
    dtypes   : pandas dtype hint per column
    """
    spec_table = [
        # (name, start_stata, end_stata, dtype, scale)
        ("year",       1,   4,   "int32",   None),
        ("serial",     5,   10,  "int64",   None),
        ("numprec",    11,  13,  "Int16",   None),
        ("strata",     14,  17,  "Int32",   None),
        ("psu",        18,  20,  "Int16",   None),
        ("nhishid",    21,  34,  "string",  None),
        ("hhweight",   35,  40,  "Int32",   None),
        ("region",     41,  42,  "Int8",    None),
        ("pernum",     43,  44,  "Int16",   None),
        ("nhispid",    45,  60,  "string",  None),
        ("hhx",        61,  67,  "string",  None),
        ("fmx",        68,  69,  "string",  None),
        ("px",         70,  71,  "string",  None),
        ("perweight",  72,  83,  "float64", None),
        ("sampweight", 84,  95,  "float64", 1_000.0),
        ("fweight",    96,  107, "float64", 1_000_000.0),
        ("supp3wt",    108, 116, "float64", None),
        ("intervwmo",  117, 118, "Int8",    None),
        ("intervwyr",  119, 122, "Int16",   None),
        ("astatflg",   123, 123, "Int8",    None),
        ("cstatflg",   124, 124, "Int8",    None),
        ("screspond",  125, 126, "Int8",    None),
        ("respond",    127, 128, "Int8",    None),
        ("age",        129, 131, "Int16",   None),
        ("sex",        132, 132, "Int8",    None),
        ("sexorien",   133, 133, "Int8",    None),
        ("marstcur",   134, 134, "Int8",    None),
        ("marstat",    135, 136, "Int8",    None),
        ("marst",      137, 138, "Int8",    None),
        ("marstcohab", 139, 139, "Int8",    None),
        ("cohabmarst", 140, 140, "Int8",    None),
        ("cohabevmar", 141, 141, "Int8",    None),
        ("birthmo",    142, 143, "Int8",    None),
        ("birthyr",    144, 147, "Int16",   None),
        ("relate",     148, 149, "Int8",    None),
        ("racenew",    150, 152, "Int16",   None),
        ("racea",      153, 155, "Int16",   None),
        ("hispeth",    156, 157, "Int8",    None),
        ("racesr",     158, 160, "Int16",   None),
        ("educrec2",   161, 162, "Int8",    None),
        ("educrec1",   163, 164, "Int8",    None),
        ("mortelig",   165, 165, "Int8",    None),
        ("mortstat",   166, 166, "Int8",    None),
        ("mortdodq",   167, 167, "Int8",    None),
        ("mortdody",   168, 171, "Int16",   None),
        ("mortucodld", 172, 173, "Int8",    None),
        ("mortwt",     174, 181, "float64", None),
        ("mortwtsa",   182, 189, "float64", None),
    ]
    colspecs = [(s - 1, e) for (_, s, e, _, _) in spec_table]
    names    = [n for (n, _, _, _, _) in spec_table]
    dtypes   = {n: d for (n, _, _, d, _) in spec_table}
    scales   = {n: s for (n, _, _, _, s) in spec_table if s is not None}
    return colspecs, names, dtypes, scales


def load_nhis(dat_path: Path, chunksize: int | None = 500_000) -> pd.DataFrame:
    """Load the rectangular .dat file into a DataFrame with right-sized dtypes."""
    colspecs, names, dtypes, scales = _colspecs()
    str_cols = [n for n, d in dtypes.items() if d == "string"]
    int_cols = [n for n, d in dtypes.items() if d not in ("string", "float64")]

    # Read everything as string first (robust to embedded blanks in narrow
    # numeric fields like astatflg, then coerce per dtype).
    reader = pd.read_fwf(
        dat_path,
        colspecs=colspecs,
        names=names,
        dtype="string",
        header=None,
        chunksize=chunksize,
    )

    pieces: list[pd.DataFrame] = []
    n_chunks = 0
    t0 = time.time()
    for chunk in reader:
        n_chunks += 1
        for c in int_cols:
            chunk[c] = pd.to_numeric(chunk[c], errors="coerce").astype(dtypes[c])
        for c in names:
            if dtypes[c] == "float64":
                chunk[c] = pd.to_numeric(chunk[c], errors="coerce")
        pieces.append(chunk)
        if n_chunks % 2 == 0:
            elapsed = time.time() - t0
            print(f"  ...read {sum(len(p) for p in pieces):,} rows ({elapsed:.1f}s)",
                  flush=True)

    df = pd.concat(pieces, ignore_index=True)
    for c in str_cols:
        df[c] = df[c].fillna("").str.strip()

    # Stata weight scaling
    for c, s in scales.items():
        df[c] = df[c] / s

    return df


def build_minor_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Roster-level minor flags and household / family-level aggregates."""

    # Roster: minor child of householder / partner (NHIS RELATE 40 / 41 / 43 / 44)
    age_ok    = df["age"].between(0, 17, inclusive="both")
    rel_kid   = df["relate"].isin([40, 41, 43, 44])
    df["hh_childminor"] = (age_ok & rel_kid).astype("int8")

    # Household totals
    df["n_hh_childminor017"] = (
        df.groupby(["year", "serial"], sort=False)["hh_childminor"]
          .transform("sum")
          .astype("int16")
    )

    # Family totals from FMX (1997+ only); fall back to household total
    fmx_clean = df["fmx"].str.strip()
    fmx_num   = pd.to_numeric(fmx_clean, errors="coerce")
    df["fmxn"] = fmx_num.where(df["year"] >= 1997)

    fam_ok = df["fmxn"].notna()
    fam_sum = (
        df.loc[fam_ok]
          .groupby(["year", "serial", "fmxn"], sort=False)["hh_childminor"]
          .transform("sum")
    )
    df["n_fam_childminor017"] = df["n_hh_childminor017"].astype("float64")
    df.loc[fam_ok, "n_fam_childminor017"] = fam_sum.astype("float64")
    df["n_fam_childminor017"] = df["n_fam_childminor017"].astype("int16")

    # Age summaries among co-resident minors only
    age_if_minor = df["age"].where(df["hh_childminor"] == 1).astype("float64")
    grp = age_if_minor.groupby([df["year"], df["serial"]], sort=False)
    df["hh_min_child_age"]  = grp.transform("min").astype("float32")
    df["hh_max_child_age"]  = grp.transform("max").astype("float32")
    df["hh_mean_child_age"] = grp.transform("mean").astype("float32")

    # Adult / parent-role flags
    df["adult_agerestr"] = ((df["age"] >= 18) & (df["age"] < 997)).astype("int8")
    df["parentrole_hh"]  = df["relate"].isin([10, 20, 21, 22, 30]).astype("int8")

    return df


def main() -> int:
    proj_root = Path(__file__).resolve().parent.parent
    dat_path  = proj_root / "nhis_00002.dat"
    out_path  = proj_root / "nhis_with_coresident_minors.parquet"

    if not dat_path.exists():
        print(f"ERROR: cannot find {dat_path}", file=sys.stderr)
        return 2

    print(f"Loading {dat_path.name} ...", flush=True)
    t0 = time.time()
    df = load_nhis(dat_path)
    print(f"Loaded {len(df):,} rows in {time.time() - t0:.1f}s", flush=True)

    print("Building minor aggregates ...", flush=True)
    df = build_minor_aggregates(df)

    print(f"Writing {out_path.name} ...", flush=True)
    df.to_parquet(out_path, engine="pyarrow", index=False, compression="zstd")

    print("Done. Merge keys: year, serial, pernum, nhispid", flush=True)
    print("Quick check: weighted death count by mortelig", flush=True)
    elig = df.loc[df["mortelig"] == 1]
    summary = (
        elig.groupby("mortstat")["mortwt"].sum().rename("weighted_n")
            .to_frame()
    )
    print(summary, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
