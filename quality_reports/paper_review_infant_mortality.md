# Manuscript Review: Infant Mortality in Wisconsin: Evidence, Equity, and Policy

**Date:** 2026-03-14  
**Reviewer:** review-paper skill  
**File:** Quarto/report.qmd  
**Type:** Policy report (descriptive, not causal inference)

---

## Summary Assessment

**Overall recommendation:** **Accept** (with minor revisions)

This is a well-executed policy report that clearly describes infant mortality disparities in Wisconsin, synthesizes evidence on interventions, and links the Birth Equity Act to the literature. The report is appropriately scoped as descriptive and evaluative rather than causal; it does not overclaim. The Poisson-based confidence intervals and detectability logic are sound. The argument—that Milwaukee is the best-powered county-level setting for evaluating interventions—is well supported by the data and tables. Strengths include transparent acknowledgment of evidence gaps for individual bills, honest treatment of suppression/imputation in WISH data, and a clear executive summary. Minor concerns center on missing citations for some cited studies (CHAMPION, Back to Sleep, DCP3) and a few presentation refinements.

---

## Strengths

1. **Clear research question and policy relevance.** The report states its aims upfront: describe rates by race and place, assess plausibility of detecting intervention effects, survey interventions, and link evidence to the Birth Equity Act. The executive summary is concise and actionable.

2. **Appropriate scope.** The report explicitly avoids causal claims. It describes disparities, summarizes intervention effect sizes from the literature, and argues for Milwaukee as the best setting for *evaluation*—not that interventions will work, but that effects could be detected there. This is appropriate for a policy report.

3. **Sound Poisson CIs and detectability logic.** The Wald-style Poisson CI for rates, $\text{rate} \pm 1.96 \times (1000\sqrt{D})/B$, is standard for count data. The minimum detectable effect logic (count must fall below lower CI bound: $D - 1.96\sqrt{D}$) is correctly implemented. The 17% and 32% benchmarks from Denmark and KMC are clearly sourced and used consistently.

4. **Honest evidence-to-policy linkage.** Section 3 ("Link to evidence in this report") explicitly grades each bill as *supported directly*, *supported indirectly*, *supported by analogy*, or *limited direct evidence*. AB 1088 (postpartum home visit) is correctly identified as most closely aligned with NFP/Denmark evidence; AB 1082–1087 receive appropriately hedged support.

5. **Transparent data limitations.** Suppression ("X" for small counts), imputation (Total − White when Black suppressed), and Rest of Wisconsin definition are all stated. The report recommends cause-specific analysis as future work.

6. **Publication-ready figures.** Figures use consistent 95% CI notation, 300 DPI, and a coherent palette (blue/red for White/Black).

---

## Major Concerns

### MC1: Missing citations for key studies

- **Dimension:** Literature  
- **Issue:** Several studies are discussed but not cited: CHAMPION (India), Back to Sleep / Safe to Sleep (U.S.), DCP3/LiST, WHO Safe Childbirth Checklist (Rajasthan), Guinea-Bissau BCG/OPV trial. A referee would expect formal citations for these.
- **Suggestion:** Add bibliography entries and in-text citations for CHAMPION, Back to Sleep (e.g., CDC or Moon et al.), DCP3_rmnch (already in bib but not cited), and the Rajasthan/Guinea-Bissau studies if available.
- **Location:** Literature Review (lines 41–49), Table @tbl-effects, AB 1082 discussion

### MC2: Table 2 detectability criterion could be clearer

- **Dimension:** Presentation  
- **Issue:** The "17% det." and "32% det." columns indicate whether the *rate reduction* exceeds the *margin* (rate minus lower CI bound). This is a one-sided detectability criterion: a reduction is "detectable" if the post-intervention rate would fall below the lower CI bound. The logic is correct but the table caption does not fully explain it.
- **Suggestion:** Add one sentence to the caption: "Det. = Yes if the absolute rate reduction exceeds the margin (i.e., the post-intervention rate would fall below the lower CI bound)."
- **Location:** Table 2 caption (line 99)

---

## Minor Concerns

### mc1: DCP3 in bibliography but not cited

- **Issue:** `DCP3_rmnch` exists in Bibliography_base.bib but is never cited in the report. The text mentions "DCP3 LiST" and "DCP3/LiST" in the literature review and AB 1082.
- **Suggestion:** Add `[@DCP3_rmnch]` where DCP3 is discussed.

### mc2: "African American" vs "Black" inconsistency

- **Issue:** Line 45 uses "African American infants" in the Back to Sleep discussion; elsewhere the report uses "Black" (Non-Hispanic Black). For consistency with WISH categories, "Black" is preferred.
- **Suggestion:** Change "African American infants" to "Black infants" for consistency.

### mc3: Table 3 "Min. averted" interpretation

- **Issue:** The caption explains "NFP spend" but not "Min. averted." A reader might not immediately grasp that this is the minimum deaths averted needed for the count to fall below the lower CI bound.
- **Suggestion:** Add "Min. averted = minimum deaths averted for one-year count to fall below lower CI bound" to the table note.

### mc4: Executive summary length

- **Issue:** The executive summary is two substantial paragraphs. Some policy audiences prefer a shorter, bulleted summary.
- **Suggestion:** Consider adding 3–4 bullet points for key takeaways; current prose is fine for academic readers.

---

## Referee Objections

These are the tough questions a top referee would likely raise:

### RO1: Why use 17% and 32% as benchmarks when the Birth Equity Act bills are not direct replications of NFP or KMC?

**Why it matters:** The detectability analysis assumes interventions could achieve 17–32% reductions. The Birth Equity Act includes doula coverage (AB 1085), dental coverage (AB 1084), and postpartum home visits (AB 1088). Only AB 1088 is closely analogous to NFP/Denmark. A referee could argue the benchmarks are optimistic for the actual package.

**How to address it:** The report already notes that AB 1088 is "most closely aligned" and that other bills have "indirect" or "limited" support. A short paragraph could explicitly state: "The 17% and 32% benchmarks are illustrative upper bounds from the strongest evidence; actual effects of the Birth Equity Act package may be smaller. Milwaukee remains the best-powered setting regardless of the true effect size."

### RO2: Is the Poisson assumption appropriate when deaths are not independent (e.g., clustering by hospital or neighborhood)?

**Why it matters:** Poisson CIs assume deaths are independent. If deaths cluster (e.g., bad years in certain hospitals), the true variance could exceed the Poisson variance, and CIs could be too narrow.

**How to address it:** Acknowledge in the methods: "The Poisson assumption treats deaths as independent; clustering could widen CIs. These intervals should be interpreted as approximate." For a descriptive report, this is a minor caveat rather than a fatal flaw.

### RO3: Why focus only on Black and White? Hispanic and other racial groups experience disparities too.

**Why it matters:** A referee might argue the report overlooks other populations. Wisconsin has smaller Hispanic and Asian populations, but they are not zero.

**How to address it:** Add one sentence: "This report focuses on Non-Hispanic Black and Non-Hispanic White infants because they have the largest sample sizes in WISH and the sharpest disparities; analysis of other racial groups would require additional data and is left for future work."

### RO4: The $48M/year NFP spend for Milwaukee Black seems large. Is that a realistic policy ask?

**Why it matters:** Policymakers may balk at the cost. The report could be seen as setting an unrealistic bar.

**How to address it:** Clarify that $48M is the spend required to avert the *minimum detectable* number of deaths (15) at NFP's cost-per-life. It is a benchmark for scale, not a recommendation to spend exactly that amount. Smaller programs may still be worthwhile even if effects are not detectable in one year; the report already notes "longer follow-up, pooled years, or cause-specific outcomes" as alternatives.

### RO5: What about selection into Milwaukee? If Black families move, would evaluation be biased?

**Why it matters:** If interventions attract or displace families, the composition of Milwaukee's Black population could change, complicating before-after comparisons.

**How to address it:** For a one-year descriptive evaluation, this is less critical. If the report is used to justify a future RCT or quasi-experiment, add: "Future impact evaluations should consider migration and selection; a randomized design would mitigate these concerns."

---

## Specific Comments

| Section | Comment |
|--------|---------|
| Executive Summary | Strong. "Policymakers should be careful when proposing interventions... that are very difficult to evaluate" is a valuable normative point. |
| Introduction | Clear four-part roadmap. The 2023 single-year rates (14.3 vs 4.4) could add "(WISH)" to clarify source. |
| Literature Review | Outcome alignment paragraph (KMC vs neonatal, safe sleep vs SIDS) is excellent—prevents over-interpretation. |
| Table 1 | "Births/yr" and "Deaths/yr" are 5-year averages; the "yr" could be misinterpreted as single-year. Consider "Avg. births/yr" and "Avg. deaths/yr." |
| Table 2 | Margin = rate − lower CI; the 17% and 32% columns are absolute rate reductions. Logic is correct; caption could be expanded (see MC2). |
| Table 3 | "Min. averted" = ceil(1.96√D). For Milwaukee Black (D=55), 1.96√55 ≈ 14.5 → 15. Correct. |
| Figures | All four figures have consistent "(95% CI, Poisson-based)" in captions. Good. |
| Policy section | Bill-by-bill evidence grading is exemplary. AB 1085 (doula) correctly notes "direct mortality evidence is limited." |
| Conclusion | Appropriately hedged. "Cause-specific analysis... is recommended as a direction for future work" is good. |
| Acknowledgments | Claude/Cursor disclosure is appropriate and transparent. |

---

## Summary Statistics

| Dimension | Rating (1–5) | Notes |
|-----------|--------------|-------|
| Argument Structure | 5 | Clear question, logical flow, conclusions supported. |
| Identification | N/A | Descriptive report; no causal claims. Appropriately scoped. |
| Econometrics | 5 | Poisson CIs appropriate; detectability logic sound. |
| Literature | 4 | Key papers cited; some (CHAMPION, Back to Sleep, DCP3) missing citations. |
| Writing | 5 | Clear, professional, consistent notation. |
| Presentation | 4 | Tables and figures well-designed; minor caption/consistency improvements. |
| **Overall** | **4.5** | **Accept.** Strong policy report with minor revisions. |

---

## Recommendation Summary

**Accept** (with minor revisions). The report achieves its aims: it describes disparities, synthesizes intervention evidence, explains why Milwaukee is the best setting for evaluation, and links the Birth Equity Act to the literature with appropriate caveats. Address MC1 (missing citations) and MC2 (Table 2 caption) for a stronger final version. The referee objections above are addressable with short clarifications; none are fatal.
