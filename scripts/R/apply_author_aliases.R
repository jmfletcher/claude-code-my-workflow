# ============================================================
# Apply author alias merges
# Purpose: Merge duplicate author strings via alias table
# Inputs: papers_authors.csv, author_aliases.csv
# Outputs: updated papers_authors.csv with author_id column
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
})

source("scripts/R/utils.R")
source("scripts/R/author_alias_helpers.R")

apply_author_aliases <- function(papers_authors, aliases_path) {
  if (!file.exists(aliases_path)) {
    return(papers_authors %>% mutate(author_id = author_raw))
  }

  aliases <- read_csv(aliases_path, show_col_types = FALSE)
  if (nrow(aliases) == 0) {
    return(papers_authors %>% mutate(author_id = author_raw))
  }

  # Validate required columns
  required <- c("author_raw", "author_id", "notes")
  missing <- setdiff(required, names(aliases))
  if (length(missing) > 0) {
    stop("author_aliases.csv missing columns: ", paste(missing, collapse = ", "))
  }

  alias_map <- aliases %>%
    select(author_raw, author_id_canonical = author_id)

  papers_authors %>%
    left_join(alias_map, by = "author_raw") %>%
    mutate(author_id = coalesce(author_id_canonical, author_raw)) %>%
    select(-author_id_canonical)
}

#' Suggest potential duplicate authors for human review
suggest_author_aliases <- function(papers_authors, min_papers = 5) {
  author_stats <- papers_authors %>%
    count(author_raw, name = "n_papers") %>%
    filter(n_papers >= min_papers) %>%
    mutate(
      last_name = sub(" .*", "", author_raw),
      initials = sub("^[^ ]+ ", "", author_raw)
    )

  suggestions <- author_stats %>%
    group_by(last_name) %>%
    filter(n() > 1) %>%
    arrange(last_name, desc(n_papers)) %>%
    ungroup()

  suggestions
}

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"
repo_root <- if (length(args) >= 2) args[2] else "."

dirs <- get_dataset_dirs(dataset_name, repo_root)
papers_path <- file.path(dirs$processed, "papers_authors.csv")
aliases_path <- file.path(dirs$processed, "author_aliases.csv")

if (!file.exists(papers_path)) {
  stop("papers_authors.csv not found. Run parse_pubmed_xml.R first.")
}

papers <- read_csv(papers_path, show_col_types = FALSE)

# Preserve raw author strings before merge (for re-runs)
if (!"author_raw_original" %in% names(papers)) {
  papers <- papers %>% mutate(author_raw_original = author_raw)
} else {
  papers <- papers %>% mutate(author_raw = author_raw_original)
}

# Build auto aliases (last name + first initial) and merge with manual entries
auto_aliases <- build_initial_aliases(papers)
manual_aliases <- if (file.exists(aliases_path)) {
  read_csv(aliases_path, show_col_types = FALSE)
} else {
  tibble(
    author_raw = character(),
    author_id = character(),
    notes = character(),
    merged_by = character(),
    merged_date = character()
  )
}

aliases_combined <- combine_alias_tables(auto_aliases, manual_aliases)
write_csv(aliases_combined, aliases_path)

cat("Auto initial-rule merges:", nrow(auto_aliases), "\n")
cat("Manual merges retained:", sum(!is_auto_initial_alias(manual_aliases$notes, manual_aliases$merged_by)), "\n")

papers_merged <- apply_author_aliases(papers, aliases_path)

write_csv(papers_merged, papers_path)

# Only refresh suggestions if file lacks human review columns
suggestions_path <- file.path(dirs$processed, "alias_suggestions.csv")
existing <- if (file.exists(suggestions_path)) {
  read_csv(suggestions_path, show_col_types = FALSE, n_max = 1)
} else {
  tibble()
}

if (!any(grepl("Combine", names(existing), ignore.case = TRUE))) {
  suggestions <- suggest_author_aliases(papers_merged)
  write_csv(suggestions, suggestions_path)
  cat("Alias suggestions refreshed.\n")
} else {
  cat("Keeping reviewed alias_suggestions.csv (not overwritten).\n")
}

cat("\n=== Alias Summary ===\n")
cat("Authors after merge:", n_distinct(papers_merged$author_id), "\n")
cat("Total alias entries:", nrow(aliases_combined), "\n")
