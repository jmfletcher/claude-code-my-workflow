# ============================================================
# Fetch ADNI publications from the study website table.
# Server-side paginated: ?q=&size={10*(page-1)}&page_no={page}, 10 rows/page.
# Row = Year | Title | Author (initials-first, ';'-separated) | Journal.
# Outputs: raw/adni_publications.csv, processed/papers_authors.csv, papers.csv
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
dataset_name <- if (length(args) >= 1) args[1] else "ADNI"
max_pages <- if (length(args) >= 2) as.integer(args[2]) else 800L

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
ensure_dataset_dirs(dirs)

base <- "https://adni.loni.usc.edu/news-publications/publications/"
UA <- "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

fetch_page <- function(page) {
  url <- paste0(base, "?q=&size=", (page - 1L) * 10L, "&page_no=", page)
  tmp <- tempfile()
  status <- system2("curl", c("-sL", "-A", shQuote(UA), "-o", tmp, shQuote(url)),
                    stdout = FALSE, stderr = FALSE)
  if (status != 0 || !file.exists(tmp)) return(NA_character_)
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
cell_text <- function(x) str_trim(gsub("\\s+", " ", unescape(gsub("<[^>]+>", " ", x))))

# Convert "A. Safai" / "W. R. Buckingham" / "C. van Dyck" -> "Safai A" / "Buckingham WR"
parse_initials_first <- function(author_field) {
  if (is.na(author_field) || author_field == "") return(character())
  parts <- str_split(author_field, ";")[[1]]
  out <- character()
  for (p in parts) {
    p <- str_trim(p)
    if (p == "" || tolower(p) %in% c("et al", "et al.")) next
    toks <- str_split(str_trim(p), "\\s+")[[1]]
    is_init <- str_detect(toks, "^[A-Z]\\.?$")
    # leading run of initials
    k <- 0L
    for (t in is_init) { if (t) k <- k + 1L else break }
    if (k == 0L || k >= length(toks)) {
      # fallback: last token initial(s)?
      m <- str_match(p, "^([A-Z](?:\\.?\\s*[A-Z]\\.?)*)\\s+(.+)$")
      if (is.na(m[1, 1])) next
      initials <- gsub("[.[:space:]]", "", m[1, 2])
      last <- str_trim(m[1, 3])
    } else {
      initials <- gsub("[.[:space:]]", "", paste(toks[seq_len(k)], collapse = ""))
      last <- paste(toks[(k + 1L):length(toks)], collapse = " ")
    }
    last <- str_trim(gsub("[.,]$", "", last))
    if (last == "") next
    out <- c(out, paste(last, initials))
  }
  unique(out)
}

extract_rows <- function(html) {
  rows <- str_match_all(html, regex("<tr[^>]*>(.*?)</tr>", dotall = TRUE))[[1]][, 2]
  if (length(rows) == 0) return(tibble())
  map_dfr(rows, function(r) {
    cells <- str_match_all(r, regex("<td[^>]*>(.*?)</td>", dotall = TRUE))[[1]][, 2]
    if (length(cells) < 4) return(NULL)
    yr <- cell_text(cells[1])
    tibble(
      pub_year = suppressWarnings(as.integer(str_extract(yr, "(19|20)[0-9]{2}"))),
      title = cell_text(cells[2]),
      author_field = cell_text(cells[3]),
      journal = cell_text(cells[4])
    )
  })
}

all_rows <- tibble()
page <- 1L
empty_streak <- 0L
repeat {
  html <- fetch_page(page)
  if (is.na(html)) { empty_streak <- empty_streak + 1L; if (empty_streak >= 3) break; page <- page + 1L; next }
  rows <- extract_rows(html)
  n <- nrow(rows)
  if (page %% 50L == 0L || page == 1L) cat("Page", page, ":", n, "rows (total", nrow(all_rows) + n, ")\n")
  if (n == 0) { empty_streak <- empty_streak + 1L; if (empty_streak >= 2) break } else empty_streak <- 0L
  all_rows <- bind_rows(all_rows, rows)
  page <- page + 1L
  if (page > max_pages) break
  Sys.sleep(0.25)
}

all_rows <- all_rows %>%
  filter(!is.na(author_field), author_field != "") %>%
  mutate(paper_id = paste0("adni_", row_number())) %>%
  distinct(title, author_field, .keep_all = TRUE)

write_csv(all_rows, file.path(dirs$raw, "adni_publications.csv"))

papers_authors <- map_dfr(seq_len(nrow(all_rows)), function(i) {
  row <- all_rows[i, ]
  authors <- parse_initials_first(row$author_field)
  if (length(authors) == 0) return(NULL)
  tibble(pmid = row$paper_id, title = row$title, pub_year = row$pub_year,
         author_raw = authors, author_id = authors,
         author_position = seq_along(authors), affiliation = NA_character_)
})
write_csv(papers_authors, file.path(dirs$processed, "papers_authors.csv"))

papers <- all_rows %>%
  transmute(pmid = paper_id, title = title, abstract = NA_character_,
            pub_year = pub_year, text = title, has_abstract = FALSE)
write_csv(papers, file.path(dirs$processed, "papers.csv"))

config$source$last_fetched <- as.character(Sys.Date())
config$source$automated_fetch_count <- nrow(all_rows)
yaml::write_yaml(config, file.path(dirs$base, "config.yaml"))

cat("\n=== ADNI Fetch Summary ===\n")
cat("Publications:", nrow(all_rows), "\n")
cat("Author rows:", nrow(papers_authors), "\n")
cat("Unique authors:", n_distinct(papers_authors$author_id), "\n")
cat("Year range:", min(all_rows$pub_year, na.rm = TRUE), "-",
    max(all_rows$pub_year, na.rm = TRUE), "\n")
