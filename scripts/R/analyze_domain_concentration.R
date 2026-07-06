# ============================================================
# Domain clustering and per-domain concentration analysis
# Clusters papers by title + abstract (TF-IDF + k-means)
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(tibble)
  library(purrr)
  library(tm)
  library(Matrix)
})

source("scripts/R/utils.R")
source("scripts/R/metrics_helpers.R")

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"
k_domains <- if (length(args) >= 2) as.integer(args[2]) else 8L

config <- load_dataset_config(dataset_name)
dirs <- get_dataset_dirs(dataset_name)
top_x_values <- config$metrics$top_x_values

papers <- read_csv(file.path(dirs$processed, "papers.csv"), show_col_types = FALSE)
papers_authors <- read_csv(
  file.path(dirs$processed, "papers_authors.csv"),
  show_col_types = FALSE
)

# --- Build corpus (preserve all documents) ---
stopwords_custom <- c(
  stopwords("english"),
  "regards", "study", "cohort", "participants", "analysis",
  "results", "methods", "background", "conclusion", "conclusions",
  "objective", "objectives", "associated", "association", "using",
  "among", "data", "risk", "factors", "model", "adjusted", "may",
  "also", "however", "compared", "within", "across", "based"
)

clean_document <- function(text) {
  text <- tolower(text)
  text <- gsub("[^a-z ]", " ", text)
  words <- unlist(strsplit(text, "\\s+"))
  words <- words[words != "" & !(words %in% stopwords_custom)]
  if (length(words) == 0) "general health" else paste(words, collapse = " ")
}

papers <- papers %>%
  mutate(clean_text = vapply(text, clean_document, character(1)))

corpus <- Corpus(VectorSource(papers$clean_text))

dtm <- DocumentTermMatrix(corpus)
dtm <- removeSparseTerms(dtm, 0.98)
mat <- as.matrix(dtm)

# --- k-means on TF-IDF-weighted matrix ---
tfidf <- weightTfIdf(dtm)
tfidf_mat <- as.matrix(tfidf)

set.seed(20260623)
km <- kmeans(tfidf_mat, centers = k_domains, nstart = 25, iter.max = 100)

# Label clusters from top TF-IDF terms
cluster_labels <- map_chr(seq_len(k_domains), function(k) {
  centers <- km$centers[k, ]
  top_terms <- names(sort(centers, decreasing = TRUE))[1:4]
  top_terms <- top_terms[!is.na(top_terms)]
  paste(top_terms, collapse = ", ")
})

domain_names <- paste0("Domain ", seq_len(k_domains), ": ", cluster_labels)

papers_domains <- papers %>%
  mutate(
    cluster = km$cluster,
    domain = domain_names[cluster]
  ) %>%
  select(pmid, title, pub_year, cluster, domain, has_abstract)

write_csv(papers_domains, file.path(dirs$processed, "papers_domains.csv"))

# --- Per-domain concentration metrics ---
domain_metrics <- map_dfr(seq_len(k_domains), function(k) {
  domain_pmids <- papers_domains %>% filter(cluster == k) %>% pull(pmid)
  if (length(domain_pmids) < 5) return(tibble())

  domain_authors <- papers_authors %>%
    filter(pmid %in% domain_pmids)

  label <- domain_names[k]
  compute_period_metrics(
    domain_authors,
    top_x_values = top_x_values,
    period_label = label,
    period_start = NA_integer_,
    period_end = NA_integer_
  ) %>%
    mutate(cluster = k, domain = label)
})

write_csv(domain_metrics, file.path(dirs$output, "domain_metrics.csv"))

# Summary table for reporting
domain_summary <- domain_metrics %>%
  filter(metric %in% c("n_papers", "n_authors", "hhi")) %>%
  pivot_wider(names_from = metric, values_from = value)

if ("top_x_share" %in% domain_metrics$metric) {
  domain_summary <- domain_summary %>%
    left_join(
      domain_metrics %>%
        filter(metric == "top_x_share", top_x == 3) %>%
        select(domain, top3_share = value),
      by = "domain"
    )
} else {
  domain_summary$top3_share <- NA_real_
}

domain_summary <- domain_summary %>% arrange(desc(hhi))

if (nrow(domain_summary) == 0) {
  stop("No domain metrics computed — check clustering output.")
}

write_csv(domain_summary, file.path(dirs$output, "domain_summary.csv"))

saveRDS(
  list(
    papers_domains = papers_domains,
    domain_metrics = domain_metrics,
    kmeans = km,
    terms = Terms(dtm)
  ),
  file.path(dirs$output, "domain_analysis.rds")
)

cat("\n=== Domain Clustering (k =", k_domains, ") ===\n")
cat("Papers clustered:", nrow(papers_domains), "\n")
cat("\nDomain summary (sorted by HHI):\n")
print(domain_summary %>% select(domain, n_papers, n_authors, hhi, top3_share))
