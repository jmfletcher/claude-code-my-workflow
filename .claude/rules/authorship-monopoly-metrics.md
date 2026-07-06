---
paths:
  - "datasets/**/*"
  - "scripts/R/**/*"
---

# Authorship Monopoly Metrics

**Precise definitions for HHI and top-x concentration measures.**

---

## Unit of Analysis

- **Population:** All papers citing the dataset (as defined by the source collection)
- **Authors:** All co-authors listed on each paper, after alias merge
- **Paper:** One PubMed record = one paper (deduplicate by PMID)

---

## Author Paper-Share

For each author *i* after alias merge:

\[
s_i = \frac{\text{number of papers with author } i \text{ as co-author}}{N_{\text{papers}}}
\]

Where \(N_{\text{papers}}\) = total distinct PMIDs in the collection.

**Notes:**
- Multi-authored papers count once per author (author gets credit for each paper they appear on)
- Shares sum to > 1 when papers have multiple authors (this is intentional — we measure author-level concentration, not paper ownership)

---

## Herfindahl-Hirschman Index (HHI)

\[
\text{HHI} = \sum_{i=1}^{N_{\text{authors}}} s_i^2
\]

**Interpretation:**
- HHI = 1.0 if one author appears on all papers
- HHI approaches 0 as authorship becomes perfectly diffuse
- Higher HHI = more concentrated authorship

**Reporting:**
- Always report raw HHI
- Optionally report normalized HHI: \(\text{HHI}_{\text{norm}} = \frac{\text{HHI} - 1/N_{\text{papers}}}{1 - 1/N_{\text{papers}}}\) (only if comparing across datasets with very different paper counts)

**By year:** If `pub_year` available, compute HHI separately for each year with ≥10 papers.

---

## Top-x Share

For a given *x*:

\[
\text{Top-}x \text{ share} = \frac{\#\{\text{papers with at least one of the top-}x \text{ authors}\}}{N_{\text{papers}}}
\]

**Top-x authors:** The *x* authors with highest paper counts (after alias merge).

**Tie-breaking:** When multiple authors tie at the x-th position, include all tied authors (effective x may exceed nominal x). Document when this occurs.

**Paper counting:** Each paper counted once regardless of how many top-x authors appear on it.

**Default x values:** 1, 3, 5, 10 (configurable in `config.yaml`).

---

## Quality Control Checks

Run after every metrics computation:

```
[ ] N_papers in raw/manifest == N_papers in processed/papers_authors.csv (distinct pmid)
[ ] N_papers in processed == N_papers used in metrics
[ ] All author_id values in papers_authors exist in author rankings
[ ] No author_id in aliases points to non-existent canonical ID
[ ] HHI in [0, 1] range
[ ] Top-x share in [0, 1] range for all x
[ ] Top-1 share <= Top-3 share <= Top-5 share <= Top-10 share (monotonicity)
[ ] Hand-check: pick 3 random papers, verify author extraction matches PubMed page
[ ] Hand-check: compute HHI on 5-author subset manually, compare to pipeline output
```

**Count mismatch protocol:**
- If raw != processed: STOP. Do not compute metrics. Investigate missing PMIDs.
- Document any intentional exclusions in dataset README with PMID list.

---

## Author Alias Merge Rules

1. **Never merge without alias table entry** — all merges recorded in `author_aliases.csv`
2. **Document rationale** in `notes` column — required, non-empty
3. **Automatic initial rule (default)** — merge authors who share the same last name and same first initial (e.g., `Bluemke D` → `Bluemke DA`, `Almeida D` → `Almeida D M`). Canonical ID = variant with highest paper count; ties broken by most complete initials, then alphabetically. Auto-entries use `merged_by = auto_initial_rule`.
4. **Manual review for ambiguous cases** — same last name but *different* first initials remain separate unless manually aliased (e.g., `Smith J` vs `Smith A`)
5. **Transitive consistency** — if A→B and B→C, then A→C must also be aliased to C
6. **Recompute after alias changes** — any new alias entries require re-running metrics

---

## Comparison Across Datasets

When comparing HHI or top-x across datasets (REGARDS vs MIDUS vs WLS):

- Use same top-x values
- Report paper counts and author counts alongside metrics
- Note source differences (PubMed collection vs Web of Science vs manual curation)
- Do not compare raw HHI across datasets with vastly different N_papers without normalized HHI
