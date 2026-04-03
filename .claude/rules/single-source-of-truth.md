---
paths:
  - "analysis/**/*"
  - "manuscript/**/*"
  - "slides/**/*"
  - "output/**/*"
  - "Figures/**/*"
---

# Single Source of Truth (Research Project)

**This project does not use Beamer lecture decks.** Authority flows from **version-controlled analysis and prose**, not from hand-edited exports.

## The chain

```
analysis/ (R scripts, documented parameters)
  ├── clean → analytic tables (CSV/RDS) with README or codebook
  ├── estimates → saved objects + session info (seed, package versions)
  └── figures → vector PDF/SVG + source script line ranges referenced in manuscript

manuscript/ (.qmd / .md + BibTeX)
  ├── numbers and claims trace to analysis outputs (or inline computed with same repo)
  └── tables: generated from code or pinned values with explicit provenance

slides/ (.qmd / .md)
  └── Key statistics and figures copied from the same outputs as the manuscript (no orphan numbers)
```

## Rules

1. **Do not** “fix” a number in the manuscript or slides without updating the analysis pipeline (or documenting a one-off exception in the session log and MEMORY.md).
2. **Figures** in `output/` or `analysis/figures/` must be reproducible from script; avoid pasting screenshots as final artifacts.
3. **Prior folders** (`Old Attempts and Results/`, ad hoc Excel) are **reference only**, not SSOT.

## When this overlaps legacy template paths

If `Slides/**/*.tex` and `Quarto/**` lecture pairs are added later, the Beamer-centric SSOT rule applies **only** to those paths; this file governs **manuscript and panel-conditioning analysis** first.
