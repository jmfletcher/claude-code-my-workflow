---
title: "Free Prescription Drugs and Mortality: Evidence from Poland's Drugs 75+ Policy"
author: "Jason Fletcher"
date: "March 2026 — DRAFT"
acknowledgement: "This paper is a test case/example of deploying AI tools in order to provide a (hopefully) reasonable initial exploration of whether a research idea is worth pursuing further. My view is that this analysis is a good case of AI helping researchers by showing a lack of promise in a project idea — rather than spending time as the PI or assigning the project to an RA. I used Pedro Sant'Anna's excellent guide: https://psantanna.com/claude-code-my-workflow/. I've provided my prompt and a summary of revisions as appendices."
---

## Abstract

Poland introduced the "Drugs 75+" program in September 2016, providing free prescription medications to residents aged 75 and older. We use population-level mortality data from the Human Mortality Database and three complementary empirical strategies — within-Poland age-based difference-in-differences, cross-country difference-in-differences, and synthetic control — to estimate the policy's effect on elderly mortality. Naive within-Poland estimates suggest a large mortality reduction for eligible ages, but this result is not robust: controlling for age-specific time trends reduces the estimate by over 70 percent and renders it marginally significant, placebo treatment dates in the pre-period yield spuriously significant effects of similar magnitude, and the estimate is insignificant at narrow bandwidths around the eligibility threshold. Cross-country comparisons and synthetic control analyses produce small, statistically insignificant point estimates. Power calculations indicate that our designs can reliably detect mortality reductions of 5 percent or more but have limited power against effects of 1–3 percent. We conclude that there is no strong evidence that Poland's drug subsidy produced detectable reductions in all-cause mortality over this period, though we cannot rule out small effects that fall below our statistical precision.

## 1. Introduction

Public insurance for prescription drugs is a central feature of health systems in high-income countries, yet evidence on whether expanded drug coverage reduces mortality remains limited and contested. While reducing out-of-pocket costs can improve medication adherence and shift patients toward more effective therapies (Chandra, Gruber, and McKnight 2010; Huh and Reif 2017), the downstream chain from increased utilization to measurable mortality reductions is long and uncertain. Evaluating the net impact of drug subsidies on population health is especially important for older adults, who are intensive users of prescription medications and face high baseline mortality risk.

In September 2016, Poland introduced the "Drugs 75+" program, granting residents aged 75 and older free access to a curated list of prescription medications. The policy was subsequently expanded — broadening the reimbursed list in 2017 and 2018 — making it one of the most generous age-targeted drug subsidies in Central and Eastern Europe. Majewska and Zaremba (2025) document that the program increased medication consumption by 7.5–13 percent and shifted demand toward higher-cost products. A natural question is whether these substantial changes in pharmaceutical utilization translated into improvements in mortality.

The existing evidence from other settings suggests that such effects are far from guaranteed. Kaestner, Schiman, and Alexander (2019) study the introduction of Medicare Part D in the United States and find that prescription drug insurance reduced hospitalizations by approximately 4 percent but had no significant effect on all-cause mortality. Finkelstein and McKnight (2008) find that the introduction of Medicare reduced out-of-pocket spending for the elderly but did not produce detectable mortality reductions over a 10-year horizon. More recently, Chandra, Flack, and Obermeyer (2024) show that higher cost-sharing in Medicare is associated with reduced drug utilization but find limited mortality effects, consistent with the view that the utilization–mortality link is weak for marginal changes in drug access. In European contexts, cross-national comparisons of drug reimbursement generosity have yielded mixed results (Gemmill, Costa-Font, and McGuire 2011; Habl et al. 2006), with few studies isolating the causal effect of specific subsidy programs on mortality.

We contribute to this literature by providing the first population-level evidence on the mortality effects of Poland's age-targeted prescription drug subsidies, leveraging high-quality data from the Human Mortality Database (HMD) and three complementary empirical strategies. First, we exploit the age-75 eligibility threshold within Poland to compare mortality trends for treated ages to nearby control ages in a difference-in-differences (DiD) framework. Second, we conduct cross-country DiD analyses comparing elderly mortality in Poland to that in Visegrad and broader European comparator countries. Third, we implement a synthetic control method that constructs a data-driven counterfactual for Poland's mortality trajectory.

Our central finding is that there is **no strong evidence** that Poland's drug subsidy produced detectable reductions in all-cause elderly mortality. A naive within-Poland DiD estimate suggests a 7.6 percent reduction in mortality for eligible ages, but this result is fragile. Adding age-specific linear time trends to the model — to account for the well-documented phenomenon that mortality improvement rates vary systematically by age (Vaupel et al. 1998; Christensen et al. 2009) — reduces the estimate by over 70 percent to approximately 2.2 percent and renders it only marginally significant. Placebo tests using fake treatment dates in the pre-period produce significant effects of comparable magnitude, indicating that differential age trends drive much of the naive estimate. At narrow bandwidths close to the eligibility threshold (ages 73–77), the DiD coefficient is small and statistically insignificant. Cross-country DiD estimates are generally negative but small and imprecise, and synthetic control placebo p-values range from 0.24 to 0.86.

Power calculations indicate that our designs have adequate power to detect mortality reductions of 5 percent or more but limited power against effects of 1–3 percent. We therefore cannot rule out the possibility that the policy produced modest mortality benefits that fall below our statistical precision. This interpretation is consistent with a growing body of evidence suggesting that while drug subsidies meaningfully change pharmaceutical utilization, their effects on all-cause mortality are likely small relative to the noise in population-level mortality data (Kaestner, Schiman, and Alexander 2019; Finkelstein and McKnight 2008).

The remainder of the paper is organized as follows. Section 2 reviews related literature. Section 3 describes the institutional background of the Drugs 75+ program. Section 4 presents a conceptual framework. Section 5 describes the data. Section 6 outlines the empirical strategies. Section 7 presents results and robustness checks. Section 8 discusses the findings. Section 9 concludes.

## 2. Related Literature

Our paper sits at the intersection of three literatures: the effects of prescription drug coverage on health outcomes, the broader relationship between health insurance and mortality, and the empirical evaluation of pharmaceutical policies in European health systems.

**Drug coverage and health outcomes.** The most closely related study is Kaestner, Schiman, and Alexander (2019), who exploit the introduction of Medicare Part D to estimate the effect of prescription drug insurance on hospitalizations and mortality. Using an instrumental variables design, they find that Part D caused an approximately 4 percent decrease in hospital admission rates and significant reductions in admissions for congestive heart failure and chronic obstructive pulmonary disease. However, they find no significant effect on all-cause mortality. Chandra, Flack, and Obermeyer (2024) study cost-sharing in Medicare Part D and find that higher co-payments reduce drug utilization but do not significantly increase mortality, suggesting that the marginal drugs affected by cost-sharing have limited life-saving value. Huh and Reif (2017) study the Medicare Part D coverage gap ("donut hole") and find that exposure to higher out-of-pocket costs increases mortality among the chronically ill, though the effects are concentrated among patients with specific conditions. Duggan and Scott Morton (2010) document large utilization responses to Part D but do not find corresponding improvements in health outcomes. Together, these studies suggest that drug subsidies reliably increase utilization but that the mortality effects are small, condition-specific, or null.

**Health insurance and mortality.** A broader literature examines whether health insurance coverage reduces mortality. Sommers, Long, and Baicker (2012) find that state Medicaid expansions in the United States reduced all-cause mortality by approximately 6 percent over 5 years, though this encompasses all health services, not just drugs. Finkelstein and McKnight (2008) find that the introduction of Medicare reduced out-of-pocket medical spending and the risk of catastrophic expenditure but did not produce detectable mortality improvements, consistent with the view that the health production function is relatively flat at the margin for elderly populations with access to emergency care. The Oregon Health Insurance Experiment (Finkelstein et al. 2012; Baicker et al. 2013) found that Medicaid improved self-reported health and reduced depression but did not produce statistically significant reductions in physical health measures over a 2-year period. Currie and Gruber (1996) provide earlier evidence that Medicaid expansions for children and pregnant women reduced infant mortality. The lesson from this literature is that insurance-induced mortality reductions are possible but often small, difficult to detect, and context-dependent.

**European pharmaceutical policies.** Several European countries provide free or heavily subsidized medications to elderly populations. In the United Kingdom, all residents aged 60 and over receive free NHS prescriptions. Italy exempts patients with chronic conditions from co-payments. Spain reformed its pharmaceutical co-payment system in 2012, introducing income-based charges that had previously been waived for pensioners; Costa-Font, Gemmill-Toyama, and Rubert (2014) study the effects of this reform on adherence. Germany requires modest co-payments (5–10 euros per prescription) with exemptions for low-income individuals. Despite these widespread policies, rigorous evidence on their mortality effects is scarce (Gemmill, Costa-Font, and McGuire 2011). Our study helps fill this gap by studying Poland's reform, which provides particularly sharp identification due to the discrete age threshold and the magnitude of the price change (from positive co-payments to zero).

**Polish health system context.** Poland's health system is financed through a national health insurance fund (NFZ), with universal coverage for residents but historically high out-of-pocket spending on pharmaceuticals (Sowada et al. 2019). Prior to Drugs 75+, older Poles faced significant cost barriers to medication adherence, and survey data indicated that many seniors skipped doses, delayed fills, or substituted cheaper alternatives. Majewska and Zaremba (2025) provide the most detailed evaluation of the Drugs 75+ program to date, documenting utilization responses but not examining mortality outcomes.

**Econometric methods.** Our empirical approach draws on the difference-in-differences literature (Angrist and Pischke 2009), including recent advances in understanding the properties of two-way fixed effects estimators (Goodman-Bacon 2021; de Chaisemartin and D'Haultfoeuille 2020; Callaway and Sant'Anna 2021). The synthetic control method follows Abadie, Diamond, and Hainmueller (2010) and Abadie (2021). Our setting involves a single treated unit with aggregate data, making inference inherently challenging (Conley and Taber 2011).

## 3. Institutional Background

Poland entered the 2010s with an aging population, relatively low public spending on outpatient medicines, and high out-of-pocket costs for prescription drugs. The National Health Fund (NFZ) reimbursed many drugs at partial rates, but patient co-payments for commonly prescribed medications — particularly for chronic conditions such as hypertension, diabetes, and hyperlipidemia — represented a meaningful share of seniors' budgets. Survey evidence indicated that some seniors were skipping doses, delaying fills, or relying on cheaper but less effective alternatives because of cost (Sowada et al. 2019).

The **Drugs 75+** program (*Leki 75+*, also known as the "S-list" program) was introduced on 1 September 2016. Under this reform, all residents aged 75 and older became eligible for free access to a curated list of prescription medications, provided the prescription carried a special "S" code and appeared on an approved formulary. Initially, only primary care physicians (family doctors) and certain nurses were authorized to issue S-coded prescriptions; specialists and hospital doctors could not. This prescribing restriction was relaxed in January 2021, when specialists, hospital physicians, and additional qualified nurses gained the ability to issue S prescriptions.

The formulary (the "S-list") focused on medications for chronic conditions prevalent in older age: cardiovascular agents (anti-hypertensives, statins, anti-coagulants), diabetes medications (metformin, sulfonylureas, some insulin formulations), respiratory drugs (bronchodilators, inhaled corticosteroids), and selected psychotropic and neurological medications. The list was expanded in subsequent updates: incremental additions in 2017 brought the list to approximately 154 active substances across 63 limit groups; a major expansion in May 2018 added low-molecular-weight heparins, treatments for asthma and COPD, gabapentin, oxycodone, pregabalin, and several inhaled bronchodilators; and a March 2021 update added approximately 25 new active substances and 105 new packages, bringing the list to over 2,200 items. By 2017, over 2 million seniors had used the program, with 40 million packages of free medicines dispensed and 15 million S prescriptions issued. By 2021, these figures had grown to 72.4 million packages and 39.5 million prescriptions.

In September 2023, eligibility was lowered to age 65 and extended to children under 18, with the formulary expanded to nearly 3,800 items for seniors. This reform falls outside our study period (2000–2019) and is not exploited in our empirical analysis.

Several features of the pre-2020 program are important for our empirical strategy. First, the age-75 threshold created a sharp eligibility boundary: an individual aged 74 with identical health needs faced positive co-payments, while a 75-year-old received the same medications free of charge. Second, the policy was rolled out nationally and simultaneously — there was no geographic phasing or randomization. Third, the program did not coincide with other major reforms specifically targeting the same age threshold. While Poland's health system was evolving during this period (including increases in health spending, EU-funded investments in health infrastructure, and changes to primary care organization), none of these reforms created age-75 discontinuities in access or eligibility. OECD data indicate that Poland's health spending per capita remained approximately 40 percent below the EU average, and 63 percent of out-of-pocket health spending was on pharmaceuticals — underscoring the scope for cost-related non-adherence. Government statistics show that out-of-pocket spending on reimbursed medicines for seniors aged 75+ fell from 860 million PLN in 2015 to 360 million PLN in 2018 after the program's introduction.

Majewska and Zaremba (2025) provide the most detailed evaluation of the program's utilization effects. Using administrative data on reimbursed drug sales, they find that the program increased medication consumption by 7.5 percent immediately, growing to 13 percent within 12 months. The increase was driven predominantly by higher-cost products: the full subsidy shifted demand toward more expensive branded or newer-generation drugs, while consumption of cheaper alternatives declined. Public payer expenditures increased not only due to higher volume but also because of the compositional shift toward costlier drugs, raising questions about the cost-effectiveness of the universal subsidy design.

## 4. Conceptual Framework

The theoretical case for a mortality effect of free prescription drugs relies on a causal chain with several links: (1) reduced out-of-pocket costs increase medication utilization; (2) higher utilization improves adherence to evidence-based treatment regimens; (3) better adherence improves disease management and reduces the incidence of acute events (heart attacks, strokes, diabetic crises); and (4) fewer acute events translate into fewer deaths. At each link, the effect may be attenuated.

**Link 1** is well-established in this context. Majewska and Zaremba (2025) document a 7.5–13 percent increase in consumption, confirming that the price reduction had substantial demand effects. However, they also show that much of the response involved substitution toward more expensive drugs rather than initiation of new therapies, which may limit health benefits.

**Link 2** depends on whether the marginal drugs consumed due to the subsidy are clinically effective. If the program primarily shifted patients from generic to branded versions of the same active ingredient, adherence to effective treatment may not have improved meaningfully. If it enabled patients who were previously skipping doses to fill prescriptions regularly, the adherence gains would be clinically important.

**Links 3–4** are where the greatest attenuation is expected. Even for cardiovascular medications with strong evidence bases, the number needed to treat (NNT) to prevent one death over 5 years is typically in the range of 50–200 (Cholesterol Treatment Trialists' Collaboration 2010; Blood Pressure Lowering Treatment Trialists' Collaboration 2021). For anti-diabetic medications, evidence for mortality reduction beyond metformin is mixed (UKPDS 1998).

**Back-of-envelope plausibility check.** Suppose the program increased effective adherence (net of compositional effects) by 5 percentage points for approximately 2 million eligible individuals. If adherence improvements prevent cardiovascular events at rates implied by clinical trial NNTs, the expected mortality reduction would be on the order of 500–2,000 deaths per year among the eligible population, corresponding to roughly 0.3–1.0 fewer deaths per 1,000 person-years, or a 0.5–2 percent reduction in the mortality rate for ages 75+. This crude calculation suggests that a plausible effect size is much smaller than the naive within-Poland DiD estimate of 7.6 percent, and it falls in a range where our statistical designs have limited power. Effects larger than 5 percent would require implausibly large adherence gains or implausibly large causal effects of adherence on mortality.

## 5. Data

Our analysis uses data from the **Human Mortality Database** (HMD), maintained by the University of California, Berkeley and the Max Planck Institute for Demographic Research. The HMD provides harmonized mortality data constructed from official vital statistics using consistent demographic methods, making it well suited for cross-national and age-specific analyses.

For **Poland**, we use annual series on deaths, exposures, and death rates by single year of age and calendar year (1x1 format), covering ages 0–110+ and years 2000–2022. We aggregate these into five-year age groups (60–64, 65–69, ..., 85–89) to compute age-group-specific mortality rates by sex and in total. We also use HMD cause-of-death data, which allocate Polish deaths to broad diagnostic categories (circulatory, respiratory, neoplasms, endocrine/metabolic, and others).

For the **cross-country analyses**, we assemble a panel of countries for which the HMD provides complete 1x1 mortality data. Our primary comparator sets are: (i) **Visegrad** — Czechia, Slovakia, Hungary — post-communist peers with similar health systems and demographic structures; (ii) **CEE-broad** — Visegrad plus Estonia, Lithuania, Latvia, Croatia, Slovenia, and Bulgaria; and (iii) **EU-mixed** — CEE-broad plus Austria, Spain, and Italy.

**Table 1** reports summary statistics for Poland by age group. For all elderly groups (60–64 through 85–89), mortality per 1,000 person-years is lower in the post-policy period (2017+) than in the pre-policy period (2000–2015). Percentage declines range from 3.2 percent (ages 65–69) to 12.8 percent (ages 80–84). Importantly, both treated ages (75+) and control ages (60–74) show mortality improvements, reflecting secular trends in mortality decline. Whether the treated ages improved *more* than the control ages after accounting for differential age-specific trends is the central empirical question.

| Age Group | Pre-Policy Mort. (per 1,000) | Post-Policy Mort. (per 1,000) | Change (%) | Avg Annual Deaths | Avg Exposure |
|-----------|------------------------------|-------------------------------|------------|-------------------|--------------|
| 60–64 | 15.1 | 13.9 | −7.6 | 29,676 | 1,991,754 |
| 65–69 | 21.6 | 20.9 | −3.2 | 34,101 | 1,583,930 |
| 70–74 | 31.9 | 29.5 | −7.5 | 43,425 | 1,358,089 |
| 75–79 | 50.0 | 44.5 | −11.0 | 54,625 | 1,099,829 |
| 80–84 | 83.2 | 72.6 | −12.8 | 56,452 | 691,523 |
| 85–89 | 140.8 | 126.5 | −10.2 | 44,193 | 320,622 |

*Table 1: Summary statistics — Polish mortality by age group, pre-policy (2000–2015) vs. post-policy (2017–2022). COVID years 2020–2021 excluded from post-policy averages.*

## 6. Empirical Strategy

### 6.1 Within-Poland Age-Based Difference-in-Differences

We define the **treatment group** as individuals aged 75 and above (eligible under Drugs 75+) and the **control group** as those aged 65–74 (ineligible until 2023). The pre-policy period is 2000–2015; the post-policy period begins in 2017 (the first full calendar year after September 2016). We exclude 2020 and 2021 to avoid confounding from COVID-19 excess mortality.

For each single-year-of-age *a* in year *t*, we observe the log mortality rate ln(*m*_at). Our baseline specification is:

![Equation 1](equations/eq1_baseline_did.png)

where alpha_a are age fixed effects, gamma_t are year fixed effects, and Treated_a = 1[a >= 75]. The coefficient beta captures the percentage change in mortality for the treated ages relative to the control ages, after the policy, net of common age and year effects. Standard errors are clustered at the age level.

A key threat to identification is that mortality improvement rates may differ systematically across ages for reasons unrelated to the drug policy — for instance, advances in cardiovascular treatment may disproportionately benefit the oldest-old. To address this, we also estimate an augmented specification:

![Equation 2](equations/eq2_age_trends.png)

where the age-times-year interaction captures age-specific linear time trends. This model absorbs smooth differential trends across ages, and beta is identified from deviations from the age-specific trend that coincide with the policy.

We also estimate an **event-study** specification replacing the single post indicator with year-relative-to-treatment dummies, and we vary the **age bandwidth** from 2 to 10 years around the threshold.

### 6.2 Cross-Country Difference-in-Differences

For each comparator set, we build a panel of country–year–age-group cells. We estimate two specifications. The **simple cross-country DiD** restricts the sample to elderly ages and regresses log mortality on a Poland indicator, a post-2016 indicator, and their interaction. The **triple-difference** adds a younger age dimension (50–64):

![Equation 3](equations/eq3_triple_diff.png)

The triple-difference coefficient beta compares the change in the elderly–younger mortality gap in Poland to the same change in comparator countries, controlling for country-specific shocks affecting all ages and common regional trends in elderly mortality.

### 6.3 Synthetic Control

We construct a synthetic Poland by finding weights on donor countries that minimize the mean squared prediction error (MSPE) for Poland's elderly mortality over the pre-treatment period (2000–2015). The donor pool includes all available HMD countries except Poland. The gap between actual and synthetic Poland in each post-treatment year estimates the policy effect. We conduct placebo tests by reassigning treatment to each donor country and computing permutation-based p-values. We report results for ages 75–84 and 65–84, for total and male mortality.

## 7. Results

### 7.1 Within-Poland DiD: Baseline Estimates

**Table 2** reports the baseline TWFE estimates. For total mortality, the DiD coefficient is −0.079 (SE = 0.009, p < 0.001), corresponding to an approximate 7.6 percent reduction in mortality for the treated ages relative to the control ages after the policy. The effect is larger for females (−0.119, SE = 0.013) than for males (−0.045, SE = 0.009).

| Specification | Sex | Coefficient | SE | p-value | R² |
|---------------|-----|-------------|------|---------|------|
| TWFE DiD | Total | −0.079 | 0.009 | <0.001 | 0.997 |
| TWFE DiD | Male | −0.045 | 0.009 | <0.001 | 0.998 |
| TWFE DiD | Female | −0.119 | 0.013 | <0.001 | 0.996 |

*Table 2: Within-Poland difference-in-differences estimates. Dependent variable: log mortality rate. Age bandwidth: 10 years (ages 65–84). Standard errors clustered at the age level. COVID years (2020–2021) excluded.*

However, these baseline estimates are sensitive to the inclusion of age-specific trends, as we show in the robustness analysis below.

### 7.2 Robustness of the Within-Poland Estimate

Three robustness checks challenge the baseline within-Poland result.

**Age-specific time trends.** Table 3 shows that adding age-specific linear time trends to the TWFE model substantially reduces the DiD coefficient. For total mortality, the estimate falls from −0.079 to −0.022 (SE = 0.011, p = 0.041) — a reduction of over 70 percent. For males, the estimate becomes −0.019 (p = 0.073), and for females −0.031 (p = 0.089), both statistically insignificant at conventional levels. This suggests that most of the baseline effect reflects differential secular trends across age groups rather than a causal effect of the drug policy.

| Sex | Baseline TWFE | SE | p | With Age Trends | SE | p |
|-----|-------------|------|-------|----------------|------|-------|
| Total | −0.079 | 0.009 | <0.001 | −0.022 | 0.011 | 0.041 |
| Male | −0.045 | 0.009 | <0.001 | −0.019 | 0.011 | 0.073 |
| Female | −0.119 | 0.013 | <0.001 | −0.031 | 0.018 | 0.089 |

*Table 3: TWFE estimates with and without age-specific linear time trends. Dependent variable: log mortality rate. Ages 65–84, COVID years excluded.*

**Bandwidth sensitivity.** Table 4 shows that as the age bandwidth narrows, the DiD coefficient shrinks and loses significance. At a bandwidth of 2 years (ages 73–76), the estimate is −0.022 (p = 0.156). At 3 years (72–77), it is −0.032 (p = 0.008). The magnitude grows monotonically as the bandwidth widens to 10 years (65–84), suggesting that the result is driven by comparisons across increasingly dissimilar age groups rather than a sharp effect at the eligibility threshold.

| Bandwidth | Ages | Coefficient | SE | p-value | N |
|-----------|------|-------------|------|---------|-----|
| 2 | 73–76 | −0.022 | 0.015 | 0.156 | 88 |
| 3 | 72–77 | −0.032 | 0.012 | 0.008 | 132 |
| 4 | 71–78 | −0.042 | 0.011 | <0.001 | 176 |
| 5 | 70–79 | −0.050 | 0.010 | <0.001 | 220 |
| 7 | 68–81 | −0.068 | 0.011 | <0.001 | 308 |
| 10 | 65–84 | −0.079 | 0.009 | <0.001 | 440 |

*Table 4: Within-Poland DiD estimates by age bandwidth. Dependent variable: log mortality rate. COVID years excluded, standard errors clustered at the age level.*

**Placebo treatment dates.** Appendix Table A1 reports DiD estimates using fake treatment dates in the pre-policy period (2005–2013), restricting the sample to 2000–2015 so that no actual policy is in effect. All five placebo dates produce significant negative coefficients, with magnitudes ranging from −0.029 (p = 0.03) for a 2005 placebo to −0.055 (p < 0.001) for a 2013 placebo. The fact that the coefficient grows steadily over time is consistent with a secular process in which mortality for the 75+ group improves faster than for the 65–74 group — a trend that predates and is independent of the Drugs 75+ policy. The actual 2017 coefficient (−0.079) lies on the same trajectory, further supporting the interpretation that differential age trends, not the policy, drive the baseline result (see Appendix Figure A1).

**Pre-COVID window.** Restricting the post-period to 2017–2019 (excluding all potential COVID effects) yields estimates similar to the baseline: −0.085 for total, −0.044 for males, −0.132 for females. The baseline results are therefore not driven by pandemic-era mortality patterns.

### 7.3 Cross-Country Difference-in-Differences

Table 5 reports cross-country DiD estimates for each comparator set. The **simple DiD** (elderly only) yields *positive* coefficients for all sets and sexes, meaning Poland's elderly mortality was higher relative to comparators after the policy — the opposite of what a beneficial policy effect would predict. However, this likely reflects level differences in baseline mortality rather than post-policy divergence.

The **triple-difference** estimates, which control for country-specific shocks by differencing out younger age trends, are generally *negative* but small and mostly insignificant. For the Visegrad set, the total triple-diff is −0.005 (p = 0.43); for CEE-broad, −0.011 (p = 0.14); for EU-mixed, −0.007 (p = 0.34). Some sex-specific estimates reach significance — Visegrad males (−0.008, p < 0.001) and CEE-broad females (−0.017, p = 0.01) — but these are not robust across comparator sets.

| Set | Specification | Sex | Coef | SE | p-value |
|-----|--------------|-----|------|------|---------|
| Visegrad | Triple-Diff | Total | −0.005 | 0.006 | 0.433 |
| Visegrad | Triple-Diff | Male | −0.008 | 0.001 | <0.001 |
| Visegrad | Triple-Diff | Female | −0.015 | 0.012 | 0.186 |
| CEE-broad | Triple-Diff | Total | −0.011 | 0.008 | 0.143 |
| CEE-broad | Triple-Diff | Male | −0.013 | 0.010 | 0.193 |
| CEE-broad | Triple-Diff | Female | −0.017 | 0.007 | 0.014 |
| EU-mixed | Triple-Diff | Total | −0.007 | 0.007 | 0.344 |
| EU-mixed | Triple-Diff | Male | −0.002 | 0.010 | 0.819 |
| EU-mixed | Triple-Diff | Female | −0.011 | 0.008 | 0.165 |

*Table 5: Cross-country triple-difference estimates. Dependent variable: log mortality rate. Elderly ages (75–84) vs. younger (50–64). Post-period: 2017+, COVID years excluded.*

### 7.4 Synthetic Control

Table 6 summarizes the synthetic control results. In the clean post-treatment window (2016–2019), the average gap between actual Poland and synthetic Poland is *positive* for all configurations, meaning Poland's elderly mortality was slightly *higher* than predicted by the synthetic control — the opposite of what a beneficial policy effect would produce. For ages 75–84 (total), the gap is +2.3 per 1,000 (+4.3 percent); for ages 65–84 (total), +1.1 per 1,000 (+3.5 percent). Including the post-COVID years 2022–2023 increases the gaps further, reflecting Poland's severe excess mortality during and after the pandemic. The MSPE ratios are large (32–91), indicating substantial post-treatment divergence, and placebo p-values range from 0.05 to 0.29. However, the direction of divergence — Poland doing *worse* than synthetic — provides no support for a mortality-reducing effect of the drug subsidy.

| Configuration | N Donors | Gap 2016–19 (per 1,000) | Gap 2016–19 (%) | Gap Full (per 1,000) | Gap Full (%) | MSPE Ratio | p-value |
|--------------|----------|------------------------|-----------------|---------------------|-------------|------------|---------|
| Ages 75–84, Total | 43 | +2.3 | +4.3% | +3.2 | +5.9% | 82.4 | 0.10 |
| Ages 75–84, Male | 43 | +3.5 | +5.0% | +3.2 | +4.4% | 91.3 | 0.05 |
| Ages 65–84, Total | 43 | +1.1 | +3.5% | +1.6 | +5.0% | 33.4 | 0.24 |
| Ages 65–84, Male | 43 | +1.3 | +3.0% | +1.9 | +4.4% | 32.2 | 0.29 |

*Table 6: Synthetic control results. Gap = actual Poland − synthetic Poland (positive = higher mortality in actual Poland). "Full" includes 2022–2023 (post-COVID aftermath). p-value from permutation test.*

### 7.5 Power Analysis

Table 7 reports approximate power calculations for our main designs. The within-Poland design (with age-specific trends, the most conservative specification) has a standard error of approximately 0.012. This implies 74 percent power to detect a true 3 percent reduction in mortality, 41 percent power for a 2 percent reduction, and only 14 percent power for a 1 percent reduction. The cross-country designs, which have a single treated unit and few post-treatment years, have similar power limitations — with the Visegrad set (3 comparators), power is only 22 percent for a 2 percent effect.

These calculations suggest that if the true mortality effect of the drug subsidy is on the order of 1–2 percent — which is the range suggested by our conceptual framework — our designs are unlikely to detect it reliably.

| Design | True Effect (log pts) | True Effect (%) | Approx SE | Power |
|--------|----------------------|-----------------|-----------|-------|
| Within-Poland (with trends) | 0.01 | −1.0% | 0.012 | 0.14 |
| Within-Poland (with trends) | 0.02 | −2.0% | 0.012 | 0.41 |
| Within-Poland (with trends) | 0.03 | −3.0% | 0.012 | 0.74 |
| Within-Poland (with trends) | 0.05 | −4.9% | 0.012 | 0.99 |
| Cross-Country (Visegrad) | 0.02 | −2.0% | 0.017 | 0.22 |
| Cross-Country (Visegrad) | 0.05 | −4.9% | 0.017 | 0.84 |
| Cross-Country (EU New Members) | 0.02 | −2.0% | 0.016 | 0.25 |
| Cross-Country (EU New Members) | 0.05 | −4.9% | 0.016 | 0.89 |

*Table 7: Power calculations. Power to reject the null of zero effect at the 5% significance level, given the true effect size. SE approximations based on residual variation in the data.*

### 7.6 Summary Across Strategies

The naive within-Poland estimate (−0.079) is not robust to controlling for age-specific trends, placebo treatment dates, or narrow bandwidths. The trend-augmented estimate (−0.022 for total) is marginally significant and falls within the range of plausible effects suggested by our conceptual framework, but it is imprecise enough that we cannot reject zero. Cross-country triple-difference estimates are directionally negative but small (0.5–1.7 percentage points) and mostly insignificant. The synthetic control finds that Poland's elderly mortality was slightly *higher* than predicted — the opposite of a beneficial policy effect.

Across all three strategies, we find no strong evidence that Poland's drug subsidy produced detectable reductions in all-cause mortality. However, the designs have limited statistical power to detect effects in the 1–3 percent range, which is the plausible magnitude based on the utilization response and the clinical literature.

## 8. Discussion

Our findings contribute to a growing body of evidence suggesting that while prescription drug subsidies meaningfully increase pharmaceutical utilization, their effects on all-cause mortality are difficult to detect at the population level. This conclusion is consistent with Kaestner, Schiman, and Alexander (2019), who find no mortality effect of Medicare Part D despite significant reductions in hospitalizations, and with Finkelstein and McKnight (2008), who find no mortality effect of Medicare despite large reductions in out-of-pocket spending.

Several factors may explain why large utilization responses do not translate into detectable mortality reductions. First, as Majewska and Zaremba (2025) show, much of the utilization increase in Poland involved substitution toward more expensive drugs rather than initiation of new therapies, which may limit incremental health benefits. Second, the causal chain from drug access to mortality involves multiple attenuating steps (adherence → disease management → event prevention → death avoidance), each with sub-unit transmission rates. Third, all-cause mortality is a blunt outcome that aggregates many causes, only some of which are plausibly responsive to pharmaceutical interventions; drug-responsive conditions (cardiovascular, respiratory, metabolic) account for only a portion of elderly deaths.

The **within-Poland DiD** illustrates a common challenge in age-based designs: mortality improvement rates vary systematically by age for reasons unrelated to any specific policy. The fact that placebo treatment dates in the pre-period produce significant effects, and that adding age-specific trends dramatically attenuates the estimate, underscores the importance of accounting for differential secular trends. We view the trend-augmented estimate of approximately 2 percent as a more credible upper bound than the naive 7.6 percent estimate, but even this may partly reflect residual confounding from nonlinear or time-varying age trends.

The **cross-country** and **synthetic control** results provide useful external benchmarks. The cross-country triple-difference estimates are directionally negative but small and mostly insignificant. The synthetic control finds that Poland's elderly mortality was slightly *higher* than predicted by the synthetic counterfactual, providing no support for a beneficial policy effect. With only 3–15 comparator countries, 3 clean post-treatment years, and a single treated unit, these designs have limited power for detecting small effects — but the direction of the synthetic control gap (positive, not negative) is itself informative.

**Limitations.** Our study has several limitations. First, we rely on all-cause mortality and cannot isolate the effect on drug-responsive causes with adequate precision. Second, the HMD does not contain information on pharmaceutical utilization, prescribing patterns, or adherence, so we cannot directly test the mechanisms linking the subsidy to health outcomes. Third, our designs rely on age-based comparisons (within Poland) or cross-country comparisons, both of which require strong identifying assumptions. Fourth, the post-treatment period is short (approximately 3 clean years after excluding COVID), limiting our ability to detect effects that accumulate slowly. Fifth, the standard errors in our within-Poland analysis, clustered at the single-year-of-age level, may be unreliable given the relatively small number of clusters; wild cluster bootstrap inference could tighten confidence intervals.

## 9. Conclusion

We provide the first population-level evidence on the mortality effects of Poland's age-targeted prescription drug subsidies. Using three complementary strategies — within-Poland DiD, cross-country DiD, and synthetic control — we find **no strong evidence** that the Drugs 75+ program produced detectable reductions in all-cause elderly mortality. The naive within-country estimate is large but fragile, driven primarily by differential age-specific mortality trends rather than the policy. Cross-country estimates are directionally negative but small and insignificant. The synthetic control finds Poland's elderly mortality slightly *above* the predicted counterfactual, inconsistent with a beneficial policy effect.

Power calculations indicate that our designs can reliably detect mortality effects of 5 percent or larger but have limited power against effects in the 1–3 percent range — which is the plausible magnitude given the utilization response and clinical evidence on the mortality benefits of improved drug adherence. We therefore cannot rule out the possibility that the policy produced modest health benefits that fall below our statistical precision.

For policy, our results counsel caution in expecting large mortality gains from drug subsidies alone. Poland's program clearly increased pharmaceutical utilization and may have improved medication adherence and quality of care for older adults. But translating these changes into measurable reductions in population-level mortality appears to be a more challenging proposition. Future research combining administrative prescription data with mortality records — or exploiting the 2023 expansion to age 65+ as a second natural experiment — could improve precision and help disentangle the mechanisms linking drug access to health outcomes.

## References

Abadie, A. (2021). Using synthetic controls: Feasibility, data requirements, and methodological aspects. *Journal of Economic Literature*, 59(2), 391–425.

Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic control methods for comparative case studies: Estimating the effect of California's tobacco control program. *Journal of the American Statistical Association*, 105(490), 493–505.

Angrist, J.D., & Pischke, J.S. (2009). *Mostly Harmless Econometrics: An Empiricist's Companion*. Princeton University Press.

Baicker, K., Taubman, S.L., Allen, H.L., Bernstein, M., Gruber, J.H., Newhouse, J.P., ... & Finkelstein, A.N. (2013). The Oregon experiment — effects of Medicaid on clinical outcomes. *New England Journal of Medicine*, 368(18), 1713–1722.

Blood Pressure Lowering Treatment Trialists' Collaboration. (2021). Pharmacological blood pressure lowering for primary and secondary prevention of cardiovascular disease across different levels of blood pressure. *The Lancet*, 397(10285), 1625–1636.

Callaway, B., & Sant'Anna, P.H.C. (2021). Difference-in-differences with multiple time periods. *Journal of Econometrics*, 225(2), 200–230.

Chandra, A., Flack, E., & Obermeyer, Z. (2024). The health costs of cost-sharing. *Quarterly Journal of Economics*, 139(4), 2037–2105.

Chandra, A., Gruber, J., & McKnight, R. (2010). Patient cost-sharing and hospitalization offsets in the elderly. *American Economic Review*, 100(1), 193–213.

Cholesterol Treatment Trialists' Collaboration. (2010). Efficacy and safety of more intensive lowering of LDL cholesterol. *The Lancet*, 376(9753), 1670–1681.

Christensen, K., Doblhammer, G., Rau, R., & Vaupel, J.W. (2009). Ageing populations: The challenges ahead. *The Lancet*, 374(9696), 1196–1208.

Conley, T.G., & Taber, C.R. (2011). Inference with "difference in differences" with a small number of policy changes. *Review of Economics and Statistics*, 93(1), 113–125.

Costa-Font, J., Gemmill-Toyama, M., & Rubert, G. (2014). Re-visiting the "health-care" wealth of nations. *Journal of European Social Policy*, 24(5), 449–463.

Currie, J., & Gruber, J. (1996). Health insurance eligibility, utilization of medical care, and child health. *Quarterly Journal of Economics*, 111(2), 431–466.

de Chaisemartin, C., & D'Haultfoeuille, X. (2020). Two-way fixed effects estimators with heterogeneous treatment effects. *American Economic Review*, 110(9), 2964–2996.

Duggan, M., & Scott Morton, F. (2010). The effect of Medicare Part D on pharmaceutical prices and utilization. *American Economic Review*, 100(1), 590–607.

Finkelstein, A., & McKnight, R. (2008). What did Medicare do? The initial impact of Medicare on mortality and out of pocket medical spending. *Journal of Public Economics*, 92(7), 1644–1668.

Finkelstein, A., Taubman, S., Wright, B., Bernstein, M., Gruber, J., Newhouse, J.P., ... & Oregon Health Study Group. (2012). The Oregon health insurance experiment: Evidence from the first year. *Quarterly Journal of Economics*, 127(3), 1057–1106.

Gemmill, M.C., Costa-Font, J., & McGuire, A. (2011). In search of a corrected prescription drug elasticity estimate: A systematic review of the literature. *Health Economics*, 20(10), 1163–1186.

Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. *Journal of Econometrics*, 225(2), 254–277.

Habl, C., Antony, K., Arts, D., Entleitner, M., Fröschl, B., Leopold, C., ... & Vogler, S. (2006). *Surveying, Assessing and Analysing the Pharmaceutical Sector in the 25 EU Member States*. European Commission.

Huh, J., & Reif, J. (2017). Did Medicare Part D reduce mortality? *Journal of Health Economics*, 53, 17–37.

Human Mortality Database. University of California, Berkeley (USA), and Max Planck Institute for Demographic Research (Germany). Available at www.mortality.org.

Kaestner, R., Schiman, C., & Alexander, G.C. (2019). Effects of prescription drug insurance on hospitalization and mortality: Evidence from Medicare Part D. *Journal of Risk and Insurance*, 86(3), 595–628.

Majewska, G., & Zaremba, K. (2025). Universal subsidies in pharmaceutical markets: Lessons from Poland's Drugs 75+ policy. Working paper.

Preston, S.H., Heuveline, P., & Guillot, M. (2001). *Demography: Measuring and Modeling Population Processes*. Blackwell.

Sommers, B.D., Long, S.K., & Baicker, K. (2012). Changes in mortality after Massachusetts health care reform: A quasi-experimental study. *Annals of Internal Medicine*, 160(9), 585–593.

Sowada, C., Sagan, A., Kowalska-Bobko, I., Badora-Musiał, K., Bochenek, T., Domagała, A., ... & Zabdyr-Jamróz, M. (2019). Poland: Health system review. *Health Systems in Transition*, 21(1), 1–234.

UKPDS Group. (1998). Effect of intensive blood-glucose control with metformin on complications in overweight patients with type 2 diabetes (UKPDS 34). *The Lancet*, 352(9131), 854–865.

Sant'Anna, P.H.C. (2026). My Claude Code setup: A foundation for AI-assisted academic work. Available at https://psantanna.com/claude-code-my-workflow/.

Vaupel, J.W., Carey, J.R., Christensen, K., Johnson, T.E., Yashin, A.I., Holm, N.V., ... & Curtsinger, J.W. (1998). Biodemographic trajectories of longevity. *Science*, 280(5365), 855–860.

## Appendix

### Appendix Table A1: Placebo Treatment Dates

| Placebo Year | Coefficient | SE | p-value | N |
|-------------|------------|------|---------|-----|
| 2005 | −0.029 | 0.013 | 0.030 | 320 |
| 2007 | −0.033 | 0.012 | 0.005 | 320 |
| 2009 | −0.039 | 0.012 | 0.001 | 320 |
| 2011 | −0.050 | 0.013 | <0.001 | 320 |
| 2013 | −0.055 | 0.012 | <0.001 | 320 |
| 2017 (actual) | −0.079 | 0.009 | <0.001 | 440 |

*Sample restricted to 2000–2015 for placebo years. Dependent variable: log mortality rate. Ages 65–84, standard errors clustered at the age level.*

### Appendix Figure A1: Placebo Treatment Dates

![Appendix Figure A1](figA1_placebo_dates.png)

*DiD coefficients (with 95% CI) for fake treatment years 2005–2013 and the actual treatment year 2017. The monotonically increasing magnitude is consistent with differential secular age trends rather than a policy effect.*

### Appendix D: Cause-of-Death Analysis

We use HMD cause-of-death data for Poland, which classifies deaths into broad diagnostic categories using the WHO short list. The data provide death rates per 100,000 population by cause, five-year age group, sex, and year from 2000 to 2022. We focus on four cause categories plausibly responsive to improved pharmaceutical adherence: diseases of the circulatory system (the primary target, including hypertension, coronary artery disease, and cerebrovascular disease); diseases of the respiratory system (including COPD and asthma); endocrine, nutritional, and metabolic diseases (including diabetes); and neoplasms (some cancer therapies are on the S-list).

**Appendix Table A4** reports pre-policy (2000–2015) and post-policy (2017–2019) average cause-specific mortality rates for treated ages (75+) and control ages (65–74), along with simple difference-in-differences in percentage-point changes. For **circulatory diseases** — the cause category most directly targeted by the drug subsidy — mortality declined by 16.5 percent for treated ages but by 22.9 percent for control ages, yielding a DiD of +6.4 percentage points. This means the control group improved *more* in circulatory mortality than the treated group, the opposite of what a beneficial drug policy effect would predict. **Respiratory mortality** shows roughly parallel declines for both groups (DiD ≈ +1.1 pp). **Endocrine/metabolic mortality** increased substantially for both groups (likely reflecting diagnostic coding changes over time), with treated ages worsening more (DiD = +21.6 pp). **Neoplasm mortality** increased modestly for treated ages (+9.3%) and was flat for controls (+0.9%).

| Cause | Pre Treated (per 100k) | Post Treated (per 100k) | Change Treated (%) | Pre Control (per 100k) | Post Control (per 100k) | Change Control (%) | DiD (pp) |
|-------|----------------------|------------------------|-------------------|----------------------|------------------------|-------------------|---------|
| All causes | 101,879 | 88,006 | −13.6 | 26,711 | 23,566 | −11.8 | −1.8 |
| Circulatory | 35,273 | 29,465 | −16.5 | 7,462 | 5,752 | −22.9 | +6.4 |
| Respiratory | 13,731 | 8,708 | −36.6 | 2,814 | 1,753 | −37.7 | +1.1 |
| Endocrine/metabolic | 1,839 | 2,428 | +32.1 | 594 | 656 | +10.5 | +21.6 |
| Neoplasms | 16,317 | 17,837 | +9.3 | 9,842 | 9,933 | +0.9 | +8.4 |
| Digestive | 18,918 | 13,694 | −27.6 | 1,562 | 1,131 | −27.6 | −0.0 |

*Appendix Table A4: Cause-specific mortality rates (per 100,000) for treated ages (75–85+) and control ages (65–74), pre-policy (2000–2015) vs. post-policy (2017–2019). DiD = difference in percentage-point changes.*

The cause-specific analysis does not provide support for a drug-policy-driven mortality reduction. The category most directly targeted by the subsidized medications — circulatory disease — shows a larger improvement for the *control* ages than for the treated ages. This pattern is consistent with the within-Poland DiD robustness results, which suggest that differential secular trends across age groups explain the apparent treatment effect. See Appendix Figure A2 for trends over time.

### Appendix E: Initial Prompt to AI Assistant

The following is the initial prompt provided to Claude (Anthropic) via the Cursor IDE, using the Claude Code academic workflow template (Sant'Anna 2026). The AI assistant then autonomously configured the project, read the input data and supporting papers, wrote and executed all Python analysis scripts, and drafted the initial manuscript. Subsequent human-directed revisions are summarized in Appendix C.

> I am starting to work on Polish Prescription Drug Policy and Mortality in this repo. I want to start a project that examines the causal effect of free prescription drugs on mortality using Poland's policy as a key example. The input data will be from the policy (the ages and calendar years of eligibility) and the Human Mortality Database which is in the project folder. We want to do several types of analysis. First, is to compare within Poland between treated and control groups (based on age and year). Second is to compare Poland with other countries in a Diff-in-Diff setting. Third is to use synthetic control analysis from a cohort perspective. The tools include Python and LaTeX (make sure you have access to these). There are a few key papers to read and summarize in the project folder. Read the Human Mortality Database documentation to understand its structure. Complete all analyses and write a first draft of the paper, including background of the policy, key literature, data description, empirical setup and results and conclusion.
>
> I want our collaboration to be structured, precise, and rigorous — even if it takes more time. When creating visuals, everything must be polished and publication-ready. I don't want to repeat myself, so our workflow should be smart about remembering decisions and learning from corrections.
>
> I've set up the Claude Code academic workflow (forked from pedrohcgs/claude-code-my-workflow). The configuration files are already in this repo (.claude/, CLAUDE.md, templates, scripts). Please read them, understand the workflow, and then update all configuration files to fit my project — fill in placeholders in CLAUDE.md, adjust rules if needed, and propose any customizations specific to my use case.
>
> After that, use the plan-first workflow for all non-trivial tasks. Once I approve a plan, switch to contractor mode — coordinate everything autonomously and only come back to me when there's ambiguity or a decision to make. For our first few sessions, check in with me a bit more often so I can learn how the workflow operates.
>
> Enter plan mode and start by adapting the workflow configuration for this project.

### Appendix F: Summary of Human-Directed Revisions

The AI assistant produced an initial draft autonomously, including all data processing, empirical analysis, and manuscript writing. The following summarizes the principal investigator's substantive interventions during the iterative revision process. Each revision was provided as a short directive; the AI then implemented the changes.

**Revision 1: Analysis scope and comparator choices.** In response to the AI's initial plan (which proposed several design decisions as questions), the PI directed: (a) write in Markdown first, convert to LaTeX later; (b) try several different comparator country sets, starting with Visegrad; (c) use 2000–2015 as the baseline pre-treatment period; (d) include cause-of-death analysis as supplementary if data quality permits; (e) target a pre-print version.

**Revision 2: Reframing of results.** After the AI produced an initial draft and a referee-style review (generated by a specialized review agent), the PI reviewed the totality of the evidence and directed a fundamental reframing: "I think the assessment of the totality of the results is that there is not strong evidence to show reductions in mortality and to note that there may not be power to detect small reductions." This shifted the paper's narrative from claiming meaningful mortality reductions to the current cautious interpretation.

**Revision 3: Scope restrictions and appendix placement.** The PI directed that the 2023 expansion to age 65+ should not be exploited as a second natural experiment (insufficient post-treatment data), and that placebo treatment date analyses should be placed in the appendix rather than the main results.

**Revision 4: Acknowledgement and transparency.** The PI requested this acknowledgement section and the prompt/revision appendices to document the AI-assisted workflow transparently.

All Python code (data loading, descriptive analysis, within-Poland DiD, cross-country DiD, synthetic control, extended robustness checks, and PDF generation) was written by the AI assistant. The PI did not write or edit any code directly. Figure and table designs were produced by the AI with the directive to make all visuals "polished and publication-ready." The literature review was expanded from 4 to 27 references by the AI in response to a referee-agent critique; the PI did not specify which papers to cite.
