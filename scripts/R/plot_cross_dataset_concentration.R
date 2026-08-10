# ============================================================
# Cross-dataset concentration landscape (top-3 and top-10 panels)
# Y: publications per year; X: top-x share; point size: years with publications
# Outputs:
#   output/figures/cross_dataset_concentration_top3.{pdf,png}
#   output/figures/cross_dataset_concentration_top10.{pdf,png}
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(ggrepel)
  library(scales)
})

source("scripts/R/utils.R")

in_path <- "output/cross_dataset_concentration.csv"
if (!file.exists(in_path)) {
  stop("Run scripts/R/build_cross_dataset_summary.R first.")
}

fig_dir <- "output/figures"
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

clean_label <- function(x) {
  x <- gsub("_", " ", x)
  x <- gsub("EdShare pre2015", "EdShare (<=2014)", x, fixed = TRUE)
  x <- gsub("EdShare post2015", "EdShare (>=2015)", x, fixed = TRUE)
  x <- gsub("EdShare post2017", "EdShare (>=2017 journals)", x, fixed = TRUE)
  x
}

raw <- read_csv(in_path, show_col_types = FALSE) %>%
  filter_cross_dataset_figure_datasets() %>%
  mutate(dataset_label = clean_label(dataset)) %>%
  filter(!is.na(papers_per_year), !is.na(n_pub_years))

if (nrow(raw) == 0) {
  stop("Missing papers_per_year or n_pub_years; rerun build_cross_dataset_summary.R")
}

n_ds <- nrow(raw)
point_color <- "#012169"
max_bubble <- 12

make_panel <- function(share_col, top_x, filename, out_csv) {
  plot_df <- raw %>%
    transmute(
      dataset_label,
      papers_per_year,
      n_pub_years,
      share = .data[[share_col]],
      point_size_mm = sqrt(n_pub_years / max(n_pub_years)) * max_bubble,
      crowded = share > 0.45 & papers_per_year < 90
    ) %>%
    arrange(crowded, share, papers_per_year) %>%
    group_by(crowded) %>%
    mutate(stagger = if_else(crowded, row_number() - (n() + 1) / 2, 0)) %>%
    ungroup() %>%
    mutate(
      nudge_x = if_else(crowded, 0.02 + abs(stagger) * 0.008, 0),
      nudge_y = case_when(
        crowded ~ -8 + stagger * 5,
        papers_per_year > 160 ~ 12,
        TRUE ~ 4
      )
    )

  p <- ggplot(plot_df, aes(x = share, y = papers_per_year, size = n_pub_years)) +
    geom_point(color = point_color, alpha = 0.82) +
    geom_text_repel(
      aes(label = dataset_label),
      data = plot_df,
      size = 2.7,
      color = "#252525",
      lineheight = 0.9,
      segment.size = 0.25,
      segment.color = "#737373",
      segment.alpha = 0.75,
      min.segment.length = 0,
      box.padding = 0.45,
      point.padding = 0.75,
      point.size = plot_df$point_size_mm,
      nudge_x = plot_df$nudge_x,
      nudge_y = plot_df$nudge_y,
      max.overlaps = Inf,
      seed = 42 + top_x,
      force = 4,
      force_pull = 0.2,
      max.iter = 20000,
      direction = "both",
      bg.color = "white",
      bg.r = 0.14,
      show.legend = FALSE
    ) +
    scale_x_continuous(
      labels = percent_format(accuracy = 1),
      limits = c(-0.02, 1.08),
      expand = expansion(mult = c(0.02, 0.08))
    ) +
    scale_y_continuous(
      labels = comma_format(),
      expand = expansion(mult = c(0.12, 0.1))
    ) +
    scale_size_area(
      name = "Years with\npublications",
      breaks = c(10, 20, 30, 40, 50, 60),
      max_size = max_bubble,
      guide = guide_legend(override.aes = list(color = point_color, alpha = 0.82))
    ) +
    coord_cartesian(clip = "off") +
    labs(
      title = paste0("Authorship concentration: top-", top_x, " authors"),
      subtitle = paste0(
        n_ds, " datasets; y = papers per calendar year (N / publication span); ",
        "point size = distinct years with ≥1 publication"
      ),
      x = paste0("Share of papers co-authored by top-", top_x, " authors"),
      y = "Publications per year",
      caption = "Source: dataset monopoly pipelines; auto-merged author aliases applied per study."
    ) +
    theme_monopoly() +
    theme(
      legend.position = "bottom",
      legend.direction = "horizontal",
      legend.box = "horizontal",
      legend.box.just = "left",
      legend.title = element_text(size = 10, margin = margin(b = 4)),
      legend.text = element_text(size = 9),
      legend.background = element_rect(fill = "white", color = NA),
      legend.margin = margin(t = 6, b = 2),
      plot.caption = element_text(size = 9, color = "#525252", hjust = 0),
      plot.margin = margin(12, 36, 18, 12)
    )

  save_publication_figure(p, filename, fig_dir, width = 13, height = 10)
  write_csv(plot_df, file.path(fig_dir, out_csv))
  p
}

make_panel("top3", 3L, "cross_dataset_concentration_top3", "cross_dataset_concentration_top3_points.csv")
make_panel("top10", 10L, "cross_dataset_concentration_top10", "cross_dataset_concentration_top10_points.csv")

cat("\n=== Cross-dataset landscape figures ===\n")
cat("Datasets:", n_ds, "\n")
cat("Output:", file.path(fig_dir, "cross_dataset_concentration_top3.pdf"), "\n")
cat("Output:", file.path(fig_dir, "cross_dataset_concentration_top10.pdf"), "\n")
