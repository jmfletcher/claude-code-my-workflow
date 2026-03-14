# QC: ChatGPT Review Verification

**Date:** March 12, 2026  
**Scope:** `paper/generate_paper.py`, `scripts/python/analysis.py`, `output/tables/*.csv`

---

## Checklist

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 1 | Table 1 column labels | **Done** | `generate_paper.py` line 534: headers `["Geography", "Sex", "White LE", "Black LE", "B-W Gap"]`; rows use `r[2], r[3], r[4]`. CSV `table2_wide_2016.csv` has columns Geography, Sex, White, Black, B-W Gap, so White=r[2], Black=r[3]. Labels and data align. |
| 2 | Female gap sentence (4.3 vs 5.4) | **Not done** | Lines 562–564: text says "The gap ranges from [4.3] (rest of Wisconsin) to [6.1] (Milwaukee). Dane County shows the **smallest** female gap (5.4 years)." Rest of WI (4.3) is smaller than Dane (5.4), so the smallest gap is rest of WI, not Dane. Fix: say rest of Wisconsin has the smallest female gap (4.3); Dane (5.4) can be described as having the highest Black female LE (78.3) or as mid-range. |
| 3 | Roesch et al. (2023) citation | **Done** | Line 327–329: "Roesch et al. (2023) found ... with male gaps **on the order of 9 to 11 years**." No 3.4–8.8. |
| 4 | Abstract Dane counterfactual donor | **Done** | Abstract (lines 202–229) does not describe the Dane counterfactual exercise (replacing Dane White with Rest-of-WI White). It only notes Dane's large male gap and uncertainty. No incorrect "statewide" donor claim. |
| 5 | Trend language vs uncertainty | **Partial** | Hedging present: "point estimates suggest" (937), "warning signal" (994), and §4.3 qualifiers. But "genuine decline" appears at 966 and "genuine and alarming" at 1023 without in-sentence caveats. Recommend softening to e.g. "a decline that point estimates suggest" and "a decline that, if confirmed, is alarming" or similar. |
| 6 | Overlapping 3-year windows | **Not done** | §3.2 (lines 408–417) describes 3-year pooling and center years but does not state that windows **overlap** or that trend figures are **smoothed** and should not be interpreted as independent year-by-year estimates. Add one sentence to methods or §3.6. |
| 7 | Denominator / Hispanic origin | **Done** | §3.1 (388–392): "Hispanic origin is not separately identified (origin = 9 for all records)... denominators include Hispanic individuals." §5 Limitations (986–988): "population denominators do not separately identify Hispanic origin, which may introduce a small upward bias." |
| 8 | Composition effect vs mortality-replacement | **Done** | Abstract: decomposition (70%, 2.6-year composition term) stated first; then "Counterfactual exercises show that if Black Milwaukeeans had the same ... mortality as Black residents in the **rest of Wisconsin**..." Distinct concepts and wording. |
| 9 | 70% decomposition vs ~47% counterfactual | **Partial** | Text says Milwaukee "contributes 70 percent" and Table 4 shows ~3.8 yr reduction (~47%); "This is consistent with the decomposition finding" (846–847) links them but does not explain that 70% = **share of the gap** (decomposition) vs ~47% = **fractional reduction in the gap** under one counterfactual. Add one clarifying sentence near Table 3/4. |
| 10 | Population-share wording (60% vs two-thirds vs 67%) | **Partial** | Abstract: "roughly **60 percent**" (208). Elsewhere: "roughly **two-thirds**" (286, 306, 349, 755, 931, 950, 1166), Appendix C "about **two-thirds**" and table "67%". Recommend standardizing to one phrase (e.g. "about two-thirds (roughly 67%)") and one source (e.g. Appendix C table). |
| 11 | Appendix C sourcing | **Done** | Table C2 caption (1188–1190): "Source: compiled from publicly available demographic estimates **following Sant'Anna (2024) workflow guidance**." No "See project documentation" only. |
| 12 | Sample context table | **Done** | Table C1 (lines 1141–1152) from `table6_sample_context_2016.csv`: "Deaths (3yr)", "Person-years (3yr)", "Crude rate (per 1,000)" by Geography, Sex, Race. File exists in `output/tables/`. |
| 13 | Bootstrap CIs for key quantities | **Partial** | §3.5 describes bootstrap CIs; §3.6 says "figures and tables that report 95 percent intervals." Paper does not explicitly state that **decomposition contributions and counterfactual results are point estimates** and that CIs are reported for LE, gaps, and changes only. Add one sentence in §3.5 or §3.6. |
| 14 | Extra whitespace / page breaks | **Partial** | No `add_page()` immediately before §4 or §5. Unconditional `add_page()` at 796 and 830 (both before §4.5). Conditional at 573, 785. Appendices use add_page for section starts. Reviewer complained of "large gaps" (e.g. before 4.4, after Fig 4, before 5); current code has no add_page between 4.3 and 4.4 or right before §5. Two new pages before 4.5 (796, 830) may still create a noticeable gap. |

---

## Summary

- **Done:** 8 of 14 items  
- **Partial:** 5 of 14 items  
- **Not done:** 2 of 14 items  

---

## Recommendations for Not done / Partial

1. **Not done – Female gap (item 2):** Replace "Dane County shows the smallest female gap (5.4 years)" with wording that rest of Wisconsin has the smallest female gap (4.3 years) and that Dane has the highest Black female LE (78.3) or a mid-range gap (5.4), so the sentence is numerically consistent.
2. **Not done – Overlapping windows (item 6):** In §3.2 or §3.6, add a sentence that the 3-year windows overlap (e.g. 2010 uses 2009–2011, 2011 uses 2010–2012) and that trend figures should be interpreted as smoothed over time, not as independent year-by-year estimates.
3. **Partial – Trend language (item 5):** Soften "genuine decline" (966) and "genuine and alarming" (1023) with in-sentence caveats (e.g. "point estimates suggest a decline" / "if confirmed, alarming").
4. **Partial – 70% vs 47% (item 9):** Near Table 3 or 4, add one sentence clarifying that the 70% is the share of the statewide gap attributable to Milwaukee in the decomposition, while the ~47% is the fractional reduction in the gap under the counterfactual (different quantities).
5. **Partial – Population share (item 10):** Standardize to one formulation (e.g. "about two-thirds (67%)") and point to Appendix C for the precise number.
6. **Partial – CIs (item 13):** In §3.5 or §3.6, state explicitly that confidence intervals are reported for life expectancy, B-W gaps, and gap changes; decomposition and counterfactual results are point estimates without CIs.
7. **Partial – Whitespace (item 14):** If the two consecutive new pages before §4.5 (lines 796 and 830) create an unwanted gap, consider removing one (e.g. keep only the conditional break when needed) so §4.5 flows without an extra blank page.
