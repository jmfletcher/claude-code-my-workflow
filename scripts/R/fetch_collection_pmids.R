# ============================================================
# Fetch PMID list for dataset collection
# Purpose: Get PMIDs via manual list, PubMed collection scrape,
#          or Entrez esearch query (from config.yaml)
# Inputs: config.yaml, optional raw/pmid_list.csv (manual override)
# Outputs: raw/pmid_list.csv, raw/pubmed_manifest.csv
# ============================================================

suppressPackageStartupMessages({
  library(rentrez)
  library(readr)
  library(dplyr)
  library(tibble)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"
repo_root <- if (length(args) >= 2) args[2] else "."

config <- load_dataset_config(dataset_name, repo_root)
dirs <- get_dataset_dirs(dataset_name, repo_root)
ensure_dataset_dirs(dirs)

pmid_path <- file.path(dirs$raw, "pmid_list.csv")
manifest_path <- file.path(dirs$raw, "pubmed_manifest.csv")

`%||%` <- function(x, y) if (is.null(x) || length(x) == 0) y else x

fetch_pubmed_collection_pmids <- function(collection_id, expected = NULL) {
  pmids <- character()
  page <- 1L
  base_url <- sprintf(
    "https://pubmed.ncbi.nlm.nih.gov/collections/%s/",
    collection_id
  )
  repeat {
    html <- system2(
      "curl",
      c(
        "-sL", "-A", "Mozilla/5.0", base_url,
        "-G", "-d", "sort=pubdate", "-d", paste0("page=", page)
      ),
      stdout = TRUE,
      stderr = FALSE
    )
    if (length(html) == 0) break
    html <- paste(html, collapse = "\n")
    page_pmids <- regmatches(
      html,
      gregexpr('data-article-id="([0-9]+)"', html, perl = TRUE)
    )[[1]]
    page_pmids <- gsub('data-article-id="([0-9]+)"', "\\1", page_pmids, perl = TRUE)
    if (length(page_pmids) == 0) break
    pmids <- c(pmids, page_pmids)
    cat("  page", page, ":", length(page_pmids), "PMIDs\n")
    page <- page + 1L
    if (!is.null(expected) && length(unique(pmids)) >= expected) break
    Sys.sleep(0.35)
  }
  unique(pmids)
}

if (file.exists(pmid_path) && file.info(pmid_path)$size > 50) {
  pmid_df <- read_csv(pmid_path, show_col_types = FALSE)
  pmids <- unique(as.character(pmid_df$pmid))
  source_type <- "manual"
  cat("Using existing pmid_list.csv:", length(pmids), "PMIDs\n")
} else {
  collection_id <- config$source$collection_id %||% NULL
  entrez_query <- config$source$automated_fetch_query %||%
    config$source$entrez_query %||% NULL
  expected <- config$source$expected_paper_count %||% NULL

  if (!is.null(collection_id) &&
      grepl("pubmed\\.ncbi\\.nlm\\.nih\\.gov/collections", config$source$collection_url %||% "")) {
    cat("Fetching PMIDs from PubMed collection", collection_id, "...\n")
    pmids <- fetch_pubmed_collection_pmids(collection_id, expected)
    source_type <- paste0("pubmed_collection_", collection_id)
    write_csv(tibble(pmid = pmids, source = source_type), pmid_path)
    cat("Wrote", length(pmids), "PMIDs to", pmid_path, "\n")
  } else if (!is.null(entrez_query)) {
    cat("Fetching PMIDs via Entrez:", entrez_query, "\n")
    search <- entrez_search(db = "pubmed", term = entrez_query, retmax = 10000)
    pmids <- search$ids
    source_type <- "esearch"
    write_csv(tibble(pmid = pmids, source = source_type), pmid_path)
    cat("Wrote", length(pmids), "PMIDs to", pmid_path, "\n")
  } else if (identical(dataset_name, "REGARDS")) {
    query <- '"NS041588"[Grant Number]'
    cat("Fetching PMIDs via Entrez (REGARDS default):", query, "\n")
    search <- entrez_search(db = "pubmed", term = query, retmax = 10000)
    pmids <- search$ids
    source_type <- "esearch"
    write_csv(tibble(pmid = pmids, source = source_type), pmid_path)
    cat("Wrote", length(pmids), "PMIDs to", pmid_path, "\n")
  } else {
    stop(
      "No PMID source configured for ", dataset_name,
      ". Set collection_id + collection_url, automated_fetch_query, or provide raw/pmid_list.csv"
    )
  }
}

fetch_time <- format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
manifest <- tibble(
  pmid = pmids,
  fetch_date = fetch_time,
  fetch_status = "pending",
  error_message = "",
  source = source_type
)
write_csv(manifest, manifest_path)

expected <- config$source$expected_paper_count
cat("Manifest:", nrow(manifest), "rows\n")
if (!is.null(expected) && length(pmids) != expected) {
  cat("NOTE: Retrieved", length(pmids), "PMIDs vs", expected,
      "in curated collection. Use manual pmid_list.csv for exact match.\n")
}
