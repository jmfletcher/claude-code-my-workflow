# ============================================================
# Total publications per dataset (horizontal bar chart)
# Output: output/figures/cross_dataset_total_publications.{pdf,png}
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
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

plot_df <- read_csv(in_path, show_col_types = FALSE) %>%
  filter_cross_dataset_figure_datasets() %>%
  mutate(
    acronym = clean_label(dataset),
    acronym = factor(acronym, levels = acronym[order(n_papers)])
  )

n_ds <- nrow(plot_df)
total_papers <- sum(plot_df$n_papers)

p <- ggplot(plot_df, aes(x = n_papers, y = acronym)) +
  geom_col(fill = "#012169", width = 0.72) +
  geom_text(
    aes(label = comma(n_papers)),
    hjust = -0.08,
    size = 2.8,
    color = "#252525"
  ) +
  scale_x_continuous(
    labels = comma_format(),
    limits = c(0, max(plot_df$n_papers) * 1.12),
    expand = expansion(mult = c(0, 0))
  ) +
  labs(
    title = "Total publications by dataset",
    subtitle = paste0(
      n_ds, " datasets; ", comma(total_papers), " publications in pipeline ",
      "(curated lists or PubMed name search)"
    ),
    x = "Publications (N)",
    y = NULL,
    caption = "Counts reflect papers in each dataset's monopoly pipeline, not external citation totals."
  ) +
  theme_monopoly() +
  theme(
    axis.text.y = element_text(size = 9, color = "#252525"),
    panel.grid.major.y = element_blank(),
    plot.caption = element_text(size = 9, color = "#525252", hjust = 0),
    plot.margin = margin(12, 16, 12, 12)
  )

fig_height <- max(8, 0.28 * n_ds + 1.5)
save_publication_figure(
  p,
  "cross_dataset_total_publications",
  fig_dir,
  width = 10,
  height = fig_height
)

write_csv(
  plot_df %>% select(acronym, dataset, n_papers) %>% arrange(desc(n_papers)),
  file.path(fig_dir, "cross_dataset_total_publications.csv")
)

cat("\n=== Total publications figure ===\n")
cat("Datasets:", n_ds, "| Total papers:", total_papers, "\n")
cat("Output:", file.path(fig_dir, "cross_dataset_total_publications.pdf"), "\n")
