# ============================================================
# Fetch NHATS publications from the study website (paginated cards).
# Each card exposes title, "Authors:" (Vancouver), year, and a DOI.
# Outputs: raw/nhats_publications.csv, processed/papers_authors.csv, papers.csv
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
dataset_name <- if (length(args) >= 1) args[1] else "NHATS"
max_pages <- if (length(args) >= 2) as.integer(args[2]) else NA_integer_

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

page_size <- 100L
base_url <- "https://www.nhats.org/publications/search"

fetch_page <- function(page) {
  url <- paste0(base_url, "?items_per_page=", page_size, "&page=", page)
  tmp <- tempfile()
  status <- system2("curl", c("-sL", "-A", "DataMonopolies/1.0", "-o", tmp, shQuote(url)),
                    stdout = FALSE, stderr = FALSE)
  if (status != 0 || !file.exists(tmp)) stop("curl failed for NHATS page ", page)
  html <- readChar(tmp, file.info(tmp)$size, useBytes = TRUE)
  unlink(tmp)
  html
}

unescape <- function(x) {
  x <- gsub("&amp;", "&", x, fixed = TRUE)
  x <- gsub("&#039;|&#39;|&rsquo;|&#8217;", "'", x)
  x <- gsub("&quot;", '"', x, fixed = TRUE)
  x <- gsub("&nbsp;", " ", x, fixed = TRUE)
  x
}

parse_vancouver_authors <- function(author_part) {
  if (is.na(author_part) || author_part == "") return(character())
  s <- gsub("\\s+et\\s+al\\.?$", "", str_trim(author_part), ignore.case = TRUE)
  parts <- str_split(s, ",\\s*")[[1]]
  authors <- character()
  for (part in parts) {
    part <- str_trim(part)
    if (part == "") next
    if (tolower(part) %in% c("jr", "jr.", "sr", "sr.", "ii", "iii", "iv")) next
    m <- str_match(part, "^(.+?)\\s+([A-Z](?:\\s*[A-Z']*)*)$")
    if (is.na(m[1, 1])) next
    authors <- c(authors, paste(str_trim(m[1, 2]), gsub("[.[:space:]]", "", m[1, 3])))
  }
  unique(authors)
}

extract_cards <- function(html) {
  # Split at each title marker; each chunk carries its own authors/year/doi
  chunks <- str_split(html, "field--label-hidden\">")[[1]]
  if (length(chunks) < 2) return(tibble())
  chunks <- chunks[-1]
  map_dfr(chunks, function(ch) {
    ch <- gsub("[\r\n\t]+", " ", ch)
    title <- str_match(ch, "^(.*?)</span>")[, 2]
    if (is.na(title)) return(NULL)
    title <- str_trim(unescape(gsub("<[^>]+>", "", title)))
    au <- str_match(ch, "Authors:</span>(.*?)</div>")[, 2]
    if (is.na(au)) return(NULL)
    author_part <- str_trim(unescape(gsub("<[^>]+>", " ", au)))
    author_part <- str_trim(gsub("\\s+", " ", author_part))
    # limit search window to this card for year/doi
    win <- substr(ch, 1, 1500)
    yr <- str_match(win, "(20[0-2][0-9])")[, 2]
    doi <- str_match(win, "doi\\.org/([^\"'<> ]+)")[, 2]
    if (!is.na(doi)) doi <- utils::URLdecode(doi)
    tibble(title = title, author_part = author_part,
           pub_year = if (!is.na(yr)) as.integer(yr) else NA_integer_,
           doi = if (is.na(doi)) NA_character_ else doi)
  })
}

all_cards <- tibble()
page <- 0L
repeat {
  html <- fetch_page(page)
  cards <- extract_cards(html)
  cat("Page", page, ":", nrow(cards), "cards\n")
  if (nrow(cards) == 0) break
  all_cards <- bind_rows(all_cards, cards)
  page <- page + 1L
  if (!is.na(max_pages) && page >= max_pages) break
  Sys.sleep(0.35)
}

all_cards <- all_cards %>%
  filter(!is.na(author_part), author_part != "") %>%
  mutate(paper_id = if_else(!is.na(doi) & doi != "",
                            paste0("nhats_doi_", gsub("[^a-zA-Z0-9]", "_", doi)),
                            paste0("nhats_seq_", row_number()))) %>%
  distinct(paper_id, .keep_all = TRUE)

write_csv(all_cards, file.path(dirs$raw, "nhats_publications.csv"))

papers_authors <- map_dfr(seq_len(nrow(all_cards)), function(i) {
  row <- all_cards[i, ]
  authors <- parse_vancouver_authors(row$author_part)
  if (length(authors) == 0) return(NULL)
  tibble(pmid = row$paper_id, title = row$title, pub_year = row$pub_year,
         author_raw = authors, author_id = authors,
         author_position = seq_along(authors), affiliation = NA_character_)
})
write_csv(papers_authors, file.path(dirs$processed, "papers_authors.csv"))

papers <- all_cards %>%
  transmute(pmid = paper_id, title = title, abstract = NA_character_,
            pub_year = pub_year, text = title, has_abstract = FALSE)
write_csv(papers, file.path(dirs$processed, "papers.csv"))

config$source$last_fetched <- as.character(Sys.Date())
config$source$automated_fetch_count <- nrow(all_cards)
yaml::write_yaml(config, file.path(dirs$base, "config.yaml"))

cat("\n=== NHATS Fetch Summary ===\n")
cat("Publications:", nrow(all_cards), "\n")
cat("Author rows:", nrow(papers_authors), "\n")
cat("Unique authors:", n_distinct(papers_authors$author_id), "\n")
cat("Year range:", min(all_cards$pub_year, na.rm = TRUE), "-",
    max(all_cards$pub_year, na.rm = TRUE), "\n")
