# Data Access Instructions

Raw data files are **not included** in this repository. This document describes how to obtain them and where to place them.

---

## 1. Forward Exam — Proficiency by Race (school level)

**Source:** Wisconsin Department of Public Instruction (DPI)

**What you need:** School-level Forward Exam proficiency rates broken down by race/ethnicity, grades 3–8, ELA and Math.

### Option A: WISEdash Public Portal (CSV export)

1. Go to [WISEdash Public Portal](https://wisedash.dpi.wi.gov/Dashboard/portalHome)
2. Topics → Assessment → Forward Exam
3. In the dashboard:
   - Level → **School**
   - Group → **Race/Ethnicity**
   - Set year, subject, grade filters as needed
4. Export as CSV

### Option B: DPI Direct Download Files (preferred for bulk analysis)

- Navigate to: DPI site → Assessment → Forward Exam → Data & Results
- Download the raw assessment result files (includes school IDs, more granular breakdowns)

**Placement:** Place downloaded CSV/Excel files in:

```
Data/
└── forward_exam/
    ├── forward_exam_<year>_school_race.csv
    └── ...
```

---

## 2. Enrollment by Race (school level)

**Source:** Wisconsin DPI enrollment datasets

**What you need:** School-level enrollment counts by race/ethnicity (denominator for proficiency rates and for constructing enrollment-based gap measures).

**Access options:**
- DPI enrollment downloads (search DPI site for "enrollment by race")
- [School District Enrollment Demographics, Wisconsin 2024 (ArcGIS)](https://www.arcgis.com/home/item.html?id=2c15aa7e7a0247b99f1573819734aeaa)

**Placement:**

```
Data/
└── enrollment/
    └── enrollment_by_race_<year>.csv
```

---

## 3. School Characteristics

**Source:** Wisconsin DPI or NCES Common Core of Data (CCD)

**Variables needed:**
- Urbanicity / locale code (urban, suburban, rural)
- Free/Reduced Price Lunch (FRPL) rate — proxy for poverty
- District size, school size
- Grade configuration

**Access:**
- DPI: search "school directory" or "school report card data"
- NCES CCD: [https://nces.ed.gov/ccd/](https://nces.ed.gov/ccd/) — Public School Universe Survey

**Placement:**

```
Data/
└── school_characteristics/
    └── school_characteristics_<year>.csv
```

---

## 4. Merge key

All DPI datasets use a **school ID** (NCES or DPI format). Confirm the ID format used across datasets before merging. Document any mismatches in `MEMORY.md`.

---

## 5. Important caveats

### Suppression
- DPI suppresses cells with fewer than 10 students
- Affects race × school breakdowns for small schools and small racial subgroups
- Document suppression rates when building analysis dataset

### Changing proficiency standards
- DPI changed cut scores in recent years
- Cross-year comparisons require checking whether standards are consistent
- See DPI documentation for the year of standard revision

### Test coverage by grade
| Test | Grades | Notes |
|------|--------|-------|
| Forward Exam | 3–8 | Primary source for school-level race gaps |
| PreACT | 9–10 | |
| ACT | 11 | |
| NAEP | State-level only | Not available at school level |
