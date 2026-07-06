# Full re-analysis after alias updates
# Resets author strings from PubMed XML, rebuilds aliases, reruns all metrics/figures

dataset_name <- "REGARDS"

run_step <- function(name, ...) {
  cat("\n---", name, "---\n")
  status <- do.call(system2, c(list(...), list(wait = TRUE)))
  if (status != 0) stop(name, " failed")
}

cat("=== REGARDS Re-analysis (updated aliases) ===\n")

run_step("Re-parse authors from XML", "Rscript",
         c("scripts/R/parse_pubmed_xml.R", dataset_name))
run_step("Build aliases from suggestions", "Rscript",
         c("scripts/R/build_author_aliases.R", dataset_name))
run_step("Apply aliases", "Rscript",
         c("scripts/R/apply_author_aliases.R", dataset_name))
run_step("Base metrics", "Rscript",
         c("scripts/R/compute_monopoly_metrics.R", dataset_name))
run_step("Base figures", "Rscript",
         c("scripts/R/plot_monopoly_figures.R", dataset_name))
run_step("Temporal analysis", "Rscript",
         c("scripts/R/analyze_temporal_concentration.R", dataset_name))
run_step("Domain analysis", "Rscript",
         c("scripts/R/analyze_domain_concentration.R", dataset_name))
run_step("Extended figures", "Rscript",
         c("scripts/R/plot_extended_analysis.R", dataset_name))

cat("\n=== Re-analysis complete ===\n")
