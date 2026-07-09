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

### Stanford SEDA 6.0 (national achievement context)

**Portal:** [Educational Opportunity Project — Data downloads](https://edopportunity.org/opportunity/data/downloads/#testscore-6) (Version 6.0).

**What to download for national comparison figures**

- **`seda_geodist_poolsub_cs_6.0.csv`** (~100 MB) — Geographic school districts, pooled grades/years; includes **race-specific** ELA and math means (`subcat` = `race`, `subgroup` = `wht`, `blk`, `hsp`, …). Use this for White vs. Black / White vs. Hispanic scatters in **cohort-scale units** (not Wisconsin proficiency %).
- **`seda_school_pool_cs_6.0.csv`** (very large) — School-level file has **all-student means only** (no race-specific columns in the public pool file). Do not expect a direct school × race national analog to DPI school cells from this file alone.

**Automated download (recommended)**

```bash
python3 analysis/11_download_seda.py
# Optional: also fetch all-student school pool (large; no race breakdown):
# python3 analysis/11_download_seda.py --include-school-pool
```

Files land in `Data/raw/seda/` (gitignored). After download, build the national context figure:

```bash
python3 analysis/12_seda_national_scatter.py
```

**Citation:** Reardon, S. F., Ho, A. D., Shear, B. R., Fahle, E. M., Kalogrides, D., saliba, j. (2026). *Stanford Education Data Archive (Version 6.0)*. https://purl.stanford.edu/xh833nn4025

---

## Cross-state school-by-race files (Figure 12 replication)

Used by `manuscript/cross-state.qmd`. Download with `python3 analysis/13_download_states.py`
(per-state: `--state CA` etc.); files land in `Data/raw/states/{st}/` (gitignored).
Harmonize with `python3 analysis/14_load_states.py` →
`output/data/panel_school_race_multistate.parquet` + QC report
`output/tables/multistate_qc.txt`. Figures: `python3 analysis/15_multistate_school_scatter.py`.

### States with scripted downloads (working as of Jul 2026)

| State | Source / URL pattern | Format | Quirks |
|---|---|---|---|
| CA | CAASPP research files, `caaspp-elpac.ets.org/caaspp/researchfiles/sb_ca{yyyy}_all_csv_v1.zip` + `sb_ca{yyyy}entities_csv.zip` | caret-delimited (`^`), latin-1 | Use the `_csv_` variant — the `_ascii_` variant is fixed-width. Schema changed in 2024: 2023 N column is `Students with Scores`, 2024+ is `Total Students Tested with Scores`. Student Group IDs: 74=Black, 78=Hispanic, 80=White. Test ID 1=ELA, 2=Math; Test Type `B` = Smarter Balanced. Suppression `*` (n<11). |
| TX | TEA TAPR CGI (`rptsvr1.tea.texas.gov/cgi/sas/broker`), POST per year/set | CSV | Campus-level. `setpick=STAAR1` has race groups × grades 3-8 RE/MA. Column code: `C{grp}{gg}A{subj}{lvl}{yy}{N/D/R}`; `lvl` 10=denominator, 1S=Approaches, 12=Meets, 13=Masters. Form params changed with the 2024 redesign (2023 uses `prgopt={y}/tapr/tapr_download.sas` + `year4`/`year2`/`topic=acct`). 2023 vintage lacks name columns (merge from 2024). 2025 vintage not yet on this endpoint. Negative values = masked. |
| IL | ISBE Report Card Public Data Set, `isbe.net/Documents/{...}.xlsx` (names vary by year) | xlsx, `IAR` sheet | School-level pooled by-race `IAR ELA/Math Proficiency Rate - {race}` columns exist 2024+ only (2023 file has per-grade level distributions only, no pooled rate). 2025 renamed `Type`→`Level` and dashed the RCDTS. No per-race N published. |
| NY | NYSED `data.nysed.gov/files/essa/{yy-yy}/SRC{yyyy}.zip` (report-card Access DB, ~350 MB) | .mdb/.accdb | Requires `mdbtools` (brew) to export `Annual EM ELA`/`Annual EM MATH` tables to CSV. Each SRC file carries two years. Use per-grade rows ELA3-ELA8 (the `ELA3_8` combined rows exist for All Students only). Filter out district codes (end `0000`), aggregates (start `00000000`), and the statewide row `111111111111`. |
| OH | Report-card blob store `reportcardstorage.education.ohio.gov/data-download-{yyyy}/BUILDING_ETHNIC_{yy}{yy}.xlsx` (2025 on `eduprdreportcardstorage1.blob.core.windows.net`) | xlsx, `RACE` sheet | URLs need the public SAS token embedded in the SPA bundle (in `13_download_states.py`). Per-grade percent proficient only, no N. `NC` = suppressed; `<`/`>` bounded values clipped. Column names carry the year span through 2023-24, dropped in 2024-25. |
| GA | GOSA `download.gosa.ga.gov/{yyyy}/EOG_...csv` | CSV | School-level `ALL GRADES` pooled EOG rows by subgroup with N. Proficiency = `PROFICIENT_PCT + DISTINGUISHED_PCT`. 2023 file lacks the `ACDMC_LVL` column (EOG-only file). |
| NC | `accrpt.tops.ncsu.edu/docs/disag_datasets/Disag_{yyyy-yy}.zip` | tab-delimited txt | Subjects RD/MA, grades 03-08, subgroups WHTE/BLCK/HISP; `pct_glp` = Grade Level Proficient (Level 3+). Drop aggregate school_codes containing `LEA`/`SEA`/`SB` (state + SBE regions + LEA rolls). District names not in file — district_id = first 3 chars of school_code (600=Charlotte-Mecklenburg, 681=Chapel Hill-Carrboro). Bounded values `<5`/`>95` clipped. |
| NJ | `nj.gov/education/assessment/results/reports/{yy}{yy}/spring/{SUBJ}{GG}_NJSLA_DATA_{yyyy-yy}.xlsx` | xlsx per subject-grade | Header on row 3 (`skiprows=2`). Race labels: `White`, `African American`, `Hispanic` under `Subgroup == "Race/Ethnicity"`. Proficiency = L4+L5. 2024-25 filenames use spaces (`%20`) instead of underscores. Suppression `*`. |

### States attempted, manual download required

| State | Blocker | Manual path |
|---|---|---|
| FL | fldoe.org blocks scripted requests (Akamai 403 regardless of user agent) | Browser-download FAST/B.E.S.T. school-level by-subgroup Excel from FDOE → K-12 Student Assessment → Results; place in `Data/raw/states/fl/` and add a loader. |
| MI | MI School Data is an interactive Power BI report; no static files | Grades 3-8 State Testing report → export table by race/ethnicity (150k row limit) while logged out; repeat per year. |
| MN | MDE Data Center (`public.education.mn.gov/MDEAnalytics/`) timed out on repeated scripted attempts | Download "Assessment" data files manually from the MDE Data Reports and Analytics portal. |
| MA | DESE `profiles.doe.mass.edu/statereport/nextgenmcas.aspx` is a session-based ASP.NET form | Select report options in browser and export; one file per year × subgroup. |

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
