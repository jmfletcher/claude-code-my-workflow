# ABCD — Authorship Concentration Analysis

**Dataset:** Adolescent Brain Cognitive Development (ABCD) Study
**Source:** [ABCD research publications](https://abcdstudy.org/research-publications/)
**Parsed publications:** 1,963
**Status:** Pipeline complete (June 2026)

---

## About ABCD

The ABCD Study® is a nationally representative longitudinal study of brain development and child health from late childhood through adolescence (~11,800 youth). This analysis measures authorship concentration among peer-reviewed publications listed on the study website.

---

## Source Details

| Field | Value |
|-------|-------|
| Source type | WordPress HTML table (paginated, Cloudflare-protected) |
| Ingest script | `scripts/abcd/ingest_publications.py` (curl_cffi + Chrome impersonation) |
| Parse script | `scripts/R/fetch_abcd_publications.R` |
| Parsed publications | 1,963 (20 pages × ~100 records) |
| With PubMed ID | 1,897 |
| Year range | 2017–2026 |
| Last fetched | 2026-06-24 |

Plain `curl` returns 403; ingestion requires `.venv-ffcws` with `curl_cffi` (shared with FFCWS ingest).

---

## Pipeline

```bash
# Full pipeline (ingest ~40s + metrics + figures)
Rscript datasets/ABCD/scripts/run_pipeline.R
```

Re-ingest only:

```bash
.venv-ffcws/bin/python scripts/abcd/ingest_publications.py
Rscript scripts/R/fetch_abcd_publications.R ABCD
```

---

## Metrics (after initial-rule alias merge)

| Metric | Value |
|--------|-------|
| Papers | 1,963 |
| Unique authors | 5,957 (691 auto-aliases) |
| HHI | 0.055 |
| Top-1 share | **6.2%** (Baker F C) |
| Top-3 share | **7.8%** |
| Top-5 share | 12.1% |
| Top-10 share | 23.2% |
| Top-20 share | 28.9% |

**Top authors:** Baker F C (122), Nagata J M (121), Ganson K T (97), Barch D M (91), Testa A (81).

**Comparison:** ABCD is among the least concentrated datasets — top-1 (6%) below FFCWS (7%) and MIDUS (8%), reflecting broad multi-site neuroimaging consortium authorship.

Figures: `output/figures/`.

---

## Raw Files

| File | Description |
|------|-------------|
| `raw/publications.json` | Full structured records from ingest |
| `raw/publications.csv` | Flat export |
| `raw/summary.json` | Scrape metadata |
| `raw/abcd_publications.csv` | Parsed pipeline input |
