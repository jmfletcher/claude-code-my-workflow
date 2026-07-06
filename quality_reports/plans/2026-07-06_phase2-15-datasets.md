# Phase 2 Plan — Add 15 NIH-Funded Clinical/Epi Datasets

**Date:** 2026-07-06
**Author:** Data Monopolies pipeline (Jason Fletcher, PI)
**Milestone frozen:** git tag `phase1-13datasets` (commit `0ffcfbc`)

---

## 1. Progress to date (Phase 1)

Phase 1 built a reusable authorship-concentration pipeline and applied it to 13
studies (15 metric sets incl. EdShare time splits). Pipeline: `raw/` → `processed/`
→ `output/`, shared code in `scripts/R/`, per-dataset config in `datasets/{name}/config.yaml`.

| Dataset | Source type | Papers | Top-1 | Top-3 | Top-10 |
|---------|-------------|-------:|------:|------:|-------:|
| REGARDS | PubMed collection | 893 | 38.6% | 74.9% | 89.8% |
| MIDUS | Study web DB (APA HTML) | 2,294 | 8.3% | 18.6% | 25.1% |
| MESA | NHLBI docx list | 1,877 | 16.7% | 29.5% | 59.6% |
| PROSPER | Project bibliography | 259 | 63.3% | 80.3% | 88.0% |
| NIH_AARP | PubMed collection | 459 | 42.5% | 54.7% | 79.7% |
| WLS | Zotero group library | 1,006 | 13.2% | 21.1% | 35.5% |
| FFCWS | Study web publications | 1,710 | 7.2% | 13.2% | 26.3% |
| ABCD | Study web publications | 1,963 | 6.2% | 7.8% | 23.2% |
| SHOW | REACH publications | 123 | 66.7% | 74.0% | 81.3% |
| ALSPAC | Bristol pub index (non-NIH) | 2,982 | 9.4% | 26.3% | 47.4% |
| CARDIA | Zenodo community | 1,364 | 31.8% | 55.1% | 74.9% |
| ARIC | Study web manuscripts | 3,410 | 19.9% | 48.2% | 71.6% |
| EdShare | Project bibliography | 989 | 2.7% | 5.0% | 13.7% |

**Reusable capabilities proven:** PubMed XML fetch/parse (`fetch_pubmed_collection.R`,
`parse_pubmed_xml.R`), grant-number PMID discovery (`fetch_collection_pmids.R`),
HTML/APA scraping (`fetch_midus_publications.R` pattern), alias build/apply,
HHI + top-x metrics, temporal + domain (TF-IDF k-means) analysis, publication figures.

**Key lessons carried forward:** (a) prefer sources that expose **PubMed IDs** so we
can reuse the robust XML→author pipeline instead of fragile citation-string parsing;
(b) author identity needs an alias-review pass (raw metrics understate concentration);
(c) `curl` via R beats Python SSL on this machine; (d) reconcile fetched-vs-expected counts.

---

## 2. Selection criteria (per user)

1. Used in the **clinical & epidemiological** literature.
2. **Likely NIH-funded** — confirmed as an explicit step (grant number recorded).
3. Ideally a **central website listing publications** stemming from the dataset.
4. We additionally run a **broad citation search** to estimate the central list's
   **coverage** (what fraction of the real literature the curated list captures).

Already-covered studies are excluded. ALSPAC (UK/Wellcome) is retained from Phase 1
but new additions are all NIH-funded.

---

## 3. The 15 datasets (funding + source verified via web, 2026-07-06)

Legend — **Access**: `pmid` = list exposes PubMed IDs (reuse XML pipeline);
`cite` = citation strings need parsing; `file` = downloadable bibliography file.

| # | Dataset | NIH funder (grant) | Central publications source | ~N listed | Access |
|---|---------|--------------------|-----------------------------|----------:|--------|
| 1 | HRS (Health & Retirement Study) | NIA (U01AG009740) | hrs.isr.umich.edu/publications (searchable bib) | 5,000+ | cite/pmid |
| 2 | WHI (Women's Health Initiative) | NHLBI | whi.org publications database | 2,583 | cite |
| 3 | Framingham Heart Study | NHLBI (75N92019D00031) | framinghamheartstudy.org/fhs-bibliography (by year, PMIDs) | thousands | pmid |
| 4 | ADNI (Alzheimer's Disease Neuroimaging) | NIA (U19AG024904) | adni.loni.usc.edu publications | ~5,500 | cite |
| 5 | Add Health | NICHD/NIA (P01HD31921) | addhealth.cpc.unc.edu/publications | 9,870 | cite |
| 6 | Nurses' Health Study (NHS/NHSII) | NCI/NHLBI (UM1CA186107 etc.) | nurseshealthstudy.org (**selected only**) | partial | cite |
| 7 | SWAN (Women's Health Across Nation) | NIA/NINR/ORWH | swanstudy.org/publications (downloadable list) | ~1,000 | file |
| 8 | Jackson Heart Study | NHLBI/NIMHD | jacksonheartstudy.org manuscript tracker | ~400 | cite |
| 9 | CHS (Cardiovascular Health Study) | NHLBI | chs-nhlbi.org/CurrentBibliography (file, n=2,315) | 2,315 | file |
| 10 | NHATS (Health & Aging Trends) | NIA (U01AG032947) | nhats.org/publications/search | 1,119 | cite |
| 11 | Sister Study | NIEHS | sisterstudy.niehs.nih.gov/English/articles.htm (+PDF, PMIDs) | ~1,000 | pmid |
| 12 | HCHS/SOL (Hispanic Community Health) | NHLBI/NIMHD | sites9.cscc.unc.edu/hchs/res-publications (table w/ PMIDs) | 500+ | pmid |
| 13 | Strong Heart Study | NHLBI | strongheartstudy.org (confirm exact pub page) | ~600 | tbd |
| 14 | BLSA (Baltimore Longitudinal Aging) | NIA (intramural) | blsa.nih.gov (confirm exact pub page) | ~800 | tbd |
| 15 | HPFS (Health Professionals Follow-up) | NCI (U01CA167552) | hsph.harvard.edu/hpfs (**selected only**) | partial | cite |

Datasets 13–15 have funding well-established but the exact scrapable publication
page will be confirmed in the first execution step for each (criterion #2/#3 gate).

**Monopoly-relevant note:** several of these (ADNI, WHI, JHS, Framingham) run formal
Publications & Presentations committees that must approve manuscripts before
submission — an institutional mechanism directly relevant to "data monopoly" framing.

---

## 4. Per-dataset workflow (reuses Phase 1 pipeline)

For each dataset:
1. **Confirm funding** — record grant number + funder in `config.yaml` (`source.funding`).
2. **Locate + fetch central list** — write/adapt a `fetch_{name}_publications.R`
   (or reuse PubMed pipeline when PMIDs are exposed). Save to `raw/`.
3. **Parse → `processed/papers_authors.csv`** — PMIDs → XML pipeline where possible;
   else APA/citation parser (MIDUS pattern).
4. **Coverage search** (see §5) → `output/coverage_estimate.csv`.
5. **Alias suggestions** → review pass → `apply_author_aliases.R`.
6. **Metrics + figures** — `compute_monopoly_metrics.R`, `plot_monopoly_figures.R`,
   temporal + domain analysis.
7. **Reconcile + document** — update `datasets/{name}/README.md`, CLAUDE.md state table.

## 5. Coverage methodology (the "likely coverage" comment)

For each dataset compute three counts and a coverage ratio:
- **N_central** — papers on the study's curated list.
- **N_search** — broad external count from two free sources:
  - **PubMed/Entrez**: `"{grant number}"[Grant Number]` OR `"{study name/acronym}"[tiab]`.
  - **OpenAlex** API: filter by funder/grant + title/abstract search on study name.
- **N_union / N_overlap** — de-duplicate central vs. search by DOI/PMID.
- **Coverage ≈ N_central / N_union**; report whether the central list appears
  comprehensive (>90%), selective (curated subset), or stale.

This is dataset-agnostic → build one helper `scripts/R/estimate_coverage.R` and call
it per dataset. Grant numbers already captured above feed the Entrez query directly.

## 6. Execution order (batched by ease → hardest)

- **Batch A (PMID/file sources — reuse robust pipeline):** HCHS/SOL, CHS, Sister,
  Framingham, NHATS. Validates coverage helper + XML reuse fastest.
- **Batch B (citation scrapers):** WHI, ADNI, SWAN, Jackson Heart, Add Health, HRS.
- **Batch C (confirm-then-build):** Strong Heart, BLSA, HPFS (+ NHS/HPFS "selected"
  lists lean heavily on the coverage search).

## 7. Risks & mitigations

- **Selective central lists (NHS, HPFS):** curated pages are not exhaustive → rely on
  coverage search; report N_central as a floor.
- **Very large lists (Add Health 9.8k, HRS 5k):** paginate politely (rate-limit),
  cache raw HTML, checkpoint.
- **Author disambiguation at scale:** auto-alias (same last name + first initial) then
  targeted manual review of top authors only.
- **Site structure drift:** each scraper validated on a 2–3 page sample first (MIDUS lesson).
- **Non-NIH surprises:** if funding can't be confirmed NIH, flag and substitute an alternate
  (candidates: PSID, MrOS, Bogalusa, Black Women's Health Study, Dunedin, NACC).

## 8. Definition of done (per dataset, quality gate ≥ 80)

Fetched count reconciled to source; `papers_authors.csv` populated; coverage estimate
recorded; metrics + figures generated; README + CLAUDE.md updated; committed.
