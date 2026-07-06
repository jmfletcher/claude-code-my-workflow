# ============================================================
# Extract paper metadata (title, abstract, year) from PubMed XML
# Outputs: datasets/{name}/processed/papers.csv
# ============================================================

suppressPackageStartupMessages({
  library(xml2)
  library(readr)
  library(dplyr)
  library(purrr)
  library(tibble)
})

source("scripts/R/utils.R")

parse_year <- function(article) {
  year <- xml_text(xml_find_first(article, ".//PubDate/Year"))
  if (is.na(year) || year == "") {
    medline <- xml_text(xml_find_first(article, ".//PubDate/MedlineDate"))
    if (!is.na(medline)) {
      m <- regmatches(medline, regexpr("[0-9]{4}", medline))
      if (length(m) > 0) return(as.integer(m[1]))
    }
    return(NA_integer_)
  }
  as.integer(year)
}

parse_abstract <- function(article) {
  parts <- xml_find_all(article, ".//Abstract/AbstractText")
  if (length(parts) == 0) return(NA_character_)
  texts <- map_chr(parts, function(p) {
    label <- xml_attr(p, "Label")
    txt <- xml_text(p)
    if (!is.na(label) && label != "") {
      paste0(label, ": ", txt)
    } else {
      txt
    }
  })
  paste(texts, collapse = " ")
}

args <- commandArgs(trailingOnly = TRUE)
dataset_name <- if (length(args) >= 1) args[1] else "REGARDS"

dirs <- get_dataset_dirs(dataset_name)
xml_path <- file.path(dirs$raw, "pubmed_records.xml")

doc <- read_xml(xml_path)
articles <- xml_find_all(doc, ".//PubmedArticle")

papers <- map_dfr(articles, function(article) {
  tibble(
    pmid = xml_text(xml_find_first(article, ".//PMID")),
    title = xml_text(xml_find_first(article, ".//ArticleTitle")),
    abstract = parse_abstract(article),
    pub_year = parse_year(article)
  )
})

papers <- papers %>%
  mutate(
    text = paste(title, coalesce(abstract, "")),
    has_abstract = !is.na(abstract) & abstract != ""
  )

out_path <- file.path(dirs$processed, "papers.csv")
write_csv(papers, out_path)

cat("Papers:", nrow(papers), "\n")
cat("With abstract:", sum(papers$has_abstract), "\n")
cat("Year range:", min(papers$pub_year, na.rm = TRUE), "-",
    max(papers$pub_year, na.rm = TRUE), "\n")
cat("Output:", out_path, "\n")

saveRDS(papers, file.path(dirs$processed, "papers.rds"))
