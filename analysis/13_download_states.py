"""
13_download_states.py — Download school-level test results by race from state DOE sites.

Cross-state extension of Figure 12 (White-vs-Black / White-vs-Hispanic school scatters).
Each state has its own downloader; a failure in one state does not block others.

Files save under Data/raw/states/{st}/ (gitignored). See DATA.md for source notes.

States and sources
------------------
  CA  CAASPP Smarter Balanced research files (caaspp-elpac.ets.org).
      Statewide "All Student Groups" caret-delimited file + entities lookup, per year.
  TX  TEA TAPR Advanced Download (rptsvr1.tea.texas.gov CGI endpoint).
      Campus-level STAAR performance by race. STAAR1-3 = current year,
      STAAR4-6 = prior year within one TAPR vintage.
  IL  ISBE Report Card Public Data Set (single large .xlsx per year).
  NY  NYSED report card database SRC{year}.zip (Access .accdb inside;
      read downstream with access_parser).
  OH  Ohio DEW report card download files (building-level achievement by subgroup).
  GA  GOSA downloadable data (Georgia Milestones EOG by subgroup, school level).
  MA  DESE next-gen MCAS achievement results by subgroup (school level).
  NC  NC DPI accountability disaggregated performance data.

Run from repo root:
  python3 analysis/13_download_states.py --state CA
  python3 analysis/13_download_states.py            # all states
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = ROOT / "Data" / "raw" / "states"


def _curl(url: str, dest: Path, post_data: dict[str, str] | None = None) -> bool:
    """Download url -> dest with curl. Returns True on success. Skips if file exists."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  [skip] {dest.name} already exists ({dest.stat().st_size:,} bytes)")
        return True
    cmd = ["curl", "-fL", "--retry", "3", "--retry-delay", "3", "--max-time", "1800",
           "-o", str(dest), url]
    if post_data:
        for k, v in post_data.items():
            cmd.extend(["--data-urlencode", f"{k}={v}"])
    print(f"  Downloading {dest.name} ...")
    try:
        subprocess.run(cmd, check=True)
        print(f"    -> {dest.stat().st_size:,} bytes")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    FAILED: {e}", file=sys.stderr)
        if dest.exists():
            dest.unlink()
        return False


# ---------------------------------------------------------------- CA
CA_YEARS = [2023, 2024, 2025]  # test-administration years (2022-23 .. 2024-25)


def download_ca() -> bool:
    """CAASPP SB research files: all-student-groups results + entities, caret-delimited."""
    out = BASE_DIR / "ca"
    ok = True
    for y in CA_YEARS:
        # "csv" variant is caret-delimited with a header row; "ascii" is fixed-width.
        ok &= _curl(
            f"https://caaspp-elpac.ets.org/caaspp/researchfiles/sb_ca{y}_all_csv_v1.zip",
            out / f"sb_ca{y}_all_csv_v1.zip",
        )
        ok &= _curl(
            f"https://caaspp-elpac.ets.org/caaspp/researchfiles/sb_ca{y}entities_csv.zip",
            out / f"sb_ca{y}entities_csv.zip",
        )
    return ok


# ---------------------------------------------------------------- TX
TX_BROKER = "https://rptsvr1.tea.texas.gov/cgi/sas/broker"
# Each TAPR vintage carries ONE year of STAAR results, split into student-group
# blocks: STAAR1 = race/ethnicity + main groups, grades 3-8 RE/MA (what we need);
# STAAR4-6 = additional groups (foster, military, ...) for the same year.
# The 2025 vintage was not available through this CGI endpoint as of Jul 2026.
TX_VINTAGES = [2023, 2024]
TX_SETS = ["STAAR1"]


def download_tx() -> bool:
    """TEA TAPR advanced download, campus-level STAAR by student group (CSV)."""
    out = BASE_DIR / "tx"
    ok = True
    for ccyy in TX_VINTAGES:
        # form params changed with the 2024 TAPR redesign
        if ccyy >= 2024:
            post = {"prgopt": f"{ccyy}/tapr/Advanced Download/getdata_{ccyy}.sas",
                    "ccyy": str(ccyy)}
        else:
            post = {"prgopt": f"{ccyy}/tapr/tapr_download.sas",
                    "year4": str(ccyy), "year2": str(ccyy)[2:],
                    "topic": "acct", "title": "Data Download"}
        for setpick in TX_SETS:
            dest = out / f"tapr{ccyy}_campus_{setpick.lower()}.csv"
            got = _curl(
                TX_BROKER,
                dest,
                post_data={
                    "_service": "marykay",
                    "_program": "perfrept.perfmast.sas",
                    "_debug": "0",
                    "sumlev": "C",
                    "setpick": setpick,
                    **post,
                },
            )
            # Guard: broker returns an HTML error page (small) when a vintage is absent.
            if got and dest.exists() and dest.stat().st_size < 100_000:
                head = dest.read_bytes()[:500].lower()
                if b"<html" in head or b"error" in head:
                    print(f"    [warn] {dest.name} looks like an error page; removing")
                    dest.unlink()
                    got = False
            ok &= got
    return ok


# ---------------------------------------------------------------- IL
IL_FILES = {
    2023: "23-RC-Pub-Data-Set.xlsx",
    2024: "24-RC-Pub-Data-Set.xlsx",
    2025: "2025-Report-Card-Public-Data-Set.xlsx",
}


def download_il() -> bool:
    """ISBE Report Card Public Data Set (one wide multi-sheet xlsx per year)."""
    out = BASE_DIR / "il"
    ok = True
    for y, fname in IL_FILES.items():
        ok &= _curl(f"https://www.isbe.net/Documents/{fname}", out / f"rc{y}.xlsx")
    return ok


# ---------------------------------------------------------------- NY
NY_FILES = {
    2024: "https://data.nysed.gov/files/essa/23-24/SRC2024.zip",
    2025: "https://data.nysed.gov/files/essa/24-25/SRC2025.zip",
}


def download_ny() -> bool:
    """NYSED report card database (Access .accdb inside zip; ~350 MB each)."""
    out = BASE_DIR / "ny"
    ok = True
    for y, url in NY_FILES.items():
        ok &= _curl(url, out / f"SRC{y}.zip")
    return ok


# ---------------------------------------------------------------- OH
# Public SAS token embedded in the report-card SPA bundle (valid through 2031).
OH_SAS = ("sv=2020-08-04&ss=b&srt=sco&sp=rlx&se=2031-07-28T05:10:18Z"
          "&st=2021-07-27T21:10:18Z&spr=https&sig=nPOvW%2Br2caitHi%2F8WhYwU7xqalHo0dFrudeJq%2B%2Bmyuo%3D")
OH_FILES: dict[str, str] = {
    # Building-level results by race/ethnicity (Disaggregated School Data category)
    "building_ethnic_2223.xlsx": "https://reportcardstorage.education.ohio.gov/data-download-2023/BUILDING_ETHNIC_2223.xlsx",
    "building_ethnic_2324.xlsx": "https://reportcardstorage.education.ohio.gov/data-download-2024/BUILDING_ETHNIC_2324.xlsx",
    "building_ethnic_2425.xlsx": "https://eduprdreportcardstorage1.blob.core.windows.net/data-download-2025/BUILDING_ETHNIC_2425.xlsx",
}


def download_oh() -> bool:
    out = BASE_DIR / "oh"
    ok = True
    for fname, url in OH_FILES.items():
        ok &= _curl(f"{url}?{OH_SAS}", out / fname)
    return ok


# ---------------------------------------------------------------- GA
GA_FILES: dict[str, str] = {
    "eog_2023.csv": "https://download.gosa.ga.gov/2023/EOG_2022-23__GA_TST_AGGR_2023-12-15_18_54_21.csv",
    "eog_2024.csv": "https://download.gosa.ga.gov/2024/EOG_2023-24__GA_TST_AGGR_2025-01-14_16_19_30.csv",
    "eog_2025.csv": "https://download.gosa.ga.gov/2025/EOG_2024-25__GA_TST_AGGR_2026-02-19_00_31_27.csv",
}


def download_ga() -> bool:
    out = BASE_DIR / "ga"
    ok = True
    for fname, url in GA_FILES.items():
        ok &= _curl(url, out / fname)
    if not GA_FILES:
        print("  [GA] no verified URLs yet; see DATA.md for manual steps")
        return False
    return ok


# ---------------------------------------------------------------- NC
NC_YEARS = ["2022-23", "2023-24", "2024-25"]


def download_nc() -> bool:
    """NC DPI accountability disaggregated datasets (school-level, by subgroup)."""
    out = BASE_DIR / "nc"
    ok = True
    for y in NC_YEARS:
        ok &= _curl(
            f"https://accrpt.tops.ncsu.edu/docs/disag_datasets/Disag_{y}.zip",
            out / f"disag_{y}.zip",
        )
    return ok


# ---------------------------------------------------------------- NJ
NJ_YEARS = {"2223": "2022-23", "2324": "2023-24", "2425": "2024-25"}
NJ_GRADES = ["03", "04", "05", "06", "07", "08"]


def download_nj() -> bool:
    """NJ DOE NJSLA spring results, one xlsx per subject-grade (school rows by subgroup)."""
    out = BASE_DIR / "nj"
    base = "https://www.nj.gov/education/assessment/results/reports"
    ok = True
    for yy, span in NJ_YEARS.items():
        # 2024-25 filenames use spaces; earlier years use underscores.
        sep = "%20" if yy == "2425" else "_"
        for subj in ["ELA", "MAT"]:
            for g in NJ_GRADES:
                fname = f"{subj}{g}{sep}NJSLA{sep}DATA{sep}{span}.xlsx"
                ok &= _curl(f"{base}/{yy}/spring/{fname}",
                            out / f"{subj.lower()}{g}_{yy}.xlsx")
    return ok


STATES = {
    "CA": download_ca,
    "TX": download_tx,
    "IL": download_il,
    "NY": download_ny,
    "OH": download_oh,
    "GA": download_ga,
    "NC": download_nc,
    "NJ": download_nj,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Download state DOE school-by-race files.")
    parser.add_argument("--state", choices=sorted(STATES), help="Single state (default: all)")
    args = parser.parse_args()

    targets = [args.state] if args.state else sorted(STATES)
    results: dict[str, bool] = {}
    for st in targets:
        print(f"\n=== {st} ===")
        try:
            results[st] = STATES[st]()
        except Exception as e:  # keep going; per-state failure is acceptable
            print(f"  [{st}] unexpected failure: {e}", file=sys.stderr)
            results[st] = False

    print("\n" + "=" * 50)
    for st, ok in results.items():
        print(f"  {st}: {'OK' if ok else 'FAILED / incomplete'}")


if __name__ == "__main__":
    main()
