# Manuscript

Quarto source for the preprint-ready manuscript.

## Files

| File | Purpose |
|------|---------|
| `main.qmd` | Main manuscript source (renders to PDF via LaTeX, or HTML) |

## Rendering

```bash
quarto render manuscript/main.qmd           # default format (PDF)
quarto render manuscript/main.qmd --to html # HTML preview
```

Output: `manuscript/main.pdf`

## Figures and tables

Reference outputs from `../output/figures/` and `../output/tables/`.
Use relative paths — do not copy files into `manuscript/`.

## Style notes

- Target: preprint (SSRN / NBER / IZA discussion paper style).
- Every number in the text must trace to a pipeline output or explicit inline computation.
- Denominators (treated and control N) must appear in captions or table footnotes.
