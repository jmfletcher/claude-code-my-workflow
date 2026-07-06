# ============================================================
# Fetch PubMed records for a dataset collection
# Purpose: Download PubMed XML for all PMIDs in manifest
# Inputs: datasets/{name}/raw/pmid_list.csv or pubmed_manifest.csv
# Outputs: datasets/{name}/raw/pubmed_records.xml, updated manifest
# ============================================================

# 0. Setup ----
suppressPackageStartupMessages({
  library(rentrez)
  library(readr)
  library(dplyr)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"
repo_root <- if (length(args) >= 2) args[2] else "."

config <- load_dataset_config(dataset_name, repo_root)
dirs <- get_dataset_dirs(dataset_name, repo_root)
ensure_dataset_dirs(dirs)

log_path <- file.path(dirs$raw, "fetch_log.txt")
if (!file.exists(log_path)) {
  file.create(log_path)
}

# 1. Load PMIDs ----
pmid_path <- file.path(dirs$raw, "pmid_list.csv")
manifest_path <- file.path(dirs$raw, "pubmed_manifest.csv")

if (!file.exists(pmid_path) && !file.exists(manifest_path)) {
  stop("No PMID list found. Run: python3 scripts/fetch_collection_pmids.py --dataset ", dataset_name)
}

if (file.exists(pmid_path)) {
  pmid_df <- read_csv(pmid_path, show_col_types = FALSE)
  pmids <- unique(as.character(pmid_df$pmid))
} else {
  manifest <- read_csv(manifest_path, show_col_types = FALSE)
  pmids <- unique(as.character(manifest$pmid))
}

log_fetch(log_path, paste("Starting fetch for", length(pmids), "PMIDs"))

`%||%` <- function(x, y) if (is.na(x) || is.null(x)) y else x

# 2. Batch fetch via rentrez ----
batch_size <- 200
sleep_secs <- if (nzchar(Sys.getenv("NCBI_API_KEY"))) 0.11 else 0.34

xml_chunks <- list()
fetch_results <- vector("list", length(pmids))
names(fetch_results) <- pmids

for (i in seq(1, length(pmids), by = batch_size)) {
  batch <- pmids[i:min(i + batch_size - 1, length(pmids))]
  batch_num <- ceiling(i / batch_size)
  n_batches <- ceiling(length(pmids) / batch_size)

  log_fetch(log_path, paste("Fetching batch", batch_num, "of", n_batches, "(", length(batch), "PMIDs)"))

  xml <- tryCatch(
    entrez_fetch(db = "pubmed", id = batch, rettype = "xml", parsed = FALSE),
    error = function(e) {
      log_fetch(log_path, paste("ERROR batch", batch_num, ":", conditionMessage(e)))
      NULL
    }
  )

  if (!is.null(xml)) {
    xml_chunks[[length(xml_chunks) + 1]] <- xml
    for (pmid in batch) {
      fetch_results[[pmid]] <- list(status = "success", error = NA_character_)
    }
  } else {
    for (pmid in batch) {
      fetch_results[[pmid]] <- list(status = "error", error = "batch fetch failed")
    }
  }

  Sys.sleep(sleep_secs)
}

# 3. Save raw XML (single valid document) ----
combine_pubmed_xml <- function(chunks) {
  articles <- character()
  for (chunk in chunks) {
    chunk <- sub("^<\\?xml[^>]*\\?>", "", chunk)
    chunk <- gsub("<!DOCTYPE[^>]*>", "", chunk)
    chunk <- gsub("</?PubmedArticleSet>", "", chunk)
    articles <- c(articles, chunk)
  }
  paste0(
    '<?xml version="1.0" encoding="UTF-8"?>\n',
    "<PubmedArticleSet>\n",
    paste(articles, collapse = "\n"),
    "\n</PubmedArticleSet>"
  )
}

xml_combined <- combine_pubmed_xml(xml_chunks)
xml_path <- file.path(dirs$raw, "pubmed_records.xml")
writeLines(xml_combined, xml_path, useBytes = TRUE)
log_fetch(log_path, paste("Wrote XML:", xml_path, "(", nchar(xml_combined), "chars)"))

# 4. Update manifest ----
fetch_time <- format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
manifest_out <- tibble(
  pmid = pmids,
  fetch_date = fetch_time,
  fetch_status = vapply(pmids, function(p) fetch_results[[p]]$status, character(1)),
  error_message = vapply(pmids, function(p) fetch_results[[p]]$error %||% "", character(1)),
  source = if (file.exists(pmid_path)) {
    src <- read_csv(pmid_path, show_col_types = FALSE)
    src$source[match(pmids, as.character(src$pmid))]
  } else {
    "esearch"
  }
)

write_csv(manifest_out, manifest_path)

# 5. QC summary ----
n_success <- sum(manifest_out$fetch_status == "success")
n_error <- sum(manifest_out$fetch_status == "error")
expected <- config$source$expected_paper_count

cat("\n=== Fetch Summary ===\n")
cat("Dataset:", dataset_name, "\n")
cat("PMIDs fetched:", n_success, "/", length(pmids), "\n")
cat("Errors:", n_error, "\n")
cat("Expected (collection):", expected, "\n")
if (!is.null(expected) && n_success != expected) {
  cat("NOTE: Count differs from curated collection (", expected, "). ",
      "See datasets/", dataset_name, "/README.md for source details.\n", sep = "")
}
