# Data Monopolies — Progress Report & Next Steps

**Date:** 2026-07-07  
**PI:** Jason Fletcher (UW–Madison)  
**Branch:** Data-Monopolies  
**Milestones:** `phase1-13datasets` (`0ffcfbc`) → Phase 2 complete (`8bf91c0` + uncommitted follow-ons)

---

## Executive summary

The project has a **production-ready authorship-concentration pipeline** applied to **31 metric sets** spanning **28 longitudinal/survey cohorts** (52,463 papers in `output/cross_dataset_concentration.csv`). Phase 2 added 15 NIH-funded clinical/epi datasets on schedule. Cross-dataset comparison figures are built and publication-oriented.

**Headline empirical pattern:** authorship concentration correlates with **data-access regime**. Gatekept or single-center cohorts (Sister, SHOW, PROSPER, Strong Heart, HCHS/SOL, BLSA) show top-1 shares of 40–89%; public-use/open resources (HRS, Add Health, NHATS, ADNI, WLS) cluster below 15%.

**Since Phase 2 wrap-up (uncommitted):** EdShare post-2017 journal subset (54 papers, top-1 33%), cross-figure EdShare filtering, WLS top-25 author figure, EdShare phase-1 archive.

---

## 1. Pipeline status

| Component | Status | Location |
|-----------|--------|----------|
| Fetch / ingest | ✅ Multiple source adapters | `scripts/R/fetch_*.R`, `scripts/edshare/`, `scripts/run_pubmed_dataset.sh` |
| Author parsing | ✅ PubMed XML + citation parsers | `parse_pubmed_xml.R`, dataset-specific fetchers |
| Alias merge | ✅ Auto + manual | `apply_author_aliases.R`, `author_aliases.csv` per dataset |
| Metrics (HHI, top-x) | ✅ Annual + overall | `compute_monopoly_metrics.R` |
| Temporal analysis | ✅ By year + careers | `analyze_temporal_concentration.R` |
| Domain analysis | ✅ TF-IDF k-means (where run) | `analyze_domain_concentration.R` |
| Figures (per dataset) | ✅ Standard suite + configurable top-N | `plot_monopoly_figures.R` |
| Cross-dataset summary | ✅ CSV + 4 figures | `build_cross_dataset_summary.R`, `plot_cross_dataset_*.R` |
| Coverage estimation | ⚠️ Partial (12/31 sets) | `estimate_coverage.R` |

**Pipeline contract:** `raw/` → `processed/` → `output/`; metrics are SSOT from scripts, not hand-edited.

---

## 2. Dataset inventory

### 2.1 All metric sets (31)

Sorted by top-1 share (from `output/cross_dataset_concentration.csv`):

| Rank | Dataset | Papers | Authors | Top-1 | Top-3 | Top-10 | Coverage |
|-----:|---------|-------:|--------:|------:|------:|-------:|---------:|
| 1 | Sister | 393 | 1,553 | 88.8% | 93.4% | 97.2% | — |
| 2 | SHOW | 123 | 339 | 66.7% | 74.0% | 81.3% | — |
| 3 | PROSPER | 259 | 193 | 63.3% | 80.3% | 88.0% | — |
| 4 | Strong Heart | 371 | 780 | 58.8% | 67.7% | 90.0% | 1.00 |
| 5 | HCHS/SOL | 642 | 2,494 | 56.4% | 79.0% | 91.0% | 0.79 |
| 6 | BLSA | 821 | 1,578 | 47.6% | 65.8% | 77.5% | 1.00 |
| 7 | NIH_AARP | 459 | 1,217 | 42.5% | 54.7% | 79.7% | — |
| 8 | HPFS | 1,384 | 1,933 | 41.6% | 68.9% | 77.7% | 1.00 |
| 9 | REGARDS | 893 | 3,487 | 38.6% | 74.9% | 89.8% | — |
| 10 | CHS | 1,866 | 10,052 | 35.6% | 58.2% | 71.2% | 0.66 |
| 11 | **EdShare (≥2017 journals)** | 54 | 94 | 33.3% | 33.3% | 40.7% | — |
| 12 | CARDIA | 1,364 | 3,215 | 31.8% | 55.1% | 74.9% | — |
| 13 | JHS | 657 | 2,663 | 27.2% | 57.1% | 72.6% | 1.00 |
| 14 | NHS | 3,450 | 4,102 | 24.7% | 41.9% | 64.2% | 1.00 |
| 15 | EdShare (≥2015) | 105 | 174 | 23.8% | 25.7% | 34.3% | — |
| 16 | SWAN | 707 | 943 | 22.9% | 52.8% | 75.5% | 1.00 |
| 17 | ARIC | 3,410 | 12,681 | 19.9% | 48.2% | 71.6% | — |
| 18 | Framingham | 4,523 | 16,127 | 19.4% | 35.4% | 67.4% | 0.72 |
| 19 | WHI | 3,467 | 6,919 | 17.7% | 27.8% | 44.0% | 1.00 |
| 20 | MESA | 1,877 | 7,234 | 16.7% | 29.5% | 59.6% | — |
| 21 | **WLS** | 1,006 | 1,650 | 13.2% | 21.1% | 35.5% | — |
| 22 | ALSPAC | 2,982 | 9,810 | 9.4% | 26.3% | 47.4% | — |
| 23 | MIDUS | 2,294 | 3,521 | 8.3% | 18.6% | 25.1% | — |
| 24 | FFCWS | 1,710 | 1,771 | 7.2% | 13.2% | 26.3% | — |
| 25 | NHATS | 1,162 | 2,006 | 6.3% | 15.2% | 25.7% | 1.00 |
| 26 | ABCD | 1,963 | 5,957 | 6.2% | 7.8% | 23.2% | — |
| 27 | Add Health | 2,664 | 4,012 | 4.2% | 9.9% | 16.8% | 1.00 |
| 28 | HRS | 4,652 | 6,916 | 4.1% | 9.0% | 14.7% | 1.00 |
| 29 | EdShare (full) | 989 | 1,059 | 2.7% | 5.0% | 13.7% | — |
| 30 | ADNI | 5,332 | 13,596 | 2.7% | 6.7% | 15.3% | 1.00 |
| 31 | EdShare (≤2014) | 884 | 904 | 2.3% | 6.0% | 20.5% | — |

**Figure-visible subset:** 28 datasets (excludes EdShare full, pre-2015, post-2015; keeps EdShare post-2017 only). Total papers in figures: **50,485**.

### 2.2 Concentration tiers (figure-visible, n=28)

| Tier | Top-1 range | Count | Examples |
|------|-------------|------:|----------|
| High | ≥ 40% | 8 | Sister, SHOW, PROSPER, Strong Heart, HCHS/SOL, BLSA, NIH_AARP, HPFS |
| Moderate | 15–40% | 11 | REGARDS, CHS, EdShare post-2017, CARDIA, JHS, NHS, SWAN, ARIC, Framingham, WHI, MESA |
| Low | < 15% | 9 | WLS, ALSPAC, MIDUS, FFCWS, NHATS, ABCD, Add Health, HRS, ADNI |

### 2.3 Source acquisition modes

| Mode | Datasets | Caveat |
|------|----------|--------|
| Curated list (scrape/file/PubMed collection) | REGARDS, MIDUS, MESA, PROSPER, NIH_AARP, WLS, FFCWS, ABCD, SHOW, ALSPAC, CARDIA, ARIC, EdShare, HCHS/SOL, CHS, Framingham, Sister, NHATS, ADNI | Coverage varies; CHS/Framingham/HCHS/SOL have measured ratios 66–79% |
| PubMed title/abstract name search | HRS, WHI, Add Health, JHS, SWAN, NHS, HPFS, Strong Heart, BLSA | Coverage = 1.0 by construction; recall depends on query |
| Curated citation subset | EdShare post-2017 | 54 journal articles from bibliography search listing |

---

## 3. Deliverables completed

### Phase 1 (tag `phase1-13datasets`)
- 13 cohorts, reusable R pipeline, alias policy, per-dataset figures

### Phase 2 (commits `4e1da93` → `8bf91c0`)
- 15 NIH-funded datasets in three batches (A/B/C)
- `estimate_coverage.R`, vectorized `parse_pubmed_xml.R`, `run_pubmed_dataset.sh`
- `output/cross_dataset_concentration.csv`
- Cross-dataset figures: top-3, top-10, total publications bar chart, acronym legend

### Post–Phase 2 (uncommitted, 2026-07-06 evening)
- **EdShare post-2017:** new dataset from curated bibliography listing; phase-1 archive at `datasets/_archive/EdShare_phase1_2026-07-06/`
- **Cross-figure EdShare filter:** only `EdShare_post2017` in main comparison plots (`filter_cross_dataset_figure_datasets()`)
- **WLS figures:** configurable `top_author_rank_figures`; top-20 + top-25 bar charts
- **Citation-list parser:** extended `fetch_edshare_publications.R` for filtered bibliography ingest

### Key outputs on disk

```
output/cross_dataset_concentration.csv
output/figures/cross_dataset_concentration_top3.{pdf,png}
output/figures/cross_dataset_concentration_top10.{pdf,png}
output/figures/cross_dataset_total_publications.{pdf,png}
output/figures/dataset_acronym_legend.{pdf,png}
datasets/{name}/output/monopoly_metrics.csv          # 31 sets
datasets/{name}/output/figures/                      # per-dataset
```

---

## 4. Known limitations & technical debt

| Issue | Impact | Priority |
|-------|--------|----------|
| **19 datasets lack coverage estimates** | Cannot distinguish curation gaps from true concentration | High |
| **PubMed tiab sources** (8 sets) | No independent validation of paper universe | High for paper |
| **Author alias quality** | Auto-merge may under- or over-merge; concentration sensitive | Medium |
| **EdShare time splits** | 4 EdShare variants; only post-2017 in figures — needs narrative clarity | Low |
| **Uncommitted work** | 4 commits ahead + local edits not on remote | Medium |
| **No manuscript/slide draft** | Empirical work not yet written up | High for dissemination |
| **MESA HHI missing** | `monopoly_metrics.csv` has NA HHI | Low |
| **Domain analysis not uniform** | Not all datasets have temporal/domain extensions | Low |

---

## 5. Git status

```
Branch: Data-Monopolies (ahead of origin by 4 commits)
Last commit: 8bf91c0 — cross-dataset figures + acronym legend
Uncommitted: EdShare post-2017, WLS top-25, figure filters, CLAUDE.md, cross-dataset CSV refresh
```

**Recommended:** single commit for post-Phase-2 follow-ons before starting Phase 3.

---

## 6. Plan — next steps

### Phase 3A: Stabilize & commit (1 session)

**Goal:** Clean repo state; all recent work tracked.

- [ ] Commit uncommitted work (EdShare post-2017, figure filters, WLS top-25, archive README)
- [ ] Re-run `build_cross_dataset_summary.R` + all cross-dataset figure scripts; verify 28 dots
- [ ] Tag milestone: `phase2-complete` or `phase2-plus-edshare`
- [ ] Update `2026-07-06_phase2-15-datasets.md` completion section with post-Phase-2 items

### Phase 3B: Coverage & data quality (2–3 sessions)

**Goal:** Strengthen empirical claims before writing.

- [ ] Run `estimate_coverage.R` on Phase 1 datasets missing coverage (REGARDS, MIDUS, MESA, WLS, etc.)
- [ ] For PubMed tiab datasets: document query strings in each `config.yaml`; run sensitivity check (alternate query, ±5% paper count)
- [ ] **Alias audit pass** on high-concentration datasets (top 10 authors): Sister, SHOW, PROSPER, Strong Heart, REGARDS
- [ ] **Alias audit pass** on low-concentration datasets: HRS, ADNI, WLS (confirm Hauser RM merge is correct)
- [ ] Fix MESA HHI if trivial; reconcile any count mismatches vs. source pages

### Phase 3C: Analytic extensions (2–4 sessions)

**Goal:** Move from descriptive tables to publishable analysis.

1. **Access-regime coding**
   - Code each dataset: `open` / `restricted` / `committee-gated` / `intramural`
   - Merge with concentration metrics → regression or stratified comparison figure

2. **Temporal trends**
   - Pool annual HHI / top-3 across datasets where `compute_by_year: yes`
   - Test: does concentration rise as cohorts mature?

3. **EdShare natural experiment**
   - Compare full (2.7%), ≤2014 (2.3%), ≥2015 (23.8%), ≥2017 journals (33.3%)
   - Frame as shift from methods papers to HS&B midlife core team

4. **Cross-dataset robustness**
   - Papers-per-year vs. concentration (already in scatter plots — add fitted line + annotation)
   - Sensitivity: top-1 vs. top-5, normalized HHI

### Phase 3D: Writing & dissemination (ongoing)

**Goal:** First paper or talk draft.

- [ ] Outline: *Authorship concentration in longitudinal social and health data*
- [ ] Figures for paper: cross-dataset scatter (top-3, top-10), WLS top-25 exemplar of dispersed authorship, Sister/SHOW exemplars of concentration
- [ ] Methods section: pipeline SSOT, alias policy, coverage methodology
- [ ] Limitations section: tiab recall, alias uncertainty, curated-list selection

**Candidate additional datasets** (if expanding sample): PSID, MrOS, Bogalusa, NACC, Black Women's Health Study — only if they strengthen the access-regime story.

### Phase 3E: Infrastructure (as needed)

- [ ] Add `top_author_rank_figures` to `_template/config.yaml`
- [ ] Document `filter_cross_dataset_figure_datasets()` in visualization standards rule
- [ ] `.gitignore` for `Rplots.pdf`
- [ ] Optional: single `scripts/run_all_cross_figures.R` orchestrator

---

## 7. Suggested immediate priorities (this week)

| Priority | Task | Effort |
|----------|------|--------|
| 1 | **Commit** post-Phase-2 work | 30 min |
| 2 | **Alias review** on Sister + WLS (bookend cases) | 2 hr |
| 3 | **Access-regime coding table** → new column in cross-dataset CSV | 2 hr |
| 4 | **Paper outline** + figure shortlist | 2 hr |
| 5 | Coverage backfill for REGARDS, WLS, MIDUS | 3 hr |

---

## 8. Success criteria for “analysis-ready”

- [ ] All figure-visible datasets have documented source + query/list URL in README
- [ ] Coverage recorded or explicitly marked N/A with rationale
- [ ] Top-author alias spot-check on ≥5 high- and ≥5 low-concentration datasets
- [ ] Cross-dataset figures regenerated from committed SSOT
- [ ] One-page empirical summary (this report §2.2) validated against fresh pipeline run
- [ ] Paper outline approved by PI

---

*Generated from pipeline outputs and git state on 2026-07-07. Reconcile by re-running `Rscript scripts/R/build_cross_dataset_summary.R` before citing exact counts.*
