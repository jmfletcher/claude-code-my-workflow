# ============================================================
# Extract PubMed IDs from the CHS bibliography .docx
# Source: https://chs-nhlbi.org/CurrentBibliography (n=2,315)
# Entries end with "PM:{PMID}"; we harvest those and feed the PubMed pipeline.
# Output: datasets/CHS/raw/pmid_list.csv
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(stringr)
  library(tibble)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "CHS"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

docx_path <- file.path(dirs$raw, "chs_bibliography.docx")
if (!file.exists(docx_path)) {
  cat("Downloading CHS bibliography docx...\n")
  status <- system2(
    "curl", c("-sL", "-A", "DataMonopolies/1.0", "-o", shQuote(docx_path),
              shQuote(config$source$docx_url)),
    stdout = FALSE, stderr = FALSE
  )
  if (status != 0 || !file.exists(docx_path)) stop("Failed to download CHS docx")
}

tmp <- tempfile()
dir.create(tmp)
on.exit(unlink(tmp, recursive = TRUE), add = TRUE)
utils::unzip(docx_path, "word/document.xml", exdir = tmp)
raw <- readChar(file.path(tmp, "word/document.xml"),
                file.info(file.path(tmp, "word/document.xml"))$size, useBytes = TRUE)

# PMIDs appear as "PM:1592445" or "PM: 1592445" (not PMC / NIHMSID)
m <- str_match_all(raw, "PM:\\s*([0-9]{4,9})")[[1]]
pmids <- unique(m[, 2])

out <- tibble(pmid = pmids, source = "chs_bibliography_docx")
write_csv(out, file.path(dirs$raw, "pmid_list.csv"))

cat("\n=== CHS PMID Extraction ===\n")
cat("PMIDs extracted:", length(pmids), "/ expected", config$source$expected_paper_count, "\n")
cat("Output:", file.path(dirs$raw, "pmid_list.csv"), "\n")
