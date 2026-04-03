---
paths:
  - "analysis/**/*.py"
  - "scripts/**/*.py"
  - "explorations/**/*.py"
---

# Python Code Standards — Panel Conditioning (UK)

**Primary analysis language for this project.** Python first; R and Stata are legacy/reference.

---

## 1. Reproducibility

- `RANDOM_SEED = YYYYMMDD` at top of each script; pass to functions explicitly.
- All packages imported at top.
- All paths relative to repository root — use `pathlib.Path` or `os.path`.
- `Path("output/figures").mkdir(parents=True, exist_ok=True)` for output dirs.
- Pin dependencies in `requirements.txt`; run `pip freeze > requirements.txt` when adding packages.

## 2. Style

- `snake_case` for variables and functions; `PascalCase` for classes (rare).
- Docstrings on all functions (one-line minimum; NumPy-style for complex ones).
- Type hints for function signatures.
- Max line length: 100 characters (same exception as R for long math expressions).

## 3. Domain correctness (mortality / week-of-birth)

- **Denominators:** Every mortality rate must have explicit `N` documented in the same script or loaded from a documented source.
- **Week alignment:** Confirm week-of-year coding matches ONS source documentation (ISO 8601 vs provider convention; week 53 edge case).
- **Group coding:** `cohort = 1` means the **treated** birth week; document in variable comment or assert statement.
- **Regression clustering:** Use `cov_type='cluster'` in `statsmodels` with `groups=week` to match Stata's `cluster(week)`.
- **Replication:** When comparing to legacy Stata, document tolerance; typical goal is numerical match within 3 significant figures.

## 4. Regression (statsmodels pattern)

```python
import statsmodels.formula.api as smf
import pandas as pd

model = smf.ols(
    "rate ~ cohort + C(age_needed) + C(year) + C(week_in_year)",
    data=df
).fit(cov_type="cluster", cov_kwds={"groups": df["week"]})
print(model.summary())
```

- Save full summary to `output/tables/` as text or LaTeX.
- Extract key coefficients as `pd.DataFrame` for manuscript tables.

## 5. Figures (matplotlib / seaborn)

```python
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", font_scale=1.2)
FIGSIZE = (8, 5)   # default; adjust per layout

fig, ax = plt.subplots(figsize=FIGSIZE)
# ... plot ...
fig.savefig("output/figures/fig_name.pdf", dpi=300, bbox_inches="tight")
plt.close()
```

- Save **PDF** for manuscript submission (vector).
- Save **PNG** (300 dpi) for slides/HTML.
- Use colorblind-safe palettes: `seaborn.color_palette("colorblind")`.
- All axes labeled with units; legend outside plot when multiple series.

## 6. Saving outputs

```python
import json

# Regression results
results_df.to_csv("output/tables/table_name.csv", index=False)

# Session info equivalent
import sys, importlib
session = {"python": sys.version, "packages": {p: importlib.import_module(p).__version__ for p in ["pandas", "statsmodels", "numpy"]}}
with open("output/session_info.json", "w") as f:
    json.dump(session, f, indent=2)
```

## 7. Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| `pd.read_excel(..., header=None)` without exploration | Always run `00_data_overview.py` first; document header rows |
| Silent row drops in merge/join | Assert row counts pre- and post-join |
| In-place DataFrame mutation without copy | Use `.copy()` or `.assign()` chains |
| Hard-coded absolute paths | `pathlib.Path(__file__).parent.parent / "Data" / "file.xls"` |

## 8. Quality checklist

```
[ ] Imports at top; no inline imports
[ ] Paths relative (pathlib)
[ ] RANDOM_SEED defined at top when relevant
[ ] Output dirs created with exist_ok=True
[ ] Figures saved as PDF + PNG
[ ] Regression clustering matches Stata specification
[ ] Session info saved to output/
[ ] Script runs end-to-end without errors from repo root
```
