---
paths:
  - "analysis/**/*.py"
  - "manuscript/**"
  - "Slides/**"
---

# Research Knowledge Base: Wisconsin Racial Achievement Gaps

<!-- Read this before creating or modifying any analysis, figure, or report content.
     Fill in [PENDING] entries as data is downloaded and inspected. -->

---

## Estimand Registry

| Estimand | Symbol | Definition | Notes |
|----------|--------|-----------|-------|
| Raw proficiency gap (Black–White) | G_BW | pct_proficient(White) − pct_proficient(Black) | School-level, same grade/subject/year |
| Raw proficiency gap (Hispanic–White) | G_HW | pct_proficient(White) − pct_proficient(Hispanic) | School-level, same grade/subject/year |
| Between-school component | G_between | Weighted avg of school-mean gaps, where weight = share of minority enrollment in each school | Accounts for sorting across schools |
| Within-school component | G_within | G_total − G_between | Gaps that exist even within same school |
| MMSD vs. state: minority comparison | G_mmsd_ext | avg(MMSD minority proficiency) − avg(same-race proficiency elsewhere in WI) | Key thought experiment 1 |
| MMSD minority vs. non-MMSD white | G_mmsd_cross | avg(non-MMSD white proficiency) − avg(MMSD minority proficiency) | Key thought experiment 2; addresses MMSD white outlier-SES problem |

Decomposition identity (verify at each aggregation level):

```
G_total = G_between + G_within
```

Tolerance: components must sum to total gap ± 0.001 percentage points.

---

## Variable Naming Conventions

Confirmed from `01_inspect_data.py` run on 2022-23 file (2026-04-03).

**Raw DPI column names (21 columns, consistent across all Forward Exam years):**

| Canonical name (our code) | DPI source column | Notes |
|--------------------------|------------------|-------|
| `year` | `SCHOOL_YEAR` | String e.g. `"2022-23"` |
| `agency_type` | `AGENCY_TYPE` | `"School District"` = district; `"Public school"` = school; `NaN` = statewide |
| `cesa` | `CESA` | Cooperative Educational Service Agency region |
| `county` | `COUNTY` | County name string |
| `district_id` | `DISTRICT_CODE` | DPI-assigned district code |
| `school_id` | `SCHOOL_CODE` | DPI-assigned school code (blank for district rows) |
| `grade_group` | `GRADE_GROUP` | e.g. `"Elementary School"`, `"[All]"` |
| `charter` | `CHARTER_IND` | Charter indicator |
| `district_name` | `DISTRICT_NAME` | Full district name e.g. `"Madison Metropolitan"` |
| `school_name` | `SCHOOL_NAME` | Full school name (blank for district rows) |
| `subject` | `TEST_SUBJECT` | `"ELA"`, `"Mathematics"`, `"Science"`, `"Social Studies"` |
| `grade` | `GRADE_LEVEL` | Integer: 3, 4, 5, 6, 7, 8, 10 |
| `test_result` | `TEST_RESULT` | `"Proficient"`, `"Advanced"`, `"Basic"`, `"Below Basic"`, `"No Test"`, `"*"` |
| `test_result_code` | `TEST_RESULT_CODE` | Numeric code for TEST_RESULT |
| `test_group` | `TEST_GROUP` | `"Forward"` or `"DLM"` (Dynamic Learning Maps = severe disabilities) |
| `group_by` | `GROUP_BY` | Category type: `"Race/Ethnicity"`, `"Gender"`, `"Economic Status"`, etc. |
| `group_by_value` | `GROUP_BY_VALUE` | Value within category (see Race Category Labels) |
| `n_at_level` | `STUDENT_COUNT` | Count of students at this TEST_RESULT level (`"*"` if suppressed) |
| `pct_at_level` | `PERCENT_OF_GROUP` | % of group at this TEST_RESULT level, 0–100 scale (`"*"` if suppressed) |
| `n_tested` | `GROUP_COUNT` | Total students tested in this group at this school/grade/subject (`"*"` if suppressed) |
| `scale_score` | `FORWARD_AVERAGE_SCALE_SCORE` | Average scale score (additional metric) |

**Data structure note:** The data is LONG format. One row = one school × grade × subject × group_by × group_by_value × test_result combination. To compute proficiency rate for a group:
```python
# Filter to Forward test, Race/Ethnicity group, grades 3-8, ELA or Math
# Proficiency rate = pct_at_level where test_result in ('Proficient', 'Advanced')
# Or compute as: (n_proficient + n_advanced) / n_tested
```

**Suppression:** Symbol is `"*"` in `STUDENT_COUNT`, `PERCENT_OF_GROUP`, `GROUP_COUNT`, `TEST_RESULT`, `TEST_RESULT_CODE`. In 2022-23: ~154K suppressed rows out of 925K total (~17%). Set all `"*"` values to `NaN`.

---

## Race Category Labels

<!-- Fill in EXACTLY as they appear in the raw DPI CSV.
     Wrong labels cause silent merge failures. -->

Confirmed from 2022-23 file. These are values of `GROUP_BY_VALUE` when `GROUP_BY == "Race/Ethnicity"`.

| Our label | DPI `GROUP_BY_VALUE` string (exact) | Notes |
|-----------|-------------------------------------|-------|
| White | `"White"` | |
| Black | `"Black"` | Note: NOT "Black or African American" — shorter label |
| Hispanic | `"Hispanic"` | |
| Asian | `"Asian"` | |
| American Indian | `"Amer Indian"` | Abbreviated |
| Pacific Islander | `"Pacific Isle"` | Abbreviated |
| Two or More Races | `"Two or More"` | |
| Unknown | `"Unknown"` | |
| Suppressed group | `"[Data Suppressed]"` | Treat as NaN |
| All students | `"All Students"` | In GROUP_BY_VALUE when GROUP_BY == "All Students" |

**Other GROUP_BY_VALUE values** (non-race): `"EL"`, `"Econ Disadv"`, `"Eng Prof"`, `"Female"`, `"Male"`, `"Migrant"`, `"Non-binary"`, `"Not Econ Disadv"`, `"Not Migrant"`, `"SwD"` (students with disabilities), `"SwoD"` (students without disabilities).

---

## School ID Format

- DPI uses its own `DISTRICT_CODE` and `SCHOOL_CODE` (NOT NCES format).
- `DISTRICT_CODE`: DPI-assigned district number (integer in data)
- `SCHOOL_CODE`: DPI-assigned school number (integer; blank/0 for district-level rows)
- Merge key for joining datasets: `(DISTRICT_CODE, SCHOOL_CODE)` or `(DISTRICT_CODE, SCHOOL_CODE, SCHOOL_YEAR)`
- MMSD `DISTRICT_NAME` = `"Madison Metropolitan"` (confirmed)
- MMSD `DISTRICT_CODE`: [PENDING — extract from data with `df[df.DISTRICT_NAME=="Madison Metropolitan"].DISTRICT_CODE.unique()`]
- Milwaukee `DISTRICT_CODE`: [PENDING — extract similarly]

---

## Zip File Structure (CRITICAL for load script)

- **2015-16 through 2022-23**: Each zip has ONE data CSV + ONE layout CSV.
  - `forward_certified_YYYY-YY.csv`
- **2023-24 and 2024-25**: Each zip has TWO data CSVs (split by subject group) + layout files.
  - `forward_certified_ELA_RDG_WRT_YYYY-YY.csv`
  - `forward_certified_MTH_SCN_SOC_YYYY-YY.csv`
  - **Load script must read and concatenate BOTH CSVs for 2023-24 and 2024-25.**

## ELL vs. EL Status Label

- 2015-16 through 2018-19: `GROUP_BY == "ELL Status"`
- 2020-21 onward: `GROUP_BY == "EL Status"` (same concept, relabeled)
- Harmonize: `df["GROUP_BY"] = df["GROUP_BY"].replace("ELL Status", "EL Status")`

## Test Coverage

| Test | Grades | Subject | Used in this project |
|------|--------|---------|---------------------|
| Forward Exam | 3–8 | ELA, Math | Yes — primary source |
| PreACT | 9–10 | — | Not in scope initially |
| ACT | 11 | — | Not in scope initially |
| NAEP | State-level only | — | Reference only, not school-level |

---

## Anti-Patterns (Do Not Do This)

| Anti-Pattern | Why It Is Wrong | Correct Approach |
|-------------|----------------|-----------------|
| Mix Forward Exam with ACT/PreACT in a single proficiency series | Different tests, different scales, different populations | Analyze each test separately; note grade bands explicitly |
| Treat proficiency rate as a continuous test score | Proficiency is a binary threshold; rate is a proportion, not a scale score | Describe as "share proficient," not "test score" |
| Use MMSD white students as the statewide White comparison group | MMSD whites are high-SES outliers; inflates apparent gap | Use all non-MMSD White students for cross-district comparisons |
| Report a race-specific rate without noting N | A rate based on 11 students is not comparable to one based on 400 | Always report N or flag suppression |
| Impute suppressed cells | DPI suppressed for privacy; imputation introduces bias | Set to NaN, log to suppression_log.csv, exclude from aggregate calculations |
| Interpret within–between decomposition causally | Decomposition is descriptive accounting, not causal | Frame as "X% of the gap is associated with cross-school sorting" |
| Compare MMSD gap to "the state gap" without specifying comparison group | "State gap" is ambiguous (all WI vs. non-MMSD vs. similar districts) | Always specify the comparison group explicitly |

---

## Known Data Quirks

<!-- Fill in as data is explored. Examples: -->

| Quirk | Impact | Resolution |
|-------|--------|-----------|
| [PENDING — fill on first data inspection] | | |

---

## Proficiency Standard Changes

<!-- Fill in once DPI documentation is reviewed -->

| Year | Change | Impact on trends |
|------|--------|-----------------|
| [PENDING] | DPI revised cut scores | Cross-year comparisons before/after this year require caveat |
