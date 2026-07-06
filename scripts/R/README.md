# Shared R Utilities

Reusable functions for the Data Monopolies pipeline. Dataset-specific orchestration lives in `datasets/{name}/scripts/`.

## Planned Functions

| Script | Purpose |
|--------|---------|
| `fetch_pubmed_collection.R` | Download PubMed records by PMID list |
| `parse_pubmed_xml.R` | Extract authors, titles, years from PubMed XML |
| `apply_author_aliases.R` | Merge authors via alias table |
| `compute_hhi.R` | Compute Herfindahl-Hirschman Index |
| `compute_topx_share.R` | Compute top-x author paper shares |
| `plot_author_rank_frequency.R` | Lorenz-style rank-frequency figure |
| `plot_topx_shares.R` | Bar chart of top-x shares |
| `plot_hhi_by_year.R` | Temporal HHI trend |

## Usage

```r
# From repo root
source("scripts/R/compute_hhi.R")
source("scripts/R/compute_topx_share.R")
```

Or via dataset pipeline:

```bash
Rscript datasets/REGARDS/scripts/run_pipeline.R
```

## Conventions

See `.claude/rules/r-code-conventions.md` for coding standards.
