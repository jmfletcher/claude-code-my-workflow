# ============================================================
# Figures for temporal and domain concentration analyses
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(scales)
  library(stringr)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
fig_dir <- dirs$figures
do_compute_hhi <- !identical(config$metrics$compute_hhi, FALSE)

temporal <- read_csv(file.path(dirs$output, "temporal_metrics.csv"), show_col_types = FALSE)
careers <- read_csv(file.path(dirs$output, "top_author_careers.csv"), show_col_types = FALSE)

n_papers <- temporal %>%
  filter(metric == "n_papers", period_type == "annual") %>%
  pull(value) %>%
  max(na.rm = TRUE)

subtitle_n <- paste0(dataset_name, " (peak year ~", n_papers, " papers)")

# --- 1. Annual concentration trend ---
annual <- temporal %>%
  filter(period_type == "annual") %>%
  mutate(year = as.integer(period))

annual_metrics <- if (do_compute_hhi) c("hhi", "top_x_share") else "top_x_share"
annual_plot <- annual %>%
  filter(metric %in% annual_metrics, is.na(top_x) | top_x == 3) %>%
  mutate(
    metric_label = if_else(metric == "hhi", "HHI", "Top-3 share")
  )

if (nrow(annual_plot) > 0) {
  if (do_compute_hhi) {
    p_annual <- ggplot(annual_plot, aes(x = year, y = value, color = metric_label)) +
      geom_line(linewidth = 0.8) +
      geom_point(size = 2) +
      facet_wrap(~metric_label, scales = "free_y", ncol = 1) +
      scale_color_manual(values = c("HHI" = "#012169", "Top-3 share" = "#b91c1c")) +
      labs(
        title = "Authorship concentration over time (annual)",
        subtitle = paste0(subtitle_n, " | Years with ≥5 papers"),
        x = "Publication year",
        y = "Value",
        color = NULL
      ) +
      theme_monopoly() +
      theme(legend.position = "none")
  } else {
    p_annual <- ggplot(annual_plot, aes(x = year, y = value)) +
      geom_line(linewidth = 0.8, color = "#b91c1c") +
      geom_point(size = 2, color = "#b91c1c") +
      scale_y_continuous(labels = percent_format()) +
      labs(
        title = "Top-3 author share over time (annual)",
        subtitle = paste0(subtitle_n, " | Years with ≥5 papers"),
        x = "Publication year",
        y = "Top-3 share"
      ) +
      theme_monopoly()
  }

  save_publication_figure(p_annual, "concentration_annual_trend", fig_dir, width = 9, height = 5)
}

# --- 2. Five-year bin concentration ---
five <- temporal %>%
  filter(period_type == "five_year")

five_wide <- five %>%
  filter(metric %in% annual_metrics, is.na(top_x) | top_x == 3) %>%
  mutate(
    metric_label = if_else(metric == "hhi", "HHI", "Top-3 share"),
    period = factor(period, levels = unique(period))
  )

if (nrow(five_wide) > 0) {
  if (do_compute_hhi) {
    p_five <- ggplot(five_wide, aes(x = period, y = value, color = metric_label, group = metric_label)) +
      geom_line(linewidth = 0.8) +
      geom_point(size = 2.5) +
      facet_wrap(~metric_label, scales = "free_y", ncol = 1) +
      scale_color_manual(values = c("HHI" = "#012169", "Top-3 share" = "#b91c1c")) +
      labs(
        title = "Authorship concentration by 5-year period",
        subtitle = subtitle_n,
        x = "Period",
        y = "Value",
        color = NULL
      ) +
      theme_monopoly() +
      theme(legend.position = "none", axis.text.x = element_text(angle = 45, hjust = 1))
  } else {
    p_five <- ggplot(five_wide, aes(x = period, y = value, group = 1)) +
      geom_line(linewidth = 0.8, color = "#b91c1c") +
      geom_point(size = 2.5, color = "#b91c1c") +
      scale_y_continuous(labels = percent_format()) +
      labs(
        title = "Top-3 author share by 5-year period",
        subtitle = subtitle_n,
        x = "Period",
        y = "Top-3 share"
      ) +
      theme_monopoly() +
      theme(axis.text.x = element_text(angle = 45, hjust = 1))
  }

  save_publication_figure(p_five, "concentration_five_year_trend", fig_dir, width = 9, height = 5)
}

# --- 3. Top author career spans (Gantt-style) ---
careers_plot <- careers %>%
  mutate(author_id = reorder(author_id, n_papers_total))

p_careers <- ggplot(careers_plot, aes(x = first_year, xend = last_year, y = author_id, yend = author_id)) +
  geom_segment(linewidth = 3, color = "#012169", alpha = 0.7) +
  geom_point(aes(x = first_year), size = 2, color = "#15803d") +
  geom_point(aes(x = last_year), size = 2, color = "#b91c1c") +
  labs(
    title = paste("Publishing span of top 10", dataset_name, "authors"),
    subtitle = "Green = first paper; red = most recent paper in sample",
    x = "Year",
    y = NULL
  ) +
  theme_monopoly()

save_publication_figure(p_careers, "top_author_career_spans", fig_dir, width = 9, height = 6)

# --- 4–6. Domain figures (optional) ---
domain_summary_path <- file.path(dirs$output, "domain_summary.csv")
papers_domains_path <- file.path(dirs$processed, "papers_domains.csv")

if (file.exists(domain_summary_path) && file.exists(papers_domains_path)) {
  domain_summary <- read_csv(domain_summary_path, show_col_types = FALSE)
  papers_domains <- read_csv(papers_domains_path, show_col_types = FALSE)

  domain_plot <- domain_summary %>%
    mutate(domain_short = str_trunc(domain, 45)) %>%
    arrange(desc(hhi)) %>%
    mutate(domain_short = factor(domain_short, levels = domain_short))

  if (do_compute_hhi) {
    p_domain_hhi <- ggplot(domain_plot, aes(x = hhi, y = domain_short)) +
      geom_col(fill = "#012169") +
      geom_text(aes(label = paste0("n=", n_papers)), hjust = -0.1, size = 3) +
      scale_x_continuous(limits = c(0, max(domain_plot$hhi) * 1.15)) +
      labs(
        title = "Authorship concentration by research domain",
        subtitle = "Domains from k-means clustering of titles + abstracts (k = 8)",
        x = "HHI",
        y = NULL
      ) +
      theme_monopoly()

    save_publication_figure(p_domain_hhi, "domain_hhi_comparison", fig_dir, width = 10, height = 7)
  }

  p_domain_top3 <- ggplot(domain_plot, aes(x = top3_share, y = domain_short)) +
  geom_col(fill = "#012169") +
  scale_x_continuous(labels = percent_format(), limits = c(0, 1)) +
  labs(
    title = "Top-3 author share by research domain",
    subtitle = "Share of domain papers co-authored by domain's top 3 authors",
    x = "Top-3 share",
    y = NULL
  ) +
  theme_monopoly()

  save_publication_figure(p_domain_top3, "domain_top3_comparison", fig_dir, width = 10, height = 7)

  domain_time <- papers_domains %>%
    filter(!is.na(pub_year)) %>%
    mutate(domain_short = str_trunc(domain, 40)) %>%
    count(pub_year, domain_short)

  p_domain_time <- ggplot(domain_time, aes(x = pub_year, y = n, color = domain_short)) +
    geom_line(linewidth = 0.7) +
    geom_point(size = 1.5) +
    labs(
      title = "Publication volume by domain over time",
      subtitle = "Based on title + abstract clustering",
      x = "Year",
      y = "Number of papers",
      color = "Domain"
    ) +
    theme_monopoly() +
    theme(legend.text = element_text(size = 7))

  save_publication_figure(p_domain_time, "domain_volume_by_year", fig_dir, width = 10, height = 6)
}

cat("\nExtended analysis figures saved to:", fig_dir, "\n")
