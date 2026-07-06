# ============================================================
# Temporal concentration analysis — annual and 5-year periods
# Captures authors entering/leaving over time
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(purrr)
  library(tibble)
})

source("scripts/R/utils.R")
source("scripts/R/metrics_helpers.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
do_compute_hhi <- !identical(config$metrics$compute_hhi, FALSE)
top_x_values <- config$metrics$top_x_values

papers_authors <- read_csv(
  file.path(dirs$processed, "papers_authors.csv"),
  show_col_types = FALSE
)

min_year <- min(papers_authors$pub_year, na.rm = TRUE)
max_year <- max(papers_authors$pub_year, na.rm = TRUE)

# Annual metrics (years with >= 5 papers)
year_counts <- papers_authors %>%
  filter(!is.na(pub_year)) %>%
  distinct(pmid, pub_year) %>%
  count(pub_year, name = "n_papers_year")

annual_years <- year_counts$pub_year[year_counts$n_papers_year >= 5]

annual_metrics <- map_dfr(annual_years, function(yr) {
  compute_period_metrics(
    papers_authors,
    top_x_values = top_x_values,
    period_label = as.character(yr),
    period_start = yr,
    period_end = yr,
    compute_hhi = do_compute_hhi
  ) %>% mutate(period_type = "annual")
})

# 5-year bin metrics (bins with >= 5 papers)
bin_starts <- seq(floor(min_year / 5) * 5, floor(max_year / 5) * 5, by = 5)

five_year_metrics <- map_dfr(bin_starts, function(start) {
  end <- start + 4
  label <- paste0(start, "-", end)
  m <- compute_period_metrics(
    papers_authors,
    top_x_values = top_x_values,
    period_label = label,
    period_start = start,
    period_end = end,
    compute_hhi = do_compute_hhi
  )
  if (nrow(m) == 0 || !"metric" %in% names(m)) return(tibble())
  n <- m %>% filter(metric == "n_papers") %>% pull(value)
  if (length(n) == 0 || n < 5) return(tibble())
  m %>% mutate(period_type = "five_year")
})

# Top-10 author career spans (entry/exit)
author_year_presence <- papers_authors %>%
  filter(!is.na(pub_year)) %>%
  distinct(author_id, pub_year) %>%
  group_by(author_id) %>%
  summarise(
    first_year = min(pub_year),
    last_year = max(pub_year),
    n_years_active = n_distinct(pub_year),
    .groups = "drop"
  )

top10 <- papers_authors %>%
  distinct(pmid, author_id) %>%
  count(author_id, name = "n_papers") %>%
  arrange(desc(n_papers)) %>%
  head(10) %>%
  pull(author_id)

author_careers <- author_year_presence %>%
  filter(author_id %in% top10) %>%
  left_join(
    papers_authors %>%
      distinct(pmid, author_id) %>%
      count(author_id, name = "n_papers_total"),
    by = "author_id"
  ) %>%
  arrange(desc(n_papers_total))

temporal_metrics <- bind_rows(annual_metrics, five_year_metrics)
write_csv(temporal_metrics, file.path(dirs$output, "temporal_metrics.csv"))
write_csv(author_careers, file.path(dirs$output, "top_author_careers.csv"))

saveRDS(
  list(temporal = temporal_metrics, careers = author_careers),
  file.path(dirs$output, "temporal_analysis.rds")
)

cat("\n=== Temporal Analysis ===\n")
cat("Annual periods:", n_distinct(annual_metrics$period), "\n")
cat("Five-year periods:", n_distinct(five_year_metrics$period), "\n")
hhi_annual <- annual_metrics %>% filter(metric == "hhi")
if (nrow(hhi_annual) > 0) {
  cat("HHI range (annual):",
      round(min(hhi_annual$value, na.rm = TRUE), 3), "-",
      round(max(hhi_annual$value, na.rm = TRUE), 3), "\n")
}
cat("\nTop author career spans:\n")
print(author_careers)
