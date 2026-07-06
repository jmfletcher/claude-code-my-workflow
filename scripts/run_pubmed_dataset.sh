#!/usr/bin/env bash
# End-to-end pipeline for a dataset acquired via PubMed (config entrez_query).
# Usage: scripts/run_pubmed_dataset.sh DATASET_NAME
set -euo pipefail
DS="$1"
R() { Rscript "scripts/R/$1" "$DS"; }

echo "### [$DS] fetch PMIDs"
R fetch_collection_pmids.R
echo "### [$DS] fetch PubMed XML"
R fetch_pubmed_collection.R
echo "### [$DS] parse authors"
R parse_pubmed_xml.R
echo "### [$DS] extract metadata"
R extract_paper_metadata.R
echo "### [$DS] apply aliases"
R apply_author_aliases.R
echo "### [$DS] metrics"
R compute_monopoly_metrics.R
echo "### [$DS] figures"
R plot_monopoly_figures.R
echo "### [$DS] temporal"
R analyze_temporal_concentration.R
echo "### [$DS] domain"
R analyze_domain_concentration.R
echo "### [$DS] extended figures"
R plot_extended_analysis.R
echo "### [$DS] coverage"
R estimate_coverage.R
echo "### [$DS] DONE"
