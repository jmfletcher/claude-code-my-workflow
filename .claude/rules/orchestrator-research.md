---
paths:
  - "analysis/**/*.py"
  - "analysis/**/*.R"
  - "scripts/**/*.py"
  - "scripts/**/*.R"
  - "explorations/**"
---

# Research Project Orchestrator (Simplified)

**For Python/R scripts, simulations, and data analysis** — use this simplified loop instead of the full multi-agent orchestrator.

**Project:** Panel Conditioning (UK). **Primary language: Python.** R is legacy/reference. Stata is reference only. Code location: `analysis/`.

## The Simple Loop

```
Plan approved → orchestrator activates
  │
  Step 1: IMPLEMENT — Execute plan steps
  │
  Step 2: VERIFY — Run code, check outputs
  │         R scripts: Rscript runs without error
  │         Simulations: set.seed reproducibility
  │         Plots: PDF/PNG created, correct format
  │         If verification fails → fix → re-verify
  │
  Step 3: SCORE — Apply quality-gates rubric
  │
  └── Score >= 80?
        YES → Done (commit when user signals)
        NO  → Fix blocking issues, re-verify, re-score
```

**No 5-round loops. No multi-agent reviews. Just: write, test, done.**

## Verification Checklist

- [ ] Script runs without errors from repo root (`python3 analysis/script.py`)
- [ ] All packages imported at top; `requirements.txt` up to date
- [ ] No hardcoded absolute paths
- [ ] `RANDOM_SEED` defined at top if stochastic (Python); `set.seed()` for R
- [ ] Output files created at expected paths (`output/figures/`, `output/tables/`)
- [ ] **Denominators / Ns** documented or computed in line with knowledge base
- [ ] Tolerance checks pass (if comparing to legacy Stata/CSV)
- [ ] Quality score >= 80
