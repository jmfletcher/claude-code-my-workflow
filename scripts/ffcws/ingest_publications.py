#!/usr/bin/env python3
"""Ingest FFCWS publications from https://ffcws.princeton.edu/publications.

Uses the site sitemap for the full URL list and curl_cffi (Chrome impersonation)
to fetch pages protected by Cloudflare.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup
    from curl_cffi import requests
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependencies. Install with:\n"
        "  pip install curl_cffi beautifulsoup4 lxml"
    ) from exc

BASE_URL = "https://ffcws.princeton.edu"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent.parent / "datasets" / "FFCWS" / "raw"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# Drupal bibcite fields we care about; keys are field class suffixes.
FIELD_MAP = {
    "title": "title",
    "author": "authors",
    "bibcite-year": "year",
    "bibcite-type": "publication_type",
    "bibcite-abst-e": "abstract",
    "keywords": "keywords",
    "bibcite-secondary-title": "secondary_title",
    "bibcite-volume": "volume",
    "bibcite-issue": "issue",
    "bibcite-pages": "pages",
    "bibcite-publisher": "publisher",
    "bibcite-place-published": "place_published",
    "bibcite-call-number": "call_number",
    "bibcite-doi": "doi",
    "bibcite-isbn": "isbn",
    "bibcite-issn": "issn",
    "bibcite-edition": "edition",
    "bibcite-language": "language",
    "bibcite-date": "date",
    "bibcite-access-date": "access_date",
    "bibcite-number-of-volumes": "number_of_volumes",
    "bibcite-number": "number",
    "bibcite-reprint-edition": "reprint_edition",
    "bibcite-short-title": "short_title",
    "bibcite-translated-title": "translated_title",
}

CSV_COLUMNS = [
    "url",
    "slug",
    "sitemap_lastmod",
    "bibcite_id",
    "title",
    "authors",
    "year",
    "publication_type",
    "abstract",
    "keywords",
    "secondary_title",
    "volume",
    "issue",
    "pages",
    "publisher",
    "place_published",
    "call_number",
    "doi",
    "isbn",
    "external_url",
    "google_scholar_url",
    "fetch_status",
    "fetch_error",
]


def fetch(session: requests.Session, url: str, *, timeout: float = 45.0) -> requests.Response:
    return session.get(url, impersonate="chrome120", timeout=timeout)


def publication_urls_from_sitemap(session: requests.Session) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()

    for page in (1, 2):
        response = fetch(session, f"{SITEMAP_URL}?page={page}")
        response.raise_for_status()
        root = ET.fromstring(response.text)
        for node in root.findall(".//sm:url", SITEMAP_NS):
            loc = node.find("sm:loc", SITEMAP_NS)
            if loc is None or not loc.text:
                continue
            url = loc.text.strip()
            if "/publications/" not in url:
                continue
            slug = urlparse(url).path.rstrip("/").split("/")[-1]
            if slug in {"publications", "contributor", "keyword"} or slug.startswith("contributor"):
                continue
            if url in seen:
                continue
            seen.add(url)
            lastmod = node.find("sm:lastmod", SITEMAP_NS)
            entries.append(
                {
                    "url": url,
                    "slug": slug,
                    "sitemap_lastmod": lastmod.text.strip() if lastmod is not None and lastmod.text else "",
                }
            )

    entries.sort(key=lambda item: item["url"])
    return entries


def field_items(field) -> list[str]:
    items: list[str] = []
    for item in field.select(".field__item"):
        link = item.find("a")
        text = link.get_text(" ", strip=True) if link else item.get_text(" ", strip=True)
        text = re.sub(r"\s*,\s*$", "", text.strip())
        if text:
            items.append(text)
    if items:
        return items
    text = field.get_text(" ", strip=True)
    label = field.select_one(".field__label")
    if label:
        label_text = label.get_text(" ", strip=True)
        if text.startswith(label_text):
            text = text[len(label_text) :].strip(" :")
    return [text] if text else []


def parse_publication_page(html: str, meta: dict[str, str]) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    record: dict[str, Any] = {
        **meta,
        "fetch_status": "ok",
        "fetch_error": "",
        "bibcite_id": "",
        "external_url": "",
        "google_scholar_url": "",
        "bibtex": "",
    }

    for field_class, key in FIELD_MAP.items():
        field = soup.select_one(f".field--name-{field_class}")
        if not field:
            continue
        values = field_items(field)
        if key in {"authors", "keywords"}:
            record[key] = values
        elif values:
            record[key] = values[0]

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        text = anchor.get_text(" ", strip=True)
        if "bibcite_reference" in href:
            match = re.search(r"bibcite_reference/(\d+)", href)
            if match:
                record["bibcite_id"] = match.group(1)
        elif text == "Google Scholar":
            record["google_scholar_url"] = href
        elif field := soup.select_one(".field--name-bibcite-url"):
            link = field.find("a", href=True)
            if link:
                record["external_url"] = link["href"]

    if not record.get("title"):
        title_el = soup.select_one("h1.page-title, h1")
        if title_el:
            record["title"] = title_el.get_text(" ", strip=True)

    return record


def fetch_bibtex(session: requests.Session, bibcite_id: str) -> str:
    url = f"{BASE_URL}/bibcite/export/bibtex/bibcite_reference/{bibcite_id}"
    response = fetch(session, url)
    response.raise_for_status()
    return response.text.strip()


def load_checkpoint(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            records[item["url"]] = item
    return records


def append_checkpoint(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def flatten_record(record: dict[str, Any]) -> dict[str, str]:
    flat: dict[str, str] = {}
    for key in CSV_COLUMNS:
        value = record.get(key, "")
        if isinstance(value, list):
            flat[key] = "; ".join(str(v) for v in value)
        elif value is None:
            flat[key] = ""
        else:
            flat[key] = str(value)
    return flat


def write_outputs(output_dir: Path, records: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "publications.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    csv_path = output_dir / "publications.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(flatten_record(record))

    bib_path = output_dir / "publications.bib"
    bib_entries = [record["bibtex"] for record in records if record.get("bibtex")]
    bib_path.write_text("\n\n".join(bib_entries) + ("\n" if bib_entries else ""), encoding="utf-8")

    summary = {
        "source": f"{BASE_URL}/publications",
        "total_records": len(records),
        "with_bibtex": sum(1 for record in records if record.get("bibtex")),
        "with_abstract": sum(1 for record in records if record.get("abstract")),
        "with_doi": sum(1 for record in records if record.get("doi")),
        "errors": sum(1 for record in records if record.get("fetch_status") != "ok"),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


def ingest(
    *,
    output_dir: Path,
    delay: float,
    limit: int | None,
    resume: bool,
    fetch_bibtex: bool,
) -> list[dict[str, Any]]:
    session = requests.Session()
    checkpoint_path = output_dir / "publications.jsonl"
    existing = load_checkpoint(checkpoint_path) if resume else {}

    if resume and existing:
        print(f"Resuming from checkpoint with {len(existing)} records", file=sys.stderr)

    print("Fetching sitemap...", file=sys.stderr)
    entries = publication_urls_from_sitemap(session)
    print(f"Found {len(entries)} publication URLs", file=sys.stderr)

    if limit is not None:
        entries = entries[:limit]

    total = len(entries)
    for index, meta in enumerate(entries, start=1):
        url = meta["url"]
        if resume and url in existing and existing[url].get("fetch_status") == "ok":
            continue

        print(f"[{index}/{total}] {url}", file=sys.stderr)
        record: dict[str, Any] = dict(meta)
        try:
            response = fetch(session, url)
            response.raise_for_status()
            record.update(parse_publication_page(response.text, meta))
            if fetch_bibtex and record.get("bibcite_id"):
                record["bibtex"] = fetch_bibtex(session, record["bibcite_id"])
                time.sleep(delay)
        except Exception as exc:  # noqa: BLE001 - collect per-record failures
            record["fetch_status"] = "error"
            record["fetch_error"] = str(exc)

        append_checkpoint(checkpoint_path, record)
        existing[url] = record
        time.sleep(delay)

    records = [existing[entry["url"]] for entry in entries if entry["url"] in existing]
    write_outputs(output_dir, records)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to wait between requests (default: 0.5)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Fetch only the first N publications")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip URLs already present with fetch_status=ok in publications.jsonl",
    )
    parser.add_argument(
        "--fetch-bibtex",
        action="store_true",
        help="Also download BibTeX for each record (doubles request volume)",
    )
    args = parser.parse_args()

    records = ingest(
        output_dir=args.output_dir,
        delay=args.delay,
        limit=args.limit,
        resume=args.resume,
        fetch_bibtex=args.fetch_bibtex,
    )
    ok = sum(1 for record in records if record.get("fetch_status") == "ok")
    print(f"Wrote {len(records)} records ({ok} ok) to {args.output_dir}")


if __name__ == "__main__":
    main()
