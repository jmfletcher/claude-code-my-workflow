# ============================================================
# Fetch and parse PROSPER publications from PPSI + PSU sources
# Primary: PPSI publications search (?search=prosper, ~260 papers)
# Supplement: ISU project bibliographies + PSU project pages
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(stringr)
  library(tibble)
  library(purrr)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "PROSPER"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

log_path <- file.path(dirs$raw, "fetch_log.txt")

fetch_html <- function(url, dest = NULL) {
  ua <- "Mozilla/5.0"
  html <- system2(
    "curl",
    c("-sL", "-A", ua, url),
    stdout = TRUE,
    stderr = FALSE
  )
  if (length(html) == 0) {
    stop("Failed to download: ", url)
  }
  html <- paste(html, collapse = "\n")
  if (!is.null(dest)) {
    dir.create(dirname(dest), recursive = TRUE, showWarnings = FALSE)
    writeLines(html, dest, useBytes = TRUE)
  }
  html
}

strip_html <- function(x) {
  x <- gsub("<[^>]+>", " ", x)
  x <- gsub("&amp;", "&", x, fixed = TRUE)
  x <- gsub("&nbsp;", " ", x, fixed = TRUE)
  x <- gsub("&#039;", "'", x, fixed = TRUE)
  str_squish(x)
}

normalize_title_key <- function(title) {
  title %>%
    tolower() %>%
    gsub("[^a-z0-9]+", " ", .) %>%
    str_squish()
}

normalize_biblio_author <- function(name) {
  name <- strip_html(name)
  name <- str_remove(name, regex("\\.$"))
  if (!str_detect(name, ",")) return(name)

  parts <- str_split(name, ",", n = 2)[[1]]
  last <- str_trim(parts[1])
  initials <- gsub("[^A-Za-z]", "", parts[2])
  paste(last, initials)
}

parse_biblio_authors <- function(block) {
  auth_match <- str_match(block, "class=\"biblio-authors\"[^>]*>(.*?)</span>")
  if (is.na(auth_match[1, 1])) return(character())

  auth_html <- auth_match[1, 2]
  auth_html <- gsub(",?\\s*&amp;?\\s*et al\\.?", "", auth_html, ignore.case = TRUE)

  links <- str_match_all(auth_html, "<a[^>]*>(.*?)</a>")[[1]][, 2]
  if (length(links) == 0) return(character())

  unique(vapply(links, normalize_biblio_author, character(1), USE.NAMES = FALSE))
}

extract_citation_blocks <- function(html) {
  project_blocks <- str_match_all(
    html,
    regex("views-field-citation.*?field-content\">(.*?)</span>\\s*</div>", dotall = TRUE)
  )[[1]][, 2]

  index_blocks <- str_match_all(
    html,
    regex("(<span class=\"biblio-authors\".*?</div>)", dotall = TRUE)
  )[[1]][, 2]

  blocks <- c(project_blocks, index_blocks)
  blocks <- blocks[!is.na(blocks) & nchar(blocks) > 0]
  unique(blocks)
}

parse_citation_block <- function(block, source_label) {
  title_match <- str_match(block, "class=\"biblio-title\"[^>]*>(.*?)</span>")
  title <- if (!is.na(title_match[1, 1])) strip_html(title_match[1, 2]) else NA_character_

  node_match <- str_match(block, "href=\"/node/(\\d+)\"")
  node_id <- if (!is.na(node_match[1, 1])) node_match[1, 2] else NA_character_

  year_match <- str_match(block, "\\((\\d{4}|In Press|in press)\\)")
  pub_year <- if (!is.na(year_match[1, 1]) && grepl("^\\d{4}$", year_match[1, 2])) {
    as.integer(year_match[1, 2])
  } else {
    NA_integer_
  }

  authors <- parse_biblio_authors(block)
  if (length(authors) == 0 || is.na(title) || title == "") return(NULL)

  paper_id <- if (!is.na(node_id)) {
    paste0("prosper_node_", node_id)
  } else {
    paste0("prosper_title_", substr(gsub("[^a-z0-9]", "", tolower(title)), 1, 40))
  }

  tibble(
    paper_id = paper_id,
    node_id = node_id,
    pub_year = pub_year,
    title = title,
    source = source_label,
    n_authors = length(authors),
    author_list = paste(authors, collapse = "|"),
    title_key = normalize_title_key(title),
    raw_citation = strip_html(block)
  )
}

parse_psu_project_citation <- function(slug, citation, source_label) {
  citation <- strip_html(citation)
  if (citation == "" || is.na(citation)) return(NULL)

  year_loc <- str_locate(citation, "\\(\\d{4}|In Press|in press")
  pub_year <- NA_integer_
  if (!is.na(year_loc[1, "start"])) {
    yr <- str_match(citation, "\\((\\d{4})")[, 2]
    if (!is.na(yr)) pub_year <- as.integer(yr)
  }

  pre <- if (!is.na(year_loc[1, "start"])) {
    substr(citation, 1, year_loc[1, "start"] - 1)
  } else {
    citation
  }
  pre <- str_trim(str_remove(pre, regex("\\.$")))

  split <- str_match(pre, "^(.+?)\\.\\s+(.+)$")
  if (is.na(split[1, 1])) return(NULL)

  auth_part <- split[1, 2]
  title <- str_trim(str_split(split[1, 3], "\\.")[[1]][1])

  authors <- str_split(auth_part, ",\\s*")[[1]] %>%
    str_trim() %>%
    discard(~ .x == "" || grepl("^(&|and)$", .x, ignore.case = TRUE)) %>%
    map_chr(~ if (str_detect(.x, ",")) normalize_biblio_author(.x) else .x) %>%
    unique()

  authors <- authors[nchar(authors) > 0]
  if (length(authors) == 0 || title == "") return(NULL)

  tibble(
    paper_id = paste0("prosper_psu_", slug),
    node_id = NA_character_,
    pub_year = pub_year,
    title = title,
    source = source_label,
    n_authors = length(authors),
    author_list = paste(authors, collapse = "|"),
    title_key = normalize_title_key(title),
    raw_citation = citation
  )
}

extract_psu_project_citations <- function(html, source_label) {
  slugs <- unique(str_match_all(
    html,
    "prevention\\.psu\\.edu/publication/([a-z0-9-]+)"
  )[[1]][, 2])

  map_dfr(slugs, function(slug) {
    pattern <- paste0("publication/", slug, "/[^\\n]*\\n\\n([^#\\n][^\\n]+)")
    m <- str_match(html, regex(pattern, ignore_case = TRUE))
    if (is.na(m[1, 1])) return(NULL)
    parse_psu_project_citation(slug, m[1, 2], source_label)
  })
}

dedupe_publications <- function(parsed_tbl) {
  parsed_tbl %>%
    arrange(desc(nchar(author_list)), source) %>%
    group_by(title_key) %>%
    slice(1) %>%
    ungroup() %>%
    mutate(
      paper_id = if_else(
        duplicated(paper_id) | is.na(paper_id),
        paste0("prosper_seq_", row_number()),
        paper_id
      )
    ) %>%
    distinct(paper_id, .keep_all = TRUE)
}

# --- Fetch sources ---
ppsi_search_url <- config$source$ppsi_search_url %||%
  "https://drupal.ppsi.iastate.edu/publications?search=prosper&page=0"
ppsi_project_urls <- config$source$ppsi_project_urls %||% character()
psu_project_urls <- config$source$psu_project_urls %||% character()

`%||%` <- function(x, y) if (is.null(x)) y else x

cat("Fetching PPSI PROSPER search corpus...\n")
ppsi_search_path <- file.path(dirs$raw, "ppsi_prosper_search.html")
ppsi_html <- fetch_html(ppsi_search_url, ppsi_search_path)
ppsi_blocks <- extract_citation_blocks(ppsi_html)
cat("  PPSI search blocks:", length(ppsi_blocks), "\n")

parsed <- map(ppsi_blocks, ~ parse_citation_block(.x, "ppsi_search"))
parsed_tbl <- bind_rows(parsed[!map_lgl(parsed, is.null)])

for (url in ppsi_project_urls) {
  label <- paste0("ppsi_", gsub("[^a-z0-9]+", "_", basename(url)))
  cat("Fetching supplemental PPSI project:", url, "\n")
  html <- fetch_html(url)
  blocks <- extract_citation_blocks(html)
  extra <- bind_rows(map(blocks, ~ parse_citation_block(.x, label)))
  parsed_tbl <- bind_rows(parsed_tbl, extra)
}

for (url in psu_project_urls) {
  label <- paste0("psu_", gsub("[^a-z0-9]+", "_", basename(url)))
  cat("Fetching supplemental PSU project:", url, "\n")
  html <- fetch_html(url)
  extra <- extract_psu_project_citations(html, label)
  parsed_tbl <- bind_rows(parsed_tbl, extra)
}

if (nrow(parsed_tbl) == 0) {
  stop("No PROSPER citations parsed from any source")
}

before_dedup <- nrow(parsed_tbl)
parsed_tbl <- dedupe_publications(parsed_tbl)
cat("Publications before dedup:", before_dedup, "| after dedup:", nrow(parsed_tbl), "\n")

out_path <- file.path(dirs$raw, "prosper_publications.csv")
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
    node_id = node_id,
    source = source,
    fetch_date = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    fetch_status = "success"
  )
write_csv(manifest, file.path(dirs$raw, "pubmed_manifest.csv"))

config$source$last_fetched <- as.character(Sys.Date())
config$source$automated_fetch_count <- nrow(parsed_tbl)
yaml::write_yaml(config, file.path(dirs$base, "config.yaml"))

log_fetch(log_path, paste0(
  "PARSE | papers=", nrow(parsed_tbl),
  " authors=", n_distinct(papers_authors$author_id),
  " deduped=", before_dedup - nrow(parsed_tbl)
))

cat("\n=== PROSPER Parse Summary ===\n")
cat("Publications:", nrow(parsed_tbl), "\n")
cat("By source:\n")
print(count(parsed_tbl, source, sort = TRUE))
cat("Author rows:", nrow(papers_authors), "\n")
cat("Unique authors:", n_distinct(papers_authors$author_id), "\n")
if (any(!is.na(parsed_tbl$pub_year))) {
  cat("Year range:", min(parsed_tbl$pub_year, na.rm = TRUE), "-",
      max(parsed_tbl$pub_year, na.rm = TRUE), "\n")
}
cat("Output:", out_path, "\n")
