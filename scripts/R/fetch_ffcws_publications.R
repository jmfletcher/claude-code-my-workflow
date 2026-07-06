# ============================================================
# Parse FFCWS publications from raw Zotero/ingest scrape
# Source: datasets/FFCWS/raw/publications.json (from ingest_publications.py)
# Outputs: processed/papers_authors.csv, processed/papers.csv
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(stringr)
  library(tibble)
  library(purrr)
  library(jsonlite)
  library(yaml)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "FFCWS"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

log_path <- file.path(dirs$raw, "fetch_log.txt")
json_path <- file.path(dirs$raw, "publications.json")

if (!file.exists(json_path)) {
  stop("Missing ", json_path, ". Run scripts/ffcws/ingest_publications.py first.")
}

records <- fromJSON(json_path, simplifyVector = FALSE)
cat("Loaded", length(records), "records from", json_path, "\n")

normalize_ffcws_author <- function(name) {
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

parse_pub_year <- function(year_val) {
  if (is.null(year_val) || length(year_val) == 0) return(NA_integer_)
  yr <- str_match(as.character(year_val), "(\\d{4})")[, 2]
  if (is.na(yr)) return(NA_integer_)
  as.integer(yr)
}

parse_record <- function(rec) {
  if (!identical(rec$fetch_status %||% "ok", "ok")) return(NULL)

  authors_raw <- rec$authors %||% list()
  if (length(authors_raw) == 0) return(NULL)

  authors <- unique(vapply(authors_raw, normalize_ffcws_author, character(1)))
  authors <- authors[!is.na(authors) & nzchar(authors)]
  if (length(authors) == 0) return(NULL)

  title <- rec$title %||% NA_character_
  if (is.na(title) || !nzchar(str_squish(title))) return(NULL)

  slug <- rec$slug %||% rec$url
  paper_id <- if (!is.null(rec$bibcite_id) && nzchar(rec$bibcite_id)) {
    paste0("ffcws_", rec$bibcite_id)
  } else {
    paste0("ffcws_", gsub("[^a-zA-Z0-9]+", "_", slug))
  }

  tibble(
    paper_id = paper_id,
    slug = rec$slug %||% NA_character_,
    bibcite_id = rec$bibcite_id %||% NA_character_,
    title = str_squish(title),
    pub_year = parse_pub_year(rec$year),
    doi = rec$doi %||% NA_character_,
    publication_type = rec$publication_type %||% NA_character_,
    url = rec$url %||% NA_character_,
    author_list = paste(authors, collapse = "|"),
    n_authors = length(authors),
    has_abstract = !is.null(rec$abstract) && nzchar(rec$abstract)
  )
}

`%||%` <- function(x, y) if (is.null(x) || length(x) == 0) y else x

parsed <- map(records, parse_record)
parsed_tbl <- bind_rows(parsed[!map_lgl(parsed, is.null)])

if (nrow(parsed_tbl) == 0) {
  stop("No FFCWS publications parsed")
}

parsed_tbl <- parsed_tbl %>%
  arrange(desc(nchar(author_list)), paper_id) %>%
  distinct(title, .keep_all = TRUE) %>%
  distinct(paper_id, .keep_all = TRUE)

out_path <- file.path(dirs$raw, "ffcws_publications.csv")
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
    has_abstract = has_abstract
  )
write_csv(papers, file.path(dirs$processed, "papers.csv"))

manifest <- parsed_tbl %>%
  transmute(
    paper_id = paper_id,
    bibcite_id = bibcite_id,
    fetch_date = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    fetch_status = "success",
    source = "ffcws_scrape"
  )
write_csv(manifest, file.path(dirs$raw, "pubmed_manifest.csv"))

config$source$last_fetched <- as.character(Sys.Date())
config$source$automated_fetch_count <- nrow(parsed_tbl)
yaml::write_yaml(config, file.path(dirs$base, "config.yaml"))

log_fetch(log_path, paste0(
  "PARSE | papers=", nrow(parsed_tbl),
  " authors=", n_distinct(papers_authors$author_id),
  " from_json=", length(records)
))

cat("\n=== FFCWS Parse Summary ===\n")
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
