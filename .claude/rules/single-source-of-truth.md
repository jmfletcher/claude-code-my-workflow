---
paths:
  - "Figures/**/*"
  - "Quarto/**/*.qmd"
  - "scripts/**/*.py"
  - "data/**/*"
---

# Single Source of Truth: Enforcement Protocol

**Python scripts are the authoritative source for ALL data and figures.** The Quarto report derives from their outputs.

## The SSOT Chain

```
data/processed/*.csv (AUTHORITATIVE DATA)
  │
  ├── scripts/python/*.py (AUTHORITATIVE ANALYSIS)
  │     ├── → Figures/*.png (derived)
  │     └── → tables, calculations (derived)
  │
  └── Quarto/report.qmd (DERIVED REPORT)
        └── → PDF output (derived)

NEVER manually edit derived artifacts (figures, PDFs).
ALWAYS regenerate from scripts when data or analysis changes.
```

---

## Data Chain

```
data/input/*.pdf (ORIGINAL SOURCE — read-only, never modify)
  ↓
data/processed/*.csv (PROCESSED DATA — from Attempt 1 or regenerated)
  ↓
scripts/python/*.py (ANALYSIS — reads CSVs, produces figures + tables)
  ↓
Figures/*.png + Quarto/report.qmd (OUTPUT — always derived)
```

---

## When to Regenerate

Regenerate ALL downstream outputs when:
- Any CSV in `data/processed/` is modified
- Any Python script in `scripts/python/` is modified
- Before any commit that includes report changes
- Before any quality review

---

## Content Fidelity Checklist

```
[ ] Table values in report match CSV data
[ ] Figure descriptions match what figures show
[ ] CI method description matches code implementation
[ ] Suppression handling described in report matches code logic
[ ] All rate calculations use same formula (code and report)
[ ] Reference to "Attempt 1" outputs verified against reference/ folder
```
