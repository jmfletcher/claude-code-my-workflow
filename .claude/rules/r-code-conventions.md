---
paths:
  - "**/*.R"
  - "analysis/**/*.R"
  - "scripts/**/*.R"
---

# R Code Standards — Panel Conditioning (UK)

**Standard:** Senior Principal Data Engineer + PhD researcher quality

---

## 1. Reproducibility

- `set.seed()` called ONCE at top (YYYYMMDD format)
- All packages loaded at top via `library()` (not `require()`)
- All paths relative to repository root
- `dir.create(..., recursive = TRUE)` for output directories

## 2. Function Design

- `snake_case` naming, verb-noun pattern
- Roxygen-style documentation
- Default parameters, no magic numbers
- Named return values (lists or tibbles)

## 3. Domain Correctness (mortality / week-of-birth)

- **Denominators:** Any rate or ratio must trace to explicit population at risk or documented rule; store treated/control **N** alongside rates.
- **Week alignment:** Confirm week-of-birth coding matches source documentation (ISO vs provider; week 53).
- **Geography:** Do not mix England & Wales tables with UK-wide series without an explicit bridge.
- **Replication:** When comparing to legacy Stata/CSV outputs, use tolerance rules from the active plan.
- Verify estimator implementations match **manuscript** definitions (not slide sketches).

## 4. Visual Identity

```r
# --- Your institutional palette ---
primary_blue  <- "#012169"
primary_gold  <- "#f2a900"
accent_gray   <- "#525252"
positive_green <- "#15803d"
negative_red  <- "#b91c1c"
```

### Custom Theme
```r
theme_custom <- function(base_size = 14) {
  theme_minimal(base_size = base_size) +
    theme(
      plot.title = element_text(face = "bold", color = primary_blue),
      legend.position = "bottom"
    )
}
```

### Figure dimensions (publication / manuscript)
```r
# Typical single-column width ~6 in; use vector PDF for submission
ggsave(filepath, width = 7, height = 4, dpi = 300)
```

## 5. RDS Data Pattern

**Heavy computations saved as RDS; manuscript/slides load pre-computed objects where appropriate.**

```r
saveRDS(result, file.path(out_dir, "descriptive_name.rds"))
```

## 6. Common Pitfalls

| Pitfall | Impact | Prevention |
|---------|--------|------------|
| Missing `bg = "white"` or transparent where needed | Poor print/PDF appearance | Set explicitly per output |
| Hardcoded paths | Breaks on other machines | Use relative paths / `here::here()` |
| Silent row drops in joins | Wrong Ns | Assert row counts; anti-join checks |

## 7. Line Length & Mathematical Exceptions

**Standard:** Keep lines <= 100 characters.

**Exception: Mathematical Formulas** -- lines may exceed 100 chars **if and only if:**

1. Breaking the line would harm readability of the math (influence functions, matrix ops, finite-difference approximations, formula implementations matching paper equations)
2. An inline comment explains the mathematical operation:
   ```r
   # Sieve projection: inner product of residuals onto basis functions P_k
   alpha_k <- sum(r_i * basis[, k]) / sum(basis[, k]^2)
   ```
3. The line is in a numerically intensive section (simulation loops, estimation routines, inference calculations)

**Quality Gate Impact:**
- Long lines in non-mathematical code: minor penalty (-1 to -2 per line)
- Long lines in documented mathematical sections: no penalty

## 8. Code Quality Checklist

```
[ ] Packages at top via library()
[ ] set.seed() once at top
[ ] All paths relative
[ ] Functions documented (Roxygen)
[ ] Figures: transparent bg, explicit dimensions
[ ] RDS: every computed object saved
[ ] Comments explain WHY not WHAT
```
