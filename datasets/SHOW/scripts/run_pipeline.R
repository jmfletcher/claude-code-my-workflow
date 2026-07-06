# SHOW authorship concentration pipeline
dataset_name <- "SHOW"

run_step <- function(name, ...) {
  cat("\n---", name, "---\n")
  status <- do.call(system2, c(list(...), list(wait = TRUE)))
  if (status != 0) stop(name, " failed")
}

cat("=== SHOW Pipeline ===\n")

run_step("Parse SHOW publications", "Rscript",
         c("scripts/R/fetch_show_publications.R", dataset_name))

run_step("Apply aliases", "Rscript",
         c("scripts/R/apply_author_aliases.R", dataset_name))

run_step("Compute metrics", "Rscript",
         c("scripts/R/compute_monopoly_metrics.R", dataset_name))

run_step("Base figures", "Rscript",
         c("scripts/R/plot_monopoly_figures.R", dataset_name))

run_step("Temporal analysis", "Rscript",
         c("scripts/R/analyze_temporal_concentration.R", dataset_name))

run_step("Extended figures", "Rscript",
         c("scripts/R/plot_extended_analysis.R", dataset_name))

cat("\n=== SHOW pipeline complete ===\n")
