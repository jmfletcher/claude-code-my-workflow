# ============================================================
# Parse SHOW publications from REACH curated CSV
# Source: datasets/SHOW/raw/reach_publications_complete_authors.csv
# Outputs: processed/papers_authors.csv, processed/papers.csv
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(stringr)
  library(tibble)
  library(purrr)
  library(yaml)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "SHOW"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

log_path <- file.path(dirs$raw, "fetch_log.txt")
csv_path <- file.path(dirs$raw, "reach_publications_complete_authors.csv")

if (!file.exists(csv_path)) {
  stop("Missing ", csv_path)
}

raw_tbl <- read_csv(csv_path, show_col_types = FALSE)
cat("Loaded", nrow(raw_tbl), "rows from REACH SHOW CSV\n")

normalize_show_author <- function(name) {
  name <- str_squish(name)
  if (!nzchar(name)) return(NA_character_)

  parts <- str_split(name, "\\s+")[[1]]
  if (length(parts) == 1) return(parts[1])

  last <- parts[length(parts)]
  first_parts <- parts[-length(parts)]
  initials <- paste0(vapply(first_parts, function(part) {
    tokens <- unlist(strsplit(gsub("[^A-Za-z-]", "", part), "-", fixed = TRUE))
    tokens <- tokens[nzchar(tokens)]
    if (length(tokens) == 0) return("")
    paste0(str_sub(tokens, 1, 1), collapse = "")
  }, character(1)), collapse = "")
  str_squish(paste(last, initials))
}

parse_author_list <- function(full_list) {
  if (is.na(full_list) || !nzchar(str_squish(full_list))) return(character())
  authors <- str_split(full_list, ";\\s*")[[1]] %>%
    str_trim() %>%
    discard(~ !nzchar(.x))
  authors <- vapply(authors, normalize_show_author, character(1))
  authors <- authors[!is.na(authors) & nzchar(authors)]
  unique(authors)
}

records <- raw_tbl %>%
  filter(is.na(duplicate_of_list_index) | duplicate_of_list_index == "") %>%
  mutate(
    title = str_squish(coalesce(canonical_title, source_title)),
    pub_year = as.integer(publication_year),
    paper_id = case_when(
      !is.na(pmid) & pmid != "" ~ paste0("show_pmid_", pmid),
      !is.na(doi) & doi != "" ~ paste0("show_doi_", gsub("[^a-zA-Z0-9]", "_", doi)),
      TRUE ~ paste0("show_idx_", list_index)
    )
  ) %>%
  filter(!is.na(title), nzchar(title))

parsed_tbl <- map_dfr(seq_len(nrow(records)), function(i) {
  row <- records[i, ]
  authors <- parse_author_list(row$full_author_list)
  if (length(authors) == 0 && !is.na(row$lead_author) && nzchar(row$lead_author)) {
    authors <- parse_author_list(row$lead_author)
  }
  if (length(authors) == 0) return(NULL)

  tibble(
    paper_id = row$paper_id,
    list_index = row$list_index,
    title = row$title,
    pub_year = row$pub_year,
    pmid = row$pmid,
    doi = row$doi,
    journal = row$journal_or_source,
    publication_type = row$publication_type,
    author_list_status = row$author_list_status,
    author_list = paste(authors, collapse = "|"),
    n_authors = length(authors)
  )
})

if (nrow(parsed_tbl) == 0) {
  stop("No SHOW publications parsed")
}

parsed_tbl <- parsed_tbl %>%
  arrange(desc(nchar(author_list)), paper_id) %>%
  distinct(title, .keep_all = TRUE) %>%
  distinct(paper_id, .keep_all = TRUE)

out_path <- file.path(dirs$raw, "show_publications.csv")
write_csv(parsed_tbl, out_path)

papers_authors <- map_dfr(seq_len(nrow(parsed_tbl)), function(i) {
  row <- parsed_tbl[i, ]
  authors <- str_split(row$author_list, "\\|")[[1]]
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

papers <- parsed_tbl %>%
  transmute(
    pmid = paper_id,
    title = title,
    abstract = NA_character_,
    pub_year = pub_year,
    text = title,
    has_abstract = FALSE
  )
write_csv(papers, file.path(dirs$processed, "papers.csv"))

manifest <- parsed_tbl %>%
  transmute(
    paper_id = paper_id,
    list_index = list_index,
    pubmed_pmid = pmid,
    fetch_date = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    fetch_status = "success",
    source = "reach_csv"
  )
write_csv(manifest, file.path(dirs$raw, "pubmed_manifest.csv"))

config$source$last_fetched <- as.character(Sys.Date())
config$source$automated_fetch_count <- nrow(parsed_tbl)
yaml::write_yaml(config, file.path(dirs$base, "config.yaml"))

log_fetch(log_path, paste0(
  "PARSE | papers=", nrow(parsed_tbl),
  " authors=", n_distinct(papers_authors$author_id),
  " csv_rows=", nrow(raw_tbl)
))

cat("\n=== SHOW Parse Summary ===\n")
cat("CSV rows:", nrow(raw_tbl), "\n")
cat("Publications parsed:", nrow(parsed_tbl), "\n")
cat("Author rows:", nrow(papers_authors), "\n")
cat("Unique authors:", n_distinct(papers_authors$author_id), "\n")
if (any(!is.na(parsed_tbl$pub_year))) {
  cat("Year range:", min(parsed_tbl$pub_year, na.rm = TRUE), "-",
      max(parsed_tbl$pub_year, na.rm = TRUE), "\n")
}
cat("Output:", out_path, "\n")

expected <- config$source$expected_paper_count
if (!is.null(expected) && nrow(parsed_tbl) != expected) {
  cat("NOTE: Parsed", nrow(parsed_tbl), "vs expected", expected, "\n")
}
