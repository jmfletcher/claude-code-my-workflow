# REGARDS — Authorship Monopoly Analysis

**Dataset:** REasons for Geographic And Racial Differences in Stroke (REGARDS)
**Source:** [PubMed collection 46426411](https://www.ncbi.nlm.nih.gov/myncbi/browse/collection/46426411/)
**Automated fetch:** Entrez grant query `"NS041588"[Grant Number]`
**Status:** Pipeline complete (2026-06-23)

---

## About REGARDS

REGARDS is a national longitudinal cohort study examining racial and regional disparities in stroke. The study enrolled 30,239 participants aged 45+ from the continental US between 2003–2007, with ongoing follow-up.

This analysis measures authorship concentration among papers citing the REGARDS study — who publishes using REGARDS data, and how concentrated is that authorship?

---

## Source Details

| Field | Value |
|-------|-------|
| Collection ID | 46426411 |
| Collection URL | https://www.ncbi.nlm.nih.gov/myncbi/browse/collection/46426411/ |
| Curated collection count | 911 papers (June 2026) |
| Automated fetch count | 894 PMIDs via grant NS041588 |
| Parsed papers | 893 (1 PMID with no extractable authors) |
| Last fetched | 2026-06-23 |

**Count reconciliation note:** My NCBI collections cannot be scraped programmatically without browser automation. The pipeline uses Entrez grant-number search as the automated source (894 papers, ~98% of curated collection). For an exact match to the 911-paper collection, export PMIDs manually from the collection page to `raw/pmid_list.csv` and re-run the pipeline.

---

## Results (2026-06-23)

| Metric | Value |
|--------|-------|
| N papers | 893 |
| N authors | 3,487 (after 18 alias merges) |
| HHI | 0.743 |
| Top-1 share | 38.6% (Judd SE) |
| Top-3 share | 74.9% |
| Top-5 share | 83.4% |
| Top-10 share | 89.8% |

**Top 3 authors (all merges applied):** Judd SE (345), Safford MM (306), Howard VJ (296)

**Interpretation:** Authorship is highly concentrated. After 18 confirmed alias merges from `alias_suggestions.csv`, Judd SE remains the top author (345 papers). Safford MM and Howard VJ rise with merges (306 and 296). Top 3 appear on ~75% of papers.

---

## Alias Merges Applied (18)

Built from reviewed `alias_suggestions.csv` via `Combine with?` column. Rows marked `Same? = Y` without a combine target were **not** merged (different individuals sharing a last name, e.g. Chen L vs Chen G).

| author_raw | → author_id |
|------------|-------------|
| Cherrington A | Cherrington AL |
| Clarke PJ | Clarke P |
| Durant R | Durant RW |
| Griffin RL | Griffin R |
| Howard V | Howard VJ |
| Judd S | Judd SE |
| Kennedy R | Kennedy RE |
| Kissela B | Kissela BM |
| Kleindorfer D | Kleindorfer DO |
| Limdi N | Limdi NA |
| Manly J | Manly JJ |
| McClellan WM | McClellan W |
| Muntner PM | Muntner P |
| Prineas R | Prineas RJ |
| Richman J | Richman JS |
| Safford M | Safford MM |
| Unverzagt F | Unverzagt FW |
| Wadley V | Wadley VG |

Re-run after alias edits: `Rscript datasets/REGARDS/scripts/run_reanalysis.R`

---

## Extended Analysis (2026-06-23)

### Temporal trends

Annual and 5-year HHI and top-3 shares are in `output/temporal_metrics.csv`. Key patterns:

- **Early period (2007–2010):** Very high concentration (annual HHI up to ~2.3 in small-N years). Top-3 often account for 100% of papers in a given year when N is small.
- **2015 onward:** HHI declines as paper volume grows and new authors enter; top-3 share stabilizes around 70–85%.
- **Career spans:** Core investigators (Howard G, Howard VJ, Safford MM) publish across 20+ years; Judd SE active 2010–2026; newer entrants (Irvin MR, Levitan EB) appear mid-period.

See figures: `concentration_annual_trend`, `concentration_five_year_trend`, `top_author_career_spans`.

### Domain clustering (k = 8, title + abstract TF-IDF)

| Domain (top terms) | N papers | HHI | Top-3 share |
|--------------------|----------|-----|-------------|
| Caregiving/family stress | 23 | 2.69 | 100% |
| Sepsis/infection | 31 | 2.53 | 100% |
| Cancer/mortality | 22 | 1.64 | 77% |
| Hypertension | 63 | 1.43 | 86% |
| Cognitive impairment | 88 | 1.09 | 81% |
| CHD/diabetes/mortality (main) | 664 | 0.79 | 75% |

**Interpretation:** Concentration is **much higher in niche domains** (caregiving, sepsis) than in the main cardiovascular/diabetes cluster. Overall HHI (0.74) masks domain-specific monopolies that would be invisible in the aggregate count.

See figures: `domain_hhi_comparison`, `domain_top3_comparison`, `domain_volume_by_year`.

**Note on HHI > 1:** With multi-author papers, author-level paper-shares sum to > 1, so HHI can exceed 1 (especially in small domains or early years). Top-x share remains bounded [0, 1].

---

## Alias Review

```
[x] 18 merges applied from reviewed alias_suggestions.csv
[ ] Additional merges if new PubMed variants appear
```

---

## Pipeline Status

```
[x] PubMed records downloaded (894 PMIDs)
[x] papers_authors.csv generated (893 papers, 10,198 author rows)
[x] alias_suggestions.csv flagged for review
[ ] author_aliases.csv reviewed by human
[x] monopoly_metrics.csv computed
[x] Figures generated (4 figures in output/figures/)
[x] Count reconciliation documented
```

---

## Re-run Pipeline

```bash
cd /path/to/Data-Monopolies
Rscript datasets/REGARDS/scripts/run_pipeline.R
```

To use exact collection PMIDs: export from My NCBI → save as `datasets/REGARDS/raw/pmid_list.csv` → re-run.
