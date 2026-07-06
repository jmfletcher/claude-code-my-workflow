---
paths:
  - "datasets/**/output/figures/**"
  - "scripts/R/**/*"
  - "output/**"
---

# Visualization Standards — Publication-Ready Figures

**All figures must meet publication quality before commit.**

Follow Kieran Healy's *Data Visualization* principles: grammar of graphics, honest scales, clarity over decoration.

---

## Required Standards

### Technical

- **Package:** `ggplot2` with project theme from `r-code-conventions.md`
- **Export formats:** PDF (vector) + PNG (300 DPI minimum)
- **Dimensions:** Explicit `ggsave(width = X, height = Y)` — never rely on defaults
- **Background:** `bg = "white"` for standalone figures; `bg = "transparent"` only for slide overlays
- **Font size:** Minimum 10pt for axis labels, 12pt for titles
- **Save source data:** `saveRDS()` plot data alongside every figure

### Design

- **Axis labels:** Sentence case with units in parentheses where applicable
- **Title:** Descriptive, not clever — state what the figure shows
- **Subtitle:** Optional context (dataset name, date range, N)
- **Legend:** Bottom or right; never overlapping data
- **Colors:** Use project palette; colorblind-safe when comparing groups
- **No chartjunk:** No 3D effects, unnecessary gridlines, or decorative elements

### Honesty

- **Y-axis:** Start at zero for bar charts; truncation requires explicit justification in caption
- **Log scales:** Label clearly; explain in caption why log is used
- **Sample size:** Always report N in subtitle or caption
- **Missing data:** Document exclusions that affect the figure

---

## Required Figure Types (Per Dataset)

| Figure | Purpose | Filename |
|--------|---------|----------|
| Author rank-frequency | Show concentration visually (Lorenz-style or bar) | `author_rank_frequency.pdf` |
| Top-x bar chart | Compare top-x shares for configured x values | `top_x_shares.pdf` |
| HHI over time | Temporal trend (if pub_year available, ≥10 papers/year) | `hhi_by_year.pdf` |

Optional (cross-dataset phase):
- Cross-dataset HHI comparison
- Lorenz curves overlaid across datasets

---

## Theme Template

```r
# From r-code-conventions.md — use consistently
theme_custom <- function(base_size = 12) {
  theme_minimal(base_size = base_size) +
    theme(
      plot.title = element_text(face = "bold", color = primary_blue, size = 14),
      plot.subtitle = element_text(color = accent_gray, size = 11),
      axis.title = element_text(color = accent_gray),
      legend.position = "bottom",
      panel.grid.minor = element_blank()
    )
}
```

---

## Export Pattern

```r
save_figure <- function(plot, filename, width = 8, height = 5) {
  out_dir <- file.path(dataset_output_dir, "figures")
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

  ggsave(file.path(out_dir, paste0(filename, ".pdf")),
         plot, width = width, height = height, bg = "white")
  ggsave(file.path(out_dir, paste0(filename, ".png")),
         plot, width = width, height = height, dpi = 300, bg = "white")

  saveRDS(ggplot_build(plot), file.path(out_dir, paste0(filename, "_data.rds")))
}
```

---

## Verification Checklist

```
[ ] PDF opens without errors
[ ] PNG is ≥300 DPI (check file properties)
[ ] All text readable at print size
[ ] No clipped labels or legends
[ ] Axis ranges honest (no misleading truncation)
[ ] N reported in subtitle or caption
[ ] Source data saved as RDS
[ ] Filename follows convention: {descriptive_name}.pdf
[ ] Figure matches data in monopoly_metrics.csv (spot-check values)
```

---

## Caption Template

For papers/reports, each figure needs a caption:

> **Figure N.** {What the figure shows}. Based on {N} papers from {dataset name} ({source}, fetched {date}). {Any exclusions or notes}.

Example:

> **Figure 1.** Distribution of paper counts across authors citing the REGARDS study. Based on 911 papers from PubMed collection 46426411 (fetched 2026-06-23). Authors merged per alias table (47 merges).
