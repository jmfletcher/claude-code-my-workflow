#!/usr/bin/env python3
"""Ingest ABCD publications from https://abcdstudy.org/research-publications/

Uses curl_cffi (Chrome impersonation) to bypass site bot protection.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    from bs4 import BeautifulSoup
    from curl_cffi import requests
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependencies. Install with:\n"
        "  python3 -m venv .venv-ffcws && source .venv-ffcws/bin/activate\n"
        "  pip install curl_cffi beautifulsoup4 lxml"
    ) from exc

BASE_URL = "https://abcdstudy.org/research-publications/"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent.parent.parent / "datasets" / "ABCD" / "raw"
)

CSV_COLUMNS = [
    "paper_id",
    "pmid",
    "title",
    "authors",
    "pub_year",
    "published",
    "journal",
    "doi",
    "external_url",
    "source_page",
]


def fetch(session: requests.Session, url: str) -> str:
    response = session.get(url, impersonate="chrome120", timeout=60)
    response.raise_for_status()
    return response.text


def parse_page(html: str, page_num: int) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        return []

    pubs: list[dict[str, Any]] = []
    current_title: str | None = None

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 5:
            current_title = cells[1].get_text(" ", strip=True)
            continue

        if len(cells) != 1 or not current_title:
            continue

        text = cells[0].get_text(" ", strip=True)
        links = row.find_all("a", href=True)
        record: dict[str, Any] = {
            "title": current_title,
            "source_page": page_num,
            "fetch_status": "ok",
        }

        for anchor in links:
            href = anchor["href"]
            label = anchor.get_text(strip=True)
            if "pubmed.ncbi.nlm.nih.gov" in href:
                match = re.search(r"/(\d+)", href)
                if match:
                    record["pmid"] = match.group(1)
            elif label == "Link to publication":
                record["external_url"] = href

        meta = text
        for anchor in links:
            meta = meta.replace(anchor.get_text(strip=True), "", 1)
        meta = meta.replace("Abstract", "", 1).strip()

        pub_match = re.search(r"Published\s*(\d{4}/\d{2}/\d{2})", meta)
        if pub_match:
            record["published"] = pub_match.group(1)
            record["pub_year"] = int(pub_match.group(1)[:4])

        journal_match = re.search(r"Journal\s*(.+?)Published", meta)
        if journal_match:
            record["journal"] = journal_match.group(1).strip()

        author_match = re.search(r"Authors\s*(.+?)(?:Keywords|DOI|$)", meta)
        if author_match:
            record["authors_raw"] = author_match.group(1).strip().rstrip(",")

        doi_match = re.search(r"DOI\s*(10\.\S+)", meta)
        if doi_match:
            record["doi"] = doi_match.group(1).strip()

        authors = [
            part.strip()
            for part in re.split(r",\s*", record.get("authors_raw", ""))
            if part.strip()
        ]
        record["authors"] = authors

        if record.get("pmid"):
            record["paper_id"] = f"abcd_{record['pmid']}"
        else:
            slug = re.sub(r"[^a-z0-9]+", "_", current_title.lower()).strip("_")[:80]
            record["paper_id"] = f"abcd_{slug}"

        pubs.append(record)
        current_title = None

    return pubs


def max_page(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")
    pages = [1]
    for anchor in soup.select("a.page-numbers"):
        label = anchor.get_text(strip=True)
        if label.isdigit():
            pages.append(int(label))
    return max(pages)


def flatten_record(record: dict[str, Any]) -> dict[str, str]:
    flat = {key: "" for key in CSV_COLUMNS}
    flat["paper_id"] = str(record.get("paper_id", ""))
    flat["pmid"] = str(record.get("pmid", ""))
    flat["title"] = str(record.get("title", ""))
    flat["authors"] = "; ".join(record.get("authors", []))
    flat["pub_year"] = str(record.get("pub_year", ""))
    flat["published"] = str(record.get("published", ""))
    flat["journal"] = str(record.get("journal", ""))
    flat["doi"] = str(record.get("doi", ""))
    flat["external_url"] = str(record.get("external_url", ""))
    flat["source_page"] = str(record.get("source_page", ""))
    return flat


def write_outputs(output_dir: Path, records: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "publications.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    csv_path = output_dir / "publications.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(flatten_record(record))

    summary = {
        "source": BASE_URL,
        "total_records": len(records),
        "with_pmid": sum(1 for record in records if record.get("pmid")),
        "with_doi": sum(1 for record in records if record.get("doi")),
        "with_authors": sum(1 for record in records if record.get("authors")),
        "errors": sum(1 for record in records if record.get("fetch_status") != "ok"),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


def ingest(*, output_dir: Path, delay: float, max_pages: int | None) -> list[dict[str, Any]]:
    session = requests.Session()
    print("Fetching page 1...", file=sys.stderr)
    first_html = fetch(session, BASE_URL)
    last_page = max_page(first_html)
    if max_pages is not None:
        last_page = min(last_page, max_pages)

    records = parse_page(first_html, 1)
    print(f"  page 1: {len(records)} records", file=sys.stderr)

    for page in range(2, last_page + 1):
        time.sleep(delay)
        url = f"{BASE_URL}page/{page}/"
        print(f"Fetching page {page}/{last_page}...", file=sys.stderr)
        html = fetch(session, url)
        batch = parse_page(html, page)
        records.extend(batch)
        print(f"  page {page}: {len(batch)} records (total {len(records)})", file=sys.stderr)

    write_outputs(output_dir, records)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()

    records = ingest(output_dir=args.output_dir, delay=args.delay, max_pages=args.max_pages)
    print(f"Wrote {len(records)} records to {args.output_dir}")


if __name__ == "__main__":
    main()
