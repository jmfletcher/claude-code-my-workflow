---
paths:
  - "Slides/**/*.tex"
  - "Quarto/**/*.qmd"
  - "docs/**"
  - "manuscript/**"
  - "analysis/**"
  - "slides/**"
---

# Task Completion Verification Protocol

**At the end of EVERY task, Claude MUST verify the output works correctly.** This is non-negotiable.

## For manuscript (`manuscript/`) — Quarto / Markdown

1. `quarto render` (or agreed build) on the target file; fix errors until clean.
2. Open the PDF/HTML output; spot-check **tables and figures** for truncation and correct cross-references.
3. Confirm **numbers in text** match pipeline outputs referenced in the methods or captions.

## For project slides (`slides/`)

1. `quarto render` (or Pandoc) per project convention; confirm **PDF** (or HTML) builds.
2. Visual scan: **fonts, axis labels, legends** readable; no placeholder titles on final exports.
3. Figures match the **same files or values** as the manuscript (no divergent “magic” numbers).

## For analysis (`analysis/**/*.R`)

1. Run `Rscript analysis/path/to/script.R` from repo root (or documented entrypoint).
2. Confirm outputs (CSV, RDS, figures) exist, non-zero size, **sensible row counts** for denominators.
3. If comparing to **legacy Stata/CSV**, run tolerance checks defined in the active plan.

## For Quarto/HTML (legacy lecture site in `docs/`)

1. Run `./scripts/sync_to_docs.sh` (or `./scripts/sync_to_docs.sh LectureN`) when editing upstream lecture Quarto that syncs to `docs/`.
2. Open HTML in browser; verify images and paths.
3. Beamer environment parity applies **only** if Beamer sources exist.

## For LaTeX/Beamer Slides (`Slides/`)

1. Compile with xelatex; check for errors and overfull boxes.
2. Open PDF to verify figures.

## For TikZ → HTML (only if using lecture TikZ pipeline)

1. Use SVG for HTML; verify freshness vs Beamer source if applicable.

## For R Scripts (generic)

1. `Rscript` the script; verify outputs.
2. Spot-check magnitudes and **N** columns where present.

## Common pitfalls

- **PDF in HTML:** browsers need SVG or embedded raster for inline diagrams.
- **Path drift:** `../Figures/` vs `docs/` — use project `output/` conventions for Panel Conditioning.
- **Stale outputs:** re-run pipeline after code changes before declaring success.

## Verification checklist

```
[ ] Build/run completed without errors
[ ] Outputs exist and pass sanity checks (including Ns/denominators)
[ ] Visual check for manuscript PDFs and slide PDFs
[ ] Reported results to user
```
