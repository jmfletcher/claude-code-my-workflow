#!/usr/bin/env python3
"""Ingest ARIC published manuscripts from the ARIC website.

Source: https://aric.cscc.unc.edu/aric9/publications/published_manuscripts
The table lists only the first two authors; full author lists are fetched from PubMed.
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
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

try:
    from bs4 import BeautifulSoup
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependencies. Install with:\n"
        "  pip install beautifulsoup4 lxml"
    ) from exc

BASE_URL = "https://aric.cscc.unc.edu/aric9/publications/published_manuscripts"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent.parent.parent / "datasets" / "ARIC" / "raw"
)
USER_AGENT = "DataMonopolies/1.0 (mailto:jasonfletcher@wisc.edu; ARIC ingest)"
DOI_RE = re.compile(r"\bdoi:\s*(10\.\S+)", re.I)
PMID_RE = re.compile(r"\bPMID:\s*(\d+)", re.I)


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


def normalize_author(last: str, given: str = "") -> str | None:
    last = re.sub(r"\s+", " ", last.strip(" ,."))
    given = re.sub(r"\s+", " ", given.strip(" ,."))
    if not last:
        return None
    if not given:
        return last
    initials = re.sub(r"[^A-Za-z]", "", given).upper()
    return f"{last} {initials}" if initials else last


def parse_author_token(token: str) -> str | None:
    token = token.strip(" ,.").replace("`", "'")
    if not token:
        return None
    match = re.match(r"^([A-Z][A-Za-z\-']+),\s*([A-Z](?:[-\s]?[A-Z])*)$", token)
    if match:
        return normalize_author(match.group(1), match.group(2))
    match = re.match(r"^([A-Z][A-Za-z\-']+)\s+([A-Z]{1,4}(?:-[A-Z]{1,4})*)$", token)
    if match:
        return normalize_author(match.group(1), match.group(2))
    return None


def parse_listed_authors(author_segment: str) -> list[str]:
    authors: list[str] = []
    tokens = [t.strip() for t in author_segment.split(",")]
    buffer: list[str] = []
    for token in tokens:
        if not token:
            continue
        if buffer:
            combined = f"{buffer[-1]}, {token}"
            parsed = parse_author_token(combined)
            if parsed:
                buffer.pop()
                authors.append(parsed)
                continue
        parsed = parse_author_token(token)
        if parsed:
            authors.append(parsed)
        else:
            buffer.append(token)
    return authors


def extract_doi(text: str) -> str | None:
    match = DOI_RE.search(text)
    if not match:
        return None
    return match.group(1).rstrip(".)").lower()


def extract_pmid(text: str) -> str | None:
    match = PMID_RE.search(text)
    return match.group(1) if match else None


def parse_title_from_citation(text: str) -> str:
    text = re.sub(r"\s*:\s*MS#.*$", "", text, flags=re.I)
    match = re.match(r"^(.+?)\.\s+(.+)$", text.strip())
    if not match:
        return text[:200].strip()
    rest = match.group(2)
    title_match = re.match(r"^(.+?)(?:\.\.|\.\s+[A-Z][A-Za-z &.-]{2,30}\.)", rest)
    if title_match:
        return title_match.group(1).strip(" .")
    return rest.split(".")[0].strip(" .")


def parse_table_page(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    if not tables:
        return []

    rows: list[dict[str, Any]] = []
    for table in tables:
        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all("td")
            if len(cells) < 2:
                continue
            ms_id = cells[0].get_text(" ", strip=True)
            citation = cells[1].get_text(" ", strip=True)
            if not ms_id or len(citation) < 40:
                continue

            pmid = extract_pmid(citation)
            doi = extract_doi(citation)
            author_seg = citation.split(".", 1)[0] if "." in citation else ""
            listed_authors = parse_listed_authors(author_seg)
            title = parse_title_from_citation(citation)

            rows.append(
                {
                    "ms_id": ms_id,
                    "citation_raw": citation,
                    "title": title,
                    "pmid": pmid,
                    "doi": doi,
                    "listed_authors": listed_authors,
                    "paper_id": f"aric_pmid_{pmid}" if pmid else f"aric_ms_{re.sub(r'[^a-z0-9]+', '_', ms_id.lower())}",
                }
            )
    return rows


def get_total_count(html: str) -> int:
    match = re.search(r"Displaying \d+ - \d+ of (\d+)", html)
    if not match:
        raise RuntimeError("Could not parse ARIC publication total")
    return int(match.group(1))


def pubmed_fetch_batch(pmids: list[str]) -> dict[str, dict[str, Any]]:
    if not pmids:
        return {}
    params = urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    )
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        xml_text = resp.read().decode("utf-8", "replace")

    root = ET.fromstring(xml_text)
    out: dict[str, dict[str, Any]] = {}
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID")
        if not pmid:
            continue
        authors: list[str] = []
        for author in article.findall(".//Author"):
            norm = normalize_author(
                author.findtext("LastName") or "",
                author.findtext("Initials") or author.findtext("ForeName") or "",
            )
            if norm:
                authors.append(norm)
        year_text = (
            article.findtext(".//PubDate/Year")
            or article.findtext(".//PubDate/MedlineDate")
            or ""
        )
        year_match = re.search(r"(\d{4})", year_text)
        pub_year = int(year_match.group(1)) if year_match else None
        title = (article.findtext(".//ArticleTitle") or "").strip()
        out[pmid] = {
            "authors": authors,
            "pub_year": pub_year,
            "title": title,
        }
    return out


def dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pmid: dict[str, dict[str, Any]] = {}
    output: list[dict[str, Any]] = []
    for record in records:
        pmid = record.get("pmid")
        if pmid and pmid in by_pmid:
            continue
        output.append(record)
        if pmid:
            by_pmid[pmid] = record
    return output


def ingest(output_dir: Path, *, items_per_page: int = 100) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = output_dir / "pubmed_cache.json"
    cache: dict[str, Any] = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))

    first_html = fetch_url(
        f"{BASE_URL}?items_per_page={items_per_page}&page=0"
    )
    total = get_total_count(first_html)
    n_pages = (total + items_per_page - 1) // items_per_page
    print(f"Total ARIC manuscripts: {total} ({n_pages} pages)", flush=True)

    rows: list[dict[str, Any]] = parse_table_page(first_html)
    for page in range(1, n_pages):
        html = fetch_url(f"{BASE_URL}?items_per_page={items_per_page}&page={page}")
        rows.extend(parse_table_page(html))
        print(f"Page {page + 1}/{n_pages}: scraped {len(rows)} rows", flush=True)
        time.sleep(0.25)

    pmids = sorted({row["pmid"] for row in rows if row.get("pmid")})
    missing_pmids = [pmid for pmid in pmids if pmid not in cache]
    print(f"Fetching PubMed metadata for {len(missing_pmids)} PMIDs", flush=True)

    batch_size = 200
    for start in range(0, len(missing_pmids), batch_size):
        batch = missing_pmids[start : start + batch_size]
        fetched = pubmed_fetch_batch(batch)
        cache.update(fetched)
        print(
            f"  PubMed batch {start // batch_size + 1}: "
            f"{min(start + batch_size, len(missing_pmids))}/{len(missing_pmids)}",
            flush=True,
        )
        time.sleep(0.12)

    cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    records: list[dict[str, Any]] = []
    no_pubmed = 0
    for row in rows:
        pmid = row.get("pmid")
        pubmed = cache.get(pmid or "", {})
        authors = pubmed.get("authors") or row.get("listed_authors") or []
        author_source = "pubmed_pmid" if pubmed.get("authors") else "listing_partial"
        if not authors:
            continue
        if author_source != "pubmed_pmid":
            no_pubmed += 1

        title = pubmed.get("title") or row.get("title") or ""
        pub_year = pubmed.get("pub_year")

        records.append(
            {
                "paper_id": row["paper_id"],
                "ms_id": row["ms_id"],
                "pmid": pmid,
                "doi": row.get("doi"),
                "title": title,
                "pub_year": pub_year,
                "citation_raw": row["citation_raw"],
                "listed_authors": row.get("listed_authors", []),
                "authors": authors,
                "n_authors": len(authors),
                "author_source": author_source,
                "fetch_status": "ok",
            }
        )

    records = dedupe_records(records)
    json_path = output_dir / "publications.json"
    json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    stats = {
        "rows_scraped": len(rows),
        "records_parsed": len(records),
        "with_pmid": sum(1 for r in records if r.get("pmid")),
        "pubmed_enriched": sum(1 for r in records if r.get("author_source") == "pubmed_pmid"),
        "listing_partial": no_pubmed,
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
