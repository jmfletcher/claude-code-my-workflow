# Plan: Adapt workflow configuration for Panel Conditioning (UK)

**Status:** COMPLETED  
**Date:** 2026-04-02

## Goal

Align `.claude/`, rules, agents, and root docs with the **Panel Conditioning in UK cohort studies** research project (mortality, week-of-birth comparisons, denominators explicit, preprint + slides deliverables).

## Approved approach

1. Add **`CLAUDE.md`** as project constitution (folder map, workflow, collaboration cadence).
2. Replace template placeholders in **`knowledge-base-template.md`** with research-oriented tables (cohorts, estimands, pitfalls).
3. Rewrite **`single-source-of-truth.md`** for R/manuscript/slides (not Beamer lectures).
4. Update **`meta-governance.md`** to state project-first identity while noting fork lineage.
5. Fill **`WORKFLOW_QUICK_REF.md`** with non-negotiables (denominators, figures, paths).
6. Add **`plan-first-workflow.md`** + **`orchestrator-protocol.md`** notes on early-session check-ins.
7. Retarget **`domain-reviewer.md`** for observational mortality / panel-conditioning substance.
8. Extend **`orchestrator-research.md`**, **`r-code-conventions.md`**, **`verification-protocol.md`** for `analysis/`, `manuscript/`, `slides/`.
9. **`beamer-quarto-sync.md`:** HTML comment that it is dormant unless lecture pairs exist.
10. **`README.md`:** Short fork banner linking to `CLAUDE.md` and GitHub branch.
11. **`MEMORY.md`:** `[LEARN]` entries for project defaults.

## Verification

- [x] `CLAUDE.md` exists and is under ~150 lines
- [x] Path-scoped rules load for intended paths (no broken frontmatter)
- [x] Plan saved to disk (this file)

## Next steps (future sessions)

- Create `analysis/`, `manuscript/`, `slides/` with initial `README` or `.qmd` when starting the pipeline.
- Fill cohort names in knowledge base once data labels are fixed.
- Optional: `renv` for R reproducibility (decision in a dedicated plan).
