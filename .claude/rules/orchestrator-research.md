---
paths:
  - "scripts/**/*.py"
  - "explorations/**"
  - "Figures/**"
---

# Research Project Orchestrator (Simplified)

**For Python scripts, data analysis, and figures** — use this simplified loop instead of the full multi-agent orchestrator.

## The Simple Loop

```
Plan approved → orchestrator activates
  │
  Step 1: IMPLEMENT — Execute plan steps
  │
  Step 2: VERIFY — Run code, check outputs
  │         Python scripts: python3 runs without error
  │         Data: CSVs created with expected columns/rows
  │         Plots: PNG created at correct DPI and palette
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

- [ ] Script runs without errors (`python3 scripts/python/filename.py`)
- [ ] All imports at top of file
- [ ] No hardcoded absolute paths
- [ ] Output files created at expected paths
- [ ] Figures use correct palette and DPI
- [ ] Tolerance checks pass (if applicable)
- [ ] Quality score >= 80
