# ============================================================
# Compute HHI and top-x authorship monopoly metrics
# Purpose: Calculate concentration measures per authorship-monopoly-metrics.md
# Inputs: papers_authors.csv (with author_id), config.yaml
# Outputs: monopoly_metrics.csv, author_rankings.csv
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(tibble)
})

source("scripts/R/utils.R")
source("scripts/R/metrics_helpers.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"
repo_root <- if (length(args) >= 2) args[2] else "."

config <- load_dataset_config(dataset_name, repo_root)
dirs <- get_dataset_dirs(dataset_name, repo_root)
papers_path <- file.path(dirs$processed, "papers_authors.csv")

if (!file.exists(papers_path)) {
  stop("papers_authors.csv not found.")
}

papers <- read_csv(papers_path, show_col_types = FALSE)
n_papers <- n_distinct(papers$pmid)

author_rankings <- papers %>%
  distinct(pmid, author_id) %>%
  count(author_id, name = "n_papers") %>%
  mutate(paper_share = n_papers / .env$n_papers) %>%
  arrange(desc(n_papers), author_id)

write_csv(author_rankings, file.path(dirs$output, "author_rankings.csv"))

# Overall metrics
top_x_values <- config$metrics$top_x_values
computed_date <- format(Sys.Date(), "%Y-%m-%d")
do_compute_hhi <- !identical(config$metrics$compute_hhi, FALSE)
compute_topx_by_year <- isTRUE(config$metrics$compute_topx_by_year)
min_papers_per_year <- config$metrics$min_papers_per_year %||% 10

`%||%` <- function(x, y) if (is.null(x)) y else x

hhi <- if (do_compute_hhi) compute_hhi(author_rankings, n_papers) else NA_real_

metrics <- tibble(
  dataset = dataset_name,
  metric = c("n_papers", "n_authors", if (do_compute_hhi) "hhi"),
  value = c(n_papers, nrow(author_rankings), if (do_compute_hhi) hhi),
  top_x = NA_integer_,
  year = NA_integer_,
  computed_date = computed_date
)

# Top-x shares
for (x in top_x_values) {
  n_at_x <- min(x, nrow(author_rankings))
  threshold_papers <- author_rankings$n_papers[n_at_x]
  top_authors <- author_rankings %>%
    filter(n_papers >= threshold_papers) %>%
    pull(author_id)

  topx <- compute_topx_share(papers, top_authors, n_papers)

  metrics <- bind_rows(
    metrics,
    tibble(
      dataset = dataset_name,
      metric = "top_x_share",
      value = topx,
      top_x = x,
      year = NA_integer_,
      computed_date = computed_date
    )
  )
}

# By-year metrics if enabled
if (isTRUE(config$metrics$compute_by_year)) {
  years <- papers %>%
    filter(!is.na(pub_year)) %>%
    distinct(pmid, pub_year) %>%
    count(pub_year, name = "n_papers_year") %>%
    filter(n_papers_year >= min_papers_per_year)

  for (i in seq_len(nrow(years))) {
    yr <- years$pub_year[i]
    n_yr <- years$n_papers_year[i]

    yr_authors <- papers %>%
      filter(pub_year == yr) %>%
      distinct(pmid, author_id) %>%
      count(author_id, name = "n_papers")

    if (do_compute_hhi) {
      hhi_yr <- compute_hhi(yr_authors, n_yr)
      metrics <- bind_rows(
        metrics,
        tibble(
          dataset = dataset_name,
          metric = "hhi",
          value = hhi_yr,
          top_x = NA_integer_,
          year = yr,
          computed_date = computed_date
        )
      )
    }

    if (compute_topx_by_year) {
      yr_rankings <- yr_authors %>% arrange(desc(n_papers), author_id)
      for (x in top_x_values) {
        top_authors <- get_top_authors(yr_rankings, x)
        topx_yr <- compute_topx_share(
          papers %>% filter(pub_year == yr),
          top_authors,
          n_yr
        )
        metrics <- bind_rows(
          metrics,
          tibble(
            dataset = dataset_name,
            metric = "top_x_share",
            value = topx_yr,
            top_x = x,
            year = yr,
            computed_date = computed_date
          )
        )
      }
    }
  }
}

write_csv(metrics, file.path(dirs$output, "monopoly_metrics.csv"))
saveRDS(list(metrics = metrics, rankings = author_rankings), file.path(dirs$output, "monopoly_results.rds"))

# QC checks
topx_vals <- metrics %>%
  filter(metric == "top_x_share", is.na(year)) %>%
  arrange(top_x) %>%
  pull(value)
monotonic <- all(diff(topx_vals) >= -1e-10)

cat("\n=== Metrics Summary ===\n")
cat("Papers:", n_papers, "\n")
cat("Authors:", nrow(author_rankings), "\n")
if (do_compute_hhi) cat("HHI:", round(hhi, 4), "\n")
for (x in top_x_values) {
  val <- metrics %>% filter(metric == "top_x_share", is.na(year), top_x == x) %>% pull(value)
  cat("Top-", x, " share:", round(val, 4), "\n", sep = "")
}
cat("Top-x monotonic:", monotonic, "\n")
cat("Output:", file.path(dirs$output, "monopoly_metrics.csv"), "\n")

if (do_compute_hhi && (hhi < 0 || hhi > 1)) warning("HHI outside [0,1]: ", hhi)
if (!monotonic) warning("Top-x shares not monotonic!")

# Print top 10 authors
cat("\nTop 10 authors:\n")
print(head(author_rankings, 10))
