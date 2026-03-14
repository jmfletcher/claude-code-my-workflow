---
paths:
  - "**/*.py"
  - "Figures/**/*.py"
  - "scripts/**/*.py"
---

# Python Code Standards

**Standard:** Senior Principal Data Engineer + PhD researcher quality

---

## 1. Reproducibility

- All imports at top of file, grouped: stdlib → third-party → local
- All paths relative to repository root (use `pathlib.Path`)
- `os.makedirs(..., exist_ok=True)` for output directories
- No hardcoded absolute paths
- Matplotlib backend set to `Agg` for headless environments
- Script runs cleanly from `python3 scripts/python/filename.py` on a fresh clone

## 2. Function Design

- `snake_case` naming, verb-noun pattern
- Type hints on all function signatures
- Docstrings (Google style) for all non-trivial functions
- Default parameters; no magic numbers
- Named return values (dicts, namedtuples, or DataFrames with labeled columns)

## 3. Domain Correctness

<!-- Customize for your field's known pitfalls -->
- Verify statistical formulas match report equations
- Check for integer vs float division in rate calculations
- Validate suppressed-count imputation (Total − White) logic

## 4. Visual Identity

```python
# --- Project palette ---
RACE_COLORS = {"White": "#2171b5", "Black": "#b2182b"}
FIGURE_DPI = 300
TITLE_CI_SUFFIX = " (95% CI, Poisson-based)"
```

### Custom Style
```python
import matplotlib.pyplot as plt

def apply_project_style(ax):
    ax.grid(True, alpha=0.25)
    ax.set_xlabel("Year")
    ax.set_ylabel("Infant mortality rate (per 1,000 live births)")
```

### Figure Dimensions
```python
fig.savefig(filepath, dpi=300, bbox_inches="tight")
```

## 5. Data Persistence Pattern

**Processed data saved as CSV; figures as PNG. Quarto report reads these outputs.**

```python
df.to_csv(output_path, index=False)
fig.savefig(figure_path, dpi=FIGURE_DPI, bbox_inches="tight")
```

## 6. Common Pitfalls

| Pitfall | Impact | Prevention |
|---------|--------|------------|
| Integer division in rates | Wrong rate values | Use `float(deaths) / births * 1000` |
| Missing `bbox_inches="tight"` | Clipped labels in figures | Always include in savefig() |
| `pd.read_csv` dtype inference | Suppressed "X" read as NaN | Use `dtype=str` then convert |
| Hardcoded paths | Breaks on other machines | Use `pathlib.Path(__file__).resolve()` |

## 7. Line Length

**Standard:** Keep lines <= 100 characters.

**Exception: Mathematical Formulas** — lines may exceed 100 chars **if and only if:**

1. Breaking the line would harm readability of the math
2. An inline comment explains the mathematical operation:
   ```python
   # Poisson 95% CI: rate ± 1.96 * (1000 * sqrt(D)) / B
   ci_half = 1.96 * (1000.0 * math.sqrt(deaths)) / births
   ```
3. The line is in a numerically intensive section

**Quality Gate Impact:**
- Long lines in non-mathematical code: minor penalty (-1 to -2 per line)
- Long lines in documented mathematical sections: no penalty

## 8. Code Quality Checklist

```
[ ] Imports at top, grouped (stdlib → third-party → local)
[ ] All paths relative (pathlib)
[ ] Functions have type hints and docstrings
[ ] Figures: explicit DPI, bbox_inches="tight"
[ ] CSV: every computed DataFrame saved
[ ] Comments explain WHY not WHAT
[ ] Script has if __name__ == "__main__": main()
[ ] No print() for status — use logging or minimal print
```
