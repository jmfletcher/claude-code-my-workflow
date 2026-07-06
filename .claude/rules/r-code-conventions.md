---
paths:
  - "**/*.R"
  - "Figures/**/*.R"
  - "scripts/**/*.R"
---

# R Code Standards

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

## 3. Domain Correctness

- HHI computed as sum of squared author paper-shares (see `authorship-monopoly-metrics.md`)
- Top-x share: each paper counted once; ties at x-th position include all tied authors
- Author merges only via `author_aliases.csv` — never inline in scripts
- PubMed author strings: `{LastName} {Initials}` format consistently
- Count reconciliation required before metrics computation

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

### Figure Dimensions for Beamer
```r
ggsave(filepath, width = 12, height = 5, bg = "transparent")
```

## 5. RDS Data Pattern

**Heavy computations saved as RDS; slide rendering loads pre-computed data.**

```r
saveRDS(result, file.path(out_dir, "descriptive_name.rds"))
```

## 6. Common Pitfalls

| Pitfall | Impact | Prevention |
|---------|--------|------------|
| Missing `bg = "white"` | Wrong background in figures | Always specify in ggsave() |
| Hardcoded paths | Breaks on other machines | Use relative paths from repo root |
| Inline author merges | Untraceable dedup | Use author_aliases.csv only |
| Skipping count reconciliation | Silent data loss | QC check before metrics |
| Missing alias notes | Undocumented merges | notes column required, non-empty |

## 7. Config and Alias Patterns

### Loading Dataset Config

```r
library(yaml)

load_dataset_config <- function(dataset_name) {
  config_path <- file.path("datasets", dataset_name, "config.yaml")
  yaml::read_yaml(config_path)
}
```

### Applying Author Aliases

```r
apply_author_aliases <- function(papers_authors, aliases_path) {
  aliases <- readr::read_csv(aliases_path, show_col_types = FALSE)
  papers_authors %>%
    dplyr::left_join(aliases, by = "author_raw") %>%
    dplyr::mutate(author_id = dplyr::coalesce(author_id.y, author_raw)) %>%
    dplyr::select(-author_id.y)
}
```

### Output Directory Pattern

```r
dataset_dir <- file.path("datasets", dataset_name)
out_dir <- file.path(dataset_dir, "output")
dir.create(file.path(out_dir, "figures"), recursive = TRUE, showWarnings = FALSE)
```

## 8. Line Length & Mathematical Exceptions

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

## 9. Code Quality Checklist

```
[ ] Packages at top via library()
[ ] set.seed() once at top
[ ] All paths relative
[ ] Functions documented (Roxygen)
[ ] Figures: white bg, explicit dimensions, PDF + PNG
[ ] RDS: every computed object saved
[ ] Author aliases applied via CSV, not inline
[ ] Count reconciliation before metrics
[ ] Comments explain WHY not WHAT
```
