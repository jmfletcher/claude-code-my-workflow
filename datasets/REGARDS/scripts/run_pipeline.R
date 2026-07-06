# ============================================================
# REGARDS Authorship Monopoly Pipeline
# Purpose: End-to-end pipeline for REGARDS dataset
# Usage: Rscript datasets/REGARDS/scripts/run_pipeline.R
# ============================================================

repo_root <- normalizePath(getwd(), winslash = "/")
dataset_name <- "REGARDS"

run_step <- function(name, ...) {
  cat("\n---", name, "---\n")
  args <- list(...)
  status <- do.call(system2, c(args, list(wait = TRUE)))
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

cat("\n=== Pipeline complete ===\n")
