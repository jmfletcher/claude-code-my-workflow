# ============================================================
# NIH-AARP Authorship Monopoly Pipeline
# Purpose: Fetch PubMed collection 62019178, compute concentration metrics
# Usage: Rscript datasets/NIH_AARP/scripts/run_pipeline.R
# ============================================================

repo_root <- normalizePath(getwd(), winslash = "/")
dataset_name <- "NIH_AARP"

run_step <- function(name, ...) {
  cat("\n---", name, "---\n")
  status <- do.call(system2, c(list(...), list(wait = TRUE)))
  if (status != 0) stop(name, " failed with status ", status)
  invisible(status)
}

cat("=== Data Monopolies Pipeline:", dataset_name, "===\n")
cat("Repo root:", repo_root, "\n")

run_step("Fetch PMID list", "Rscript",
         c("scripts/R/fetch_collection_pmids.R", dataset_name))

run_step("Fetch PubMed records", "Rscript",
         c("scripts/R/fetch_pubmed_collection.R", dataset_name))

run_step("Parse authors", "Rscript",
         c("scripts/R/parse_pubmed_xml.R", dataset_name))

run_step("Apply aliases", "Rscript",
         c("scripts/R/apply_author_aliases.R", dataset_name))

run_step("Compute metrics", "Rscript",
         c("scripts/R/compute_monopoly_metrics.R", dataset_name))

run_step("Generate figures", "Rscript",
         c("scripts/R/plot_monopoly_figures.R", dataset_name))

run_step("Temporal analysis", "Rscript",
         c("scripts/R/analyze_temporal_concentration.R", dataset_name))

run_step("Extended figures", "Rscript",
         c("scripts/R/plot_extended_analysis.R", dataset_name))

cat("\n=== Pipeline complete ===\n")
