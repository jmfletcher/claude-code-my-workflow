#!/usr/bin/env python3
"""Ingest EdSHARe bibliography from edshareproject.org.

Source: https://edshareproject.org/research-and-publications/bibliography
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

try:
    from bs4 import BeautifulSoup
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependencies. Install with:\n"
        "  pip install beautifulsoup4 lxml"
    ) from exc

BASE_URL = "https://edshareproject.org/research-and-publications/bibliography"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent.parent.parent / "datasets" / "EdShare" / "raw"
)
USER_AGENT = "DataMonopolies/1.0 (mailto:jasonfletcher@wisc.edu; EdShare ingest)"
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s<\"]+)", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
ET_AL_RE = re.compile(r"\bet\s+al\.?\b", re.I)


def fetch_url(url: str, *, retries: int = 4) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", "replace")
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2**attempt)
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError(f"Failed to fetch {url}")


ORG_MARKERS = (
    "center",
    "institute",
    "bureau",
    "department",
    "consortium",
    "statistics",
    "college",
    "university",
    "office",
    "division",
    "school",
)


def normalize_author(name: str) -> str | None:
    name = re.sub(r"\s+", " ", name.strip(" ;."))
    if not name or ET_AL_RE.search(name):
        return None

    lower = name.lower()
    if any(marker in lower for marker in ORG_MARKERS) and len(name.split()) >= 2:
        return name

    if "," in name:
        last, given = [part.strip() for part in name.split(",", 1)]
    else:
        parts = name.split()
        if len(parts) == 1:
            return parts[0]
        last = parts[-1]
        given = " ".join(parts[:-1])
    initials = "".join(token[0].upper() for token in re.split(r"[\s-]+", given) if token)
    return f"{last} {initials}" if initials else last


def parse_authors(author_segment: str) -> list[str]:
    authors: list[str] = []
    for token in author_segment.split(";"):
        norm = normalize_author(token)
        if norm:
            authors.append(norm)
    return authors


def parse_entry(item: BeautifulSoup) -> dict[str, Any] | None:
    text = item.get_text(" ", strip=True)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    if len(text) < 40:
        return None

    year_match = re.search(r"\b((?:19|20)\d{2})\.\s+", text)
    if not year_match:
        return None
    pub_year = int(year_match.group(1))
    author_segment = text[: year_match.start()].strip(" .;")
    authors = parse_authors(author_segment)
    if not authors:
        return None

    title_link = item.select_one("a[href*='/publication-']")
    title = title_link.get_text(" ", strip=True) if title_link else ""
    if not title:
        quote_match = re.search(r'["“](.+?)["”]', text)
        title = quote_match.group(1).strip() if quote_match else text[:200]

    doi = None
    doi_link = item.select_one("a[href*='doi.org']")
    if doi_link:
        href = doi_link.get("href", "")
        doi_match = DOI_RE.search(href) or DOI_RE.search(doi_link.get_text())
        doi = doi_match.group(1).rstrip(".)") if doi_match else None
    if not doi:
        doi_match = DOI_RE.search(text)
        doi = doi_match.group(1).rstrip(".)") if doi_match else None

    pub_id = None
    if title_link and title_link.get("href"):
        pub_id = title_link["href"].rstrip("/").split("/")[-1]

    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:80]
    paper_id = f"edshare_doi_{re.sub(r'[^a-z0-9]', '_', doi.lower())}" if doi else f"edshare_{pub_id or slug}"

    return {
        "paper_id": paper_id,
        "publication_id": pub_id,
        "title": title,
        "pub_year": pub_year,
        "doi": doi.lower() if doi else None,
        "citation_raw": text,
        "authors": authors,
        "n_authors": len(authors),
        "author_source": "listing",
        "fetch_status": "ok",
    }


def get_last_page(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")
    last = soup.select_one(".pager__item--last a")
    if last and last.get("href"):
        match = re.search(r"[?&]page=(\d+)", last["href"])
        if match:
            return int(match.group(1))
    return 0


def parse_page(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    records: list[dict[str, Any]] = []
    for item in soup.select("div.views-row p.bibliography-item"):
        parsed = parse_entry(item)
        if parsed:
            records.append(parsed)
    return records


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


def ingest(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    first_html = fetch_url(f"{BASE_URL}?page=0")
    last_page = get_last_page(first_html)
    records = parse_page(first_html)
    print(f"EdSHARe bibliography pages: 0-{last_page}", flush=True)

    for page in range(1, last_page + 1):
        html = fetch_url(f"{BASE_URL}?page={page}")
        records.extend(parse_page(html))
        if page % 10 == 0 or page == last_page:
            print(f"Page {page}/{last_page}: cumulative {len(records)}", flush=True)
        time.sleep(0.2)

    records = dedupe_records(records)
    json_path = output_dir / "publications.json"
    json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    stats = {
        "pages_crawled": last_page + 1,
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
