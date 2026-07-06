# ============================================================
# Build author_aliases.csv from reviewed alias_suggestions.csv
# Reads "Combine with?" as target line number in suggestions file
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tibble)
})

source("scripts/R/utils.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"
repo_root <- if (length(args) >= 2) args[2] else "."

dirs <- get_dataset_dirs(dataset_name, repo_root)
suggestions_path <- file.path(dirs$processed, "alias_suggestions.csv")
aliases_path <- file.path(dirs$processed, "author_aliases.csv")

if (!file.exists(suggestions_path)) {
  stop("alias_suggestions.csv not found: ", suggestions_path)
}

suggestions <- read_csv(suggestions_path, show_col_types = FALSE)

# Map file line number -> author_raw (header is line 1)
line_lookup <- tibble(
  file_line = seq_len(nrow(suggestions) + 1L),
  author_raw = c(NA_character_, suggestions$author_raw)
)

build_merge <- function(source_line, target_line, notes_suffix = "") {
  source_name <- line_lookup$author_raw[line_lookup$file_line == source_line]
  target_name <- line_lookup$author_raw[line_lookup$file_line == target_line]
  if (length(source_name) == 0 || is.na(source_name)) {
    stop("Invalid source line: ", source_line)
  }
  if (length(target_name) == 0 || is.na(target_name)) {
    stop("Invalid target line: ", target_line)
  }
  tibble(
    author_raw = source_name,
    author_id = target_name,
    notes = paste0(
      "Merged per reviewed alias_suggestions.csv (line ", source_line,
      " -> ", target_line, "). ", notes_suffix
    ),
    merged_by = "jmfletcher",
    merged_date = as.character(Sys.Date())
  )
}

# Rows with explicit Combine with? (value = target line in this file)
combine_col <- grep("Combine", names(suggestions), value = TRUE)[1]
merges <- list()

for (i in seq_len(nrow(suggestions))) {
  target_line <- suggestions[[combine_col]][i]
  if (is.na(target_line) || target_line == "") next
  source_line <- i + 1L # +1 for header row
  target_line <- as.integer(target_line)

  # Judd S lists combine=14 (Clarke PJ line); user intent is Judd SE (line 24)
  if (suggestions$author_raw[i] == "Judd S" && target_line == 14L) {
    target_line <- 24L
  }

  merges[[length(merges) + 1]] <- build_merge(
    source_line, target_line,
    if (suggestions$author_raw[i] == "Judd S") "Corrected target line to Judd SE." else ""
  )
}

aliases <- bind_rows(merges) %>%
  distinct(author_raw, .keep_all = TRUE) %>%
  filter(author_raw != author_id)

write_csv(aliases, aliases_path)

cat("Built", nrow(aliases), "alias merges ->", aliases_path, "\n")
print(aliases %>% select(author_raw, author_id))
