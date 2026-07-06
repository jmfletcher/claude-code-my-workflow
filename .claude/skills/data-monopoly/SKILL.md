---
name: data-monopoly
description: End-to-end authorship monopoly analysis — download PubMed citations, extract co-authors, apply alias merges, compute HHI and top-x shares, generate publication-ready figures. Use when user mentions download citations, compute HHI, authorship monopoly, REGARDS PubMed, or dataset concentration.
argument-hint: "[dataset name, e.g., REGARDS]"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Edit", "Bash", "Task"]
---

# Data Monopoly Analysis Workflow

Run the full authorship concentration pipeline for a dataset: fetch citations → extract authors → apply aliases → compute HHI/top-x → generate figures.

**Input:** `$ARGUMENTS` — dataset name (e.g., `REGARDS`) or description of the analysis goal.

---

## Constraints

- **Follow pipeline protocol** in `.claude/rules/dataset-pipeline-protocol.md`
- **Follow metric definitions** in `.claude/rules/authorship-monopoly-metrics.md`
- **Follow PubMed protocol** in `.claude/rules/pubmed-collection-protocol.md`
- **Follow visualization standards** in `.claude/rules/visualization-standards.md`
- **Follow R conventions** in `.claude/rules/r-code-conventions.md`
- **Save scripts** to `scripts/R/` (shared) or `datasets/{name}/scripts/` (dataset-specific)
- **Save outputs** to `datasets/{name}/output/`
- **Run domain-reviewer** after metrics computation
- **Run r-reviewer** on generated scripts before presenting results

---

## Workflow Phases

### Phase 1: Setup and Configuration

1. Read dataset config: `datasets/{name}/config.yaml`
2. Verify folder structure exists (create from `_template/` if not)
3. Read any existing alias table: `datasets/{name}/processed/author_aliases.csv`
4. Confirm top-x values and source details with user if first run

### Phase 2: Fetch Citations

1. Read `.claude/rules/pubmed-collection-protocol.md`
2. Export PMID list from PubMed collection (or use saved manifest)
3. Batch fetch via `rentrez::entrez_fetch()`
4. Save to `datasets/{name}/raw/pubmed_manifest.csv` and `pubmed_records.xml`
5. **QC:** Reconcile count with expected collection size

### Phase 3: Extract Authors

1. Parse PubMed XML → `datasets/{name}/processed/papers_authors.csv`
2. Author string format: `{LastName} {Initials}`
3. Extract: pmid, title, pub_year, author_raw, author_position, affiliation
4. **QC:** Spot-check 5 random papers against PubMed web page

### Phase 4: Apply Author Aliases

1. Load `author_aliases.csv` (create empty template if first run)
2. Flag potential duplicates for human review (same last name + similar initials)
3. Apply merges via alias table only — never inline
4. Generate `author_id` column (canonical ID after merge)
5. **Checkpoint:** Present alias suggestions to user for review

### Phase 5: Compute Metrics

1. Read `.claude/rules/authorship-monopoly-metrics.md`
2. Compute author paper-shares: \(s_i = \text{papers by author } i / N_{\text{papers}}\)
3. Compute HHI: \(\sum_i s_i^2\)
4. Compute top-x shares for configured x values
5. Compute by-year metrics if pub_year available (≥10 papers/year)
6. Save to `datasets/{name}/output/monopoly_metrics.csv` and `author_rankings.csv`
7. **QC:** Hand-check HHI on 5-author subset; verify top-x monotonicity

### Phase 6: Generate Figures

1. Read `.claude/rules/visualization-standards.md`
2. Author rank-frequency plot (Lorenz-style or bar)
3. Top-x bar chart
4. HHI over time (if year data available)
5. Export PDF + PNG at 300 DPI; save source data as RDS
6. **QC:** Open figures, verify labels readable, values match metrics

### Phase 7: Review and Report

1. Run domain-reviewer agent on pipeline outputs
2. Run r-reviewer agent on generated scripts
3. Address Critical and Major issues
4. Update CLAUDE.md project state table
5. Write session log to `quality_reports/session_logs/`
6. Present summary with metrics table and figure paths

---

## Script Structure

Shared utilities go in `scripts/R/`:

```r
# scripts/R/compute_hhi.R
# scripts/R/compute_topx_share.R
# scripts/R/apply_author_aliases.R
# scripts/R/parse_pubmed_xml.R
# scripts/R/fetch_pubmed_collection.R
```

Dataset orchestration in `datasets/{name}/scripts/run_pipeline.R`:

```r
# ============================================================
# REGARDS Authorship Monopoly Pipeline
# Purpose: Fetch, parse, compute HHI and top-x for REGARDS
# Inputs: config.yaml, PubMed collection 46426411
# Outputs: papers_authors.csv, monopoly_metrics.csv, figures/
# ============================================================

# 0. Setup ----
# 1. Fetch PubMed records ----
# 2. Parse authors ----
# 3. Apply aliases ----
# 4. Compute metrics ----
# 5. Generate figures ----
# 6. QC and report ----
```

---

## Important

- **Count reconciliation is mandatory.** Never compute metrics if raw != processed paper counts.
- **Alias merges require human approval** during bootstrap period. Flag, don't auto-merge.
- **Recompute metrics** after any alias table change.
- **Document exclusions** in dataset README if papers are intentionally dropped.
- **Bootstrap check-ins:** Follow checkpoint cadence in first 3 sessions.

---

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| Count mismatch | Missing PMIDs in fetch | Check fetch_log.txt, re-fetch failed PMIDs |
| HHI > 1 | Wrong formula (paper-level shares) | Use author-level paper-shares |
| Top-x not monotonic | Tie-breaking error | Include all tied authors at x-th position |
| Empty author list | XML parsing error | Check PubMed XML structure for record |
| Rate limit error | Too many Entrez requests | Add NCBI_API_KEY to .Renviron, increase sleep |
