# ============================================================
# Parse PubMed XML into papers_authors.csv
# Purpose: Extract authors, titles, years from raw XML
# Inputs: datasets/{name}/raw/pubmed_records.xml
# Outputs: datasets/{name}/processed/papers_authors.csv
# ============================================================

suppressPackageStartupMessages({
  library(xml2)
  library(readr)
  library(dplyr)
  library(purrr)
  library(tibble)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"
repo_root <- if (length(args) >= 2) args[2] else "."

dirs <- get_dataset_dirs(dataset_name, repo_root)
xml_path <- file.path(dirs$raw, "pubmed_records.xml")

if (!file.exists(xml_path)) {
  stop("PubMed XML not found: ", xml_path)
}

# 1. Parse XML ----
doc <- read_xml(xml_path)
articles <- xml_find_all(doc, ".//PubmedArticle")

parse_year <- function(article) {
  year <- xml_text(xml_find_first(article, ".//PubDate/Year"))
  if (is.na(year) || year == "") {
    medline <- xml_text(xml_find_first(article, ".//PubDate/MedlineDate"))
    if (!is.na(medline)) {
      m <- regmatches(medline, regexpr("[0-9]{4}", medline))
      if (length(m) > 0) return(as.integer(m[1]))
    }
    return(NA_integer_)
  }
  as.integer(year)
}

parse_authors <- function(article, pmid, title, pub_year) {
  author_nodes <- xml_find_all(article, ".//AuthorList/Author")
  if (length(author_nodes) == 0) return(NULL)

  last_name <- xml_text(xml_find_first(author_nodes, "./LastName"))
  initials <- xml_text(xml_find_first(author_nodes, "./Initials"))
  collective <- xml_text(xml_find_first(author_nodes, "./CollectiveName"))
  aff <- xml_text(xml_find_first(author_nodes, ".//Affiliation"))

  author_raw <- trimws(paste(last_name, ifelse(is.na(initials), "", initials)))
  use_collective <- !is.na(collective) & collective != ""
  author_raw[use_collective] <- collective[use_collective]
  author_raw[is.na(last_name) & !use_collective] <- NA_character_

  tibble(
    pmid = pmid,
    title = title,
    pub_year = pub_year,
    author_raw = author_raw,
    author_id = author_raw,
    author_position = seq_along(author_nodes),
    affiliation = ifelse(is.na(aff), "", aff)
  )
}

records <- map_dfr(articles, function(article) {
  pmid <- xml_text(xml_find_first(article, ".//PMID"))
  title <- xml_text(xml_find_first(article, ".//ArticleTitle"))
  pub_year <- parse_year(article)
  parse_authors(article, pmid, title, pub_year)
})

records <- records %>%
  filter(!is.na(author_raw), author_raw != "")

out_path <- file.path(dirs$processed, "papers_authors.csv")
write_csv(records, out_path)

# QC
n_papers <- n_distinct(records$pmid)
n_authors <- n_distinct(records$author_id)
n_rows <- nrow(records)

cat("\n=== Parse Summary ===\n")
cat("Papers:", n_papers, "\n")
cat("Unique authors (raw):", n_authors, "\n")
cat("Paper-author rows:", n_rows, "\n")
cat("Output:", out_path, "\n")

saveRDS(records, file.path(dirs$processed, "papers_authors.rds"))
