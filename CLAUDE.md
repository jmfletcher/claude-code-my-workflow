# CLAUDE.MD -- Data Monopolies Research Project

**Project:** Data Monopolies
**Institution:** University of Wisconsin–Madison
**Branch:** Data-Monopolies
**PI:** Jason Fletcher

---

## Core Principles

- **Plan first** — enter plan mode before non-trivial tasks; save plans to `quality_reports/plans/`
- **Verify after** — run scripts, reconcile counts, confirm outputs at the end of every task
- **Pipeline SSOT** — `raw/` → `processed/` → `output/`; never hand-edit metrics without rerunning scripts
- **Author aliases** — `author_aliases.csv` is authoritative for deduplication; document every merge
- **Quality gates** — nothing ships below 80/100
- **[LEARN] tags** — when corrected, save `[LEARN:category] wrong → right` to MEMORY.md
- **Bootstrap check-ins** — first 3 sessions: checkpoint after config, download QC, and first metrics (see `.claude/rules/bootstrap-checkins.md`)

---

## Research Goal

For each longitudinal/survey dataset, download all papers citing that dataset, extract all co-authors, and compute authorship concentration measures:

- **HHI** (Herfindahl-Hirschman Index) over author paper-share distribution
- **Top-x share:** fraction of all papers co-authored by the dataset's top *x* authors

**First dataset:** REGARDS via [PubMed collection 46426411](https://www.ncbi.nlm.nih.gov/myncbi/browse/collection/46426411/)

**Planned datasets:** MIDUS, Wisconsin Longitudinal Study, MESA, others

---

## Folder Structure

```
Data-Monopolies/
├── CLAUDE.MD                    # This file
├── .claude/                     # Rules, skills, agents, hooks
├── datasets/                    # One subfolder per dataset
│   ├── _template/               # Canonical structure for new datasets
│   └── REGARDS/                 # First dataset (in progress)
│       ├── config.yaml          # Collection URL, metadata, top-x values
│       ├── raw/                 # Downloaded PubMed records
│       ├── processed/           # papers_authors.csv, author_aliases.csv
│       ├── output/              # monopoly_metrics.csv, figures/
│       └── scripts/             # Dataset-specific orchestration
├── scripts/R/                   # Shared utilities (fetch, parse, compute)
├── output/                      # Cross-dataset comparisons (later)
├── quality_reports/             # Plans, specs, session logs
├── explorations/                # Research sandbox (see rules)
├── templates/                   # Session log, quality report templates
├── Slides/                      # Beamer (secondary — future paper/talk)
├── Quarto/                      # RevealJS (secondary — future paper/talk)
└── master_supporting_docs/      # Reference papers
```

---

## Commands

```bash
# Run REGARDS pipeline (once implemented)
Rscript datasets/REGARDS/scripts/run_pipeline.R

# Shared utilities
Rscript scripts/R/fetch_pubmed_collection.R --dataset REGARDS
Rscript scripts/R/compute_monopoly_metrics.R --dataset REGARDS

# R environment
R -e "renv::restore()"

# Quality score (legacy — slides)
python scripts/quality_score.py Quarto/file.qmd
```

---

## Metric Definitions (Summary)

See `.claude/rules/authorship-monopoly-metrics.md` for full definitions.

| Metric | Formula | Notes |
|--------|---------|-------|
| Author paper-share | \(s_i = \text{papers by author } i / N_{\text{papers}}\) | After alias merge |
| HHI | \(\sum_i s_i^2\) | Report raw; normalized optional |
| Top-x share | \(\#\{\text{papers with ≥1 of top-x authors}\} / N_{\text{papers}}\) | Each paper counted once |

---

## Quality Thresholds

| Score | Gate | Meaning |
|-------|------|---------|
| 80 | Commit | Good enough to save |
| 90 | PR | Ready for deployment |
| 95 | Excellence | Aspirational |

---

## Skills Quick Reference

| Command | What It Does |
|---------|-------------|
| `/data-monopoly [dataset]` | End-to-end citation download + monopoly metrics |
| `/data-analysis [dataset]` | General R analysis within dataset folder |
| `/review-r [file]` | R code quality review |
| `/lit-review [topic]` | Literature search + synthesis |
| `/research-ideation [topic]` | Research questions + strategies |
| `/commit [msg]` | Stage, commit, PR, merge |
| `/learn [skill-name]` | Extract discovery into persistent skill |
| `/context-status` | Show session health + context usage |
| `/deep-audit` | Repository-wide consistency audit |
| `/compile-latex [file]` | 3-pass XeLaTeX + bibtex (secondary) |
| `/deploy [LectureN]` | Render Quarto + sync to docs/ (secondary) |

---

## Author Identity Policy

1. Start with source author strings (PubMed, APA, or Vancouver format → `{LastName} {Initials}`)
2. Maintain `author_aliases.csv` per dataset as the dedup authority
3. **Default auto-merge:** same last name + same first initial → canonical ID with highest paper count
4. Manual aliases override auto-merges when needed; every entry requires a `notes` rationale
5. Never apply merges without recording them in `author_aliases.csv`

---

## Current Project State

| Dataset | Source | Status | Papers | Top-1 | Top-3 | Top-10 |
|---------|--------|--------|--------|-------|-------|--------|
| REGARDS | [PubMed 46426411](https://www.ncbi.nlm.nih.gov/myncbi/browse/collection/46426411/) | 18 aliases applied | 893 | 38.6% | 74.9% | 89.8% |
| MIDUS | [MIDUS pub database](https://midus.wisc.edu/pubdatabase.php) | 333 auto-aliases | 2,294 | 8.3% | 18.6% | 25.1% |
| MESA | [NHLBI docx list](https://tools.mesa-nhlbi.org/MESA_Files/publications/MESA_Published_Papers_Chronological_5-6-2026.docx) | 1,181 auto-aliases | 1,877 | 16.7% | 29.5% | 59.6% |
| PROSPER | [PPSI search + project biblio](https://drupal.ppsi.iastate.edu/publications?search=prosper&page=0) | 14 auto-aliases | 259 | 63.3% | 80.3% | 88.0% |
| NIH_AARP | [PubMed 62019178](https://pubmed.ncbi.nlm.nih.gov/collections/62019178/?sort=pubdate) | 92 auto-aliases | 459 | 42.5% | 54.7% | 79.7% |
| WLS | [Zotero group library](https://www.zotero.org/groups/5400572/wisconsinlongitudinalstudy/items/7DFUY4LF/library) | 128 auto-aliases | 1,006 | 13.2% | 21.1% | 35.5% |
| FFCWS | [FFCWS publications](https://ffcws.princeton.edu/publications) | 39 auto-aliases | 1,710 | 7.2% | 13.2% | 26.3% |
| ABCD | [ABCD research publications](https://abcdstudy.org/research-publications/) | 691 auto-aliases | 1,963 | 6.2% | 7.8% | 23.2% |
| SHOW | [REACH SHOW publications](https://reach.med.wisc.edu/research/#publications) | 36 auto-aliases | 123 | 66.7% | 74.0% | 81.3% |
| ALSPAC | [Bristol publications index](https://www.bristol.ac.uk/alspac/researchers/publications/) | 1,304 auto-aliases | 2,982 | 9.4% | 26.3% | 47.4% |
| CARDIA | [Zenodo cardia-cc community](https://zenodo.org/communities/cardia-cc/records) | 459 auto-aliases | 1,364 | 31.8% | 55.1% | 74.9% |
| ARIC | [ARIC published manuscripts](https://aric.cscc.unc.edu/aric9/publications/published_manuscripts) | 2,237 auto-aliases | 3,410 | 19.9% | 48.2% | 71.6% |
| EdShare | [EdSHARe bibliography](https://edshareproject.org/research-and-publications/bibliography) | 66 auto-aliases | 989 | 2.7% | 5.0% | 13.7% |
| EdShare (≤2014) | EdSHARe bibliography subset | 63 auto-aliases | 884 | 2.3% | 6.0% | 20.5% |
| EdShare (≥2015) | EdSHARe bibliography subset | 8 auto-aliases | 105 | 23.8% | 25.7% | 34.3% |
| HCHS/SOL | [HCHS/SOL publications](https://sites9.cscc.unc.edu/hchs/res-publications) | 296 auto-aliases; ~79% coverage | 642 | 56.4% | 79.0% | 91.0% |
| CHS | [CHS bibliography](https://chs-nhlbi.org/CurrentBibliography) | 1,757 auto-aliases; ~66% coverage | 1,866 | 35.6% | 58.2% | 71.2% |
| Framingham | [FHS bibliography](https://www.framinghamheartstudy.org/fhs-bibliography/) | 2,835 auto-aliases; ~72% coverage | 4,523 | 19.4% | 35.4% | 67.4% |
| Sister | [Sister Study articles](https://sisterstudy.niehs.nih.gov/English/articles.htm) | 130 auto-aliases; citation-only | 393 | 88.8% | 93.4% | 97.2% |
| NHATS | [NHATS publications](https://www.nhats.org/publications/search) | 218 auto-aliases; citation-only | 1,162 | 6.3% | 15.2% | 25.7% |
| HRS | [HRS publications](https://hrs.isr.umich.edu/publications) (PubMed name search) | 403-blocked; PubMed tiab | 4,652 | 4.1% | 9.0% | 14.7% |
| WHI | [WHI](https://www.whi.org/) (PubMed name search) | 403-blocked; PubMed tiab | 3,467 | 17.7% | 27.8% | 44.0% |
| Add Health | [Add Health publications](https://addhealth.cpc.unc.edu/publications/) (PubMed name search) | JS site; PubMed tiab | 2,664 | 4.2% | 9.9% | 16.8% |
| JHS | [Jackson Heart Study](https://www.jacksonheartstudy.org/) (PubMed name search) | JS site; PubMed tiab | 657 | 27.2% | 57.1% | 72.6% |
| SWAN | [SWAN](https://www.swanstudy.org/publications/) (PubMed name search) | site not scrapable; PubMed tiab | 707 | 22.9% | 52.8% | 75.5% |
| ADNI | [ADNI publications](https://adni.loni.usc.edu/news-publications/publications/) | 3,516 auto-aliases; scraped table | 5,332 | 2.7% | 6.7% | 15.3% |

---

## Key Rules (Read Before Working)

| Rule | Purpose |
|------|---------|
| `constitutional-governance.md` | Non-negotiable project principles |
| `dataset-pipeline-protocol.md` | File schemas, pipeline SSOT |
| `authorship-monopoly-metrics.md` | HHI and top-x definitions |
| `pubmed-collection-protocol.md` | PubMed download standards |
| `visualization-standards.md` | Publication-ready figures |
| `bootstrap-checkins.md` | Early-session checkpoint cadence |
| `plan-first-workflow.md` | When and how to plan |
| `orchestrator-protocol.md` | Contractor mode after approval |
