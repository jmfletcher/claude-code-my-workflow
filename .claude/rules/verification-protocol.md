---
paths:
  - "Quarto/**/*.qmd"
  - "scripts/**/*.py"
  - "docs/**"
---

# Task Completion Verification Protocol

**At the end of EVERY task, Claude MUST verify the output works correctly.** This is non-negotiable.

## For Quarto Reports (.qmd → PDF):
1. Run `quarto render Quarto/report.qmd --to pdf`
2. Verify PDF was created with non-zero size
3. Check for render warnings or errors
4. Spot-check that figures and tables appear
5. Report verification results

## For Python Scripts:
1. Run `python3 scripts/python/filename.py`
2. Verify output files (CSV, PNG) were created with non-zero size
3. Spot-check values for reasonable magnitude
4. Verify figures use correct palette (White=#2171b5, Black=#b2182b)
5. Check figure DPI is 300

## For Quarto/HTML (if deployed):
1. Run `quarto render Quarto/report.qmd --to html`
2. Open HTML in browser: `open` (macOS)
3. Verify images display correctly
4. Check for overflow or layout issues

## Common Pitfalls:
- **Missing dependencies**: Run `pip install pandas matplotlib pdfplumber` first
- **Relative paths**: Scripts should work from project root
- **Assuming success**: Always verify output files exist AND contain correct content
- **Stale figures**: If data changed, regenerate all figures before rendering report

## Verification Checklist:
```
[ ] Output file created successfully
[ ] No compilation/render errors
[ ] Images/figures display correctly
[ ] Values match expected (spot-check against reference/)
[ ] Reported results to user
```
