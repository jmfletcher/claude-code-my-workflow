#!/usr/bin/env python3
"""Fetch PMIDs for a My NCBI PubMed collection.

Priority:
1. Use datasets/{dataset}/raw/pmid_list.csv if present (manual export from collection)
2. Fall back to Entrez esearch using grant number query (automated, may differ from collection count)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# REGARDS NIH grant — 894 papers vs 911 in curated collection (June 2026)
REGARDS_ESearch_QUERY = '"NS041588"[Grant Number]'


def fetch_esearch_pmids(query: str, retmax: int = 10000) -> list[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(retmax),
        "retmode": "json",
    }
    url = f"{ESEARCH_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=120) as resp:
        data = json.load(resp)
    result = data["esearchresult"]
    ids = result.get("idlist", [])
    count = int(result.get("count", 0))
    if count > len(ids):
        raise RuntimeError(f"eSearch returned {len(ids)} IDs but count={count}; increase retmax")
    return ids


def read_manual_pmids(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    pmids = re.findall(r"\b(\d{7,8})\b", text)
    # preserve order, deduplicate
    seen: set[str] = set()
    ordered: list[str] = []
    for pmid in pmids:
        if pmid not in seen:
            seen.add(pmid)
            ordered.append(pmid)
    return ordered


def write_pmid_list(pmids: list[str], out_path: Path, source: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["pmid", "source"])
        writer.writeheader()
        for pmid in pmids:
            writer.writerow({"pmid": pmid, "source": source})


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch PMIDs for dataset collection")
    parser.add_argument("--dataset", required=True, help="Dataset name, e.g. REGARDS")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument(
        "--query",
        default=REGARDS_ESearch_QUERY,
        help="Entrez query when no manual pmid_list.csv",
    )
    args = parser.parse_args()

    repo = Path(args.repo_root)
    raw_dir = repo / "datasets" / args.dataset / "raw"
    manual_path = raw_dir / "pmid_list.csv"
    out_path = raw_dir / "pmid_list.csv"

    if manual_path.exists() and manual_path.stat().st_size > 50:
        # Already have manual list — don't overwrite unless forced
        pmids = read_manual_pmids(manual_path)
        source = "manual"
        print(f"Using existing {manual_path}: {len(pmids)} PMIDs")
    else:
        print(f"Fetching PMIDs via Entrez: {args.query}")
        time.sleep(0.4)
        pmids = fetch_esearch_pmids(args.query)
        source = "esearch"
        write_pmid_list(pmids, out_path, source)
        print(f"Wrote {len(pmids)} PMIDs to {out_path} (source: {source})")

    manifest_path = raw_dir / "pubmed_manifest.csv"
    fetch_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["pmid", "fetch_date", "fetch_status", "error_message", "source"]
        )
        writer.writeheader()
        for pmid in pmids:
            writer.writerow(
                {
                    "pmid": pmid,
                    "fetch_date": fetch_time,
                    "fetch_status": "pending",
                    "error_message": "",
                    "source": source,
                }
            )
    print(f"Wrote manifest: {manifest_path} ({len(pmids)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
