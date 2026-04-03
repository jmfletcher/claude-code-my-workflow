# Slides

Short slide deck summarising main findings (~15 slides).
Source: Quarto RevealJS (`main.qmd`).

## Rendering

```bash
quarto render slides/main.qmd            # HTML (RevealJS, for screen)
quarto render slides/main.qmd --to pdf   # PDF (via headless Chromium)
```

## Content outline

1. Motivation: does being surveyed change you?
2. Design: UK week-of-birth natural experiment
3. Three cohorts: NSHD 1946, NCDS 1958, BCS70 1970
4. Data: ONS administrative mortality counts
5. Empirical strategy: treated vs control weeks, FE regression
6. Main result: mortality profiles [diverge / track]
7. By age: age-interval estimates
8. Robustness
9. Comparison with WLS (Warren et al. 2022)
10. Conclusion

## Figure convention

All figures sourced from `../output/figures/` — same files as manuscript.
