# ============================================================
# Scrape PubMed IDs from the Framingham Heart Study bibliography.
# The bibliography is split across decade + per-year pages; each entry
# carries "(PubMed PMID: NNNN". We crawl all bibliography pages and harvest PMIDs.
# Output: datasets/Framingham/raw/pmid_list.csv
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(stringr)
  library(tibble)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "Framingham"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

get_url <- function(url) {
  tmp <- tempfile()
  status <- system2("curl", c("-sL", "-A", "DataMonopolies/1.0", "-o", tmp, shQuote(url)),
                    stdout = FALSE, stderr = FALSE)
  if (status != 0 || !file.exists(tmp)) return(NA_character_)
  html <- readChar(tmp, file.info(tmp)$size, useBytes = TRUE)
  unlink(tmp)
  html
}

index_url <- "https://www.framinghamheartstudy.org/fhs-bibliography/"
index_html <- get_url(index_url)
if (is.na(index_html)) stop("Could not fetch FHS bibliography index")

# Collect all bibliography page URLs (decade indexes + per-year leaves)
hrefs <- str_match_all(index_html, 'href="(https://www\\.framinghamheartstudy\\.org/[^"]*biblio[^"]*)"')[[1]][, 2]
hrefs <- unique(hrefs)
hrefs <- hrefs[!grepl("wp-json|oembed|format=xml", hrefs)]
hrefs <- union(hrefs, index_url)

cat("Bibliography pages to crawl:", length(hrefs), "\n")

all_pmids <- character()
for (u in hrefs) {
  html <- get_url(u)
  if (is.na(html)) { cat("  FAIL:", u, "\n"); next }
  # PMIDs appear as pubmed links and/or "PubMed ... : NNNN" text
  ids <- c(
    str_match_all(html, "pubmed[/=]([0-9]{4,9})")[[1]][, 2],
    str_match_all(html, "pubmed\\.ncbi\\.nlm\\.nih\\.gov/([0-9]{4,9})")[[1]][, 2],
    str_match_all(html, "PubMed[^0-9<]{0,20}:?\\s*([0-9]{4,9})")[[1]][, 2]
  )
  pm <- unique(ids[!is.na(ids)])
  new <- setdiff(pm, all_pmids)
  all_pmids <- c(all_pmids, new)
  cat("  ", length(pm), "PMIDs (", length(new), "new ) <-", sub(".*/", "", sub("/$", "", u)), "\n")
  Sys.sleep(0.3)
}

all_pmids <- unique(all_pmids)
out <- tibble(pmid = all_pmids, source = "framingham_website")
write_csv(out, file.path(dirs$raw, "pmid_list.csv"))

cat("\n=== Framingham PMID Scrape ===\n")
cat("Total unique PMIDs:", length(all_pmids), "\n")
cat("Output:", file.path(dirs$raw, "pmid_list.csv"), "\n")
