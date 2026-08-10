# Shared utilities for Data Monopolies pipeline

#' Load dataset config.yaml
load_dataset_config <- function(dataset_name, repo_root = ".") {
  config_path <- file.path(repo_root, "datasets", dataset_name, "config.yaml")
  if (!file.exists(config_path)) {
    stop("Config not found: ", config_path)
  }
  yaml::read_yaml(config_path)
}

#' Resolve dataset directory paths
get_dataset_dirs <- function(dataset_name, repo_root = ".") {
  base <- file.path(repo_root, "datasets", dataset_name)
  list(
    base = base,
    raw = file.path(base, "raw"),
    processed = file.path(base, "processed"),
    output = file.path(base, "output"),
    figures = file.path(base, "output", "figures"),
    scripts = file.path(base, "scripts")
  )
}

#' Ensure dataset directories exist
ensure_dataset_dirs <- function(dirs) {
  for (d in c(dirs$raw, dirs$processed, dirs$output, dirs$figures)) {
    dir.create(d, recursive = TRUE, showWarnings = FALSE)
  }
}

#' Filter datasets shown in cross-dataset summary figures
filter_cross_dataset_figure_datasets <- function(df) {
  df %>% dplyr::filter(
    !grepl("^EdShare", .data$dataset) | .data$dataset == "EdShare_post2017"
  )
}

#' Append line to fetch log
log_fetch <- function(log_path, message) {
  line <- paste0(format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC"), " | ", message, "\n")
  cat(line, file = log_path, append = TRUE)
}

#' Project visualization theme
theme_monopoly <- function(base_size = 12) {
  primary_blue <- "#012169"
  accent_gray <- "#525252"
  ggplot2::theme_minimal(base_size = base_size) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", color = primary_blue, size = 14),
      plot.subtitle = ggplot2::element_text(color = accent_gray, size = 11),
      axis.title = ggplot2::element_text(color = accent_gray),
      legend.position = "bottom",
      panel.grid.minor = ggplot2::element_blank()
    )
}

#' Save figure as PDF + PNG with source data RDS
save_publication_figure <- function(plot, filename, out_dir, width = 8, height = 5) {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(
    file.path(out_dir, paste0(filename, ".pdf")),
    plot, width = width, height = height, bg = "white"
  )
  ggplot2::ggsave(
    file.path(out_dir, paste0(filename, ".png")),
    plot, width = width, height = height, dpi = 300, bg = "white"
  )
  saveRDS(ggplot2::ggplot_build(plot), file.path(out_dir, paste0(filename, "_data.rds")))
}
