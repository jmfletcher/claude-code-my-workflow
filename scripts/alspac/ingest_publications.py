#!/usr/bin/env python3
"""Ingest ALSPAC publications from the Bristol publications index.

Source: https://www.bristol.ac.uk/alspac/researchers/publications/
When a listing uses "et al.", full author lists are fetched via Crossref (DOI)
with PubMed (DOI/title) fallback.
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

BASE_URL = "https://www.bristol.ac.uk"
INDEX_URL = f"{BASE_URL}/alspac/researchers/publications/"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent.parent.parent / "datasets" / "ALSPAC" / "raw"
)
USER_AGENT = "DataMonopolies/1.0 (mailto:jasonfletcher@wisc.edu; ALSPAC ingest)"
AUTHOR_START = re.compile(r"^[A-Z][A-Za-z\-`']+, [A-Z]")
DOI_RE = re.compile(r"\b(?:doi:\s*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[^\s,;]+)", re.I)
PMID_RE = re.compile(r"\b(?:PubMed|PMID)[:\s]*(\d{6,8})\b", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
ET_AL_RE = re.compile(r"\bet\s+al\.?\b", re.I)


def fetch_url(url: str, *, timeout: float = 60.0, retries: int = 4) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(2**attempt)
                continue
            raise
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2**attempt)
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError(f"Failed to fetch {url}")


def get_index_pages() -> list[str]:
    html = fetch_url(INDEX_URL)
    soup = BeautifulSoup(html, "lxml")
    pages: list[str] = []
    for anchor in soup.select("a[href]"):
        href = anchor["href"]
        if not re.search(r"/alspac/researchers/publications/[^/]+/?$", href):
            continue
        if href.startswith("/"):
            href = BASE_URL + href
        if href.rstrip("/") == INDEX_URL.rstrip("/"):
            continue
        if href not in pages:
            pages.append(href)
    return sorted(set(pages))


def parse_citations_from_page(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one(".main__content") or soup
    cites: list[str] = []

    for li in main.find_all("li"):
        text = re.sub(r"\s+", " ", li.get_text(" ", strip=True))
        if len(text) >= 50 and YEAR_RE.search(text):
            cites.append(text)

    if cites:
        return cites

    text = main.get_text("\n", strip=True)
    blocks = re.split(r"(?=^[A-Z][A-Za-z\-`']+, [A-Z])", text, flags=re.M)
    for block in blocks:
        block = re.sub(r"\s+", " ", block.strip())
        if len(block) >= 80 and YEAR_RE.search(block):
            cites.append(block)
    return cites


def extract_doi(text: str) -> str | None:
    match = DOI_RE.search(text)
    if not match:
        return None
    doi = match.group(1).rstrip(".)")
    return doi.lower()


def extract_pmid(text: str) -> str | None:
    match = PMID_RE.search(text)
    return match.group(1) if match else None


def extract_year(text: str, page_slug: str | None = None) -> int | None:
    slug_year: int | None = None
    if page_slug:
        match = re.match(r"^(\d{4})", page_slug)
        if match:
            slug_year = int(match.group(1))

    candidates: list[int] = []
    patterns = [
        r"\b((?:19|20)\d{2})\b\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
        r"[;,.\s]((?:19|20)\d{2})\s*[;:]\s*\d",
        r"\(((?:19|20)\d{2})\)",
        r",\s*((?:19|20)\d{2})\.",
        r"\.\s*((?:19|20)\d{2})\s*[;:]",
        r"\b((?:19|20)\d{2})\b\s*$",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            year = int(match.group(1))
            if 1990 <= year <= 2026:
                candidates.append(year)

    if candidates:
        return candidates[-1]
    if slug_year and 1990 <= slug_year <= 2026:
        return slug_year
    return None


def normalize_author(last: str, given: str = "") -> str | None:
    last = re.sub(r"\s+", " ", last.strip(" ,."))
    given = re.sub(r"\s+", " ", given.strip(" ,."))
    if not last:
        return None
    if not given:
        return last
    initials: list[str] = []
    for token in re.split(r"[\s-]+", given):
        token = re.sub(r"[^A-Za-z]", "", token)
        if token:
            initials.append(token[0].upper())
    if not initials:
        return last
    return f"{last} {''.join(initials)}"


def clean_name_token(token: str) -> str:
    token = token.strip(" ,.")
    token = token.replace("`", "'")
    token = re.sub(r"\s+", " ", token)
    return token


def parse_author_token(token: str) -> str | None:
    token = clean_name_token(token)
    if not token or ET_AL_RE.search(token):
        return None

    match = re.match(r"^([A-Z][A-Za-z\-']+),\s*([A-Z](?:[-\s]?[A-Z])*)$", token)
    if match:
        return normalize_author(match.group(1), match.group(2))

    match = re.match(r"^([A-Z][A-Za-z\-']+)\s+([A-Z]{1,4}(?:-[A-Z]{1,4})*)$", token)
    if match:
        return normalize_author(match.group(1), match.group(2))

    return None


PERIOD_AUTHOR_RE = re.compile(
    r"^(?:[A-Z][A-Za-z\-']+|[a-z]+)(?:\s+(?:[A-Z][A-Za-z\-']+|[a-z]+))*\s+[A-Z]{1,4}\.?$"
)


def parse_period_separated_authors(citation: str) -> tuple[list[str], str]:
    """Parse 'Last I. Last I. Title. Journal' format used on some ALSPAC pages."""
    text = re.sub(r"\s+", " ", citation.strip())
    parts = [p.strip() for p in re.split(r"\.\s+", text) if p.strip()]
    authors: list[str] = []
    title_parts: list[str] = []

    for idx, part in enumerate(parts):
        if PERIOD_AUTHOR_RE.match(part) and not title_parts:
            norm = parse_author_token(part.rstrip("."))
            if norm:
                authors.append(norm)
                continue
        title_parts = parts[idx:]
        break

    title = ""
    if title_parts:
        title = title_parts[0]
        if len(title) < 12 and len(title_parts) > 1:
            title = title_parts[1]
    return authors, title.strip(" .,")


def split_author_title_rest(citation: str) -> tuple[str, str, str]:
    """Return (author_segment, title, remainder) from a citation string."""
    text = citation.strip()
    text = re.sub(r"\s*https?://\S+", "", text)
    text = re.sub(r"\s*doi:\s*10\.\S+", "", text, flags=re.I)

    period_authors, period_title = parse_period_separated_authors(citation)
    if len(period_authors) >= 2 and period_title:
        author_seg = ", ".join(period_authors)
        return author_seg, period_title, text

    if ET_AL_RE.search(text):
        match = re.search(r"^(.*?)\bet\s+al\.?\s*[,.\s]*(.*)$", text, re.I)
        if match:
            author_seg = match.group(1).strip(" ,.")
            rest = match.group(2).strip()
            title = extract_title_from_rest(rest)
            return author_seg, title, rest

    # Quoted title (older entries)
    quote_match = re.search(r"^(.*?),\s*'(.+?)'\s*,?\s*(.*)$", text)
    if quote_match:
        return quote_match.group(1).strip(" ,."), quote_match.group(2).strip(), quote_match.group(3)

    # Standard: authors end at ". Title"
    match = re.search(r"^(.+?)\.\s+([A-Z0-9].*)$", text)
    if match:
        author_seg = match.group(1)
        rest = match.group(2)
        title = extract_title_from_rest(rest)
        return author_seg.strip(" ,."), title, rest

    return text, "", text


def extract_title_from_rest(rest: str) -> str:
    rest = rest.strip()
    if not rest:
        return ""

    # Title usually ends at ". Journal" or ", Journal"
    for sep in (". ", ", "):
        parts = rest.split(sep, 1)
        if len(parts) == 2 and len(parts[0]) >= 8:
            return parts[0].strip(" .,")

    # Fallback: first sentence-ish chunk
    match = re.match(r"^(.{8,200}?)(?:\.\s+[A-Z][a-z]+|\,\s+\d{4})", rest)
    if match:
        return match.group(1).strip(" .,")
    return rest[:200].strip(" .,")


def parse_listed_authors(author_segment: str) -> list[str]:
    authors: list[str] = []
    if not author_segment:
        return authors

    # Comma-separated "Last, I" tokens; stop before title-like fragments
    tokens = [t.strip() for t in author_segment.split(",")]
    buffer: list[str] = []
    for token in tokens:
        if not token:
            continue
        if ET_AL_RE.search(token):
            break
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


def crossref_authors(doi: str) -> list[str]:
    encoded = urllib.parse.quote(doi, safe="")
    url = f"https://api.crossref.org/works/{encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    message = payload.get("message", {})
    authors: list[str] = []
    for author in message.get("author", []):
        norm = normalize_author(author.get("family", ""), author.get("given", ""))
        if norm:
            authors.append(norm)
    return authors


def pubmed_esearch(term: str) -> list[str]:
    params = urllib.parse.urlencode(
        {"db": "pubmed", "term": term, "retmode": "json", "retmax": 3}
    )
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("esearchresult", {}).get("idlist", [])


def pubmed_authors_from_ids(pmids: list[str]) -> list[str]:
    if not pmids:
        return []
    params = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "id": ",".join(pmids[:1]),
            "retmode": "xml",
        }
    )
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml_text = resp.read().decode("utf-8", "replace")

    root = ET.fromstring(xml_text)
    authors: list[str] = []
    for author in root.findall(".//Author"):
        last = author.findtext("LastName") or ""
        initials = author.findtext("Initials") or author.findtext("ForeName") or ""
        norm = normalize_author(last, initials)
        if norm:
            authors.append(norm)
    return authors


def crossref_search_authors(title: str, year: int | None) -> list[str]:
    query = re.sub(r"[^\w\s]", " ", title).strip()
    if len(query) < 8:
        return []
    params = {
        "query.bibliographic": query,
        "rows": 3,
        "select": "DOI,title,author,published",
    }
    if year:
        params["filter"] = f"from-pub-date:{year}-01-01,until-pub-date:{year}-12-31"
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    items = payload.get("message", {}).get("items", [])
    if not items:
        return []

    target = re.sub(r"\W+", "", title.lower())[:60]
    for item in items:
        item_title = ""
        if item.get("title"):
            item_title = item["title"][0]
        item_key = re.sub(r"\W+", "", item_title.lower())[:60]
        if not target or target[:30] in item_key or item_key[:30] in target:
            authors: list[str] = []
            for author in item.get("author", []):
                norm = normalize_author(author.get("family", ""), author.get("given", ""))
                if norm:
                    authors.append(norm)
            if authors:
                return authors
    return []


def enrich_authors(
    *,
    citation: str,
    doi: str | None,
    pmid: str | None,
    title: str,
    year: int | None,
    cache: dict[str, Any],
) -> tuple[list[str], str, str | None]:
    """Return (authors, source, error)."""
    cache_key = doi or pmid or f"title:{title}:{year}"
    if cache_key in cache:
        cached = cache[cache_key]
        return cached["authors"], cached["source"], cached.get("error")

    authors: list[str] = []
    source = "listing"
    error: str | None = None

    try:
        if doi:
            try:
                authors = crossref_authors(doi)
                if authors:
                    source = "crossref_doi"
            except Exception as exc:  # noqa: BLE001
                error = f"crossref_doi:{exc}"

            if not authors:
                time.sleep(0.12)
                pmids = pubmed_esearch(f"{doi}[doi]")
                authors = pubmed_authors_from_ids(pmids)
                if authors:
                    source = "pubmed_doi"
                    error = None

        if not authors and pmid:
            authors = pubmed_authors_from_ids([pmid])
            if authors:
                source = "pubmed_pmid"
                error = None

        if not authors and title:
            safe_title = re.sub(r'["\']', " ", title).strip()
            if year:
                term = f'"{safe_title}"[Title] AND {year}[pdat]'
            else:
                term = f'"{safe_title}"[Title]'
            time.sleep(0.12)
            pmids = pubmed_esearch(term)
            authors = pubmed_authors_from_ids(pmids)
            if authors:
                source = "pubmed_title"
                error = None
            else:
                time.sleep(0.12)
                authors = crossref_search_authors(title, year)
                if authors:
                    source = "crossref_title"
                    error = None

    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    cache[cache_key] = {"authors": authors, "source": source, "error": error}
    return authors, source, error


def is_correspondence_noise(citation: str) -> bool:
    lowered = citation.lower()
    return "-to:" in lowered or lowered.startswith("comment on ") or "author reply" in lowered


def parse_citation(
    citation: str,
    *,
    page_slug: str,
    cache: dict[str, Any],
    enrich_et_al: bool,
) -> dict[str, Any] | None:
    if len(citation) < 50 or not YEAR_RE.search(citation):
        return None
    if is_correspondence_noise(citation):
        return None

    doi = extract_doi(citation)
    pmid = extract_pmid(citation)
    year = extract_year(citation, page_slug)
    has_et_al = bool(ET_AL_RE.search(citation))

    author_seg, title, _rest = split_author_title_rest(citation)
    listed_authors = parse_listed_authors(author_seg)

    authors = listed_authors
    author_source = "listing"
    enrich_error: str | None = None

    if has_et_al and enrich_et_al:
        enriched, author_source, enrich_error = enrich_authors(
            citation=citation,
            doi=doi,
            pmid=pmid,
            title=title,
            year=year,
            cache=cache,
        )
        if enriched and len(enriched) >= len(listed_authors):
            authors = enriched
        elif listed_authors:
            authors = listed_authors
            author_source = "listing_partial_et_al"
            if enrich_error:
                enrich_error = enrich_error or "enrichment_returned_fewer_authors"
        time.sleep(0.15)
    elif pmid and len(authors) <= 6:
        enriched, author_source, enrich_error = enrich_authors(
            citation=citation,
            doi=doi,
            pmid=pmid,
            title=title,
            year=year,
            cache=cache,
        )
        if enriched and len(enriched) > len(authors):
            authors = enriched
        time.sleep(0.12)
    elif not authors and (doi or pmid or title):
        enriched, author_source, enrich_error = enrich_authors(
            citation=citation,
            doi=doi,
            pmid=pmid,
            title=title,
            year=year,
            cache=cache,
        )
        if enriched:
            authors = enriched
        time.sleep(0.12)

    if not authors:
        return None

    slug_base = re.sub(r"[^a-z0-9]+", "_", (title or citation)[:80].lower()).strip("_")
    paper_id = f"alspac_{page_slug}_{slug_base}"[:120]
    if doi:
        paper_id = f"alspac_doi_{re.sub(r'[^a-z0-9]', '_', doi.lower())}"

    return {
        "paper_id": paper_id,
        "citation_raw": citation,
        "title": title,
        "pub_year": year,
        "doi": doi,
        "pmid": pmid,
        "page_slug": page_slug,
        "has_et_al": has_et_al,
        "author_source": author_source,
        "enrich_error": enrich_error,
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
        title_key = re.sub(r"\W+", " ", (record.get("title") or "").lower()).strip()

        existing = None
        if doi and doi in by_doi:
            existing = by_doi[doi]
        elif title_key and title_key in by_title:
            existing = by_title[title_key]

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


def ingest(
    output_dir: Path,
    *,
    enrich_et_al: bool = True,
    max_pages: int | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = output_dir / "enrichment_cache.json"
    cache: dict[str, Any] = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))

    pages = get_index_pages()
    if max_pages is not None:
        pages = pages[:max_pages]

    records: list[dict[str, Any]] = []
    for index, page_url in enumerate(pages, start=1):
        slug = page_url.rstrip("/").split("/")[-1]
        html = fetch_url(page_url)
        citations = parse_citations_from_page(html)
        for citation in citations:
            parsed = parse_citation(
                citation,
                page_slug=slug,
                cache=cache,
                enrich_et_al=enrich_et_al,
            )
            if parsed:
                records.append(parsed)
        print(f"[{index}/{len(pages)}] {slug}: {len(citations)} citations", flush=True)
        time.sleep(0.2)

    cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    records = dedupe_records(records)

    json_path = output_dir / "publications.json"
    json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    stats = {
        "pages_crawled": len(pages),
        "raw_records": len(records),
        "with_doi": sum(1 for r in records if r.get("doi")),
        "with_et_al": sum(1 for r in records if r.get("has_et_al")),
        "enriched": sum(1 for r in records if r.get("author_source", "").startswith(("crossref", "pubmed"))),
        "partial_et_al": sum(1 for r in records if r.get("author_source") == "listing_partial_et_al"),
        "failed_enrich": sum(1 for r in records if r.get("has_et_al") and r.get("author_source") == "listing_partial_et_al"),
    }
    (output_dir / "ingest_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory for publications.json",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip Crossref/PubMed enrichment for et al entries",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limit pages crawled (for testing)",
    )
    args = parser.parse_args()

    stats = ingest(
        args.output_dir,
        enrich_et_al=not args.no_enrich,
        max_pages=args.max_pages,
    )
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
