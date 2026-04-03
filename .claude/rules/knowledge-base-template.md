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

<!-- Fill in once DPI CSV files are downloaded and inspected.
     Use EXACTLY the column names that appear in the raw files. -->

| Canonical name (our code) | DPI source column | Notes |
|--------------------------|------------------|-------|
| `school_id` | [PENDING] | NCES or DPI format — confirm on download |
| `district_id` | [PENDING] | |
| `district_name` | [PENDING] | |
| `school_name` | [PENDING] | |
| `county` | [PENDING] | |
| `race_group` | [PENDING] | See Race Category Labels below |
| `grade` | [PENDING] | Integer or string? Confirm |
| `subject` | [PENDING] | ELA / Math — confirm exact strings |
| `year` | [PENDING] | School year (e.g., 2022–23 or 2023) |
| `n_tested` | [PENDING] | Denominator — confirm column name |
| `n_proficient` | [PENDING] | Numerator — may need to compute from pct |
| `pct_proficient` | [PENDING] | May be 0–100 or 0–1 — confirm on load |
| `suppressed` | (derived) | `True` where DPI cell is `*` or N < 10 |

---

## Race Category Labels

<!-- Fill in EXACTLY as they appear in the raw DPI CSV.
     Wrong labels cause silent merge failures. -->

| Our label | DPI string (raw) | Notes |
|-----------|-----------------|-------|
| White | [PENDING] | |
| Black | [PENDING] | Likely "Black or African American" |
| Hispanic | [PENDING] | Likely "Hispanic" |
| Asian | [PENDING] | |
| American Indian | [PENDING] | |
| Two or More Races | [PENDING] | |
| All students | [PENDING] | Used for total/denominator checks |

**[LEARN action]:** As soon as `01_load_and_clean.py` is run, paste the actual race strings here and add a `[LEARN:data]` entry to `MEMORY.md`.

---

## School ID Format

- DPI data may use a state-assigned ID, an NCES ID, or both.
- NCES format: 7-digit state code + 5-digit district + 5-digit school = 12 digits total.
- Confirm format on first download; document in `MEMORY.md` and update this table.
- MMSD district ID: [PENDING — confirm from DPI data]
- Milwaukee district ID: [PENDING — confirm from DPI data]

---

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
