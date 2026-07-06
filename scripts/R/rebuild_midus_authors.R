# Rebuild papers_authors.csv from midus_publications.csv (no re-fetch)
suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(stringr)
  library(tibble)
  library(purrr)
})

source("scripts/R/utils.R")

parse_apa_authors <- function(author_part) {
  if (is.na(author_part) || author_part == "") return(character())
  s <- author_part
  s <- gsub(",?\\s*&\\s*", ", ", s)
  s <- gsub("\\.\\s*$", "", s)
  matches <- str_match_all(
    s,
    "([A-Z][A-Za-z\\-' ]+?),\\s+((?:[A-Z]\\.?\\s*)+)"
  )[[1]]
  if (nrow(matches) == 0) return(character())
  apply(matches, 1, function(m) {
    paste(str_trim(m[2]), gsub("[.\\s]", "", m[3]))
  })
}

dataset_name <- if (length(commandArgs(trailingOnly = TRUE)) >= 1) {
  commandArgs(trailingOnly = TRUE)[1]
} else {
  "MIDUS"
}

dirs <- get_dataset_dirs(dataset_name)
all_pubs <- read_csv(file.path(dirs$raw, "midus_publications.csv"), show_col_types = FALSE)

papers_authors <- map_dfr(seq_len(nrow(all_pubs)), function(i) {
  row <- all_pubs[i, ]
  authors <- parse_apa_authors(row$author_part)
  if (length(authors) == 0) return(NULL)
  tibble(
    pmid = row$paper_id,
    title = row$title,
    pub_year = row$pub_year,
    author_raw = authors,
    author_id = authors,
    author_position = seq_along(authors),
    affiliation = NA_character_
  )
})

write_csv(papers_authors, file.path(dirs$processed, "papers_authors.csv"))
cat("Rebuilt author rows:", nrow(papers_authors), "\n")
cat("Papers with authors:", n_distinct(papers_authors$pmid), "/", nrow(all_pubs), "\n")
