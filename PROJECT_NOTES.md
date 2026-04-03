# Wisconsin Schools — Racial Achievement Gap Analysis

## Project Goal

Build a school-level dataset of racial achievement gaps across Wisconsin, using publicly available DPI data. Merge test scores with enrollment demographics to produce proficiency rates, weighted measures, and potentially segregation/exposure metrics.

---

## Primary Data Source: WISEdash Public Portal

Wisconsin Department of Public Instruction (DPI) public-facing data system.

**URL:** https://wisedash.dpi.wi.gov/Dashboard/portalHome

### Available data:
- Test scores: Forward Exam, ACT, PreACT
- Breakdowns by race/ethnicity
- School-level AND district-level
- Time trends
- Other cuts: FRPL, EL, disability status

### Navigation path:
1. Topics → Assessment
2. Choose: Forward Exam (grades 3–8) OR ACT / PreACT
3. In dashboard:
   - Level → School
   - Group → Race/Ethnicity
   - Add filters: year, subject, grade
4. Download as CSV for analysis

---

## Alternative: DPI Direct Download Files

Raw files posted by DPI — less user-friendly but more powerful for analysis.

**Where to find:**
- DPI site → Assessment → Forward Exam → Data & Results

**Advantages over dashboard:**
- Include school IDs (for merging)
- Allow merges to other DPI datasets
- Sometimes more granular breakdowns than the dashboard UI

---

## Assessment Tests (by grade band)

| Test | Grades | Notes |
|------|--------|-------|
| Forward Exam | 3–8 | Primary source for school-level race gaps |
| PreACT | 9–10 | |
| ACT | 11 | |
| NAEP | State-level only | Not available at school level |

---

## Benchmark: Statewide Racial Proficiency Gaps (ELA)

These are rough DPI-reported figures for calibration:

| Group | ELA Proficiency (approx.) |
|-------|--------------------------|
| White | ~60%+ |
| Hispanic | ~30–35% |
| Black | ~15–20% |

Gaps persist across subjects and grades, visible at both statewide and school levels.

---

## Recommended Workflow

1. **Download assessment data** (Forward Exam CSVs from DPI)
2. **Merge with:**
   - Enrollment by race (DPI enrollment datasets)
   - School characteristics: urbanicity, FRPL %, etc.
3. **Build:**
   - Race-specific proficiency rates by school
   - Weighted gap measures
   - Segregation / exposure metrics (optional)

### Useful external merge dataset:
- [School District Enrollment Demographics, Wisconsin 2024 (ArcGIS)](https://www.arcgis.com/home/item.html?id=2c15aa7e7a0247b99f1573819734aeaa)

---

## Important Caveats

### 1. Suppression
- Small cells (<10 students) are suppressed at school level
- Affects race × school breakdowns at smaller schools — plan for this in analysis

### 2. Changing proficiency standards
- DPI changed cut scores recently
- Time trends are **not always directly comparable** across years
- Check DPI documentation for when standards changed

### 3. Test discontinuities
- Different tests for different grade bands (see table above)
- Forward Exam is the most consistent source for trend analysis

---

## Next Steps

- [ ] Download most recent Forward Exam data files from DPI
- [ ] Download enrollment by race data from DPI
- [ ] Explore WISEdash dashboard to understand variable structure
- [ ] Design merge key (school ID format)
- [ ] Decide on years of analysis (check for standard changes)
- [ ] Build school-level racial proficiency rate dataset
- [ ] Explore aggregation to county / district level
