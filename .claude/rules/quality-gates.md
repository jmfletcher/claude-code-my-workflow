---
paths:
  - "analysis/**/*.py"
  - "manuscript/**"
  - "Slides/**"
  - "Quarto/**/*.qmd"
---

# Quality Gates & Scoring Rubrics

## Thresholds

- **80/100 = Commit** — good enough to save
- **90/100 = Required for manuscript figures and tables**
- **95/100 = Excellence** — aspirational

---

## Python Scripts (.py)

| Severity | Issue | Deduction |
|----------|-------|-----------|
| Critical | Syntax / runtime error | -100 |
| Critical | Hardcoded absolute path | -20 |
| Critical | Suppressed cells imputed (not set to NaN) | -30 |
| Critical | Denominator `n_tested` not tracked in output | -20 |
| Major | Figure saved without both PDF + PNG | -10 |
| Major | Race labels inconsistent across scripts (silent mismatch) | -10 |
| Major | Decomposition components do not sum to total ± 0.001 pp | -15 |
| Major | Script not runnable from repo root with no arguments | -10 |
| Minor | No module-level docstring on analysis script | -2 |
| Minor | Imports not at top of file | -2 |

---

## Quarto Slides / Manuscript (.qmd)

| Severity | Issue | Deduction |
|----------|-------|-----------|
| Critical | Compilation failure | -100 |
| Critical | Broken citation | -15 |
| Critical | Figure reference not found | -15 |
| Major | Text overflow | -5 |
| Major | Notation inconsistency | -3 |
| Minor | Font size below 9pt | -2 per instance |

---

## Beamer Slides (.tex) — dormant for this project

| Severity | Issue | Deduction |
|----------|-------|-----------|
| Critical | XeLaTeX compilation failure | -100 |
| Critical | Undefined citation | -15 |
| Critical | Overfull hbox > 10pt | -10 |

---

## Enforcement

- **Score < 80:** Block commit. List blocking issues.
- **Score 80–89:** Allow commit, warn. List recommendations.
- **Score < 90:** Not acceptable for manuscript figures or tables.
- User can override with explicit justification.

---

## Quality Reports

Generated **only at merge time**. Use `templates/quality-report.md` for format.
Save to `quality_reports/merges/YYYY-MM-DD_[branch-name].md`.

---

## Tolerance Thresholds (Research)

| Quantity | Tolerance | Rationale |
|----------|-----------|-----------|
| Proficiency rates | Exact match (integer counts ÷ N) | No floating-point variability in source data |
| Within + between decomposition sum | ± 0.001 percentage points | Rounding from weighted averages |
| Cross-year comparisons | Same proficiency standard only | DPI cut score revision makes cross-standard trends unreliable |
