# Shared monopoly metric helpers

suppressPackageStartupMessages({
  library(dplyr)
  library(tibble)
})

compute_hhi <- function(author_counts, n_papers) {
  if (n_papers == 0 || nrow(author_counts) == 0) return(NA_real_)
  shares <- author_counts$n_papers / n_papers
  sum(shares^2)
}

compute_topx_share <- function(papers_authors, top_authors, n_papers) {
  if (n_papers == 0) return(NA_real_)
  papers_with_top <- papers_authors %>%
    filter(author_id %in% top_authors) %>%
    distinct(pmid) %>%
    nrow()
  papers_with_top / n_papers
}

get_top_authors <- function(author_rankings, x) {
  n_at_x <- min(x, nrow(author_rankings))
  if (n_at_x == 0) return(character())
  threshold <- author_rankings$n_papers[n_at_x]
  author_rankings %>%
    filter(n_papers >= threshold) %>%
    pull(author_id)
}

compute_period_metrics <- function(papers_authors, top_x_values = c(1, 3, 5, 10),
                                   period_label, period_start, period_end,
                                   compute_hhi = TRUE) {
  period_papers <- papers_authors
  if (!is.na(period_start) && !is.na(period_end)) {
    period_papers <- period_papers %>%
      filter(pub_year >= period_start, pub_year <= period_end)
  }

  n_papers <- n_distinct(period_papers$pmid)
  if (n_papers == 0) {
    return(tibble())
  }

  rankings <- period_papers %>%
    distinct(pmid, author_id) %>%
    count(author_id, name = "n_papers") %>%
    arrange(desc(n_papers))

  n_authors <- nrow(rankings)
  hhi <- if (isTRUE(compute_hhi)) compute_hhi(rankings, n_papers) else NA_real_

  rows <- tibble(
    period = period_label,
    period_start = period_start,
    period_end = period_end,
    metric = c("n_papers", "n_authors", if (isTRUE(compute_hhi)) "hhi"),
    value = c(n_papers, n_authors, if (isTRUE(compute_hhi)) hhi),
    top_x = NA_integer_
  )

  for (x in top_x_values) {
    top_authors <- get_top_authors(rankings, x)
    topx <- compute_topx_share(period_papers, top_authors, n_papers)
    rows <- bind_rows(
      rows,
      tibble(
        period = period_label,
        period_start = period_start,
        period_end = period_end,
        metric = "top_x_share",
        value = topx,
        top_x = x
      )
    )
  }

  rows
}
