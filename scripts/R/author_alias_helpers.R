# Author alias helpers — shared parsing and auto-merge logic

suppressPackageStartupMessages({
  library(dplyr)
  library(tibble)
  library(stringr)
})

#' Parse author string into last name and first initial for matching
parse_author_match_key <- function(author_raw) {
  s <- str_trim(author_raw)
  s <- str_remove(s, regex("\\s+(Jr\\.?|Sr\\.?|II|III|IV)$", ignore_case = TRUE))

  m <- str_match(s, "^(.+?)\\s+([A-Z][A-Za-z'\\-. ]*)$")
  last_name <- ifelse(is.na(m[, 1]), s, str_trim(m[, 2]))
  initials_clean <- gsub("[^A-Za-z]", "", m[, 3])
  first_initial <- toupper(substr(initials_clean, 1, 1))
  first_initial[is.na(m[, 1]) | initials_clean == ""] <- NA_character_

  tibble(last_name = last_name, first_initial = first_initial)
}

#' Choose canonical author_id within a duplicate group
choose_canonical_author <- function(variants) {
  variants %>%
    arrange(desc(n_papers), desc(nchar(author_raw)), author_raw) %>%
    slice(1) %>%
    pull(author_raw)
}

AUTO_ALIAS_NOTE <- "Auto-merge: same last name and first initial (project rule)"
AUTO_ALIAS_MERGER <- "auto_initial_rule"

is_auto_initial_alias <- function(notes, merged_by = NA_character_) {
  auto_note <- !is.na(notes) &
    grepl("^Auto-merge: same last name and first initial", notes, fixed = TRUE)
  auto_merger <- !is.na(merged_by) & merged_by == AUTO_ALIAS_MERGER
  auto_note | auto_merger
}

#' Build alias table rows from last-name + first-initial rule
build_initial_aliases <- function(papers_authors, min_group_size = 2L) {
  author_col <- if ("author_raw_original" %in% names(papers_authors)) {
    "author_raw_original"
  } else {
    "author_raw"
  }

  stats <- papers_authors %>%
    distinct(.data[[author_col]]) %>%
    rename(author_raw = !!sym(author_col)) %>%
    left_join(
      papers_authors %>%
        distinct(pmid, author_raw = .data[[author_col]]) %>%
        count(author_raw, name = "n_papers"),
      by = "author_raw"
    )

  keys <- parse_author_match_key(stats$author_raw)
  stats <- bind_cols(stats, keys) %>%
    filter(!is.na(first_initial), first_initial != "") %>%
    mutate(match_key = paste(last_name, first_initial, sep = "|"))

  groups <- stats %>%
    group_by(match_key) %>%
    filter(n() >= min_group_size) %>%
    group_modify(function(variants, key) {
      canonical <- choose_canonical_author(variants)
      variants %>%
        filter(author_raw != canonical) %>%
        transmute(
          author_raw,
          author_id = canonical,
          notes = AUTO_ALIAS_NOTE,
          merged_by = AUTO_ALIAS_MERGER,
          merged_date = as.character(Sys.Date())
        )
    }) %>%
    ungroup() %>%
    select(-match_key)

  groups
}

#' Merge auto-generated aliases with manual entries (manual wins on author_raw)
combine_alias_tables <- function(auto_aliases, manual_aliases) {
  manual_aliases <- manual_aliases %>%
    filter(!is_auto_initial_alias(notes, merged_by)) %>%
    mutate(merged_date = as.character(merged_date))

  auto_aliases <- auto_aliases %>%
    mutate(merged_date = as.character(merged_date))

  bind_rows(manual_aliases, auto_aliases) %>%
    distinct(author_raw, .keep_all = TRUE) %>%
    filter(author_raw != author_id)
}
