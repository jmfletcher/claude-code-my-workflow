# ============================================================
# Generate publication-ready monopoly figures
# Purpose: Author rank-frequency, top-x bar chart, HHI by year, papers by year
# Inputs: monopoly_metrics.csv, author_rankings.csv, papers_authors.csv
# Outputs: datasets/{name}/output/figures/*.pdf + .png
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(scales)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"
repo_root <- if (length(args) >= 2) args[2] else "."

config <- load_dataset_config(dataset_name, repo_root)
dirs <- get_dataset_dirs(dataset_name, repo_root)
fig_dir <- dirs$figures
do_compute_hhi <- !identical(config$metrics$compute_hhi, FALSE)
compute_topx_by_year <- isTRUE(config$metrics$compute_topx_by_year)

metrics <- read_csv(file.path(dirs$output, "monopoly_metrics.csv"), show_col_types = FALSE)
rankings <- read_csv(file.path(dirs$output, "author_rankings.csv"), show_col_types = FALSE)
papers <- read_csv(file.path(dirs$processed, "papers_authors.csv"), show_col_types = FALSE)

n_papers <- metrics %>% filter(metric == "n_papers") %>% pull(value)
n_authors <- metrics %>% filter(metric == "n_authors") %>% pull(value)
hhi <- if (do_compute_hhi) {
  metrics %>% filter(metric == "hhi", is.na(year)) %>% pull(value)
} else {
  NA_real_
}
fetch_note <- config$source$collection_url

subtitle_base <- paste0(
  dataset_name, " (N = ", n_papers, " papers, ", n_authors, " authors)"
)

# 1. Author rank-frequency (Lorenz-style) ----
rankings_plot <- rankings %>%
  arrange(desc(n_papers)) %>%
  mutate(
    rank = row_number(),
    cum_papers = cumsum(n_papers),
    cum_share = cum_papers / sum(n_papers)
  )

p1 <- ggplot(rankings_plot, aes(x = rank, y = cum_share)) +
  geom_line(linewidth = 0.8, color = "#012169") +
  geom_abline(slope = 0, intercept = 0, linetype = "dashed", color = "#525252", alpha = 0.5) +
  scale_y_continuous(labels = percent_format(), limits = c(0, 1)) +
  labs(
    title = "Cumulative share of papers by author rank",
    subtitle = subtitle_base,
    x = "Author rank (by paper count)",
    y = "Cumulative share of papers"
  ) +
  theme_monopoly()

save_publication_figure(p1, "author_rank_frequency", fig_dir, width = 8, height = 5)

# 2. Top-x bar chart ----
topx_data <- metrics %>%
  filter(metric == "top_x_share", is.na(year)) %>%
  mutate(top_x = factor(top_x, levels = config$metrics$top_x_values))

p2 <- ggplot(topx_data, aes(x = top_x, y = value)) +
  geom_col(fill = "#012169", width = 0.6) +
  geom_text(aes(label = percent(value, accuracy = 0.1)), vjust = -0.5, size = 3.5) +
  scale_y_continuous(labels = percent_format(), limits = c(0, 1), expand = expansion(mult = c(0, 0.08))) +
  labs(
    title = "Share of papers co-authored by top-x authors",
    subtitle = subtitle_base,
    x = "Top-x authors",
    y = "Share of papers"
  ) +
  theme_monopoly()

save_publication_figure(p2, "top_x_shares", fig_dir, width = 7, height = 5)

# 3. HHI by year (optional) ----
hhi_year <- metrics %>%
  filter(metric == "hhi", !is.na(year)) %>%
  arrange(year)

if (do_compute_hhi && nrow(hhi_year) > 0) {
  p3 <- ggplot(hhi_year, aes(x = year, y = value)) +
    geom_line(linewidth = 0.8, color = "#012169") +
    geom_point(size = 2, color = "#012169") +
    labs(
      title = "Authorship concentration (HHI) over time",
      subtitle = paste0(subtitle_base, " — years with ≥10 papers"),
      x = "Publication year",
      y = "HHI"
    ) +
    theme_monopoly()

  save_publication_figure(p3, "hhi_by_year", fig_dir, width = 8, height = 5)
}

# 3b. Top-x share by year (optional) ----
topx_year <- metrics %>%
  filter(metric == "top_x_share", !is.na(year)) %>%
  mutate(top_x = factor(top_x, levels = config$metrics$top_x_values))

if (compute_topx_by_year && nrow(topx_year) > 0) {
  min_yr <- config$metrics$min_papers_per_year %||% 10
  p3b <- ggplot(topx_year, aes(x = year, y = value, color = top_x, group = top_x)) +
    geom_line(linewidth = 0.8) +
    geom_point(size = 2) +
    scale_y_continuous(labels = percent_format()) +
    scale_color_brewer(palette = "Dark2") +
    labs(
      title = "Top-x author share over time",
      subtitle = paste0(subtitle_base, " — years with ≥", min_yr, " papers"),
      x = "Publication year",
      y = "Share of papers",
      color = "Top-x"
    ) +
    theme_monopoly()

  save_publication_figure(p3b, "top_x_by_year", fig_dir, width = 9, height = 5)
}

# 4. Top 20 authors bar chart ----
top20 <- head(rankings, 20) %>%
  mutate(author_id = reorder(author_id, n_papers))

p4 <- ggplot(top20, aes(x = n_papers, y = author_id)) +
  geom_col(fill = "#012169") +
  labs(
    title = "Top 20 authors by paper count",
    subtitle = subtitle_base,
    x = "Number of papers",
    y = NULL
  ) +
  theme_monopoly()

save_publication_figure(p4, "top20_authors", fig_dir, width = 8, height = 7)

# 5. Papers by publication year ----
papers_by_year <- papers %>%
  filter(!is.na(pub_year)) %>%
  distinct(pmid, pub_year) %>%
  count(pub_year, name = "n_papers") %>%
  arrange(pub_year)

year_range <- if (nrow(papers_by_year) > 0) {
  paste0(min(papers_by_year$pub_year), "–", max(papers_by_year$pub_year))
} else {
  "N/A"
}

p5 <- ggplot(papers_by_year, aes(x = pub_year, y = n_papers)) +
  geom_col(fill = "#012169", width = 0.85) +
  scale_x_continuous(breaks = pretty_breaks(n = 12)) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = "Number of papers citing the dataset by publication year",
    subtitle = paste0(subtitle_base, " — ", year_range),
    x = "Publication year",
    y = "Number of papers"
  ) +
  theme_monopoly()

save_publication_figure(p5, "papers_by_year", fig_dir, width = 9, height = 5)

`%||%` <- function(x, y) if (is.null(x)) y else x

cat("\n=== Figures saved to:", fig_dir, "===\n")
cat("  author_rank_frequency.pdf/png\n")
cat("  top_x_shares.pdf/png\n")
if (do_compute_hhi && nrow(hhi_year) > 0) cat("  hhi_by_year.pdf/png\n")
if (compute_topx_by_year && nrow(topx_year) > 0) cat("  top_x_by_year.pdf/png\n")
cat("  top20_authors.pdf/png\n")
cat("  papers_by_year.pdf/png\n")
