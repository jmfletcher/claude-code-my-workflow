# ============================================================
# Fetch and parse MESA publications from NHLBI chronological docx
# Source: https://tools.mesa-nhlbi.org/MESA_Files/publications/
# Outputs: raw/mesa_publications.csv, processed/papers_authors.csv
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
dataset_name <- if (length(args) >= 1) args[1] else "MESA"
docx_arg <- if (length(args) >= 2) args[2] else NA_character_

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

log_path <- file.path(dirs$raw, "fetch_log.txt")

default_docx <- file.path(
  dirs$raw,
  "MESA_Published_Papers_Chronological_5-6-2026.docx"
)
docx_path <- if (!is.na(docx_arg) && nzchar(docx_arg)) docx_arg else default_docx

if (!file.exists(docx_path)) {
  source_url <- config$source$collection_url
  cat("Downloading MESA publications docx...\n")
  status <- system2(
    "curl",
    c("-sL", "-A", "DataMonopolies/1.0", "-o", shQuote(docx_path), shQuote(source_url)),
    stdout = FALSE,
    stderr = FALSE
  )
  if (status != 0 || !file.exists(docx_path)) {
    stop("Failed to download MESA docx from ", source_url)
  }
}

extract_docx_paragraphs <- function(path) {
  tmp <- tempfile()
  dir.create(tmp)
  on.exit(unlink(tmp, recursive = TRUE), add = TRUE)
  utils::unzip(path, "word/document.xml", exdir = tmp)
  xml_path <- file.path(tmp, "word/document.xml")
  raw <- readChar(xml_path, file.info(xml_path)$size, useBytes = TRUE)
  raw <- gsub("</w:p>", "\n", raw, fixed = TRUE)
  raw <- gsub("<[^>]+>", "", raw)
  raw <- gsub("&amp;", "&", raw, fixed = TRUE)
  raw <- gsub("&lt;", "<", raw, fixed = TRUE)
  raw <- gsub("&gt;", ">", raw, fixed = TRUE)
  texts <- str_trim(strsplit(raw, "\n", fixed = TRUE)[[1]])
  texts[nchar(texts) > 0]
}

merge_citations <- function(paragraphs) {
  paragraphs <- paragraphs[
    !grepl("^(PUBLISHED PAPERS|CHRONOLOGICAL)", paragraphs, ignore.case = TRUE)
  ]
  cites <- character()
  buf <- character()
  year_end <- "\\.\\s*\\d{4}[;:][^\\.]+\\.\\s*$"

  for (p in paragraphs) {
    buf <- c(buf, p)
    joined <- str_squish(paste(buf, collapse = " "))
    if (grepl(year_end, joined)) {
      cites <- c(cites, joined)
      buf <- character()
    }
  }

  if (length(buf) > 0) {
    cites <- c(cites, str_squish(paste(buf, collapse = " ")))
  }
  cites
}

parse_vancouver_authors <- function(author_part) {
  if (is.na(author_part) || author_part == "") return(character())

  s <- author_part
  s <- gsub("\\s+et\\s+al\\.?$", "", s, ignore.case = TRUE)
  s <- str_trim(s)

  parts <- str_split(s, ",\\s*")[[1]]
  authors <- character()
  suffixes <- c("jr", "jr.", "sr", "sr.", "ii", "iii", "iv")

  for (part in parts) {
    part <- str_trim(part)
    if (part == "") next

    if (tolower(part) %in% suffixes) {
      if (length(authors) > 0) {
        authors[length(authors)] <- paste(authors[length(authors)], part)
      }
      next
    }

    m <- str_match(part, "^(.+?)\\s+([A-Z](?:\\s*[A-Z']*)*)$")
    if (is.na(m[1, 1])) next

    last <- str_trim(m[1, 2])
    initials <- gsub("[.\\s]", "", m[1, 3])
    authors <- c(authors, paste(last, initials))
  }

  unique(authors)
}

parse_citation <- function(citation) {
  year_loc <- str_locate(citation, "\\.\\s*(\\d{4})[;:]")
  if (is.na(year_loc[1, "start"])) return(NULL)

  year_match <- str_match(citation, "\\.\\s*(\\d{4})[;:]")
  pub_year <- as.integer(year_match[1, 2])
  pre <- substr(citation, 1, year_loc[1, "start"] - 1)

  split <- str_match(pre, "^(.+?)\\.\\s+(.+)$")
  if (is.na(split[1, 1])) return(NULL)

  author_part <- split[1, 2]
  title_journal <- split[1, 3]
  title <- str_trim(str_remove(title_journal, "\\.[^.]*$"))
  authors <- parse_vancouver_authors(author_part)

  if (length(authors) == 0) return(NULL)

  paper_slug <- gsub("[^a-zA-Z0-9]+", "_", tolower(title))
  paper_slug <- substr(paper_slug, 1, 40)
  paper_id <- paste0("mesa_", pub_year, "_", paper_slug)

  tibble(
    paper_id = paper_id,
    pub_year = pub_year,
    title = title,
    author_part = author_part,
    n_authors = length(authors),
    raw_citation = citation
  )
}

cat("Parsing MESA docx:", docx_path, "\n")
paragraphs <- extract_docx_paragraphs(docx_path)
citations <- merge_citations(paragraphs)
cat("Paragraphs:", length(paragraphs), "| Merged citations:", length(citations), "\n")

parsed <- map(citations, parse_citation)
parsed_tbl <- bind_rows(parsed[!map_lgl(parsed, is.null)])

if (nrow(parsed_tbl) == 0) {
  stop("No citations parsed from MESA docx")
}

parsed_tbl <- parsed_tbl %>%
  mutate(
    paper_id = if_else(
      duplicated(paper_id) | is.na(paper_id),
      paste0(paper_id, "_", row_number()),
      paper_id
    )
  ) %>%
  distinct(paper_id, .keep_all = TRUE)

fail_n <- length(citations) - nrow(parsed_tbl)
if (fail_n > 0) {
  cat("WARNING:", fail_n, "citations failed author parse\n")
}

out_path <- file.path(dirs$raw, "mesa_publications.csv")
write_csv(parsed_tbl, out_path)

papers_authors <- map_dfr(seq_len(nrow(parsed_tbl)), function(i) {
  row <- parsed_tbl[i, ]
  authors <- parse_vancouver_authors(row$author_part)
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

manifest <- tibble(
  paper_id = parsed_tbl$paper_id,
  fetch_date = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
  fetch_status = "success",
  source = "mesa_docx"
)
write_csv(manifest, file.path(dirs$raw, "pubmed_manifest.csv"))

config$source$last_fetched <- as.character(Sys.Date())
config$source$automated_fetch_count <- nrow(parsed_tbl)
yaml::write_yaml(config, file.path(dirs$base, "config.yaml"))

log_fetch(log_path, paste0(
  "PARSE | papers=", nrow(parsed_tbl),
  " authors=", n_distinct(papers_authors$author_id),
  " failed=", fail_n
))

cat("\n=== MESA Parse Summary ===\n")
cat("Citations parsed:", nrow(parsed_tbl), "/", length(citations), "\n")
cat("Author rows:", nrow(papers_authors), "\n")
cat("Unique authors:", n_distinct(papers_authors$author_id), "\n")
cat("Year range:", min(parsed_tbl$pub_year), "-", max(parsed_tbl$pub_year), "\n")
cat("Output:", out_path, "\n")
