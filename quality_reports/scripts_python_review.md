# Python Code Review: scripts/python/ (Combined)
**Date:** 2025-03-14
**Reviewer:** python-reviewer agent

## Summary
- **Total issues:** 14
- **Critical:** 1 (blocks correctness or reproducibility)
- **High:** 3 (blocks professional quality)
- **Medium:** 6 (improvement recommended)
- **Low:** 4 (style / polish)

---

## Issues

### Issue 1: validate() crashes when expected columns are missing
- **File:** `scripts/python/01_load_and_clean.py`:51-73
- **Category:** Error Handling
- **Severity:** Critical
- **Current:**
  ```python
  def validate(df: pd.DataFrame, geo: str) -> list[str]:
      """Run validation checks; return list of warnings."""
      warnings = []
      for col in EXPECTED_COLUMNS:
          if col not in df.columns:
              warnings.append(f"Missing column: {col}")

      if (df["births"] < 0).any():  # KeyError if "births" missing
          warnings.append("Negative birth counts found")
      # ... more column accesses
  ```
- **Proposed fix:**
  ```python
  def validate(df: pd.DataFrame, geo: str) -> list[str]:
      """Run validation checks; return list of warnings."""
      warnings = []
      missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
      if missing:
          warnings.extend(f"Missing column: {c}" for c in missing)
          return warnings  # Cannot run further checks without required columns

      if (df["births"] < 0).any():
          warnings.append("Negative birth counts found")
      # ... rest of checks
  ```
- **Rationale:** If any expected column is missing, the function appends a warning but then raises `KeyError` when accessing `df["births"]` or other columns. Early return ensures all missing-column warnings are reported without crashing.

---

### Issue 2: Unused ci_95_poisson result in build_table3
- **File:** `scripts/python/03_tables.py`:109-114
- **Category:** Domain Correctness / Polish
- **Severity:** High
- **Current:**
  ```python
      for _, r in averages.iterrows():
          deaths = r["approx_annual_deaths"]
          lo, hi = ci_95_poisson(deaths, r["approx_annual_births"])

          d_lo = deaths - 1.96 * math.sqrt(deaths) if deaths > 0 else 0
          d_hi = deaths + 1.96 * math.sqrt(deaths) if deaths > 0 else 0
          ci_deaths = f"{max(0, int(round(d_lo)))}–{int(round(d_hi))}"
  ```
- **Proposed fix:**
  ```python
      for _, r in averages.iterrows():
          deaths = r["approx_annual_deaths"]
          d_lo = deaths - 1.96 * math.sqrt(deaths) if deaths > 0 else 0
          d_hi = deaths + 1.96 * math.sqrt(deaths) if deaths > 0 else 0
          ci_deaths = f"{max(0, int(round(d_lo)))}–{int(round(d_hi))}"
  ```
- **Rationale:** `ci_95_poisson` returns rate-based CI bounds; the table uses count-based CI (`d_lo`, `d_hi`). The `lo, hi` variables are never used. Remove the dead call to avoid confusion and unnecessary computation.

---

### Issue 3: ASCII-art banners and excessive console output
- **File:** `scripts/python/01_load_and_clean.py`:77-120
- **Category:** Console Output
- **Severity:** High
- **Current:**
  ```python
  def main() -> None:
      print("=" * 60)
      print("DATA VALIDATION REPORT")
      print("=" * 60)
      # ... per-geography, per-race prints ...
      print("\n" + "=" * 60)
      if all_ok:
          print("ALL GEOGRAPHIES PASSED VALIDATION")
      # ...
  ```
- **Proposed fix:**
  ```python
  def main() -> None:
      print("DATA VALIDATION REPORT")
      # ... structured output without decorative separators ...
      if all_ok:
          print("ALL GEOGRAPHIES PASSED VALIDATION")
      else:
          print("WARNINGS FOUND — review above")
  ```
- **Rationale:** `.claude/rules/python-code-conventions.md` and the review protocol flag "No ASCII-art banners or decorative separators" and "Minimal print() calls — one per major milestone at most." The validation report is useful, but `"=" * 60` separators and per-race prints inside loops violate these standards.

---

### Issue 4: Per-iteration printing in loops
- **File:** `scripts/python/02_figures.py`:74-83
- **Category:** Console Output
- **Severity:** Medium
- **Current:**
  ```python
  for geo in GEOGRAPHIES:
      # ...
      out = plot_geo(geo)
      print(f"Saved {out}")

  print(f"\nAll figures saved to {FIGURE_DIR}/")
  ```
- **Proposed fix:**
  ```python
  for geo in GEOGRAPHIES:
      # ...
      plot_geo(geo)
  print(f"Figures saved to {FIGURE_DIR}")
  ```
- **Rationale:** Protocol: "No per-iteration printing inside loops." One summary line after the loop suffices.

---

### Issue 5: Verbose table and markdown dumps to stdout
- **File:** `scripts/python/03_tables.py`:136-151, `scripts/python/04_detectability.py`:154-156
- **Category:** Console Output
- **Severity:** Medium
- **Current:**
  ```python
  print(f"Table 1 → {t1_path}")
  print(t1.to_string(index=False))
  # ... repeated for t2, t3
  ```
  ```python
  print(f"Written → {out_path}")
  print()
  print(md)
  ```
- **Proposed fix:**
  ```python
  print(f"Table 1 → {t1_path}")
  # Remove print(t1.to_string(...)); user can inspect CSV directly
  ```
  ```python
  print(f"Written → {out_path}")
  # Remove print(md); user can read the file
  ```
- **Rationale:** "Minimal print() calls — one per major milestone." Full table/markdown dumps are excessive; file paths are sufficient for confirmation.

---

### Issue 6: No file existence checks before read_csv
- **File:** `scripts/python/02_figures.py`:39, `scripts/python/03_tables.py`:39, `scripts/python/04_detectability.py`:36
- **Category:** Error Handling
- **Severity:** Medium
- **Current:**
  ```python
  df = pd.read_csv(DATA_DIR / CSV_FILES[geo])
  ```
- **Proposed fix:**
  ```python
  path = DATA_DIR / CSV_FILES[geo]
  if not path.exists():
      raise FileNotFoundError(f"Missing: {path}")
  df = pd.read_csv(path)
  ```
- **Rationale:** `01_load_and_clean.py`'s `load_geo` already checks existence and raises a clear error. `02_figures` checks in `main()` before calling `plot_geo`, but `plot_geo` itself does not; `03_tables` and `04_detectability` never check. Adding checks at read sites yields consistent, clear errors and makes functions robust when called directly.

---

### Issue 7: Duplicated CSV_FILES across four scripts
- **File:** `scripts/python/01_load_and_clean.py`:24-29, `02_figures.py`:29-34, `03_tables.py`:27-32, `04_detectability.py`:25-30
- **Category:** Structure
- **Severity:** Medium
- **Current:** Each script defines the same `CSV_FILES` dict.
- **Proposed fix:** Add to `config.py`:
  ```python
  CSV_FILES = {
      "state": "state_infant_mortality_by_race.csv",
      "milwaukee": "milwaukee_infant_mortality_by_race.csv",
      "dane": "dane_infant_mortality_by_race.csv",
      "rest_of_wisconsin": "rest_of_wisconsin_infant_mortality_by_race.csv",
  }
  ```
  Then import from config in each script.
- **Rationale:** Single source of truth; adding a geography or renaming files requires one change.

---

### Issue 8: ci_95_poisson does not guard against None for deaths
- **File:** `scripts/python/config.py`:50-64
- **Category:** Error Handling
- **Severity:** Low
- **Current:**
  ```python
  def ci_95_poisson(deaths: int, births: int) -> tuple[float, float]:
      if births is None or births == 0:
          return (0.0, 0.0)
      rate = 1000.0 * deaths / births  # TypeError if deaths is None
  ```
- **Proposed fix:**
  ```python
  def ci_95_poisson(deaths: int, births: int) -> tuple[float, float]:
      if births is None or births == 0 or deaths is None:
          return (0.0, 0.0)
  ```
- **Rationale:** Callers use `int(round(...))`, so `deaths` is typically an int. Defensive handling of `None` avoids cryptic `TypeError` if misused.

---

### Issue 9: plot_geo lacks file existence check
- **File:** `scripts/python/02_figures.py`:37-41
- **Category:** Error Handling
- **Severity:** Low
- **Current:**
  ```python
  def plot_geo(geo: str) -> Path:
      """Generate rate-by-race figure for one geography. Returns output path."""
      df = pd.read_csv(DATA_DIR / CSV_FILES[geo])
  ```
- **Proposed fix:**
  ```python
  def plot_geo(geo: str) -> Path:
      path = DATA_DIR / CSV_FILES[geo]
      if not path.exists():
          raise FileNotFoundError(f"Missing: {path}")
      df = pd.read_csv(path)
  ```
- **Rationale:** Makes `plot_geo` safe when called directly (e.g., from tests or other modules) without relying on `main()`'s pre-check.

---

### Issue 10: Raw detectability results not persisted as CSV
- **File:** `scripts/python/04_detectability.py`:33-88, 151-156
- **Category:** Data Persistence
- **Severity:** Medium
- **Current:** Only `detectability_summary.md` is written; `compute_detectability()` returns a list of dicts that is not saved.
- **Proposed fix:**
  ```python
  results = compute_detectability()
  results_df = pd.DataFrame(results)
  results_df.to_csv(OUTPUT_DIR / "detectability_raw.csv", index=False)
  md = generate_markdown(results)
  out_path.write_text(md, encoding="utf-8")
  ```
- **Rationale:** "Both raw results AND summary tables saved." Saving the raw results as CSV supports reproducibility and downstream analysis.

---

### Issue 11: sys.path manipulation for config import
- **File:** `scripts/python/01_load_and_clean.py`:18-19, `02_figures.py`:22-23, `03_tables.py`:19-20, `04_detectability.py`:17-18
- **Category:** Reproducibility
- **Severity:** Low
- **Current:**
  ```python
  sys.path.insert(0, str(Path(__file__).resolve().parent))
  from config import ...
  ```
- **Proposed fix:** Run scripts from project root with `python -m scripts.python.01_load_and_clean` or add project root to `PYTHONPATH`. Alternatively, use a proper package layout with `__init__.py` and relative imports.
- **Rationale:** `sys.path.insert` is brittle and can conflict with other packages. Running as a module or using `PYTHONPATH` is cleaner.

---

### Issue 12: config.py uses Path.mkdir vs os.makedirs
- **File:** `scripts/python/config.py`:44-47
- **Category:** Reproducibility
- **Severity:** Low (informational)
- **Current:**
  ```python
  def ensure_dirs() -> None:
      FIGURE_DIR.mkdir(parents=True, exist_ok=True)
      OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  ```
- **Proposed fix:** No change required. `Path.mkdir(parents=True, exist_ok=True)` is equivalent to `os.makedirs(..., exist_ok=True)` and is idiomatic for pathlib.
- **Rationale:** Conventions mention `os.makedirs`; pathlib is acceptable and preferred when using `Path` throughout.

---

### Issue 13: 01_load_and_clean has no output persistence
- **File:** `scripts/python/01_load_and_clean.py`
- **Category:** Data Persistence
- **Severity:** Low (informational)
- **Current:** Docstring states "Outputs: Validation report to stdout"; no CSV or log file written.
- **Proposed fix:** Consider writing a validation log to `output/validation_report.txt` or similar for auditability. Optional; current design may be intentional.
- **Rationale:** For full reproducibility, a persisted validation log can be useful; the current design is acceptable if validation is meant only for interactive use.

---

### Issue 14: Line length in generate_markdown
- **File:** `scripts/python/04_detectability.py`:126-129
- **Category:** Polish
- **Severity:** Low
- **Current:**
  ```python
  "| Geography | Race | Rate | 95% CI | Margin | "
  "17% det? | 32% det? | Deaths/yr | Min averted | NFP $M |",
  ```
- **Proposed fix:** Split long table header lines for readability; the string concatenation is valid but the lines approach or exceed 100 characters.
- **Rationale:** Conventions recommend lines ≤ 100 characters where possible.

---

## Checklist Summary

| Category              | Pass | Issues |
|-----------------------|------|--------|
| Structure & Header    | Yes  | 1 (CSV_FILES duplication) |
| Console Output        | No   | 3 (banners, per-iteration, verbose dumps) |
| Reproducibility       | Yes  | 1 (sys.path; minor) |
| Functions             | Yes  | 0 |
| Domain Correctness     | No   | 1 (unused ci_95_poisson) |
| Figures               | Yes  | 0 |
| Data Persistence      | No   | 2 (raw detectability, optional validation log) |
| Comments              | Yes  | 0 |
| Error Handling        | No   | 3 (validate crash, missing file checks, None guard) |
| Polish                | Yes  | 2 (dead code, line length) |

---

## Script-by-Script Notes

### config.py
- Strong: Clear docstring, pathlib, type hints, correct Poisson formulas.
- Minor: Optional `deaths is None` guard in `ci_95_poisson`.

### 01_load_and_clean.py
- Critical: `validate()` will crash on missing columns.
- High: ASCII banners and per-iteration prints violate console hygiene.

### 02_figures.py
- Strong: MPLBACKEND set, 300 DPI, bbox_inches, RACE_COLORS, grid, legend.
- Medium: Per-figure prints; `plot_geo` could add file check for robustness.

### 03_tables.py
- High: Unused `ci_95_poisson` call in `build_table3`.
- Medium: Verbose table dumps; no file existence checks in `load_period_averages`.

### 04_detectability.py
- Medium: Raw results not saved as CSV; full markdown printed; no file checks.
- Low: Long lines in table header.
