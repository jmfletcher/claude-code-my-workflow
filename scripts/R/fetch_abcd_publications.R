# ============================================================
# Parse ABCD publications from ingest scrape
# Source: datasets/ABCD/raw/publications.json
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
dataset_name <- if (length(args) >= 1) args[1] else "ABCD"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

log_path <- file.path(dirs$raw, "fetch_log.txt")
json_path <- file.path(dirs$raw, "publications.json")

if (!file.exists(json_path)) {
  stop(
    "Missing ", json_path,
    ". Run: .venv-ffcws/bin/python scripts/abcd/ingest_publications.py"
  )
}

records <- fromJSON(json_path, simplifyVector = FALSE)
cat("Loaded", length(records), "records from", json_path, "\n")

`%||%` <- function(x, y) if (is.null(x) || length(x) == 0) y else x

normalize_abcd_author <- function(name) {
  name <- str_squish(name)
  if (!nzchar(name)) return(NA_character_)
  if (str_detect(name, ",")) {
    parts <- str_split(name, ",", n = 2)[[1]]
    last <- str_trim(parts[1])
    initials <- gsub("[^A-Za-z]", "", parts[2])
    return(str_squish(paste(last, initials)))
  }
  name
}

parse_authors <- function(authors) {
  if (length(authors) == 0) return(character())
  authors <- vapply(authors, normalize_abcd_author, character(1))
  authors <- authors[!is.na(authors) & nzchar(authors)]
  unique(authors)
}

parse_record <- function(rec) {
  if (!identical(rec$fetch_status %||% "ok", "ok")) return(NULL)

  authors <- parse_authors(rec$authors %||% list())
  if (length(authors) == 0 && !is.null(rec$authors_raw)) {
    authors <- parse_authors(str_split(rec$authors_raw, ",\\s*")[[1]])
  }
  if (length(authors) == 0) return(NULL)

  title <- rec$title %||% NA_character_
  if (is.na(title) || !nzchar(str_squish(title))) return(NULL)

  paper_id <- rec$paper_id %||% {
    if (!is.null(rec$pmid) && nzchar(rec$pmid)) {
      paste0("abcd_", rec$pmid)
    } else {
      paste0("abcd_", gsub("[^a-zA-Z0-9]+", "_", title))
    }
  }

  pub_year <- rec$pub_year %||% NA_integer_
  if (is.null(pub_year) || is.na(pub_year)) {
    pub_year <- NA_integer_
  }

  tibble(
    paper_id = paper_id,
    pmid = rec$pmid %||% NA_character_,
    title = str_squish(title),
    pub_year = as.integer(pub_year),
    doi = rec$doi %||% NA_character_,
    journal = rec$journal %||% NA_character_,
    external_url = rec$external_url %||% NA_character_,
    author_list = paste(authors, collapse = "|"),
    n_authors = length(authors)
  )
}

parsed <- map(records, parse_record)
parsed_tbl <- bind_rows(parsed[!map_lgl(parsed, is.null)])

if (nrow(parsed_tbl) == 0) {
  stop("No ABCD publications parsed")
}

parsed_tbl <- parsed_tbl %>%
  arrange(desc(nchar(author_list)), paper_id) %>%
  distinct(title, .keep_all = TRUE) %>%
  distinct(paper_id, .keep_all = TRUE)

out_path <- file.path(dirs$raw, "abcd_publications.csv")
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
    pubmed_pmid = pmid,
    fetch_date = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    fetch_status = "success",
    source = "abcd_website"
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

cat("\n=== ABCD Parse Summary ===\n")
cat("Publications parsed:", nrow(parsed_tbl), "\n")
cat("With PubMed ID:", sum(!is.na(parsed_tbl$pmid) & parsed_tbl$pmid != ""), "\n")
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
