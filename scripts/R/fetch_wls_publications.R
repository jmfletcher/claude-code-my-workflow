# ============================================================
# Fetch WLS publications from Zotero group library API
# Source: https://www.zotero.org/groups/wisconsinlongitudinalstudy
# Outputs: raw/wls_publications.csv, processed/papers_authors.csv
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
dataset_name <- if (length(args) >= 1) args[1] else "WLS"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

log_path <- file.path(dirs$raw, "fetch_log.txt")

`%||%` <- function(x, y) if (is.null(x) || length(x) == 0 || (is.character(x) && !any(nzchar(x)))) y else x

zotero_get <- function(group_id, start, limit = 100L) {
  base <- sprintf("https://api.zotero.org/groups/%s/items/top", group_id)
  raw <- system2(
    "curl",
    c(
      "-sL", "-D", "-", "-H", "Zotero-API-Version: 3", base,
      "-G", "-d", paste0("start=", start), "-d", paste0("limit=", limit),
      "-d", "format=json"
    ),
    stdout = TRUE,
    stderr = FALSE
  )
  if (length(raw) == 0) {
    stop("Zotero API request failed: ", base)
  }
  text <- paste(raw, collapse = "\n")
  split <- strsplit(text, "\r\n\r\n|\n\n", perl = TRUE)[[1]]
  if (length(split) < 2) stop("Unexpected Zotero API response")
  hdr <- split[1]
  body <- paste(split[-1], collapse = "\n")
  total_line <- grep("^Total-Results:", strsplit(hdr, "\n")[[1]], value = TRUE)
  total <- if (length(total_line)) {
    as.integer(sub(".*:\\s*", "", total_line[1]))
  } else {
    NA_integer_
  }
  list(body = body, total = total)
}

fetch_all_zotero_items <- function(group_id) {
  limit <- 100L
  start <- 0L
  all_items <- list()
  total <- NA_integer_

  repeat {
    resp <- zotero_get(group_id, start, limit)
    if (is.na(total) && !is.na(resp$total)) total <- resp$total
    batch <- fromJSON(resp$body, simplifyVector = FALSE)
    if (length(batch) == 0) break
    all_items <- c(all_items, batch)
    cat("  fetched", length(all_items), "/", total, "\n")
    start <- start + limit
    if (!is.na(total) && length(all_items) >= total) break
    Sys.sleep(0.35)
  }
  all_items
}

normalize_zotero_creator <- function(creator) {
  if (!is.null(creator$name) && nzchar(creator$name)) {
    return(str_squish(creator$name))
  }
  last <- creator$lastName %||% ""
  first <- creator$firstName %||% ""
  if (!nzchar(last)) return(NA_character_)
  initials <- str_replace_all(first, "[^A-Za-z]+", " ")
  initials <- initials %>%
    str_split("\\s+") %>%
    unlist() %>%
    str_sub(1, 1) %>%
    paste(collapse = "")
  str_squish(paste(last, initials))
}

parse_zotero_creators <- function(creators) {
  if (length(creators) == 0) return(character())
  types <- vapply(creators, function(c) c$creatorType %||% "author", character(1))
  author_creators <- creators[types == "author"]
  if (length(author_creators) == 0) author_creators <- creators
  authors <- vapply(author_creators, normalize_zotero_creator, character(1))
  authors <- authors[!is.na(authors) & nzchar(authors)]
  unique(authors)
}

parse_pub_year <- function(item) {
  date_val <- item$meta$parsedDate %||% item$data$date %||% ""
  if (!nzchar(date_val)) return(NA_integer_)
  yr <- str_match(date_val, "(\\d{4})")[, 2]
  if (is.na(yr)) return(NA_integer_)
  as.integer(yr)
}

parse_zotero_item <- function(item) {
  data <- item$data
  item_type <- data$itemType %||% "unknown"
  if (item_type %in% c("attachment", "note")) return(NULL)

  creators <- data$creators %||% list()
  authors <- parse_zotero_creators(creators)
  if (length(authors) == 0) return(NULL)

  key <- data$key
  title <- data$title %||% data$name %||% NA_character_
  if (is.na(title) || !nzchar(title)) return(NULL)

  tibble(
    paper_id = paste0("wls_zotero_", key),
    zotero_key = key,
    item_type = item_type,
    title = str_squish(title),
    pub_year = parse_pub_year(item),
    doi = data$DOI %||% NA_character_,
    url = data$url %||% NA_character_,
    author_list = paste(authors, collapse = "|"),
    n_authors = length(authors)
  )
}

group_id <- config$source$zotero_group_id %||% "5400572"
cat("Fetching WLS Zotero group", group_id, "...\n")
items <- fetch_all_zotero_items(group_id)

parsed <- map(items, parse_zotero_item)
parsed_tbl <- bind_rows(parsed[!map_lgl(parsed, is.null)])

if (nrow(parsed_tbl) == 0) {
  stop("No WLS publications parsed from Zotero library")
}

parsed_tbl <- parsed_tbl %>% distinct(paper_id, .keep_all = TRUE)

out_path <- file.path(dirs$raw, "wls_publications.csv")
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
    zotero_key = zotero_key,
    item_type = item_type,
    fetch_date = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    fetch_status = "success",
    source = paste0("zotero_group_", group_id)
  )
write_csv(manifest, file.path(dirs$raw, "pubmed_manifest.csv"))

config$source$last_fetched <- as.character(Sys.Date())
config$source$automated_fetch_count <- nrow(parsed_tbl)
yaml::write_yaml(config, file.path(dirs$base, "config.yaml"))

log_fetch(log_path, paste0(
  "PARSE | papers=", nrow(parsed_tbl),
  " authors=", n_distinct(papers_authors$author_id),
  " zotero_items=", length(items)
))

cat("\n=== WLS Zotero Parse Summary ===\n")
cat("Zotero items fetched:", length(items), "\n")
cat("Publications parsed:", nrow(parsed_tbl), "\n")
cat("By item type:\n")
print(count(parsed_tbl, item_type, sort = TRUE))
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
