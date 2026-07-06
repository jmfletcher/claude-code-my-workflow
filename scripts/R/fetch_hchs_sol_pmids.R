# ============================================================
# Scrape HCHS/SOL publication PMIDs from the study website
# Source: https://sites9.cscc.unc.edu/hchs/res-publications
# Each publication row links to pubmed.ncbi.nlm.nih.gov/{PMID}.
# Output: datasets/HCHS_SOL/raw/pmid_list.csv (feeds PubMed XML pipeline)
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(stringr)
  library(tibble)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "HCHS_SOL"
max_pages <- if (length(args) >= 2) as.integer(args[2]) else NA_integer_

dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

base_url <- "https://sites9.cscc.unc.edu/hchs/res-publications"
page_size <- 50L

fetch_page <- function(page) {
  url <- paste0(base_url, "?items_per_page=", page_size, "&page=", page)
  tmp <- tempfile()
  status <- system2(
    "curl", c("-sL", "-A", "DataMonopolies/1.0", "-o", tmp, shQuote(url)),
    stdout = FALSE, stderr = FALSE
  )
  if (status != 0 || !file.exists(tmp)) stop("curl failed for page ", page)
  html <- readChar(tmp, file.info(tmp)$size, useBytes = TRUE)
  unlink(tmp)
  html
}

extract_pmids <- function(html) {
  m <- str_match_all(html, "pubmed\\.ncbi\\.nlm\\.nih\\.gov/([0-9]+)")[[1]]
  if (nrow(m) == 0) return(character())
  unique(m[, 2])
}

all_pmids <- character()
page <- 0L
repeat {
  html <- fetch_page(page)
  pmids <- extract_pmids(html)
  new_pmids <- setdiff(pmids, all_pmids)
  cat("Page", page, ":", length(pmids), "PMIDs (", length(new_pmids), "new )\n")
  if (length(new_pmids) == 0) break
  all_pmids <- c(all_pmids, new_pmids)
  page <- page + 1L
  if (!is.na(max_pages) && page >= max_pages) break
  Sys.sleep(0.35)
}

all_pmids <- unique(all_pmids)
out <- tibble(pmid = all_pmids, source = "hchs_sol_website")
write_csv(out, file.path(dirs$raw, "pmid_list.csv"))

cat("\n=== HCHS/SOL PMID Scrape ===\n")
cat("Total unique PMIDs:", length(all_pmids), "\n")
cat("Output:", file.path(dirs$raw, "pmid_list.csv"), "\n")
