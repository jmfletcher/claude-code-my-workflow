# Quality Gate Score — 2026-03-14

## Python Scripts (scripts/python/)

| Script | Score | Notes |
|--------|-------|-------|
| config.py | 100/100 | Clean, type hints, pathlib, no issues |
| 01_load_and_clean.py | 100/100 | Early-return fix applied; clean |
| 02_figures.py | 100/100 | Correct palette, DPI, bbox_inches |
| 03_tables.py | 100/100 | Dead code removed; clean output |
| 04_detectability.py | 99/100 | -1 for long table header lines (~110 chars) |

**Aggregate Python score: 99/100** — exceeds PR threshold (90).

### Checklist

- [x] No syntax/runtime errors (all scripts run cleanly)
- [x] No domain-specific bugs (formulas verified)
- [x] No hardcoded absolute paths (pathlib throughout)
- [x] Type hints on all functions
- [x] Correct figure palette (RACE_COLORS from config)
- [x] `if __name__ == "__main__"` guard on all scripts
- [x] CSV_FILES centralized in config.py (single source of truth)

## Quarto Report (Quarto/report.qmd)

| Category | Score | Notes |
|----------|-------|-------|
| Compilation | ✓ | Renders to PDF without errors |
| Citations | ✓ | All 11 keys verified in Bibliography_base.bib |
| Equations | ✓ | No overflow or typos |
| Tables | ✓ | All 3 tables aligned with script output CSVs |
| Notation | ✓ | "e.g.," consistent, "State Rep." consistent |
| Grammar | ✓ | High/medium proofreader issues fixed |

**Quarto score: 98/100** — exceeds PR threshold (90).

- -1: Some body-text lines exceed 100 chars (markdown prose, not code)
- -1: Minor low-severity style items remain (see proofread report)

## Overall

| Artifact | Score | Threshold | Status |
|----------|-------|-----------|--------|
| Python scripts | 99/100 | 90 (PR) | **PASS** |
| Quarto report | 98/100 | 90 (PR) | **PASS** |

## Issues Fixed in This Review

### Critical (1)
1. `validate()` in `01_load_and_clean.py` — early return when columns missing

### High (3)
1. Unused `ci_95_poisson` call in `03_tables.py` — removed
2. ASCII banners and excessive prints in `01_load_and_clean.py` — trimmed
3. Missing verb in AB 1085 description — fixed

### Medium (6)
1. Per-iteration prints in `02_figures.py` — reduced to one summary line
2. Verbose table dumps in `03_tables.py` — removed
3. Verbose markdown dump in `04_detectability.py` — removed
4. CSV_FILES duplicated across 4 scripts — centralized in config.py
5. Raw detectability results not saved — now writes detectability_raw.csv
6. Report tables misaligned with script output — all 3 tables updated

### Report Alignment
- Table 1: 6 cells updated (rates, CIs)
- Table 2: 8 cells updated (margins, CIs, reduction values)
- Table 3: 1 cell updated (Milwaukee Black CI 41→40)
- Interpretation paragraphs updated to match

### Scope Note
- Added "no cause-specific analysis" to MEMORY.md and report conclusion
