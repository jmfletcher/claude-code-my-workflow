# ============================================================
# Estimate coverage of a dataset's curated publication list
# against a broad PubMed search for the dataset.
#
# Compares:
#   N_central  = PMIDs on the study's curated list (raw/pmid_list.csv)
#   N_search   = PMIDs from a broad Entrez query (config source.coverage_query)
#   overlap    = central PMIDs also found by the search
#   coverage   = N_central_in_pubmed / N_union  (how complete the curated list is)
#
# Output: datasets/{name}/output/coverage_estimate.csv
#
# Notes:
# - Only PMID-indexed papers are comparable; central items without a PMID are
#   counted separately (central_no_pmid) and excluded from the ratio.
# - Uses PubMed only (free via rentrez). OpenAlex can be layered in later.
# ============================================================

suppressPackageStartupMessages({
  library(rentrez)
  library(readr)
  library(dplyr)
  library(tibble)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else stop("Usage: estimate_coverage.R <DATASET>")

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)

query <- config$source$coverage_query
if (is.null(query) || is.na(query) || query == "") {
  stop("No source.coverage_query in config.yaml for ", dataset_name)
}

# --- Central list PMIDs ---
pmid_path <- file.path(dirs$raw, "pmid_list.csv")
central_pmids <- character()
central_no_pmid <- 0L
if (file.exists(pmid_path)) {
  cl <- read_csv(pmid_path, show_col_types = FALSE)
  central_pmids <- unique(as.character(cl$pmid[!is.na(cl$pmid) & cl$pmid != ""]))
} else {
  # fall back to processed papers_authors.csv pmid column
  pa <- read_csv(file.path(dirs$processed, "papers_authors.csv"), show_col_types = FALSE)
  pm <- unique(as.character(pa$pmid))
  is_num <- grepl("^[0-9]+$", pm)
  central_pmids <- pm[is_num]
  central_no_pmid <- sum(!is_num)
}

cat("Central PMIDs:", length(central_pmids), "\n")
cat("Broad query:", query, "\n")

# --- Broad PubMed search ---
sleep_secs <- if (nzchar(Sys.getenv("NCBI_API_KEY"))) 0.11 else 0.34
search <- entrez_search(db = "pubmed", term = query, retmax = 0, use_history = FALSE)
n_search_total <- search$count
cat("PubMed hits for query:", n_search_total, "\n")

# Page through IDs (retmax cap 9999 per call)
search_pmids <- character()
step <- 5000L
for (start in seq(0, max(0, n_search_total - 1), by = step)) {
  s <- entrez_search(db = "pubmed", term = query, retmax = step, retstart = start)
  search_pmids <- c(search_pmids, s$ids)
  Sys.sleep(sleep_secs)
}
search_pmids <- unique(as.character(search_pmids))

# --- Compare ---
overlap <- intersect(central_pmids, search_pmids)
central_only <- setdiff(central_pmids, search_pmids)   # on list, missed by query
search_only <- setdiff(search_pmids, central_pmids)    # in literature, not on list
union_n <- length(union(central_pmids, search_pmids))

coverage_ratio <- if (union_n > 0) length(central_pmids) / union_n else NA_real_
recall_of_query <- if (length(search_pmids) > 0) length(overlap) / length(search_pmids) else NA_real_

result <- tibble(
  dataset = dataset_name,
  metric = c("n_central_pmid", "n_central_no_pmid", "n_query_hits",
             "n_overlap", "n_central_only", "n_search_only", "n_union",
             "coverage_ratio", "curated_share_of_query"),
  value = c(length(central_pmids), central_no_pmid, n_search_total,
            length(overlap), length(central_only), length(search_only), union_n,
            round(coverage_ratio, 4), round(recall_of_query, 4)),
  computed_date = as.character(Sys.Date())
)

out_path <- file.path(dirs$output, "coverage_estimate.csv")
write_csv(result, out_path)

cat("\n=== Coverage Estimate:", dataset_name, "===\n")
cat("Curated list (PMID):    ", length(central_pmids), "\n")
cat("Broad PubMed query hits:", n_search_total, "\n")
cat("Overlap:                ", length(overlap), "\n")
cat("On list, not in query:  ", length(central_only), "\n")
cat("In query, not on list:  ", length(search_only), "\n")
cat("Union (PMID):           ", union_n, "\n")
cat(sprintf("Curated list covers ~%.1f%% of the PMID union.\n", 100 * coverage_ratio))
cat("Output:", out_path, "\n")
