# Data Access Instructions

Raw data files are **not included** in this repository (gitignored). This document describes how to obtain them and where to place them, plus a complete history of Wisconsin assessment changes.

---

## Quick Download

```bash
# Download all Forward Exam years (recommended starting point):
python3 analysis/00_download_data.py --era forward

# Download only specific years:
python3 analysis/00_download_data.py --era forward --years 2018-19 2021-22 2022-23

# Inspect what's in the downloaded files:
python3 analysis/00_download_data.py --list
python3 analysis/01_inspect_data.py

# Download WKCE historical (large files, different test — optional):
python3 analysis/00_download_data.py --era wkce
```

Files land in `Data/raw/forward/` and `Data/raw/wkce/` (both gitignored).

---

## 1. Forward Exam — Proficiency by Race (school level)

**Source:** Wisconsin Department of Public Instruction (DPI)
**DPI download page:** https://dpi.wi.gov/wisedash/download-files/type?field_wisedash_upload_type_value=Forward

### Available years and flags

| School Year | File | Size | Status | Flag |
|-------------|------|------|--------|------|
| 2015-16 | `forward_certified_2015-16.zip` | ~8 MB | Available | Baseline year |
| 2016-17 | `forward_certified_2016-17.zip` | ~8 MB | Available | |
| 2017-18 | `forward_certified_2017-18.zip` | ~9 MB | Available | |
| 2018-19 | `forward_certified_2018-19.zip` | ~8 MB | Available | Last pre-COVID clean year |
| **2019-20** | **DOES NOT EXIST** | — | **MISSING** | **Federal COVID waiver — no state testing** |
| 2020-21 | `forward_certified_2020-21.zip` | ~8 MB | Available | **COVID-DISRUPTED** — low participation, optional testing |
| 2021-22 | `forward_certified_2021-22.zip` | ~8 MB | Available | Recovery year |
| 2022-23 | `forward_certified_2022-23.zip` | ~8 MB | Available | Last year of original standards |
| 2023-24 | `forward_certified_2023-24.zip` | ~14 MB | Available | **NEW STANDARDS** — cut scores changed |
| 2024-25 | `forward_certified_2024-25.zip` | ~14 MB | Available | **NEW STANDARDS** — not comparable to 2015-22 |

### Recommended analysis windows

| Window | Years | Rationale |
|--------|-------|-----------|
| **Primary** | 2015-16 to 2022-23 (excl. 2019-20, 2020-21) | Same test, same standards, no COVID disruption |
| **Extended (with caveats)** | Add 2023-24, 2024-25 | Label as "new standards era"; do not compare proficiency rates directly to pre-2023-24 |
| **COVID sensitivity check** | Include 2020-21 | Show results with/without — treat as robustness |
| **Historical (separate analysis)** | WKCE 2003-04 to 2013-14 | Label as "different assessment"; do not trend with Forward Exam |

### Placement

```
Data/
└── raw/
    └── forward/
        ├── forward_certified_2015-16.zip
        ├── forward_certified_2016-17.zip
        ├── forward_certified_2017-18.zip
        ├── forward_certified_2018-19.zip
        ├── forward_certified_2020-21.zip    ← COVID flag
        ├── forward_certified_2021-22.zip
        ├── forward_certified_2022-23.zip
        ├── forward_certified_2023-24.zip    ← new standards
        └── forward_certified_2024-25.zip    ← new standards
```

---

## 2. WKCE Scale Score Summary Data (pre-Forward era, Keo files)

**Source:** Wisconsin DPI statewide WKCE Scale Score Summary (SSS) files, compiled ~2013-2014 by prior research team.

**Coverage:** 2003-04 through 2013-14 (11 years). Statewide and district-level. Five subjects: Reading, Language Arts, Mathematics, Science, Social Studies. Grades 3–8 and 10.

**Key variables:** Mean scale score, percentile distributions (10th, 25th, 50th, 75th, 90th) by race/ethnicity, gender, EL status, Special Education status, Economic status.

**Race categories:**
- Pre-2010-11: 5 categories (American Indian, Asian/Pacific Islander, Black, Hispanic, White)
- 2010-11 onward: 7 categories (split Asian/Pacific Islander; added Two or More Races)

**Codebook:** See `Data/archive/keo_compiled/layout_EXW_IAS_SPS_SSS (1).xls` for student group codes and column definitions. See `Data/archive/keo_compiled/MMSD Data Documentation.docx` for field descriptions.

### Placement (already populated from Keo Data)

```
Data/
└── raw/
│   └── wkce_sss/
│       ├── 2003 raw/       ← 3 TXT files (Grade03, Grade04, Grade05 subjects)
│       ├── 2004 raw/
│       ├── 2005 raw/
│       ├── 2006 raw/       ← 7 TXT files (grades 3–8 + 10)
│       ├── 2007 raw/
│       ├── 2008 raw/
│       ├── 2009 raw/
│       ├── 2010 raw/
│       ├── 2011 raw/
│       ├── 2012 raw/
│       └── 2013-14 raw/    ← 6 TXT files
└── archive/
    └── keo_compiled/       ← Excel and Stata files (reference only; do not use for analysis)
```

**Analysis script:** `analysis/03_load_wkce.py` (skeleton created; reads SSS TXT files using the layout codebook).

---

## 2b. WKCE / WINSS All-Topics Historical Data (optional, large files)

**Source:** WINSS Historical Data Files via DPI
**DPI page:** https://dpi.wi.gov/wisedash/public/download-files/winss-historical

These are ALL-TOPICS files (large: 50–300 MB each). Assessment data is one topic among many inside each zip. The Keo SSS TXT files (section 2 above) are a pre-extracted, cleaner version of the same WKCE data — prefer those for assessment analysis.

### Placement (if downloaded)

```
Data/
└── raw/
    └── wkce/
        ├── all_topics_winss_2003-04.zip
        ├── ...
        └── all_topics_winss_2011-12.zip
```

---

## 3. Wisconsin Assessment History (complete timeline)

### Chronology of Wisconsin statewide assessments (grades 3-8)

| Era | Assessment | Years Active | Grades | Notes |
|-----|-----------|-------------|--------|-------|
| Pre-2003 | WSAS (Wisconsin Student Assessment System) | 1986–2002 | 4, 8, 10 | Only selected grades; limited school-level data |
| 2003–2014 | WKCE (Wisconsin Knowledge and Concepts Exam) | 2003-04 to 2013-14 | 3-8, 10 | Replaced WSAS; major comparability break with prior era |
| 2014-15 | Smarter Balanced (transition) | 2014-15 ONLY | 3-8 | Results never certified/released; treat as missing |
| 2015–present | Forward Exam | 2015-16 to present | 3-8 | Current assessment; two sub-eras (see below) |

### Forward Exam sub-eras

| Sub-era | Years | Standards | Notes |
|---------|-------|-----------|-------|
| Original | 2015-16 to 2022-23 | Original Wisconsin Academic Standards | Results directly comparable within this window |
| New | 2023-24 to present | Updated Wisconsin Academic Standards | DPI explicitly advises against cross-era trend comparisons |

### Race/ethnicity category changes

| Period | Categories | Notes |
|--------|-----------|-------|
| Pre-2010-11 | 5 categories: American Indian, Asian/Pacific Islander, Black, Hispanic, White | |
| 2010-11 onward (WKCE) | 7 categories: added "Two or More Races"; split Asian/Pacific Islander into "Asian" and "Native Hawaiian/Pacific Islander" | Cross-period comparisons require caution |
| Forward Exam (2015-16 onward) | 7+ categories, same expanded scheme | Exact labels confirmed by running `01_inspect_data.py` |

---

## 4. Enrollment by Race (school level)

**Source:** Wisconsin DPI enrollment datasets

**Variables needed:**
- School-level enrollment counts by race/ethnicity
- Serves as denominator for proficiency rates and for constructing gap measures

**Access:**
- DPI enrollment downloads: search "enrollment" at https://dpi.wi.gov/wisedash/download-files
- ArcGIS 2024 dataset: https://www.arcgis.com/home/item.html?id=2c15aa7e7a0247b99f1573819734aeaa

**Placement:**

```
Data/
└── raw/
    └── enrollment/
        └── enrollment_YYYY-YY.zip  (or .csv)
```

---

## 5. School Characteristics

**Source:** Wisconsin DPI or NCES Common Core of Data (CCD)

**Variables needed:**
- Urbanicity / locale code
- Free/Reduced Price Lunch (FRPL) rate — poverty proxy
- District size, school size, grade configuration

**NCES CCD:** https://nces.ed.gov/ccd/

**Placement:**

```
Data/
└── raw/
    └── characteristics/
        └── school_chars_YYYY-YY.csv
```

---

## 6. COVID years — protocol

The analysis should handle COVID years explicitly:

1. **2019-20:** No data exists. Gap in time series. Mark as missing in all plots.
2. **2020-21:** Data exists but participation was much lower than normal.
   - Default: exclude from trend lines and decomposition analysis.
   - Option: include in a robustness appendix table with N annotated.
   - Flag in all figures with a dashed line or gap marker.

```python
# Standard exclusion list used across all scripts:
EXCLUDE_YEARS = ["2019-20", "2020-21"]
COVID_YEARS = ["2020-21"]   # has data but disrupted
```

---

## 7. New standards — protocol (2023-24 onward)

DPI changed the proficiency cut scores in 2023-24 with the new Forward Exam version.

- Do **not** plot 2023-24+ on the same trend line as 2015-22 without a visible break.
- Use a vertical dashed line or different line style to mark the standards change.
- Label in figure captions: "Note: 2023–24 reflects updated proficiency standards not directly comparable to prior years."
- Report 2023-24 results separately in a "current snapshot" section of the report.

---

## 8. Merge key

All DPI datasets use a school/district ID assigned by DPI. Confirm the exact format when running `01_inspect_data.py`. The NCES school ID (12 digits) and the DPI agency_key are different — document which format each dataset uses.

**Expected format:**
- `district_number`: DPI-assigned (4-digit or 6-digit)
- `school_number`: DPI-assigned (4-digit)
- NCES format: state FIPS (55) + district code (5 digits) + school code (5 digits) = 12 digits

Confirm and record in `.claude/rules/knowledge-base-template.md` once data is downloaded.
