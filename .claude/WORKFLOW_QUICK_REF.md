# Workflow Quick Reference — Panel Conditioning (UK)

**Model:** Contractor (you direct; Claude orchestrates). **Early sessions:** more frequent check-ins until you signal to taper.

---

## The loop

```
Your instruction
    ↓
[PLAN] if multi-file, ambiguous, or >1 hour → save plan → your approval
    ↓
[EXECUTE] Implement → verify → review → score
    ↓
[REPORT] Summary + what’s ready + open questions
    ↓
Repeat
```

---

## I ask you when

- **Identification / estimand:** treated vs control weeks, parallel trends, scope (E&W vs UK).
- **Denominator source:** which column/file defines \(N_{b,t}\) or population counts.
- **Figure or table fork:** e.g., cumulative vs annual; age vs calendar time.
- **Scope creep:** “Also rerun Stata legacy?” vs fresh R-only pipeline.

---

## I execute when

- Running agreed analysis scripts, regenerating figures, updating manuscript/slides from same outputs.
- Verification (R runs, `quarto render`, file sanity checks).
- Logging decisions to `quality_reports/session_logs/` and `[LEARN]` to `MEMORY.md`.

---

## Quality gates

| Score | Action |
|-------|--------|
| ≥ 80 | OK to commit |
| < 80 | Fix blocking issues |
| ≥ 90 | Target for manuscript figures and core tables |

---

## Non-negotiables

- **Paths:** `here::here()` or repo-root-relative paths in R; no machine-specific absolute paths in committed code.
- **Reproducibility:** `set.seed()` once at top when relevant; record key package versions (sessionInfo or renv).
- **Denominators:** treated and control **N** must be explicit wherever rates appear; no orphan rates in prose.
- **Figures:** publication-ready — consistent theme, axis labels with units, readable fonts; vector PDF for print pipeline.
- **Numerical tolerance:** define in plan when comparing to legacy Stata/CSV outputs (e.g. rounding vs exact match).

---

## Preferences

**Visual:** ggplot2 + shared theme; colorblind-safe palettes; avoid chartjunk.

**Reporting:** Precise, structured; prefer tables + figure notes that stand alone for a referee.

**Session logs:** Post-plan, incremental on decisions/corrections, end-of-session summary.

**Replication:** Rebuild end-to-end from documented inputs; legacy `Old Attempts and Results/` for parity checks only.

---

## Exploration mode

Experimental ideas → `explorations/` with **fast-track** rules (lower threshold). Promote stable code into `analysis/`.

---

## Pointers

- Constitution: `CLAUDE.md`
- Domain registry: `.claude/rules/knowledge-base-template.md`
- SSOT: `.claude/rules/single-source-of-truth.md`
