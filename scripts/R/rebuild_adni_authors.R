# ============================================================
# Rebuild ADNI papers_authors.csv from raw/adni_publications.csv.
# The ADNI table mixes two author formats:
#   (1) initials-first, ';'-separated:  "D. J. Terstege; Y. Ren; ..."
#   (2) last-first, ','-separated w/ 'and': "Chen, Q, Abrigo, J and Chu, WCW"
# No re-scrape required.
# ============================================================

suppressPackageStartupMessages({
  library(readr); library(dplyr); library(stringr); library(tibble); library(purrr)
})

source("scripts/R/utils.R")
dataset_name <- "ADNI"
dirs <- get_dataset_dirs(dataset_name)

raw <- read_csv(file.path(dirs$raw, "adni_publications.csv"), show_col_types = FALSE)

# Format 1: "A. B. Lastname" (leading initials, may be multiword surname)
parse_one_initials_first <- function(p) {
  p <- str_trim(p)
  toks <- str_split(p, "\\s+")[[1]]
  is_init <- str_detect(toks, "^\\p{Lu}\\.?$")
  k <- 0L
  for (t in is_init) { if (t) k <- k + 1L else break }
  if (k == 0L || k >= length(toks)) return(NA_character_)
  initials <- gsub("[.[:space:]]", "", paste(toks[seq_len(k)], collapse = ""))
  last <- str_trim(gsub("[.,]+$", "", paste(toks[(k + 1L):length(toks)], collapse = " ")))
  last <- str_trim(gsub("^[^\\p{L}]+", "", last, perl = TRUE))
  if (last == "") return(NA_character_)
  paste(last, initials)
}

# Format 2: last-first tokens (comma/"and" separated) as (surname, given) pairs.
# given may be initials ("W.", "YX"), or full names ("Jialin", "Rachel F").
initials_from_given <- function(g) {
  words <- str_split(str_trim(g), "[^A-Za-z]+")[[1]]
  words <- words[words != ""]
  if (length(words) == 0) return("")
  paste(vapply(words, function(w) {
    if (toupper(w) == w) w else toupper(substr(w, 1, 1))
  }, character(1)), collapse = "")
}

is_consortium <- function(surname) {
  str_detect(surname, regex(paste0("initiative|neuroimaging|consortium|\\bgroup\\b|network|",
                                   "investigators|alzheimer|aging brain|rejuvenation|",
                                   "\\bstudy\\b|collaborat"),
                            ignore_case = TRUE))
}

parse_last_first_commas <- function(s) {
  s <- gsub("\\s+and\\s+", ", ", s)
  toks <- str_trim(str_split(s, ",")[[1]])
  toks <- toks[toks != ""]
  out <- character()
  i <- 1L
  while (i < length(toks) + 1L) {
    surname <- toks[i]
    given <- if (i + 1L <= length(toks)) toks[i + 1L] else ""
    i <- i + 2L
    if (is_consortium(surname)) next
    inits <- initials_from_given(given)
    surname <- str_trim(gsub("[.,]+$", "", surname))
    surname <- str_trim(gsub("^[^\\p{L}]+", "", surname, perl = TRUE))
    if (surname == "" || inits == "") next
    out <- c(out, paste(surname, inits))
  }
  unique(out[out != ""])
}

parse_adni_authors <- function(field) {
  if (is.na(field) || field == "") return(character())
  field <- str_trim(gsub("\\s+et al\\.?$", "", field, ignore.case = TRUE))
  if (str_detect(field, ";")) {
    parts <- str_split(field, ";")[[1]]
    res <- vapply(parts, parse_one_initials_first, character(1))
    return(unique(res[!is.na(res)]))
  }
  # no semicolon: could be single initials-first author OR last-first comma list
  if (str_detect(field, ",")) {
    res <- parse_last_first_commas(field)
    if (length(res) > 0) return(res)
  }
  r <- parse_one_initials_first(field)
  if (is.na(r)) character() else r
}

papers_authors <- map_dfr(seq_len(nrow(raw)), function(i) {
  row <- raw[i, ]
  authors <- parse_adni_authors(row$author_field)
  if (length(authors) == 0) return(NULL)
  tibble(pmid = row$paper_id, title = row$title, pub_year = row$pub_year,
         author_raw = authors, author_id = authors,
         author_position = seq_along(authors), affiliation = NA_character_)
})
write_csv(papers_authors, file.path(dirs$processed, "papers_authors.csv"))

papers <- raw %>%
  transmute(pmid = paper_id, title = title, abstract = NA_character_,
            pub_year = pub_year, text = title, has_abstract = FALSE)
write_csv(papers, file.path(dirs$processed, "papers.csv"))

cat("Rebuilt ADNI authors\n")
cat("Papers with authors:", n_distinct(papers_authors$pmid), "/", nrow(raw), "\n")
cat("Author rows:", nrow(papers_authors), "\n")
cat("Unique authors:", n_distinct(papers_authors$author_id), "\n")
