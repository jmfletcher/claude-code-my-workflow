"""
11_download_seda.py — Download Stanford SEDA (Educational Opportunity Project) CSVs.

SEDA 6.0 (https://edopportunity.org/opportunity/data/downloads/#testscore-6):

- seda_geodist_poolsub_cs_6.0.csv — Geographic district, pooled grades/years, math + ELA
  in one row per district × demographic slice (race rows include White, Black, Hispanic means).
  Use this for national White vs. Black / White vs. Hispanic ELA-style scatters (cohort scale).

- seda_school_pool_cs_6.0.csv — School-level pooled means for *all students only* (no race
  breakdown in columns). Optional; large (~hundreds of MB).

Files save under Data/raw/seda/ (gitignored). Uses curl to avoid macOS Python SSL verify issues.

Run from repo root:
  python3 analysis/11_download_seda.py
  python3 analysis/11_download_seda.py --include-school-pool   # optional; very large
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "Data" / "raw" / "seda"

BASE = "https://stacks.stanford.edu/file/xh833nn4025"

FILES = {
    "geodist_poolsub": "seda_geodist_poolsub_cs_6.0.csv",
    "school_pool": "seda_school_pool_cs_6.0.csv",
}


def _curl_download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["curl", "-fL", "--retry", "3", "--retry-delay", "2", "-o", str(dest), url]
    print(f"  Downloading -> {dest.name}")
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download SEDA 6.0 CSVs from Stanford.")
    parser.add_argument(
        "--include-school-pool",
        action="store_true",
        help="Also download seda_school_pool_cs_6.0.csv (very large; all-student means only, no race).",
    )
    args = parser.parse_args()

    print("=" * 65)
    print("11_download_seda.py — SEDA 6.0 (Stanford stacks)")
    print("=" * 65)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    _curl_download(f"{BASE}/{FILES['geodist_poolsub']}", OUT_DIR / FILES["geodist_poolsub"])

    if args.include_school_pool:
        _curl_download(f"{BASE}/{FILES['school_pool']}", OUT_DIR / FILES["school_pool"])
    else:
        print("  (Skipping school pool; use --include-school-pool if needed.)")

    print("Done.")
    print(f"  Data directory: {OUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"curl failed: {e}", file=sys.stderr)
        sys.exit(1)
