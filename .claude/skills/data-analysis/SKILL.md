---
name: data-analysis
description: End-to-end Python data analysis workflow from exploration through analysis to publication-ready tables and figures
argument-hint: "[dataset path or description of analysis goal]"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Edit", "Bash", "Task"]
---

# Data Analysis Workflow

Run an end-to-end data analysis in Python: load, explore, analyze, and produce publication-ready output.

**Input:** `$ARGUMENTS` — a dataset path (e.g., `data/processed/state_infant_mortality_by_race.csv`) or a description of the analysis goal (e.g., "compute detectability thresholds for all geographies").

---

## Constraints

- **Follow Python code conventions** in `.claude/rules/python-code-conventions.md`
- **Save all scripts** to `scripts/python/` with descriptive names
- **Save all outputs** (figures as PNG, tables as CSV) to `Figures/` and `output/`
- **Use project palette** for all figures (check `.claude/rules/python-code-conventions.md`)
- **Run python-reviewer** on the generated script before presenting results

---

## Workflow Phases

### Phase 1: Setup and Data Loading

1. Read `.claude/rules/python-code-conventions.md` for project standards
2. Create Python script with proper module docstring (purpose, inputs, outputs)
3. Import all packages at top, grouped: stdlib → third-party → local
4. Load and inspect the dataset with `pandas`

### Phase 2: Exploratory Data Analysis

Generate diagnostic outputs:
- **Summary statistics:** `.describe()`, missingness rates, dtypes
- **Distributions:** Histograms for key continuous variables
- **Relationships:** Scatter plots, correlation matrices
- **Time patterns:** Plot trends over time
- **Group comparisons:** Compare across race, geography

Save all diagnostic figures to `output/diagnostics/`.

### Phase 3: Main Analysis

Based on the research question:
- **Descriptive analysis:** Rates, CIs, cross-tabulations
- **Statistical tests:** Where appropriate (document assumptions)
- **Multiple specifications:** Start simple, progressively add complexity
- **Effect sizes:** Report alongside raw estimates

### Phase 4: Publication-Ready Output

**Tables:**
- Use `pandas` DataFrames formatted as CSV or markdown
- Include all standard elements: estimates, CIs, N
- Export as `.csv` for Quarto inclusion

**Figures:**
- Use `matplotlib` with project palette (White=#2171b5, Black=#b2182b)
- Set DPI to 300 for publication quality
- Include proper axis labels (sentence case, units)
- Export with `bbox_inches="tight"`: `fig.savefig(path, dpi=300, bbox_inches="tight")`

### Phase 5: Save and Review

1. Save all DataFrames as CSV
2. Create output directories with `os.makedirs(..., exist_ok=True)`
3. Run the python-reviewer agent on the generated script:

```
Delegate to the python-reviewer agent:
"Review the script at scripts/python/[script_name].py"
```

4. Address any Critical or High issues from the review.

---

## Script Structure

Follow this template:

```python
"""
[Descriptive Title]

Purpose: [What this script does]
Inputs: [Data files]
Outputs: [Figures, tables, CSV files]
"""

import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import pandas as pd
import matplotlib.pyplot as plt

# --- Config ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
FIGURE_DIR = PROJECT_ROOT / "Figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

RACE_COLORS = {"White": "#2171b5", "Black": "#b2182b"}
FIGURE_DPI = 300


def main():
    # 1. Data Loading
    # [Load and clean data]

    # 2. Analysis
    # [Compute rates, CIs, tables]

    # 3. Figures
    # [Publication-ready output]

    # 4. Export
    # [to_csv for all DataFrames, savefig for all figures]
    pass


if __name__ == "__main__":
    main()
```

---

## Important

- **Reproduce, don't guess.** If the user specifies an analysis, run exactly that.
- **Show your work.** Print summary statistics before jumping to conclusions.
- **Check for issues.** Look for missing data, division by zero, unexpected types.
- **Use relative paths.** All paths relative to repository root via `pathlib`.
- **No hardcoded values.** Use variables for sample restrictions, date ranges, etc.
