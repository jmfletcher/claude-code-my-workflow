---
paths:
  - "analysis/**/*.py"
  - "explorations/**"
---

# Research Project Orchestrator (Python)

**For Python analysis scripts and data pipelines** — use this simplified loop instead of the full multi-agent orchestrator.

## The Simple Loop

```
Plan approved → orchestrator activates
  │
  Step 1: IMPLEMENT — Execute plan steps
  │
  Step 2: VERIFY — Run code, check outputs
  │         Python scripts: run without error from repo root
  │         Data outputs: expected CSVs created in output/tables/
  │         Figures: PDF + PNG pair created in output/figures/
  │         Suppression log: written to output/tables/suppression_log.csv if applicable
  │         Decomposition: within + between sums to total ± 0.001 pp
  │         If verification fails → fix → re-verify
  │
  Step 3: SCORE — Apply quality-gates rubric (Python Scripts section)
  │
  └── Score >= 80?
        YES → Done (commit when user signals)
        NO  → Fix blocking issues, re-verify, re-score
```

**No 5-round loops. No multi-agent reviews. Just: write, test, done.**

## Verification Checklist

- [ ] Script runs from repo root: `python3 analysis/NN_script_name.py`
- [ ] No hardcoded absolute paths — all paths built from `ROOT = Path(__file__).resolve().parents[1]`
- [ ] All imports at top of file
- [ ] Output files created at expected paths under `output/`
- [ ] Suppression log written (if any suppressed cells encountered)
- [ ] Denominator (`n_tested`) preserved in all intermediate and output datasets
- [ ] Decomposition components sum to total ± 0.001 pp (if applicable)
- [ ] Figures saved as both PDF and PNG
- [ ] Race labels match knowledge base exactly (no silent mismatches)
- [ ] Quality score >= 80

## Script Naming Convention

```
analysis/
  00_data_overview.py      # inspect raw files, confirm column names
  01_load_and_clean.py     # build tidy dataset, handle suppression
  02_state_gaps.py         # RQ1: state-level gaps by race/grade/subject
  03_decomposition.py      # RQ2: within–between decomposition
  04_mmsd_analysis.py      # RQ3: MMSD deep-dive and cross-district comparisons
  05_figures.py            # all publication figures
  06_tables.py             # all publication tables
```
