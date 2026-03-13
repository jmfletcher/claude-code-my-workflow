# Manuscript Review: Free Prescription Drugs and Mortality: Evidence from Poland

**Date:** 2026-03-11
**Reviewer:** review-paper skill
**File:** Paper/main.md

## Summary Assessment

**Overall recommendation:** Revise & Resubmit (Major Revision)

This paper asks an important and timely question — whether Poland's age-targeted free prescription drug program (Drugs 75+) reduced elderly mortality — and assembles three complementary empirical strategies using high-quality HMD data. The topic is policy-relevant, the data are well-suited for the question, and the multi-strategy approach is commendable. The paper is clearly written and the institutional background section is informative.

However, the paper has several significant issues that must be addressed before it is ready for submission. The most serious concern is a **misinterpretation of the main coefficient** — the regressions are estimated on log mortality, but the text interprets the coefficient as a level change (deaths per 1,000). This changes the entire framing of the results. Beyond this, the **identification strategy for the within-Poland DiD is under-developed**: comparing mortality trends across wide age ranges (65–84) raises serious concerns about differential aging-related trends that have nothing to do with drug policy. The **literature review is extremely thin** (4 references), several **citations contain factual errors**, and the paper lacks an abstract, a theoretical framework, and formal tables/figures embedded in the text. The cross-country and synthetic control results are largely null, and the paper needs a more honest reckoning with the tension between the strong within-Poland result and the weak external evidence.

## Strengths

1. **Important, policy-relevant question.** The mortality effects of age-targeted drug subsidies are under-studied, and Poland's program offers a clean natural experiment with sharp age thresholds.

2. **Multi-strategy approach.** Using within-country DiD, cross-country DiD, and synthetic control provides triangulation. The honest reporting of null results from the latter two strategies builds credibility.

3. **Good institutional background.** The description of the Drugs 75+ program, drawing on Majewska & Zaremba (2025), is detailed and useful.

4. **Transparent, reproducible pipeline.** The numbered Python scripts make the analysis fully reproducible.

5. **Sensible robustness checks.** Bandwidth variation, COVID exclusion, and multiple comparator sets are all appropriate.

## Major Concerns

### MC1: Misinterpretation of Log Mortality Coefficients

- **Dimension:** Econometrics / Argument
- **Issue:** The dependent variable in all within-Poland regressions is **log mortality** (`log_mx = np.log(mx_total)` in `02_within_poland_did.py`). The paper states: "The basic DiD coefficient for total mortality is −0.079 (SE 0.009), meaning that mortality in the treated age group (75+) fell by about **7.9 deaths per 1,000 person-years** relative to the control group." This is incorrect. A coefficient of −0.079 on log mortality means approximately a **7.9 percent decrease** in the mortality rate, not 7.9 deaths per 1,000. Given that baseline mortality for the 75–84 age group is roughly 50–83 per 1,000, a 7.9% reduction would correspond to roughly 4–6.5 fewer deaths per 1,000 — still meaningful, but the paper's claim of "about 8 fewer deaths per 1,000" in the Discussion section is wrong.
- **Suggestion:** Correct all text that interprets the DiD coefficient. Clearly state the dependent variable is log(mortality rate). Report the implied level effect using the correct transformation (exp(−0.079) − 1 ≈ −7.6%). Consider also reporting results in levels as a robustness check.
- **Location:** Results Section (Within-Poland DiD), Discussion section ("about 8 fewer deaths per 1,000")

### MC2: Identification Threat — Differential Age Trends

- **Dimension:** Identification
- **Issue:** The within-Poland DiD compares ages 75+ to ages 65–74 (with a bandwidth of 10). The parallel trends assumption requires that, absent the policy, mortality trends for these two groups would have evolved identically. But there are strong reasons to expect **differential secular trends across age groups** that have nothing to do with the drug policy: improvements in cardiovascular treatment, cancer screening, vaccination programs, and other medical advances often have age-differentiated effects. The event study helps, but the pre-treatment period (2000–2015) is very long, and small pre-trend divergences can compound. The paper needs to take this threat much more seriously.
- **Suggestion:** (a) Add age-specific linear or quadratic trends to the TWFE model as a robustness check. (b) Conduct a placebo test using earlier "fake" treatment dates (e.g., 2008 or 2012) to see if similar-magnitude effects appear. (c) Use the 2023 expansion to age 65+ as a second natural experiment — if the same DiD approach shows an effect for ages 65–74 after 2023, that corroborates the 2016 finding. (d) Narrow the age bandwidth to be as close to the 75 threshold as possible (e.g., 73–77) and show results.
- **Location:** Empirical Strategy, Strategy 1

### MC3: Extremely Thin Literature Review

- **Dimension:** Literature
- **Issue:** The paper cites only **4 references**: Abadie et al. (2010), HMD, Kaestner et al. (2019), and Majewska & Zaremba (2025). A serious submission on this topic needs engagement with at least 20–30 papers. Missing literatures include:
  - **Drug coverage and mortality:** Chandra, Flack, & Obermeyer (2024, QJE); Duggan & Scott Morton (2010); Huh & Reif (2017)
  - **Health insurance and mortality:** Sommers et al. (2012, NEJM); Finkelstein & McKnight (2008); Currie & Gruber (1996)
  - **European drug subsidy programs:** literature on UK, Italy, Spain, Germany free drug policies for elderly
  - **Polish health system:** Sowada et al. (2019, HiT)
  - **Synthetic control methods:** Abadie (2021, JEL survey); Doudchenko & Imbens (2016)
  - **DiD methodology:** Callaway & Sant'Anna (2021); de Chaisemartin & d'Haultfoeuille (2020); Goodman-Bacon (2021)
  - **Mortality measurement:** Preston et al. (2001, Demography textbook)
- **Suggestion:** Add a dedicated "Related Literature" section (or expand the introduction) engaging with these bodies of work. Position the contribution explicitly relative to the drug insurance, health insurance, and European health policy literatures.
- **Location:** Introduction, new Literature Review section

### MC4: Incorrect Reference Details

- **Dimension:** Literature / Presentation
- **Issue:** Two of the four references contain factual errors:
  - **Kaestner et al. (2019):** Listed as "Kaestner, R., Long, C., & Alexander, G." The actual co-authors are Robert Kaestner, **Cuping Schiman**, and G. Caleb Alexander. There is no "Long." The journal volume/pages are also incorrect — the paper lists 86(4), 807–843, but the actual citation is 86(3), 595–628.
  - **Majewska & Zaremba (2025):** Listed as "Majewska, A., & Zaremba, A." The actual authors are **Gosia** Majewska and **Krzysztof** Zaremba — initials should be G. and K., not A. and A. The title in the reference is also fabricated — the actual title is "Universal Subsidies in Pharmaceutical Markets: Lessons from Poland's Drugs 75+ Policy."
- **Suggestion:** Correct all reference entries against the actual papers (which are in `master_supporting_docs/supporting_papers/`). Build a proper BibTeX file.
- **Location:** References section

### MC5: No Abstract

- **Dimension:** Presentation
- **Issue:** The paper has no abstract. Every economics paper — working paper or submission — needs a 100–150 word abstract summarizing the question, method, and key findings.
- **Suggestion:** Write a concise abstract.
- **Location:** Before Introduction

### MC6: Tension Between Strong Within-Poland and Null External Results

- **Dimension:** Argument
- **Issue:** The within-Poland DiD shows a large, statistically significant effect (−7.9% in log mortality). But the cross-country DiD triple-diff is mostly insignificant (p-values from 0.14 to 0.82), and the synthetic control p-values range from 0.24 to 0.86. The paper acknowledges this tension but doesn't adequately grapple with what it means. If the policy truly reduced mortality by ~8%, we would expect to see *some* signal in the cross-country and synthetic control analyses. The fact that we don't could mean: (a) the within-Poland estimate is driven by differential age trends (MC2 above), (b) the cross-country designs lack power, or (c) the true effect is much smaller than the within-Poland estimate suggests.
- **Suggestion:** Add a formal power calculation for the cross-country designs. Discuss more explicitly what the divergence across strategies implies for the credibility of the within-Poland result. Consider presenting the within-Poland estimate as an *upper bound* rather than the preferred estimate.
- **Location:** Discussion, Summary across strategies

### MC7: Missing Theoretical/Conceptual Framework

- **Dimension:** Argument
- **Issue:** The paper jumps from institutional background directly to empirics with no model or conceptual framework. A referee wants to understand: *through what mechanisms* would free drugs reduce mortality? What is the chain from zero co-pays → adherence → health outcomes → mortality? What magnitudes are plausible given what we know about drug effectiveness? Without this framework, the reader has no way to judge whether −7.9% is too large, too small, or about right.
- **Suggestion:** Add a short "Conceptual Framework" section after Institutional Background that lays out the causal chain (price reduction → adherence → disease management → hospitalization/mortality) and provides back-of-envelope plausibility checks using Majewska & Zaremba's utilization estimates.
- **Location:** New section between Institutional Background and Data

## Minor Concerns

### mc1: Paper References Script Filenames
- **Issue:** The Data section mentions "Script `00_data_loading.py` parses the raw HMD text files..." This is inappropriate for an academic paper. Implementation details belong in a replication README.
- **Suggestion:** Remove all references to specific script filenames. Describe the data processing abstractly.

### mc2: Tables and Figures Not Embedded
- **Issue:** Tables and figures are referenced in text but exist only as separate CSV/image files. The paper reads as a narrative with pointers to external files rather than a self-contained manuscript.
- **Suggestion:** Embed actual formatted tables and figure references in the manuscript. The current "Tables and figures (reference)" paragraph at the end of the Data section is especially awkward — it reads like a README, not a paper.

### mc3: No Female Synthetic Control Results
- **Issue:** The synthetic control analysis is run for Total and Male only, not Female. Given that the within-Poland DiD finds the largest effect for females (−0.119), this is a notable omission.
- **Suggestion:** Add female SCM configurations.

### mc4: COVID Handling Needs More Detail
- **Issue:** The paper says COVID years are "excluded or treated separately" but doesn't specify exactly which specifications exclude them. The code shows 2020–2021 are dropped by default. This is reasonable but should be stated explicitly and discussed. Also, 2022–2023 may have unusual mortality patterns (COVID recovery, excess mortality aftermath) that warrant discussion.
- **Suggestion:** Be explicit about COVID treatment. Consider a specification that drops 2020–2023 entirely to test whether results hold for 2017–2019 alone (the "cleanest" post-treatment window).

### mc5: Standard Error Clustering
- **Issue:** Within-Poland DiD clusters at the age level. With only 20 clusters (single-year ages 65–84), cluster-robust SEs may be unreliable. The code uses `cov_kwds={"groups": df["Age"]}` which gives 20 clusters.
- **Suggestion:** Report wild cluster bootstrap p-values as a robustness check. Also consider clustering at the age-group level (fewer clusters but more appropriate for the treatment assignment).

### mc6: Dependent Variable Units Inconsistent Across Strategies
- **Issue:** Within-Poland uses log(mortality rate). Cross-country DiD also uses log. But the synthetic control operates on mortality rate levels. This makes it hard to compare magnitudes across strategies.
- **Suggestion:** Either use the same transformation everywhere, or provide an explicit reconciliation of how to compare coefficients across designs.

### mc7: No "Drugs 65+" Analysis
- **Issue:** The 2023 expansion to age 65+ is described in the institutional background but never exploited empirically. This is a missed opportunity — it provides a second natural experiment with a different age threshold.
- **Suggestion:** Even a brief analysis of the 2023 expansion (comparing ages 65–74 before and after September 2023 vs ages 55–64) would significantly strengthen the paper.

### mc8: Donor Pool Size Inconsistency
- **Issue:** The paper says "43 countries in our main runs" but the config and data loading showed 37 countries in the HMD data (or 50 in the cross-country deaths file, which includes sub-national units). The actual table shows "N Donors = 43." This should be verified and explained.
- **Suggestion:** Clearly list which entities are in the donor pool.

## Referee Objections

### RO1: "Your within-Poland DiD is just capturing differential secular mortality trends by age, not the drug policy."

**Why it matters:** This is the most likely fatal objection. Mortality improvement rates vary by age for many reasons unrelated to drug policy. The 75+ age group may simply be on a steeper improvement trajectory than the 65–74 group due to advances in cardiovascular treatment, blood pressure management, or diabetes care that disproportionately benefit the oldest-old. The event study helps, but 15 years of pre-data with slowly diverging trends might not look like a violation of parallel trends yet still bias the estimate.

**How to address it:** (a) Placebo treatment dates. (b) Age-specific trends in the TWFE model. (c) Use the 2023 expansion as a separate experiment. (d) Compare to differential age trends in comparator countries (if 75+ improved more than 65–74 everywhere, it's not Poland-specific). (e) Show results for narrow bandwidths (73–77) where the ages are most similar.

### RO2: "With only 4 references and incorrect citations, the paper doesn't demonstrate familiarity with the literature."

**Why it matters:** A referee receiving this paper would immediately question whether the authors are aware of the relevant empirical literature on drug coverage and mortality. The Chandra et al. (2024, QJE) paper — which studies the mortality effects of cost-sharing in Medicare — is directly relevant and not cited. The broader health insurance → mortality literature is absent entirely. Incorrect author names signal carelessness.

**How to address it:** Comprehensive literature review. Fix all citations.

### RO3: "The cross-country and synthetic control results are null. Why should I believe the within-Poland estimate?"

**Why it matters:** The paper's own evidence from two out of three strategies fails to find a significant effect. The within-Poland estimate could be large because of age-trend confounds (RO1). A skeptical referee will read the paper as "one significant result from a potentially confounded design plus two null results from cleaner designs" and conclude the true effect is likely small or zero.

**How to address it:** (a) Power analysis showing the cross-country designs are underpowered. (b) More honest framing: present the within-Poland result as suggestive and the cross-country/SCM as bounding. (c) The 2023 expansion as corroboration. (d) Consider that the true effect is small — which is consistent with Kaestner et al.'s null mortality result for Part D.

### RO4: "A 7.9% reduction in mortality from a drug subsidy seems implausibly large."

**Why it matters:** Even generous interpretations of the utilization effects (7.5–13% increase in drug consumption, per Majewska & Zaremba) would need to translate through a long causal chain (more drugs → better adherence → better disease management → fewer deaths) to produce a nearly 8% mortality reduction. Kaestner et al. found zero effect on mortality for Medicare Part D, which provided broader coverage to a larger population. If the true effect were this large, it would be one of the most cost-effective public health interventions ever studied.

**How to address it:** Back-of-envelope calculation using the utilization elasticity from Majewska & Zaremba and mortality-adherence gradients from the clinical literature. If the calculation yields a much smaller predicted effect (e.g., 1–2%), the within-Poland estimate may be upward biased.

### RO5: "How do you separate the Drugs 75+ effect from contemporaneous health system changes in Poland?"

**Why it matters:** Poland's health system was evolving throughout this period — healthcare spending was increasing, EU accession effects were ongoing, other health reforms may have been introduced. If any of these disproportionately benefited the 75+ age group, they would confound the estimate. The paper claims the drug policy was "rolled out nationally, without major concurrent overhauls" but provides no evidence for this claim.

**How to address it:** Provide a timeline of other health system reforms in Poland (2010–2023) and argue that none specifically targeted the same age threshold. Cite the Sowada et al. (2019) Health in Transition report for background on concurrent reforms.

## Specific Comments

### Introduction
- Para 1: Well-motivated. The opening sentence is strong.
- Para 3: The characterization of Kaestner et al. as finding "at best, modest effects on all-cause mortality" is accurate (they find no significant effect).
- Missing: No statement of contribution beyond "the first comprehensive, population-based evidence" — what specific gap does this fill?

### Institutional Background
- Good level of detail on the policy. The description draws effectively on Majewska & Zaremba.
- Missing: No discussion of what drugs are on the list. Is it cardiovascular? Respiratory? Cancer? The composition matters for predicting mortality effects.
- Missing: No discussion of compliance/take-up. What share of eligible individuals actually used the program?

### Data
- The description is clear but too focused on the pipeline mechanics. Remove references to Python scripts and parquet files.
- The "Tables and figures (reference)" paragraph should be deleted — this is a catalog, not exposition.
- The cause-of-death analysis is mentioned but never actually exploited in the results beyond a single figure reference.

### Empirical Strategy
- The "Overview for policy readers" subsection is well-intentioned but unusual for an economics paper. Consider moving it to an appendix or eliminating it — the standard subsections already explain the strategies clearly.
- Strategy 1: The specification needs a formal equation (Y = α + β₁Treated + β₂Post + β₃Treated×Post + ε). Currently it's described only in words.
- Strategy 2: Same — needs formal specification.
- Strategy 3: The SCM description is adequate but should mention what matching variables are used (just the outcome? or also covariates?).

### Results
- Table 1 claims 65–69 declined by −3.2% but 60–64 declined by −7.6%. This is odd — the group just below the control boundary declined more than the first control group. Worth discussing.
- The claim that effects are "twice as large for women" is true in coefficient terms (−0.119 vs −0.045) but should be related to baseline mortality differences. Women have lower baseline mortality at every age, so a larger log-point reduction may reflect a smaller absolute reduction.

### Discussion
- Too short. Needs deeper engagement with mechanisms, external validity, and the tension across strategies.
- The "about 8 fewer deaths per 1,000" claim repeats the misinterpretation from MC1.

### Conclusion
- Appropriate length but inherits the framing issues.

## Summary Statistics

| Dimension | Rating (1-5) |
|-----------|-------------|
| Argument Structure | 3 |
| Identification | 2 |
| Econometrics | 2.5 |
| Literature | 1.5 |
| Writing | 3.5 |
| Presentation | 2 |
| **Overall** | **2.5** |
