# ============================================================
# Aggregate authorship-concentration metrics across all datasets.
# Reads each datasets/*/output/monopoly_metrics.csv (+ coverage_estimate.csv)
# and writes output/cross_dataset_concentration.csv, sorted by Top-1 share.
# ============================================================

suppressPackageStartupMessages({
  library(readr); library(dplyr); library(tidyr); library(purrr); library(stringr)
})

source("scripts/R/utils.R")

ds_dirs <- list.dirs("datasets", recursive = FALSE)
ds_dirs <- ds_dirs[!grepl("_template|_archive", ds_dirs)]

read_one <- function(d) {
  mpath <- file.path(d, "output", "monopoly_metrics.csv")
  if (!file.exists(mpath)) return(NULL)
  m <- read_csv(mpath, show_col_types = FALSE)
  name <- basename(d)
  base_m <- m %>% filter(is.na(year))
  get_metric <- function(met) {
    v <- base_m$value[base_m$metric == met][1]
    suppressWarnings(as.numeric(v))
  }
  get_topx <- function(x) {
    v <- base_m$value[base_m$metric == "top_x_share" & base_m$top_x == x][1]
    suppressWarnings(as.numeric(v))
  }
  cov_path <- file.path(d, "output", "coverage_estimate.csv")
  cov_ratio <- NA_real_
  if (file.exists(cov_path)) {
    cov <- read_csv(cov_path, show_col_types = FALSE)
    cr <- cov$value[cov$metric == "coverage_ratio"]
    if (length(cr) > 0) cov_ratio <- suppressWarnings(as.numeric(cr[1]))
  }
  year_min <- NA_integer_
  year_max <- NA_integer_
  year_span <- NA_integer_
  n_pub_years <- NA_integer_
  papers_per_year <- NA_real_
  pa_path <- file.path(d, "processed", "papers_authors.csv")
  if (file.exists(pa_path)) {
    pa <- read_csv(pa_path, show_col_types = FALSE)
    paper_years <- pa %>%
      distinct(pmid, pub_year) %>%
      filter(!is.na(pub_year))
    if (nrow(paper_years) > 0) {
      year_min <- min(paper_years$pub_year)
      year_max <- max(paper_years$pub_year)
      year_span <- year_max - year_min + 1L
      n_pub_years <- n_distinct(paper_years$pub_year)
      papers_per_year <- nrow(paper_years) / year_span
    }
  }
  tibble(
    dataset = name,
    n_papers = as.integer(get_metric("n_papers")),
    n_authors = as.integer(get_metric("n_authors")),
    hhi = round(get_metric("hhi"), 4),
    top1 = round(get_topx(1), 4),
    top3 = round(get_topx(3), 4),
    top5 = round(get_topx(5), 4),
    top10 = round(get_topx(10), 4),
    coverage_ratio = if (is.na(cov_ratio)) NA_real_ else round(cov_ratio, 4),
    year_min = year_min,
    year_max = year_max,
    year_span = year_span,
    n_pub_years = n_pub_years,
    papers_per_year = if (is.na(papers_per_year)) NA_real_ else round(papers_per_year, 2)
  )
}

summary_tbl <- map_dfr(ds_dirs, read_one) %>%
  filter(!is.na(n_papers)) %>%
  arrange(desc(top1))

out_path <- "output/cross_dataset_concentration.csv"
dir.create("output", showWarnings = FALSE)
write_csv(summary_tbl, out_path)

cat("\n=== Cross-dataset concentration (", nrow(summary_tbl), "datasets ) ===\n", sep = "")
print(summary_tbl, n = nrow(summary_tbl))
cat("\nOutput:", out_path, "\n")
