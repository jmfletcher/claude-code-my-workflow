# ============================================================
# Parse EdSHARe publications from bibliography scrape JSON
# Source: datasets/EdShare/raw/publications.json
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
dataset_name <- if (length(args) >= 1) args[1] else "EdShare"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

log_path <- file.path(dirs$raw, "fetch_log.txt")
json_path <- config$source$publications_json %||% file.path(dirs$raw, "publications.json")
if (!file.exists(json_path) && !is.null(config$source$parent_dataset)) {
  parent_dirs <- get_dataset_dirs(config$source$parent_dataset)
  json_path <- file.path(parent_dirs$raw, "publications.json")
}

if (!file.exists(json_path)) {
  stop(
    "Missing ", json_path,
    ". Run: .venv-ffcws/bin/python scripts/edshare/ingest_publications.py"
  )
}

records <- fromJSON(json_path, simplifyVector = FALSE)
cat("Loaded", length(records), "records from", json_path, "\n")

year_min <- config$source$pub_year_min %||% NULL
year_max <- config$source$pub_year_max %||% NULL
if (!is.null(year_min) || !is.null(year_max)) {
  records <- Filter(function(rec) {
    yr <- rec$pub_year %||% NULL
    if (is.null(yr) || length(yr) == 0 || is.na(as.integer(yr))) return(FALSE)
    yr <- as.integer(yr)
    if (!is.null(year_min) && yr < as.integer(year_min)) return(FALSE)
    if (!is.null(year_max) && yr > as.integer(year_max)) return(FALSE)
    TRUE
  }, records)
  cat(
    "Year filter",
    if (!is.null(year_min)) paste0(">=", year_min) else "",
    if (!is.null(year_max)) paste0("<=", year_max) else "",
    "->", length(records), "records\n"
  )
}

`%||%` <- function(x, y) if (is.null(x) || length(x) == 0) y else x

parse_record <- function(rec) {
  if (!identical(rec$fetch_status %||% "ok", "ok")) return(NULL)

  authors_raw <- rec$authors %||% list()
  authors <- unique(as.character(authors_raw))
  authors <- authors[nzchar(authors)]
  if (length(authors) == 0) return(NULL)

  title <- rec$title %||% NA_character_
  if (is.na(title) || !nzchar(str_squish(title))) return(NULL)

  tibble(
    paper_id = rec$paper_id,
    publication_id = rec$publication_id %||% NA_character_,
    title = str_squish(title),
    pub_year = as.integer(rec$pub_year %||% NA_integer_),
    doi = rec$doi %||% NA_character_,
    author_source = rec$author_source %||% "listing",
    author_list = paste(authors, collapse = "|"),
    n_authors = length(authors)
  )
}

parsed <- map(records, parse_record)
parsed_tbl <- bind_rows(parsed[!map_lgl(parsed, is.null)])

if (nrow(parsed_tbl) == 0) {
  stop("No EdShare publications parsed")
}

parsed_tbl <- parsed_tbl %>%
  arrange(desc(n_authors), paper_id) %>%
  distinct(title, .keep_all = TRUE) %>%
  distinct(paper_id, .keep_all = TRUE)

out_path <- file.path(dirs$raw, "edshare_publications.csv")
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
    publication_id = publication_id,
    doi = doi,
    fetch_date = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    fetch_status = "success",
    source = "edshare_bibliography"
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

cat("\n=== EdShare Parse Summary ===\n")
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
