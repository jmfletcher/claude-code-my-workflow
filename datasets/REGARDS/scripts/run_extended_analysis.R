# Extended REGARDS analysis: temporal trends + domain clustering
# Usage: Rscript datasets/REGARDS/scripts/run_extended_analysis.R

dataset_name <- "REGARDS"

run_step <- function(name, ...) {
  cat("\n---", name, "---\n")
  status <- do.call(system2, c(list(...), list(wait = TRUE)))
  if (status != 0) stop(name, " failed")
}

cat("=== Extended Analysis:", dataset_name, "===\n")

run_step("Re-apply aliases", "Rscript", c("scripts/R/build_author_aliases.R", dataset_name))
run_step("Apply aliases", "Rscript", c("scripts/R/apply_author_aliases.R", dataset_name))
run_step("Recompute base metrics", "Rscript", c("scripts/R/compute_monopoly_metrics.R", dataset_name))
run_step("Extract paper metadata", "Rscript", c("scripts/R/extract_paper_metadata.R", dataset_name))
run_step("Temporal concentration", "Rscript", c("scripts/R/analyze_temporal_concentration.R", dataset_name))
run_step("Domain clustering", "Rscript", c("scripts/R/analyze_domain_concentration.R", dataset_name))
run_step("Extended figures", "Rscript", c("scripts/R/plot_extended_analysis.R", dataset_name))

cat("\n=== Extended analysis complete ===\n")
