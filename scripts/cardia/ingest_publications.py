#!/usr/bin/env python3
"""Ingest CARDIA publications from the Zenodo community API.

Source: https://zenodo.org/communities/cardia-cc/records
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

COMMUNITY = "cardia-cc"
API_BASE = f"https://zenodo.org/api/communities/{COMMUNITY}/records"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent.parent.parent / "datasets" / "CARDIA" / "raw"
)
USER_AGENT = "DataMonopolies/1.0 (mailto:jasonfletcher@wisc.edu; CARDIA ingest)"


def fetch_json(url: str, *, retries: int = 4) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2**attempt)
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError(f"Failed to fetch {url}")


def normalize_author(name: str) -> str | None:
    name = re.sub(r"\s+", " ", name.strip())
    if not name:
        return None

    if "," in name:
        last, given = [part.strip() for part in name.split(",", 1)]
    else:
        parts = name.split()
        if len(parts) == 1:
            return parts[0]
        last = parts[0]
        given = " ".join(parts[1:])

    initials = re.sub(r"[^A-Za-z]", "", given).upper()
    if initials:
        return f"{last} {initials}"
    return last


def parse_record(rec: dict[str, Any]) -> dict[str, Any] | None:
    metadata = rec.get("metadata") or {}
    creators = metadata.get("creators") or []
    authors = []
    for creator in creators:
        norm = normalize_author(creator.get("name", ""))
        if norm:
            authors.append(norm)
    authors = list(dict.fromkeys(authors))
    if not authors:
        return None

    title = metadata.get("title") or rec.get("title")
    if not title or not str(title).strip():
        return None

    pub_date = metadata.get("publication_date") or ""
    year_match = re.match(r"(\d{4})", str(pub_date))
    pub_year = int(year_match.group(1)) if year_match else None

    doi = metadata.get("doi") or rec.get("doi")
    resource_type = (metadata.get("resource_type") or {}).get("title")
    zenodo_id = rec.get("id")

    paper_id = f"cardia_doi_{re.sub(r'[^a-z0-9]', '_', doi.lower())}" if doi else f"cardia_zenodo_{zenodo_id}"

    return {
        "paper_id": paper_id,
        "zenodo_id": zenodo_id,
        "conceptrecid": rec.get("conceptrecid"),
        "title": str(title).strip(),
        "pub_year": pub_year,
        "doi": doi,
        "resource_type": resource_type,
        "url": rec.get("links", {}).get("self_html"),
        "authors": authors,
        "n_authors": len(authors),
        "fetch_status": "ok",
    }


def dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_doi: dict[str, dict[str, Any]] = {}
    by_title: dict[str, dict[str, Any]] = {}
    output: list[dict[str, Any]] = []

    for record in records:
        doi = record.get("doi")
        title_key = re.sub(r"\W+", " ", record["title"].lower()).strip()
        existing = by_doi.get(doi) if doi else by_title.get(title_key) if title_key else None
        if existing:
            if record["n_authors"] > existing["n_authors"]:
                existing.update(record)
            continue
        output.append(record)
        if doi:
            by_doi[doi] = record
        if title_key:
            by_title[title_key] = record
    return output


def ingest(output_dir: Path, *, page_size: int = 25) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    page = 1
    total: int | None = None
    records: list[dict[str, Any]] = []

    while True:
        params = urllib.parse.urlencode(
            {"page": page, "size": page_size, "sort": "newest"}
        )
        data = fetch_json(f"{API_BASE}?{params}")
        hits = data["hits"]["hits"]
        if total is None:
            total = data["hits"]["total"]
            print(f"Total Zenodo records: {total}", flush=True)
        if not hits:
            break

        for rec in hits:
            parsed = parse_record(rec)
            if parsed:
                records.append(parsed)

        print(f"Page {page}: cumulative parsed {len(records)}", flush=True)
        if total is not None and page * page_size >= total:
            break
        page += 1
        time.sleep(0.35)

    records = dedupe_records(records)
    json_path = output_dir / "publications.json"
    json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    stats = {
        "zenodo_total": total,
        "records_parsed": len(records),
        "with_doi": sum(1 for r in records if r.get("doi")),
        "median_authors": sorted(r["n_authors"] for r in records)[len(records) // 2],
    }
    (output_dir / "ingest_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    stats = ingest(args.output_dir)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
