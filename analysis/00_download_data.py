"""
Download Wisconsin DPI assessment data files.

Forward Exam (2015-16 to 2024-25): school-level proficiency by race, grades 3-8.
WKCE / WINSS (2003-04 to 2013-14): pre-Forward historical data (different test).

Run from repo root:
    python3 analysis/00_download_data.py

Downloads go to Data/raw/forward/ and Data/raw/wkce/ (gitignored).
After download, inspect with:
    python3 analysis/01_inspect_data.py
"""

import sys
import time
import zipfile
from pathlib import Path

try:
    import requests
    _USE_REQUESTS = True
except ImportError:
    _USE_REQUESTS = False
    import ssl
    from urllib.request import urlretrieve, urlopen, Request
    from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# Repo root and output dirs
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
FORWARD_DIR = ROOT / "Data" / "raw" / "forward"
WKCE_DIR = ROOT / "Data" / "raw" / "wkce"
FORWARD_DIR.mkdir(parents=True, exist_ok=True)
WKCE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Assessment timeline and measurement notes
# ---------------------------------------------------------------------------
#
# Wisconsin has used three distinct assessment systems since 2000:
#
#   ERA 1 — WKCE (Wisconsin Knowledge and Concepts Examination)
#     Years:   2003-04 through 2013-14
#     Grades:  3-8, 10 (ELA & Math); 4, 8, 10 (Science, Social Studies)
#     Note:    In 2010-11, race/ethnicity categories expanded from 5 → 7
#              (added "Two or More Races" and refined Asian/Pacific Islander).
#              Pre/post 2010-11 race comparisons require caution.
#     Files:   Available via WINSS Historical Data Files (all_topics_winss_*.zip)
#              and WISEdash (wisedash_YYYY-YY_*.zip)
#
#   ERA 2 — Smarter Balanced (transition year)
#     Year:    2014-15 ONLY
#     Note:    Never publicly released as certified data due to transition issues.
#              Treat as a gap year for longitudinal analysis.
#
#   ERA 3 — Wisconsin Forward Exam
#     Years:   2015-16 through present
#     Grades:  3-8 (ELA & Math); 4, 8 (Science); 4, 8, 10 (Social Studies)
#     CRITICAL: 2019-20 — NO STATE TESTING (federal COVID waiver). File does not exist.
#     CAUTION:  2020-21 — COVID disruption. Testing was optional/limited.
#              Participation rates were much lower than normal years.
#              Include in downloads but FLAG in analysis; exclude from trend lines.
#     CAUTION:  2023-24 onward — NEW version of Forward Exam with UPDATED STANDARDS.
#              Proficiency cut scores changed. Results NOT directly comparable to
#              2015-16 through 2022-23. DPI explicitly cautions against cross-era
#              trend analysis without adjustments.
#
# RECOMMENDED ANALYSIS WINDOWS:
#   Preferred:  2015-16 to 2022-23 (7 years, same test & standards, no COVID)
#   Extended:   Add 2023-24 and 2024-25 with explicit "new standards" break notation
#   Historical: Add WKCE era separately, labelled as a different assessment
#   EXCLUDE:    2019-20 (no data), 2020-21 (flag only; do not include in trends)
#
# ---------------------------------------------------------------------------

# Forward Exam files available from DPI
FORWARD_FILES = [
    # (school_year, url, covid_flag, standard_change_flag)
    ("2015-16", "https://dpi.wi.gov/sites/default/files/wise/downloads/forward_certified_2015-16.zip", False, False),
    ("2016-17", "https://dpi.wi.gov/sites/default/files/wise/downloads/forward_certified_2016-17.zip", False, False),
    ("2017-18", "https://dpi.wi.gov/sites/default/files/wise/downloads/forward_certified_2017-18.zip", False, False),
    ("2018-19", "https://dpi.wi.gov/sites/default/files/wise/downloads/forward_certified_2018-19.zip", False, False),
    # 2019-20: NO FILE EXISTS — federal COVID waiver, no state testing
    ("2020-21", "https://dpi.wi.gov/sites/default/files/wise/downloads/forward_certified_2020-21.zip", True,  False),
    ("2021-22", "https://dpi.wi.gov/sites/default/files/wise/downloads/forward_certified_2021-22.zip", False, False),
    ("2022-23", "https://dpi.wi.gov/sites/default/files/wise/downloads/forward_certified_2022-23.zip", False, False),
    ("2023-24", "https://dpi.wi.gov/sites/default/files/wise/downloads/forward_certified_2023-24.zip", False, True),
    ("2024-25", "https://dpi.wi.gov/sites/default/files/wise/downloads/forward_certified_2024-25.zip", False, True),
]

# WKCE / WINSS files (pre-Forward era)
# Note: WINSS files are large (~50-300 MB) and contain ALL topics, not just assessment.
# The assessment data is extracted in 01_inspect_data.py.
# URL pattern: https://dpi.wi.gov/sites/default/files/wise/downloads/all_topics_winss_YYYY-YY.zip
# These cover up to ~2011-12. Later WKCE years (2012-13, 2013-14) may be in WISEdash format.
WKCE_FILES = [
    # (school_year, url, race_change_flag)
    ("2003-04", "https://dpi.wi.gov/sites/default/files/wise/downloads/all_topics_winss_2003-04.zip", False),
    ("2004-05", "https://dpi.wi.gov/sites/default/files/wise/downloads/all_topics_winss_2004-05.zip", False),
    ("2005-06", "https://dpi.wi.gov/sites/default/files/wise/downloads/all_topics_winss_2005-06.zip", False),
    ("2006-07", "https://dpi.wi.gov/sites/default/files/wise/downloads/all_topics_winss_2006-07.zip", False),
    ("2007-08", "https://dpi.wi.gov/sites/default/files/wise/downloads/all_topics_winss_2007-08.zip", False),
    ("2008-09", "https://dpi.wi.gov/sites/default/files/wise/downloads/all_topics_winss_2008-09.zip", False),
    ("2009-10", "https://dpi.wi.gov/sites/default/files/wise/downloads/all_topics_winss_2009-10.zip", False),
    ("2010-11", "https://dpi.wi.gov/sites/default/files/wise/downloads/all_topics_winss_2010-11.zip", True),  # race categories changed
    ("2011-12", "https://dpi.wi.gov/sites/default/files/wise/downloads/all_topics_winss_2011-12.zip", True),
]


def download_file(url: str, dest: Path, label: str) -> bool:
    """
    Download url to dest. Returns True on success.
    Uses requests if available (handles macOS SSL certs more reliably),
    falls back to urllib with a permissive SSL context.
    """
    if dest.exists():
        size_mb = dest.stat().st_size / 1_000_000
        print(f"  [skip] {label} already exists ({size_mb:.1f} MB)")
        return True

    print(f"  [download] {label} ...", end="", flush=True)
    tmp = dest.with_suffix(".tmp")
    try:
        if _USE_REQUESTS:
            # requests handles macOS certificate issues gracefully
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)
        else:
            # Fallback: urllib with unverified SSL context
            # (acceptable for government data downloads on a local machine)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            import urllib.request
            with urllib.request.urlopen(url, context=ctx, timeout=120) as r, open(tmp, "wb") as f:
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)

        tmp.rename(dest)
        size_mb = dest.stat().st_size / 1_000_000
        print(f" done ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f" ERROR: {e}")
        if tmp.exists():
            tmp.unlink()
        return False


def verify_zip(path: Path) -> bool:
    """Return True if the zip file is valid."""
    try:
        with zipfile.ZipFile(path) as z:
            bad = z.testzip()
            return bad is None
    except zipfile.BadZipFile:
        return False


def download_forward(years: list[str] | None = None) -> None:
    """
    Download Forward Exam zip files.

    Args:
        years: list of school years to download, e.g. ["2022-23", "2023-24"].
               If None, downloads all available years.
    """
    print("\n=== Forward Exam Downloads ===")
    print("NOTE: 2019-20 is MISSING — no state testing (COVID federal waiver)\n")

    results = []
    for school_year, url, covid_flag, std_flag in FORWARD_FILES:
        if years is not None and school_year not in years:
            continue

        flags = []
        if covid_flag:
            flags.append("COVID-DISRUPTED")
        if std_flag:
            flags.append("NEW-STANDARDS")
        flag_str = f"  [{', '.join(flags)}]" if flags else ""

        label = f"Forward {school_year}{flag_str}"
        dest = FORWARD_DIR / f"forward_certified_{school_year}.zip"
        ok = download_file(url, dest, label)

        if ok and not verify_zip(dest):
            print(f"  [warn] {label}: zip verification failed — re-downloading")
            dest.unlink()
            ok = download_file(url, dest, label)

        results.append((school_year, ok, covid_flag, std_flag))
        time.sleep(0.5)  # be polite to DPI servers

    # Summary
    print("\nForward Exam download summary:")
    print(f"  {'Year':<10} {'Status':<10} {'Flags'}")
    print(f"  {'-'*10} {'-'*10} {'-'*30}")
    print(f"  {'2019-20':<10} {'MISSING':<10} No state testing (COVID)")
    for year, ok, covid, std in results:
        flags = " | ".join(filter(None, [
            "COVID-disrupted" if covid else "",
            "NEW-STANDARDS (cut scores changed)" if std else "",
        ]))
        status = "OK" if ok else "FAILED"
        print(f"  {year:<10} {status:<10} {flags}")


def download_wkce(years: list[str] | None = None) -> None:
    """
    Download WKCE / WINSS historical zip files.

    These are large all-topics files (~50-300 MB each). The assessment-specific
    data is extracted in 01_inspect_data.py.

    Args:
        years: list of school years to download. If None, downloads all.
    """
    print("\n=== WKCE / WINSS Historical Downloads ===")
    print("NOTE: These are ALL-TOPICS files (large). Assessment data extracted separately.")
    print("NOTE: 2010-11 onward — race/ethnicity categories expanded (5 → 7 groups)\n")

    results = []
    for school_year, url, race_flag in WKCE_FILES:
        if years is not None and school_year not in years:
            continue

        flag_str = "  [RACE-CATEGORIES-CHANGED]" if race_flag else ""
        label = f"WKCE/WINSS {school_year}{flag_str}"
        dest = WKCE_DIR / f"all_topics_winss_{school_year}.zip"
        ok = download_file(url, dest, label)
        results.append((school_year, ok, race_flag))
        time.sleep(1.0)

    print("\nWKCE/WINSS download summary:")
    print(f"  {'Year':<10} {'Status':<10} {'Flags'}")
    print(f"  {'-'*10} {'-'*10} {'-'*30}")
    for year, ok, race in results:
        flag = "Race categories changed (5→7)" if race else ""
        status = "OK" if ok else "FAILED"
        print(f"  {year:<10} {status:<10} {flag}")


def list_zip_contents(era: str = "forward") -> None:
    """Print the files inside each downloaded zip without extracting."""
    src_dir = FORWARD_DIR if era == "forward" else WKCE_DIR
    zips = sorted(src_dir.glob("*.zip"))
    if not zips:
        print(f"No zip files found in {src_dir}")
        return
    for z in zips:
        try:
            with zipfile.ZipFile(z) as zf:
                names = zf.namelist()
                print(f"\n{z.name}:")
                for n in names:
                    info = zf.getinfo(n)
                    print(f"  {n}  ({info.file_size / 1000:.0f} KB)")
        except zipfile.BadZipFile:
            print(f"\n{z.name}: CORRUPT")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Download Wisconsin DPI assessment data files."
    )
    parser.add_argument(
        "--era",
        choices=["forward", "wkce", "all"],
        default="forward",
        help=(
            "Which era to download. "
            "'forward' = Forward Exam 2015-16 to 2024-25 (recommended). "
            "'wkce' = WKCE/WINSS historical 2003-04 to 2011-12 (different test). "
            "'all' = both eras."
        ),
    )
    parser.add_argument(
        "--years",
        nargs="+",
        metavar="YYYY-YY",
        help="Download only specific school years, e.g. --years 2022-23 2023-24",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List contents of already-downloaded zip files without downloading.",
    )
    args = parser.parse_args()

    print(f"Data directory: {ROOT / 'Data' / 'raw'}")
    print(f"Era: {args.era}")
    if args.years:
        print(f"Years: {', '.join(args.years)}")

    if args.list:
        if args.era in ("forward", "all"):
            print("\n--- Forward Exam zip contents ---")
            list_zip_contents("forward")
        if args.era in ("wkce", "all"):
            print("\n--- WKCE/WINSS zip contents ---")
            list_zip_contents("wkce")
        sys.exit(0)

    if args.era in ("forward", "all"):
        download_forward(years=args.years)

    if args.era in ("wkce", "all"):
        download_wkce(years=args.years)

    print("\nDone. Next step:")
    print("  python3 analysis/01_inspect_data.py")
    print("  This will unzip, read column names, confirm race labels, and fill in the knowledge base.")
