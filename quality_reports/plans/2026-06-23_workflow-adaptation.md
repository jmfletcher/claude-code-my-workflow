# Workflow Adaptation Plan — Data Monopolies

**Status:** COMPLETED  
**Date:** 2026-06-23  
**Approved by:** Jason Fletcher

---

## Summary

Retargeted the forked Claude Code academic workflow from lecture/slides to the Data Monopolies research pipeline: dataset-centric folders, PubMed ingestion, co-author extraction, HHI/top-x monopoly metrics, R-primary code, and manual author alias curation.

---

## Design Choices (Confirmed)

- **Language:** R primary (`rentrez`, `tidyverse`); Python only when clearly needed
- **Author identity:** PubMed author strings + per-dataset manual alias/merge table
- **Rigor:** Plan-first for non-trivial work; publication-ready figures; decisions persisted to disk and MEMORY.md

---

## Completed Items

### Core Configuration
- [x] CLAUDE.md rewritten for Data Monopolies
- [x] README.md replaced with project overview
- [x] MEMORY.md bootstrap entries added
- [x] .gitignore updated for raw downloads

### New Rules Created
- [x] constitutional-governance.md (5 articles)
- [x] dataset-pipeline-protocol.md (CSV schemas, folder structure)
- [x] authorship-monopoly-metrics.md (HHI, top-x definitions)
- [x] pubmed-collection-protocol.md (REGARDS collection 46426411)
- [x] visualization-standards.md (publication-ready figures)
- [x] bootstrap-checkins.md (early session cadence)

### Existing Rules Updated
- [x] single-source-of-truth.md (scoped to Slides/Quarto; pipeline SSOT noted)
- [x] verification-protocol.md (dataset pipeline section)
- [x] quality-gates.md (pipeline rubric)
- [x] r-code-conventions.md (config/alias patterns)
- [x] domain-reviewer.md (bibliometrics referee)
- [x] exploration-folder-protocol.md (graduation to datasets/)
- [x] orchestrator-protocol.md (bootstrap reference)
- [x] WORKFLOW_QUICK_REF.md (non-negotiables filled)

### Skills
- [x] data-monopoly/SKILL.md created
- [x] data-analysis/SKILL.md paths updated

### Scaffold
- [x] datasets/_template/ with README, config.yaml, alias header
- [x] datasets/REGARDS/ with README, config.yaml, folder structure
- [x] scripts/R/README.md with planned utilities

### Settings
- [x] settings.json permissions added (curl, wget, R -e)
- [x] protect-files.sh updated (settings.json unprotected for project config)

---

## Verification Checklist

```
[x] CLAUDE.md reads correctly with no [PLACEHOLDERS]
[x] constitutional-governance.md has 5 articles
[x] dataset-pipeline-protocol.md defines CSV schemas
[x] authorship-monopoly-metrics.md defines HHI and top-x precisely
[x] domain-reviewer.md targets bibliometrics not lectures
[x] REGARDS scaffold exists with config.yaml
[x] Plan saved to quality_reports/plans/
[ ] git diff reviewed with user before any commit
```

---

## Next Task (Separate Plan)

REGARDS pilot pipeline:
1. Spec: confirm top-x = {1, 3, 5, 10} and publication year extraction
2. Implement scripts/R/fetch_pubmed_collection.R + compute_monopoly_metrics.R
3. Download collection, build alias table starter
4. Produce first metrics table + 2–3 publication-ready figures
5. Bootstrap checkpoint #2 for user review
