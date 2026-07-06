---
paths:
  - "datasets/**/raw/**"
  - "scripts/R/**/*"
---

# PubMed Collection Protocol

**Standards for downloading and parsing PubMed citation collections.**

---

## Source Types

| Type | Example | Access Method |
|------|---------|---------------|
| My NCBI Collection | REGARDS collection `46426411` | Entrez API via `rentrez` |
| Saved search | TBD for future datasets | Entrez esearch + efetch |
| Manual PMID list | Fallback | Direct efetch by PMID |

---

## REGARDS Collection (First Dataset)

- **Collection ID:** `46426411`
- **URL:** https://www.ncbi.nlm.nih.gov/myncbi/browse/collection/46426411/
- **Expected count:** 911 papers (as of June 2026 — verify on fetch)
- **Config location:** `datasets/REGARDS/config.yaml`

---

## Download Protocol

### 1. Authentication

- Optional `NCBI_API_KEY` in `.Renviron` (gitignored) for higher rate limits
- Without key: max 3 requests/second
- With key: max 10 requests/second

### 2. Fetch Strategy

```r
# Preferred: rentrez package
library(rentrez)

# For My NCBI collections, export PMID list from collection page
# or use Entrez query if collection is linked to a saved search
# Then batch efetch:
entrez_fetch(db = "pubmed", id = pmid_list, rettype = "xml")
```

**Batch size:** 200 PMIDs per request (Entrez limit).

**Rate limiting:** `Sys.sleep(0.34)` between requests without API key; `Sys.sleep(0.11)` with key.

### 3. Raw Storage

Save to `datasets/{name}/raw/`:

| File | Contents |
|------|----------|
| `pubmed_manifest.csv` | PMID, fetch_date, fetch_status |
| `pubmed_records.xml` | Full XML response (gitignored if >1MB) |
| `fetch_log.txt` | Timestamped log of API calls and any errors |

### 4. Manifest Schema

| Column | Type | Description |
|--------|------|-------------|
| `pmid` | string | PubMed ID |
| `fetch_date` | datetime | ISO timestamp of fetch |
| `fetch_status` | string | "success", "error", "not_found" |
| `error_message` | string | Error details if failed (nullable) |

---

## Parsing Protocol

Extract from PubMed XML for each record:

| Field | XML Path | Required |
|-------|----------|----------|
| PMID | `MedlineCitation/PMID` | Yes |
| Title | `Article/ArticleTitle` | Yes |
| Pub Year | `Article/Journal/JournalIssue/PubDate/Year` | No (fallback to MedlineDate) |
| Authors | `AuthorList/Author` | Yes |
| Author Last Name | `Author/LastName` | Yes |
| Author Initials | `Author/Initials` | Yes |
| Affiliation | `Author/AffiliationInfo/Affiliation` | No |

**Author string format:** `{LastName} {Initials}` (e.g., "Howard G", "Howard VJ")

---

## Verification

After every fetch:

```
[ ] Manifest row count matches expected collection count (±documented exclusions)
[ ] All PMIDs return valid XML (no fetch_status = "error" without investigation)
[ ] Spot-check 5 random PMIDs against PubMed web page (title, author count)
[ ] No duplicate PMIDs in manifest
[ ] fetch_log.txt has no unexplained errors
[ ] pubmed_records.xml is well-formed XML
```

**If count mismatch:**
1. Compare manifest PMIDs to collection page PMID list
2. Document missing/extra PMIDs in dataset README
3. Do NOT proceed to metrics until reconciled

---

## Re-fetch Policy

- Re-fetch if collection updated (check collection page date)
- Re-fetch if >6 months since last fetch for active collections
- Always create new manifest; do not overwrite previous manifest (rename to `pubmed_manifest_YYYY-MM-DD.csv`)

---

## Known Limitations

- My NCBI collections require manual PMID export or web scraping for collection membership (Entrez has no direct "collection ID" API)
- Author names may vary across papers for the same person (handled by alias table)
- PubMed coverage is biomedical only — not suitable for all social science datasets
- Affiliation data is incomplete for older papers

---

## Alternative Sources (Future Datasets)

| Dataset | Likely Source | Notes |
|---------|---------------|-------|
| MIDUS | Web of Science / manual | May need different parser |
| WLS | Web of Science / manual | May need different parser |
| MESA | PubMed collection | Similar protocol |

Document source-specific deviations in each dataset's README.
