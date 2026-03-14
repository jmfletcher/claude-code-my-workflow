---
paths:
  - "**/*.py"
  - "scripts/**/*.py"
---

# Python Code Standards

**Standard:** Senior Principal Data Engineer + PhD researcher quality

---

## 1. Reproducibility

- `np.random.seed()` or `random.seed()` called ONCE at top
- All imports at top, grouped: stdlib → third-party → local
- All paths relative to repository root using `pathlib.Path`
- `os.makedirs(..., exist_ok=True)` for output directories

## 2. Function Design

- `snake_case` naming, verb-noun pattern
- Docstrings (Google or NumPy style)
- Type hints for function signatures
- Default parameters, no magic numbers
- Return named structures (dicts, DataFrames, namedtuples)

## 3. Domain Correctness

- Verify life table implementations match Preston et al. (2001) formulas
- Check that age intervals, `_na_x` values, and open-ended intervals are correct
- Validate that population parsing produces expected counts

## 4. Visual Identity

```python
# --- UW-Madison palette ---
UW_RED       = "#c5050c"
UW_DARK_RED  = "#9b0000"
ACCENT_GRAY  = "#525252"
LIGHT_GRAY   = "#dadfe1"
WHITE_POP    = "#4a7fb5"  # Blue for "White" population lines
BLACK_POP    = "#d62728"  # Red for "Black" population lines
```

### Custom Theme
```python
import matplotlib.pyplot as plt

def set_mortality_theme():
    plt.rcParams.update({
        "figure.figsize": (8, 6),
        "figure.dpi": 300,
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "legend.loc": "best",
        "legend.framealpha": 0.9,
    })
```

### Figure Export
```python
fig.savefig(filepath, dpi=300, bbox_inches="tight", facecolor="white")
```

## 5. Data Persistence Pattern

**Heavy computations saved as parquet or pickle; downstream scripts load pre-computed data.**

```python
df.to_parquet(output_dir / "descriptive_name.parquet")
result.to_pickle(output_dir / "descriptive_name.pkl")
```

## 6. Common Pitfalls

| Pitfall | Impact | Prevention |
|---------|--------|------------|
| Hardcoded paths | Breaks on other machines | Use `pathlib.Path` with relative paths |
| Wrong population file parsing | Garbled race/age/sex data | Use `pd.read_fwf()` with explicit `colspecs` |
| Open interval `_na_x` wrong | LE estimate biased | Use `1/M_85+` for open-ended group |
| Forgetting non-Hispanic filter | Inflated denominators | Always filter origin != Hispanic |
| Single-year rates for small pops | Wildly unstable estimates | Pool 3 years minimum for substate |
| County FIPS confusion | Wrong geographic subset | Milwaukee=55079, Dane=55025 |
| Dane County Black pop too small | Noisy or impossible LE | Flag cell sizes; consider wider pooling |
| Rest-of-WI double counting | Inflated state remainder | Exclude BOTH Milwaukee and Dane |
| Integer overflow in population | Silent wrong counts | Use `int64` dtype explicitly |
| pandas groupby dropping NaN | Missing subgroups silently | Use `dropna=False` in groupby |

## 7. Line Length & Mathematical Exceptions

**Standard:** Keep lines <= 100 characters.

**Exception: Mathematical Formulas** -- lines may exceed 100 chars **if and only if:**

1. Breaking the line would harm readability of the math (life table computations, demographic formulas)
2. An inline comment explains the mathematical operation:
   ```python
   # Person-years lived: L_x = n * (l_x - d_x) + n_a_x * d_x
   L_x = interval_width * (l_x - d_x) + n_a_x * d_x
   ```
3. The line is in a numerically intensive section (life table construction, pooled rate computation)

**Quality Gate Impact:**
- Long lines in non-mathematical code: minor penalty (-1 to -2 per line)
- Long lines in documented mathematical sections: no penalty

## 8. Code Quality Checklist

```
[ ] Imports at top, grouped properly
[ ] Random seed set once at top
[ ] All paths relative via pathlib
[ ] Functions have docstrings + type hints
[ ] Figures: explicit dpi, bbox_inches="tight"
[ ] Intermediate results saved (parquet/pickle)
[ ] Comments explain WHY not WHAT
```

## 9. Required Packages

Core stack for this project:
```
pandas
numpy
matplotlib
geopandas
```
