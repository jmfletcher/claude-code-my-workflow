# ============================================================
# Fetch MIDUS publications from UW publication database
# Source: https://midus.wisc.edu/pubdatabase.php
# Outputs: raw/midus_publications.csv, raw/fetch_log.txt
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
dataset_name <- if (length(args) >= 1) args[1] else "MIDUS"
max_pages <- if (length(args) >= 2) as.integer(args[2]) else NA_integer_

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

log_path <- file.path(dirs$raw, "fetch_log.txt")
base_url <- "https://midus.wisc.edu/pubdatabase.php"

fetch_page <- function(page, page_size = 30) {
  url <- paste0(
    base_url,
    "?search=%20&field=Author&date=&to=",
    "&pagesize=", page_size,
    "&order=Date&cf=0&page=", page
  )
  tmp <- tempfile()
  status <- system2(
    "curl",
    c("-sL", "-A", "DataMonopolies/1.0", "-o", tmp, shQuote(url)),
    stdout = FALSE, stderr = FALSE
  )
  if (status != 0 || !file.exists(tmp)) {
    stop("curl failed for page ", page)
  }
  html <- readChar(tmp, file.info(tmp)$size, useBytes = TRUE)
  unlink(tmp)
  html
}

extract_citations <- function(html) {
  # Normalize line breaks; do not use ignore.case here (would convert <BR> too)
  html <- gsub("<br\\s*/?>", "\n", html, ignore.case = FALSE)
  html <- gsub("<BR>", "\n", html, fixed = TRUE)
  blocks <- unlist(strsplit(html, "\n", fixed = TRUE))
  blocks <- trimws(blocks)
  blocks <- blocks[nchar(blocks) > 0]

  is_citation <- grepl("\\(\\d{4}\\)\\.", blocks) &
    !grepl("^View publication", blocks, ignore.case = TRUE)

  citation_idx <- which(is_citation)
  if (length(citation_idx) == 0) return(tibble())

  map_dfr(citation_idx, function(i) {
    citation <- gsub("<[^>]+>", " ", blocks[i])
    citation <- gsub("\\s+", " ", citation)
    citation <- trimws(citation)

    doi <- NA_character_
    if (i < length(blocks)) {
      doi_block <- paste(blocks[i:(min(i + 2, length(blocks)))], collapse = " ")
      doi <- str_match(doi_block, "DOI:([0-9./a-zA-Z-]+)")[, 2]
      doi <- str_trim(doi)
    }
    if (is.na(doi) || doi == "") return(NULL)

    year_match <- str_match(citation, "\\((\\d{4})\\)\\.\\s*(.+)$")
    if (is.na(year_match[1, 1])) return(NULL)

    pub_year <- as.integer(year_match[1, 2])
    rest <- year_match[1, 3]
    author_part <- str_match(citation, "^(.+?)\\(\\d{4}\\)\\.\\s*")[, 2]

    title <- str_match(rest, "^(.+?)\\.[A-Z][^\\.]*,")[, 2]
    if (is.na(title)) {
      title <- str_split(rest, "\\.")[[1]][1]
    }
    title <- str_trim(title)

    paper_id <- paste0("midus_doi_", gsub("[^a-zA-Z0-9]", "_", doi))

    tibble(
      paper_id = paper_id,
      pub_year = pub_year,
      title = title,
      doi = doi,
      author_part = author_part,
      raw_citation = citation
    )
  })
}

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
    last <- str_trim(m[2])
    initials <- gsub("[.\\s]", "", m[3])
    paste(last, initials)
  })
}

# First page: get total hits and page count
cat("Fetching MIDUS page 1...\n")
html1 <- fetch_page(1)
hits <- as.integer(str_match(html1, "Number of hits:\\s*(\\d+)")[, 2])
page_size <- 30L
total_pages <- ceiling(hits / page_size)

if (!is.na(max_pages)) {
  total_pages <- min(total_pages, max_pages)
  cat("Test mode: fetching", total_pages, "of", ceiling(hits / page_size), "pages\n")
}

cat("Expected publications:", hits, "| Pages:", total_pages, "\n")
writeLines(
  paste0(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), " | START | hits=", hits, " pages=", total_pages),
  log_path
)

all_pubs <- extract_citations(html1)
cat("Page 1:", nrow(all_pubs), "publications\n")

if (nrow(all_pubs) == 0) {
  stop("No publications parsed from page 1 — check HTML structure")
}

if (total_pages > 1) {
  for (page in 2:total_pages) {
    Sys.sleep(0.35)
    html <- fetch_page(page)
    pubs <- extract_citations(html)
    all_pubs <- bind_rows(all_pubs, pubs)
    if (page %% 10 == 0 || page == total_pages) {
      cat("Page", page, ":", nrow(pubs), "pubs | cumulative:", nrow(all_pubs), "\n")
    }
  }
}

all_pubs <- all_pubs %>% distinct(paper_id, .keep_all = TRUE)

# Assign IDs for any rows missing paper_id
all_pubs <- all_pubs %>%
  mutate(
    paper_id = if_else(
      is.na(paper_id),
      paste0("midus_seq_", row_number()),
      paper_id
    )
  )

out_path <- file.path(dirs$raw, "midus_publications.csv")
write_csv(all_pubs, out_path)

# Build papers_authors.csv
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

processed_path <- file.path(dirs$processed, "papers_authors.csv")
write_csv(papers_authors, processed_path)

# papers.csv for domain clustering
papers <- all_pubs %>%
  transmute(
    pmid = paper_id,
    title = title,
    abstract = NA_character_,
    pub_year = pub_year,
    text = title,
    has_abstract = FALSE
  )
write_csv(papers, file.path(dirs$processed, "papers.csv"))

manifest <- tibble(
  paper_id = all_pubs$paper_id,
  fetch_date = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
  fetch_status = "success",
  source = "midus_web"
)
write_csv(manifest, file.path(dirs$raw, "pubmed_manifest.csv"))

config$source$last_fetched <- as.character(Sys.Date())
config$source$automated_fetch_count <- nrow(all_pubs)
yaml_path <- file.path(dirs$base, "config.yaml")
yaml::write_yaml(config, yaml_path)

cat("\n=== MIDUS Fetch Summary ===\n")
cat("Publications:", nrow(all_pubs), "/", hits, "\n")
cat("Author rows:", nrow(papers_authors), "\n")
cat("Unique authors:", n_distinct(papers_authors$author_id), "\n")
cat("Output:", out_path, "\n")

if (nrow(all_pubs) != hits && is.na(max_pages)) {
  cat("NOTE: Count mismatch vs expected", hits, "\n")
}
