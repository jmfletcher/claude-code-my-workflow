# CARDIA authorship concentration pipeline
dataset_name <- "CARDIA"

run_step <- function(name, ...) {
  cat("\n---", name, "---\n")
  status <- do.call(system2, c(list(...), list(wait = TRUE)))
  if (status != 0) stop(name, " failed")
}

cat("=== CARDIA Pipeline ===\n")

python <- if (file.exists(".venv-ffcws/bin/python")) {
  ".venv-ffcws/bin/python"
} else {
  "python3"
}

run_step("Ingest CARDIA publications", python,
         c("scripts/cardia/ingest_publications.py",
           "--output-dir", "datasets/CARDIA/raw"))

run_step("Parse CARDIA publications", "Rscript",
         c("scripts/R/fetch_cardia_publications.R", dataset_name))

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

cat("\n=== CARDIA pipeline complete ===\n")
