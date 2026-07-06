# ============================================================
# Dataset acronym reference figure for cross-dataset plots
# Output: output/figures/dataset_acronym_legend.{pdf,png}
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(purrr)
  library(ggplot2)
  library(yaml)
  library(stringr)
})

source("scripts/R/utils.R")

fig_dir <- "output/figures"
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

clean_label <- function(x) {
  x <- gsub("_", " ", x)
  x <- gsub("EdShare pre2015", "EdShare (<=2014)", x, fixed = TRUE)
  x <- gsub("EdShare post2015", "EdShare (>=2015)", x, fixed = TRUE)
  x
}

# Prefer datasets included in the cross-dataset concentration summary
in_path <- "output/cross_dataset_concentration.csv"
if (file.exists(in_path)) {
  focus <- read_csv(in_path, show_col_types = FALSE)$dataset
} else {
  focus <- NULL
}

ds_dirs <- list.dirs("datasets", recursive = FALSE)
ds_dirs <- ds_dirs[!grepl("_template", ds_dirs)]

read_config <- function(d) {
  cfg_path <- file.path(d, "config.yaml")
  if (!file.exists(cfg_path)) return(NULL)
  cfg <- yaml::read_yaml(cfg_path)
  if (is.null(cfg$dataset$name) || is.null(cfg$dataset$full_name)) return(NULL)
  tibble(
    dataset = cfg$dataset$name,
    acronym = clean_label(cfg$dataset$name),
    full_name = cfg$dataset$full_name
  )
}

legend_df <- map_dfr(ds_dirs, read_config) %>%
  distinct(dataset, .keep_all = TRUE)

if (!is.null(focus)) {
  legend_df <- legend_df %>% filter(dataset %in% focus)
}

legend_df <- legend_df %>%
  arrange(acronym) %>%
  mutate(
    label = paste0(acronym, " — ", full_name),
    panel_col = (row_number() - 1L) %% 2L,
    row = (row_number() - 1L) %/% 2L,
    x = if_else(panel_col == 0L, 0, 0.52)
  )

n_rows <- max(legend_df$row) + 1L

p <- ggplot(legend_df, aes(x = x, y = -row)) +
  geom_text(
    aes(label = label),
    hjust = 0,
    vjust = 1,
    size = 3.2,
    color = "#252525",
    lineheight = 0.95
  ) +
  scale_x_continuous(limits = c(-0.01, 1.01), expand = c(0, 0)) +
  scale_y_continuous(limits = c(-n_rows - 0.3, 0.5), expand = c(0, 0)) +
  coord_cartesian(clip = "off") +
  labs(
    title = "Dataset acronyms and full names",
    subtitle = paste0(nrow(legend_df), " longitudinal datasets in cross-dataset concentration figures"),
    caption = "Acronyms match labels used in cross_dataset_concentration_top3/top10 figures."
  ) +
  theme_void(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", color = "#012169", size = 14, hjust = 0),
    plot.subtitle = element_text(color = "#525252", size = 11, hjust = 0, margin = margin(b = 8)),
    plot.caption = element_text(color = "#525252", size = 9, hjust = 0),
    plot.margin = margin(16, 20, 16, 20),
    axis.text.x = element_blank(),
    axis.title.x = element_blank(),
    axis.ticks = element_blank()
  )

fig_height <- max(8, 0.22 * n_rows + 1.8)
save_publication_figure(
  p,
  "dataset_acronym_legend",
  fig_dir,
  width = 13.5,
  height = fig_height
)

write_csv(
  legend_df %>% select(acronym, full_name, dataset),
  file.path(fig_dir, "dataset_acronym_legend.csv")
)

cat("\n=== Dataset acronym legend ===\n")
cat("Entries:", nrow(legend_df), "\n")
cat("Output:", file.path(fig_dir, "dataset_acronym_legend.pdf"), "\n")
