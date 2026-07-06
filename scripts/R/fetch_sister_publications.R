# ============================================================
# Parse Sister Study publications from the NIEHS articles page.
# Entries are Vancouver-style citations inside <li> elements:
#   "Authors. Title. Journal. Year;..."  (few carry PubMed links)
# Outputs: raw/sister_publications.csv, processed/papers_authors.csv, papers.csv
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
dataset_name <- if (length(args) >= 1) args[1] else "Sister"

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

url <- config$source$collection_url
tmp <- tempfile()
status <- system2("curl", c("-sL", "-A", "DataMonopolies/1.0", "-o", tmp, shQuote(url)),
                  stdout = FALSE, stderr = FALSE)
if (status != 0) stop("curl failed for Sister articles page")
html <- readChar(tmp, file.info(tmp)$size, useBytes = TRUE)
unlink(tmp)

# Split into <li> blocks
li_blocks <- str_match_all(html, regex("<li[^>]*>(.*?)</li>", dotall = TRUE))[[1]][, 2]

clean_text <- function(x) {
  x <- gsub("<[^>]+>", " ", x)
  x <- gsub("&amp;", "&", x, fixed = TRUE)
  x <- gsub("&#8217;|&rsquo;|&#39;", "'", x)
  x <- gsub("&nbsp;", " ", x, fixed = TRUE)
  x <- gsub("&#8230;|&hellip;", "...", x)
  x <- gsub("\\s+", " ", x)
  str_trim(x)
}

texts <- vapply(li_blocks, clean_text, character(1))
# Keep citation-like: starts with "Lastname Initials" and contains a 19xx/20xx year
is_cite <- str_detect(texts, "^[A-Z][A-Za-z'-]+ [A-Z]") &
  str_detect(texts, "(19|20)[0-9]{2}")
cites <- unique(texts[is_cite])
# Also capture PubMed links per block (positional, best-effort)

parse_vancouver_authors <- function(author_part) {
  if (is.na(author_part) || author_part == "") return(character())
  s <- author_part
  s <- gsub("\\.{3}|…", "", s)              # drop ellipsis (truncated author lists)
  s <- gsub("\\s+et\\s+al\\.?$", "", s, ignore.case = TRUE)
  s <- str_trim(s)
  parts <- str_split(s, ",\\s*")[[1]]
  authors <- character()
  suffixes <- c("jr", "jr.", "sr", "sr.", "ii", "iii", "iv")
  for (part in parts) {
    part <- str_trim(part)
    if (part == "") next
    if (tolower(part) %in% suffixes) next
    m <- str_match(part, "^(.+?)\\s+([A-Z](?:\\s*[A-Z']*)*)$")
    if (is.na(m[1, 1])) next
    last <- str_trim(m[1, 2])
    initials <- gsub("[.[:space:]]", "", m[1, 3])
    authors <- c(authors, paste(last, initials))
  }
  unique(authors)
}

parse_cite <- function(citation) {
  # authors = text up to first ". " that precedes the title
  # year = first standalone 19xx/20xx
  ym <- str_match(citation, "\\b((?:19|20)[0-9]{2})\\b")
  pub_year <- if (!is.na(ym[1, 2])) as.integer(ym[1, 2]) else NA_integer_
  split <- str_match(citation, "^(.+?)\\.\\s+(.+)$")
  if (is.na(split[1, 1])) return(NULL)
  author_part <- split[1, 2]
  rest <- split[1, 3]
  title <- str_trim(str_split(rest, "\\.")[[1]][1])
  authors <- parse_vancouver_authors(author_part)
  if (length(authors) == 0) return(NULL)
  tibble(author_part = author_part, title = title, pub_year = pub_year,
         n_authors = length(authors), raw_citation = citation)
}

parsed <- map(cites, parse_cite)
parsed_tbl <- bind_rows(parsed[!map_lgl(parsed, is.null)])
parsed_tbl <- parsed_tbl %>%
  mutate(paper_id = paste0("sister_", row_number()))

write_csv(parsed_tbl, file.path(dirs$raw, "sister_publications.csv"))

papers_authors <- map_dfr(seq_len(nrow(parsed_tbl)), function(i) {
  row <- parsed_tbl[i, ]
  authors <- parse_vancouver_authors(row$author_part)
  if (length(authors) == 0) return(NULL)
  tibble(pmid = row$paper_id, title = row$title, pub_year = row$pub_year,
         author_raw = authors, author_id = authors,
         author_position = seq_along(authors), affiliation = NA_character_)
})
write_csv(papers_authors, file.path(dirs$processed, "papers_authors.csv"))

papers <- parsed_tbl %>%
  transmute(pmid = paper_id, title = title, abstract = NA_character_,
            pub_year = pub_year, text = title, has_abstract = FALSE)
write_csv(papers, file.path(dirs$processed, "papers.csv"))

config$source$last_fetched <- as.character(Sys.Date())
config$source$automated_fetch_count <- nrow(parsed_tbl)
yaml::write_yaml(config, file.path(dirs$base, "config.yaml"))

cat("\n=== Sister Parse Summary ===\n")
cat("Citations parsed:", nrow(parsed_tbl), "/", length(cites), "\n")
cat("Author rows:", nrow(papers_authors), "\n")
cat("Unique authors:", n_distinct(papers_authors$author_id), "\n")
cat("Year range:", min(parsed_tbl$pub_year, na.rm = TRUE), "-",
    max(parsed_tbl$pub_year, na.rm = TRUE), "\n")
