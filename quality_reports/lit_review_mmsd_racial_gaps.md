# Literature Review: Racial Achievement Gaps in Wisconsin and MMSD

**Date:** 2026-04-03
**Query:** Academic and policy literature on MMSD racial achievement gaps, Wisconsin statewide gaps, and school boundary redesign

---

## Summary

Wisconsin's Black-White proficiency gap is among the largest in the nation and has remained stubbornly persistent over two decades. On the 2024 NAEP, Wisconsin posted the largest fourth-grade reading gap between Black and White students nationwide — exceeding Mississippi, Louisiana, and South Carolina. On the Forward Exam, the statewide Black-White proficiency gap runs approximately 43 percentage points. MMSD's internal gap is even larger because its White student population is a high-SES outlier: MMSD White students average 54-67% proficiency in ELA while MMSD Black students average only 8-10%, a gap of 45-55 pp that exceeds the statewide average gap substantially. This pattern — a district with a large, visible within-district gap driven largely by a high-SES White population rather than low-performing minority students — is underexplored in the academic literature.

The academic literature on racial achievement gaps and school segregation, led most prominently by Sean Reardon and colleagues at the Stanford Education Data Archive (SEDA), establishes that geographic variation in gaps is strongly explained by income differences between racial groups, residential segregation, and differential school poverty. Wisconsin's position at the top of the national gap rankings is likely explained by a combination of extreme residential segregation in Milwaukee, the outlier-SES composition of White students in college-town districts like Madison, and Black poverty rates that are among the highest in any state. A separate policy literature addresses whether boundary redrawing can reduce segregation: research shows that redrawing attendance zones within districts achieves at most 5-14% reductions in segregation, while redrawing district boundaries themselves could reduce 40%+ of segregation — a distinction critical for interpreting the MMSD boundary review.

The literature does not contain a rigorous peer-to-peer comparison of MMSD minority students against same-race peers in Milwaukee, Green Bay, or Kenosha — nor a systematic decomposition of the MMSD gap into within-school vs. between-school components. Our analysis fills these gaps directly.

---

## Key Papers and Reports

### Reardon, Kalogrides & Shores (2019) — The Geography of Racial/Ethnic Test Score Gaps
- **Main contribution:** Estimates Black-White and Hispanic-White achievement gaps for hundreds of metro areas and thousands of school districts using ~200 million standardized tests (2009-2013); identifies correlates of geographic variation.
- **Method:** State accountability tests scaled to NAEP via equipercentile linking (SEDA); multilevel regression of gap magnitude on district and metro-area characteristics.
- **Key finding:** Achievement gaps range from near zero to >1.5 SD across districts. Economic, demographic, segregation, and schooling factors explain 43-72% of variation. The strongest correlates are racial differences in parental income, parental education, and racial school segregation.
- **Relevance:** Foundational framework for our decomposition analysis. Establishes that MMSD's large gap is most likely driven by the extreme SES difference between its White and Black populations rather than unusually poor outcomes for minority students. Directly motivates our comparison of MMSD minority students to non-MMSD Wisconsin White students.
- **Citation (verified):** Reardon, S.F., Kalogrides, D., & Shores, K. (2019). The geography of racial/ethnic test score gaps. *American Journal of Sociology*, 124(4), 1164-1221. DOI: 10.1086/700678. CEPA working paper wp16-10.

### Matheny, Thompson, Townley-Flores & Reardon (2023) — Uneven Progress: Recent Trends in Achievement Disparities 2009-2019
- **Main contribution:** Documents that Black-White and poor-nonpoor achievement gaps grew between 2009 and 2019 using SEDA data. White-Hispanic gaps shrank. No correlation between overall achievement gains and gap reduction.
- **Method:** SEDA district-level panel 2009-2019; regression of gap trends on within-district segregation, teacher certification, and school characteristics.
- **Key finding:** Within-district racial and socioeconomic segregation levels and trends are the strongest predictors of achievement disparity trends. Districts that increased racial segregation over this period showed widening gaps.
- **Relevance:** Provides the national baseline for interpreting MMSD's stable gaps across our Forward Exam window (2015-2023). The stability of MMSD's BW gap is the norm nationally, not an exception.
- **Citation (verified):** Matheny, K.T., Thompson, M.E., Townley-Flores, C., & Reardon, S.F. (2023). Uneven progress: Recent trends in academic performance among U.S. school districts. *American Educational Research Journal*, 60(3). DOI: 10.3102/00028312221134769.

### Reardon, Weathers, Fahle, Jang & Kalogrides (2024) — Is Separate Still Unequal? School Segregation and Achievement Gaps
- **Main contribution:** 11 years of data from all U.S. public school districts; establishes that current-day school segregation strongly predicts gap magnitude in 3rd grade and gap growth from 3rd to 8th grade. The mechanism is school poverty concentration — racial segregation matters because it concentrates minority students in high-poverty schools. Teacher quality differences explain ~20% of the effect.
- **Method:** Panel regression using SEDA and CCD; instrumental variable approach for causal identification.
- **Key finding:** Racial segregation per se does not independently predict gaps after controlling for school poverty exposure. This suggests poverty concentration, not racial mixing per se, is the proximate mechanism.
- **Relevance:** Critical caution for MMSD boundary debate: rezoning that moves minority students to schools with lower poverty but leaves underlying SES drivers unchanged will produce limited gains. Also implies that comparing MMSD Black students to Milwaukee Black students (who face more concentrated school poverty) requires poverty controls to isolate school effects.
- **Citation (verified):** Reardon, S.F., Weathers, E.S., Fahle, E.M., Jang, H., & Kalogrides, D. (2024). Is separate still unequal? New evidence on school segregation and racial academic achievement gaps. *American Sociological Review*, 89(6), 971-1010. Originally CEPA Working Paper No. 19-06 (2019).

### Fahle, Reardon, Shear, Ho, Saliba & Kalogrides (2023) — Stanford Education Data Archive (SEDA) Technical Documentation
- **Main contribution:** Documents construction of SEDA2022 — the primary national dataset linking state test scores to NAEP for cross-district and cross-state achievement comparisons. Methods applicable for placing Wisconsin and MMSD gaps in national context.
- **Key details:** District-level math and reading achievement, grades 3-8, 2019 and 2022; created for COVID-era comparison in partnership with Harvard CEPR.
- **Relevance:** If we want to formally place MMSD's BW gap in the national distribution (rather than just comparing to Wisconsin districts), SEDA is the tool. Edopportunity.org provides public access.
- **Citation (verified):** Fahle, E.M., Reardon, S.F., Shear, B.R., Ho, A.D., Saliba, J., & Kalogrides, D. (2023). Stanford Education Data Archive Technical Documentation (SEDA2022, Version 2.0). Educational Opportunity Project at Stanford University. DOI: purl.stanford.edu/db586ns4974.

### Gillani, N., Beeferman, D., Vega-Pourheydarian, C., Overney, C., Van Hentenryck, P., and Roy, D. (2023) — Redrawing Attendance Boundaries to Promote Racial and Ethnic Diversity
- **Main contribution:** Uses combinatorial optimization algorithms to simulate redrawn attendance zones for 98 US elementary districts. Shows meaningful but limited segregation reduction potential.
- **Method:** Algorithmic boundary optimization minimizing White/non-White segregation while constraining travel time and school size changes. Applied to districts serving 3+ million students.
- **Key finding:** Median 14% relative decrease in White/non-White segregation achievable while requiring ~20% of students to switch schools and slightly reducing travel times.
- **Relevance:** Directly applicable to MMSD's "Building for the Future" boundary review. The 14% estimate is an upper bound under optimal algorithmic conditions — real-world constraints (community preferences, feeder patterns, programming) will reduce this. Our school-level decomposition (only 18% of MMSD's BW gap is between schools) implies that even optimal rezoning could close at most ~14% × 18% ≈ 2.5 pp of the ~47 pp within-MMSD BW gap.
- **Citation status:** Published. *Educational Researcher*, 2023. DOI: 10.3102/0013189X231170858. Also available as arXiv:2303.07603.

### Sorensen, L.C., Holt, S.B., and Engberg, J. (2024) — School Desegregation by Redrawing District Boundaries
- **Main contribution:** Shows that redrawing school *district* boundaries (not just attendance zones) could reduce 40%+ of segregation in median areas, versus <5% from attendance zone redrawing within districts.
- **Method:** Computational simulation of alternative district boundaries for US counties using redistricting algorithms.
- **Key finding:** Two-thirds of US school segregation occurs between districts rather than within districts. District-level boundary changes are far more powerful than within-district attendance zone changes.
- **Relevance:** Our district-level decomposition found that ~47% of Wisconsin's BW gap is between districts. This aligns with the national finding. However, MMSD is a single district — district boundary changes are legally and politically much more complex. The more actionable lever for MMSD is within-district attendance zones, which address only the 18% between-school component.
- **Citation status:** Published. *Scientific Reports*, 2024. PMC11436629. Available at nature.com/articles/s41598-024-71578-x.

### Richards, M.P. (2014) — The Gerrymandering of School Attendance Zones and Segregation
- **Main contribution:** Analyzed 15,290 attendance zones across 663 US districts. Found that irregularly shaped zones generally exacerbate racial segregation — the shaping of zones reflects and reinforces residential sorting.
- **Method:** Geospatial analysis of attendance zone shapes and racial composition using School Attendance Boundary Survey (SABS) data.
- **Key finding:** Zone gerrymandering increases segregation on average, though in districts under desegregation orders, irregular zones more often promote integration.
- **Relevance:** Background context for MMSD boundary review. Suggests that the current MMSD zone shapes may be contributing to, not offsetting, within-district segregation. Verifying this with MMSD-specific geospatial data would be a useful extension.
- **Citation status:** Published. *American Educational Research Journal*, 2014. DOI: 10.3102/0002831214553652.

### Wisconsin Institute for Law & Liberty — WILL (2026) — Beyond Race: What Really Drives Wisconsin's Achievement Gap
- **Main contribution:** Policy report attributing ~42% of the relationship between Black student share and proficiency to school poverty rates; 3.6% to disability identification. Argues family structure and early literacy explain remaining gap.
- **Method:** Cross-school regression of Forward Exam proficiency on racial composition, FRPL rate, disability rate, and demographic controls.
- **Key finding:** Controlling for poverty substantially reduces (but does not eliminate) the Black-White proficiency gap. Family structure (married household rate) and early literacy practices cited as unmeasured mediators.
- **Relevance:** Provides a conservative benchmark for what poverty can explain. Important to note that this is a policy advocacy report (WILL is a conservative law and policy organization) and the causal interpretation of poverty mediation is contested. The analysis does not address why Black students in Wisconsin face higher poverty rates, nor the role of residential segregation in generating that poverty concentration.
- **Limitations to flag:** Cross-sectional, school-level regression; cannot separate compositional effects from causal school effects. Family structure variables are ecological (county-level) rather than individual. Ideological framing ("failed race-based policies") does not affect the core empirical finding, but the interpretation requires caution.
- **Citation status:** Report, March 2026. URL: will-law.org/wp-content/uploads/2026/03/RaceAchievementStudy-web.pdf

### City Forward Collective (2026) — North Side Schools Failing Black Students
- **Main contribution:** Policy report documenting that 22 of Wisconsin's 50 lowest-performing schools are on Milwaukee's North Side; ~57% of Wisconsin's Black students attend Milwaukee schools, mostly North Side.
- **Key finding:** ~30,000 Black students enrolled in 1- or 2-star rated schools; North Side MPS enrollment has fallen by 4,500 students 2019-25, concentrating resources in half-empty buildings.
- **Relevance:** Essential context for peer comparison analysis. MMSD Black students (~1,900 tested per year) are a small fraction of Wisconsin's Black student population compared to Milwaukee (~30,000). Our finding that MMSD Black ELA proficiency (~8-10%) is *lower* than Milwaukee Black proficiency (~16-22%) — despite MMSD's higher overall district reputation — is a key substantive result. The City Forward report helps explain the Milwaukee reference point.
- **Citation status:** Report, February/March 2026. Urban Milwaukee coverage: urbanmilwaukee.com/2026/03/01.

### MMSD "Building for the Future" — Boundary and Attendance Area Review (2025-2027)
- **Main contribution:** MMSD's official two-year boundary review process, conducted with third-party vendor MGT. Guiding principles include "socio-economic, linguistic, and racial diversity within and across schools."
- **Key finding:** This is the policy motivation for our entire project. The review is actively underway; MMSD has not yet released preliminary boundary scenarios as of April 2026.
- **Relevance:** Our school-level decomposition (82% of MMSD BW gap is within schools, 18% between schools) is a direct input to evaluating the potential impact of boundary changes. The district should be made aware that even full integration across MMSD's 51 elementary schools would affect only the 18% between-school component.
- **Citation status:** Official MMSD document. Available at mmsd.org/about/building-for-the-future-boundary-review.

### MMSD Annual Report (2022-2023)
- **Key metrics:** Overall 4-year graduation rate 88%; Forward ELA Grade 3 proficiency 34% (down 5.09% from prior year); teachers of color 15%.
- **Context:** MMSD "Meets Expectations" in state report cards overall despite severe racial gaps. This is explained by the high performance of White students inflating the overall metric.
- **Relevance:** Confirms our data finding that MMSD's aggregate performance masks extreme dispersion by race.
- **Citation status:** Official district document. Available at accountability.madison.k12.wi.us.

### Wisconsin DPI — WISEdash Achievement Gap Dashboard
- **Main contribution:** Official state data portal tracking proficiency gaps by race, district, and year.
- **Relevance:** Data source that corroborates our panel construction. Useful for verifying our computed gaps against the official DPI gap dashboard.
- **Citation status:** Web resource. dpi.wi.gov/wisedash/districts/about-data/achievement-gap.

---

## Thematic Organization

### Theoretical Contributions

The dominant theoretical framework comes from the Reardon school: racial achievement gaps are fundamentally explained by socioeconomic differences between racial groups (parental income, education) that are amplified by residential and school segregation. Segregation concentrates minority students in high-poverty schools, which compounds disadvantage. This framework predicts that gaps will be largest in places with (a) the largest Black-White income gap and (b) the highest residential segregation — both of which describe Wisconsin, particularly Milwaukee.

A competing framework (more prominent in policy circles, as in the WILL report) attributes gaps to family structure and early childhood factors, treating poverty as a mediator rather than a root cause. This view is methodologically conservative in that it acknowledges economic disadvantage but disputes systemic/structural explanations. For our analysis, the key empirical implication is the same: poverty concentration is the strongest measurable predictor of gaps.

Neither framework has been applied specifically to decompose the MMSD gap into its within-school and between-school components, or to compare MMSD minority students against same-race peers in peer districts.

### Empirical Findings

**National landscape:** BW achievement gaps average approximately 0.7-0.9 SD nationally (Reardon 2019). Wisconsin's gap ranks at or near the top nationally on NAEP (2024: largest fourth-grade reading gap). On the Forward Exam, Wisconsin's 2024-25 BW gap is 43 pp in overall proficiency. Our analysis found statewide Forward Exam BW gaps of 37-40 pp in ELA, 42-44 pp in Math for primary years (2015-2023) — consistent with DPI-reported figures.

**Within vs. between:** Our decomposition found that approximately 47% of Wisconsin's district-level BW gap is between districts and 53% within districts. This is somewhat lower than the national finding (~67% between districts) from Sorensen et al. (2024), likely because Wisconsin's within-district gaps at MMSD and other large districts are unusually large. Within MMSD specifically, the BW gap is ~82% within schools and only 18% between schools.

**Trend stability:** Wisconsin's gaps have shown no meaningful trend toward closure across our Forward Exam window (2015-2023), consistent with Reardon et al.'s (2022) national finding that gaps grew slightly between 2009-2019.

**MMSD vs. Milwaukee:** Our data show MMSD Black ELA proficiency (~8-10%) is lower than Milwaukee Black proficiency (~16-22%), counter to the intuition that MMSD's higher overall ratings reflect better outcomes for minority students. This is likely explained by (a) Milwaukee's larger Black population making the district proficiency estimates more stable, (b) differential poverty composition within the Black student populations, and/or (c) selection effects in which MMSD Black families are higher-income on average but still far below MMSD White families. This finding deserves further investigation.

### Methodological Innovations

- **SEDA linked scales:** Reardon and colleagues' method of linking state test scores to NAEP via equipercentile linking allows cross-state and cross-year gap comparison. Applicable if we want to benchmark MMSD against national distributions rather than just Wisconsin.
- **Within-between decomposition:** Our implementation follows the standard Oaxaca-style linear decomposition. An alternative approach (used by Reardon for segregation indices) would decompose exposure indices rather than mean proficiency — this would be more appropriate if we want to connect our gap decomposition to standard segregation indices (dissimilarity, exposure) in future work.
- **Algorithmic boundary optimization:** Gillani et al.'s approach (combinatorial optimization with travel-time constraints) is directly applicable to MMSD's boundary review and could be run on MMSD's school attendance data as a future extension.

---

## Gaps and Opportunities

1. **No peer comparison for MMSD minority students exists in the literature.** No published study compares MMSD Black or Hispanic student proficiency against same-race peers in Milwaukee, Green Bay, or other Wisconsin districts. Our RQ3 analysis fills this gap directly. The finding that MMSD Black proficiency is *lower* than Milwaukee Black proficiency (despite MMSD's higher reputation) is a novel and policy-relevant result.

2. **The MMSD "outlier SES White" problem is unaddressed.** The literature recognizes that Madison-area White households are high-SES, but no study has explicitly decomposed what share of the apparent MMSD racial gap is attributable to the SES outlier status of MMSD White students vs. unusually poor outcomes for minority students. Our RQ3 comparison of MMSD minority against non-MMSD Wisconsin White students begins to address this.

3. **No longitudinal analysis connects WKCE (pre-2015) to Forward Exam trends for MMSD.** The WKCE SSS data (2003-2013) allow reconstruction of scale score gaps at the district level for this historical period. Connecting this to the Forward Exam era (with appropriate caveats about cross-era comparability) would provide a 20-year perspective on whether MMSD's racial gap has changed since desegregation-era programs wound down.

4. **The school-level decomposition has no published precedent for MMSD.** Our finding that 82% of MMSD's BW gap is within schools (not between schools) has direct implications for boundary redrawing policy, but this figure has not been published. It is the most actionable single statistic for MMSD policymakers considering the 2025-27 boundary review.

5. **Poverty mediation is underexplored at the MMSD level.** The WILL report documents poverty's role statewide but not within MMSD specifically. MMSD's FRPL data by school and race would allow a more targeted mediation analysis: how much of the within-MMSD BW gap is explained by FRPL-rate differences, and how much persists within similar-poverty schools?

---

## Suggested Next Steps

- **Obtain MMSD FRPL-by-race data** to run a poverty mediation analysis within MMSD schools. DPI enrollment downloads include FRPL breakdowns.
- **Incorporate SEDA data** (edopportunity.org) to place MMSD's BW gap in national distribution — useful for the report's framing section.
- **Review the MGT boundary review process** at mmsd.org/about/building-for-the-future-boundary-review for any preliminary scenarios or data released since April 2026.
- **Read Gillani et al. (2023) in full** to extract their specific findings for districts similar in size and composition to MMSD, as this directly calibrates what MMSD's boundary review can realistically achieve.
- **Examine the City Forward Collective (2026) report** in full for their school-level data on North Side Milwaukee — useful for contextualizing the Milwaukee comparison in our peer analysis.
- **Search for any UW-Madison or Wisconsin Policy Forum analyses** of MMSD racial gaps, as local institutions often have district-level analyses that do not appear in national academic searches.

---

## BibTeX Entries

```bibtex
@article{reardon2019geography,
  title     = {The Geography of Racial/Ethnic Test Score Gaps},
  author    = {Reardon, Sean F. and Kalogrides, Demetra and Shores, Kenneth},
  journal   = {American Journal of Sociology},
  volume    = {124},
  number    = {4},
  pages     = {1164--1221},
  year      = {2019},
  doi       = {10.1086/700678},
  note      = {CEPA working paper wp16-10}
}

@article{matheny2023uneven,
  title     = {Uneven Progress: Recent Trends in Academic Performance Among {U.S.} School Districts},
  author    = {Matheny, Kaylee T. and Thompson, Marissa E. and Townley-Flores, Carrie and Reardon, Sean F.},
  journal   = {American Educational Research Journal},
  volume    = {60},
  number    = {3},
  year      = {2023},
  doi       = {10.3102/00028312221134769}
}

@article{reardon2024separate,
  title     = {Is Separate Still Unequal? {New} Evidence on School Segregation and Racial Academic Achievement Gaps},
  author    = {Reardon, Sean F. and Weathers, Ericka S. and Fahle, Erin M. and Jang, Heewon and Kalogrides, Demetra},
  journal   = {American Sociological Review},
  volume    = {89},
  number    = {6},
  pages     = {971--1010},
  year      = {2024},
  note      = {Originally CEPA Working Paper No.\ 19-06, 2019}
}

@techreport{fahle2023seda,
  title     = {Stanford Education Data Archive Technical Documentation ({SEDA2022}, Version 2.0)},
  author    = {Fahle, Erin M. and Reardon, Sean F. and Shear, Benjamin R. and Ho, Andrew D. and Saliba, Jim and Kalogrides, Demetra},
  institution = {Educational Opportunity Project at Stanford University},
  year      = {2023},
  url       = {https://purl.stanford.edu/db586ns4974}
}

@article{gillani2023redrawing,
  title     = {Redrawing Attendance Boundaries to Promote Racial and Ethnic Diversity in Elementary Schools},
  author    = {Gillani, Nabeel and Beeferman, Doug and Vega-Pourheydarian, Cesar and Overney, Cassandra and Van Hentenryck, Pascal and Roy, Deb},
  journal   = {Educational Researcher},
  year      = {2023},
  doi       = {10.3102/0013189X231170858},
  note      = {Also arXiv:2303.07603}
}

@article{sorensen2024desegregation,
  title     = {School desegregation by redrawing district boundaries},
  author    = {Sorensen, Lucy C. and Holt, Stephen B. and Engberg, John},
  journal   = {Scientific Reports},
  year      = {2024},
  doi       = {10.1038/s41598-024-71578-x},
  pmcid     = {PMC11436629}
}

@article{richards2014gerrymandering,
  title     = {The Gerrymandering of School Attendance Zones and the Segregation of Public Schools: {A} Geospatial Analysis},
  author    = {Richards, Meredith P.},
  journal   = {American Educational Research Journal},
  year      = {2014},
  doi       = {10.3102/0002831214553652}
}

@report{will2026beyondrace,
  title     = {Beyond Race: What Really Drives {Wisconsin}'s Achievement Gap},
  author    = {{Wisconsin Institute for Law \& Liberty}},
  year      = {2026},
  url       = {https://will-law.org/wp-content/uploads/2026/03/RaceAchievementStudy-web.pdf},
  note      = {Policy advocacy report; interpret with methodological caution}
}

@report{cityforward2026northside,
  title     = {North Side Schools Failing Black Students},
  author    = {{City Forward Collective}},
  year      = {2026},
  url       = {https://milwaukeenns.org/2026/02/26/new-report-finds-that-north-side-schools-are-failing-black-students/}
}

@misc{mmsd2025boundary,
  title     = {Building for the Future: Boundary and Attendance Area Review 2025--2027},
  author    = {{Madison Metropolitan School District}},
  year      = {2025},
  url       = {https://mmsd.org/about/building-for-the-future-boundary-review}
}

@misc{mmsd2023annual,
  title     = {{MMSD} 2022--2023 Annual Report},
  author    = {{Madison Metropolitan School District}},
  year      = {2023},
  url       = {https://accountability.madison.k12.wi.us/about/mmsd-excellence-together/strategic-framework/2023-2024-annual-report}
}

@misc{dpi_wisedash_gap,
  title     = {{WISEdash} for Districts Achievement Gap Dashboard},
  author    = {{Wisconsin Department of Public Instruction}},
  url       = {https://dpi.wi.gov/wisedash/districts/about-data/achievement-gap}
}
```

---

## Citation Status Notes

- **Reardon et al. citations:** All verified against CEPA publications page and journal DOIs (April 2026). Note that "Is Separate Still Unequal?" circulated as CEPA WP 19-06 for several years before its 2024 ASR publication — use the journal citation (Reardon et al. 2024) in the manuscript.
- **WILL report (2026):** Policy advocacy report, not peer-reviewed. Use for descriptive context only; flag that its causal claims (family structure as driver) are not established by the cross-sectional design.
- **City Forward Collective (2026):** Policy report; useful for North Side Milwaukee enrollment and performance context. Methodology not specified in detail.
- **MMSD boundary review:** Ongoing through 2027; check mmsd.org for preliminary boundary scenarios as they are released.
