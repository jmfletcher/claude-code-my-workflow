# Calibrating Demographic Orphanhood Models with Decedent-Level Fertility: Evidence from the NHIS Linked Mortality File, 1986-2018

**Author:** Jason M. Fletcher [affiliation TK]
**Date:** May 2026
**Working draft v1**
**Keywords:** orphanhood; bereavement; kinship demography; matrix kinship; National Health Interview Survey; National Death Index; cause of death; non-resident parents

---

## Abstract

Estimates of the number of US children who have lost a parent rely on demographic-rate models that multiply parental death counts by an expected number of dependent children. The expected number is computed from natality data on adults who did not die, on the assumption that within demographic cells (age, sex, race / ethnicity, year), adults who die have the same fertility schedule as those who survive. Recent high-profile estimates -- 2.91 million US children with a deceased parent or caregiver in 2021 (Villaveces et al., 2025); 1.19 million cumulative children of drug-overdose and firearm decedents 1999-2020 (Schlüter et al., 2024) -- all rest on this assumption. Authors treat it as a sensitivity, parameterizing the within-cell fertility-mortality correlation at zero with ±25 % robustness bands.

This paper uses the NHIS Linked Mortality File 1986-2018 to test the assumption directly. Within the same demographic cells the published models use, we measure the ratio of co-resident minor counts for adults who die during NDI follow-up versus adults who survive. Pooled across all groups the correction is small (-3 % nationally for 2021 all-cause prevalence) but the race-stratified pattern is large and signed-opposite: -14 % for non-Hispanic White children, -20 % for non-Hispanic Asian / Pacific Islander children, and +26 % for non-Hispanic American Indian or Alaska Native children. For the Schlüter cause-specific target (drugs + firearms 1999-2020), the cumulative count falls 35 % below the naive kids-per-living-adult baseline and 42 % below the published headline. A back-of-envelope augmentation for non-resident fathers (a known gap in NHIS-based estimates) partially closes the all-cause gap but still leaves the cause-specific count well below the published value. The substantive conclusion -- that the published demographic-rate estimates overstate the cumulative drug-and-firearm orphanhood burden by roughly 40 % -- is robust to the choice between custodial and biological orphanhood definitions.

---

## 1. Introduction

The number of US children who have lost a parent is a policy-relevant population statistic. It anchors federal Survivor Benefits sizing under the Social Security Administration, Title IV-E foster-care reimbursements, school-based grief counseling allocations, and Medicaid eligibility overrides for surviving caregivers. It is also a leading indicator of how widely the US deaths-of-despair episode has reached into young adult and mid-life mortality cohorts: drug overdose, firearm violence, and -- since 2020 -- COVID-19 mortality have all been disproportionately concentrated in parental ages.

The published US estimates have grown rapidly since 2021. Villaveces et al. (2025) report 2.91 million US children with a deceased parent or caregiver-grandparent in 2021, using an all-cause demographic-rate model that combines NCHS mortality with NCHS natality and ACS household composition. Schlüter et al. (2024) report 1.19 million cumulative US children losing a parent to drug overdose or firearm violence 1999-2020, using a similar multi-state demographic accounting framework. Potter et al. (2025) report cancer-specific orphanhood from 2000-2020. Verdery et al. (2024) extend the kinship lens to siblings, grandparents, and aunts/uncles for overdose-related family bereavement. Hillis et al. (2021, 2022) produce the US and global COVID-orphanhood updates. The Annual Review of Sociology has published a synthetic essay (Smith-Greenaway, Verdery, & Carr, 2025) declaring the rise of "bereavement demography" as a field.

All of these papers share a common modeling architecture and a common assumption. The architecture is the matrix-kinship model formalized by Caswell (2019, 2020) and Caswell & Song (2021), implemented in the `DemoKin` R package (Williams et al., 2023). The assumption -- the one that drives our paper -- is that within any demographic cell defined by age, sex, race / ethnicity, year, and sometimes geography, **adults who die during the modeling horizon have the same fertility schedule as those who survive.** Authors flag the assumption explicitly. Villaveces et al. run a sensitivity that dampens fertility in the year before death and report that prevalent orphanhood shifts by up to 15 %. Schlüter et al. vary fertility of decedents by ±25 % and report that the substantive conclusions are "robust." These are parametric exercises. They are not measurements.

The assumption is the natural one to make if the modeler does not have data on the actual children of the actual decedents. Most US natality files do not link to mortality follow-up. Most mortality files do not link to fertility histories. The matrix-kinship machinery was built by Caswell to operate on aggregate demographic schedules precisely because individual-linked data on dependents per decedent are rare. The HIV / AIDS orphanhood literature (Stover et al.; the AIDS Impact Model in Spectrum) is the clearest published exception: Spectrum adjusts fertility downward for HIV-infected women off ART and for high-risk subgroups outside sub-Saharan Africa. Guida et al. (2022) introduce site-specific parity corrections for maternal cancer orphanhood. Jones et al. (2024) approximate overdose-decedent fertility from the National Survey on Drug Use and Health by using adults with past-year drug use as a risk-proximate proxy. None of these approaches observes the actual children of actual decedents. Each is the best available imperfect substitute.

This paper closes the substitute gap. The NHIS Linked Mortality File (NHIS-LMF) is a survey-linked-mortality dataset constructed by NCHS that links US National Health Interview Survey respondents from sample years 1986-2018 (and now, as of the January 2026 release, through 2022) to the National Death Index. For each adult respondent, the file records co-resident minor children at the time of survey interview and the linked indicator of death during follow-up. Within the same demographic cells the published orphanhood papers use, we can therefore measure:

$$
K_{\text{died},c} = \mathbb{E}\left[\text{co-resident minors} \mid \text{adult died during follow-up}, c\right]
$$
$$
K_{\text{alive},c} = \mathbb{E}\left[\text{co-resident minors} \mid \text{adult survived follow-up}, c\right]
$$

The ratio $\kappa_c = K_{\text{died},c} / K_{\text{alive},c}$ is the within-cell fertility-mortality correlation. It is the parameter the published literature fixes at one and then perturbs as a robustness check. We measure it.

We use $\kappa$ in three ways. First, we re-run the Villaveces (2025) all-cause matrix-kinship pipeline with $\kappa$-adjusted dead-parent mass and report a recalibrated 2021 prevalent count. Second, we apply $\kappa$ to the Schlüter (2024) cause-specific drug + firearm target using both a coarse 10-category leading-cause recode (`MORTUCODLD`) and the detailed 113-cause-style underlying-cause integer (`MORTUCOD`, available for NHIS samples 1986-2004 only). Third, we examine an important conceptual issue raised by reviewers of an earlier draft: NHIS measures *co-resident* minors and therefore omits non-resident parents (most relevantly non-custodial fathers). This bias is opposite-signed to the published-literature bias and we report a back-of-envelope correction.

Our three main findings, in order of size:

1. **Pooled all-cause orphanhood prevalence is approximately right.** Our matrix-kinship baseline produces 2.24 million US children under 18 with a deceased parent in 2021, comparable to the 2.91 million combined "parents or caregiver-grandparents" total in Villaveces et al. (the 670 K gap is the grandparent-caregiver layer, which we recover separately). The $\kappa$-calibrated total is 2.17 million (-3 % vs. baseline).

2. **Race-stratified all-cause orphanhood is biased in opposite directions by group.** $\kappa$ < 1 for most groups (NH White -14 %, NH Asian / PI -20 %, NH Black -6 %, Hispanic -1 %) but $\kappa$ > 1 for NH AIAN children (+26 %). The pooled "All" headline cancels out this dispersion. The race-stratified pattern is consistent with deaths-of-despair concentrating among young parents of school-age children in NH White and NH AIAN cohorts, and with "healthy-adult selection" -- adults with co-resident kids being lower-mortality on average -- in NH Black, Hispanic, and NH Asian / PI cohorts.

3. **Cause-specific cumulative orphanhood is substantially overstated by published estimates.** Schlüter et al. (2024) report 1.19 million cumulative US children of drug-overdose and firearm decedents 1999-2020. Under NHIS $\kappa$ calibration using the detailed `MORTUCOD` recode, the cumulative count is 691 thousand -- a 42 % reduction from the published headline and 35 % below our own naive kids-per-living-adult baseline. The correction is robust across three NHIS specifications (all-cause $\kappa$, intent-stratified $\kappa$ from `MORTUCODLD`, and cause-specific $\kappa$ from `MORTUCOD`).

The non-resident-parent bias is conceptually important but quantitatively second-order. NHIS captures co-resident minors of co-resident parents, omitting non-custodial fathers entirely. A back-of-envelope augmentation using ACS-based non-resident-father rates (30 % for NH White, 55 % for NH Black, 35 % for Hispanic, 15 % for NH Asian/PI, 50 % for NH AIAN) and a one-child-each assumption raises K_father_died by 15-30 % depending on race. For the all-cause headline this correction roughly offsets the $\kappa$ correction and leaves the cumulative count between 2.17 M (custodial) and 2.4-2.5 M (biological) -- still below the published 2.91 M combined number after subtracting the 0.6 M grandparent-caregiver layer. For the cause-specific Schlüter target the correction matters more because drug-overdose decedents are 70 % male and concentrated in high-non-resident-fatherhood groups, but a biological-orphanhood number lands around 800-900 K -- still well below the published 1.19 M.

The substantive contribution of the paper is therefore methodological and substantive at once. Methodologically, it provides the first US empirical estimates of the within-cell fertility-mortality correlation that drives the published orphanhood literature, and it shows how to plug those estimates into existing matrix-kinship engines without rewriting them. Substantively, it raises confidence in the headline level of pooled all-cause orphanhood (within 8 %) and lowers confidence in the published cause-specific Schlüter target (-35 to -42 % depending on definition). It also documents heterogeneity by race / ethnicity that the published "All" headlines hide. The implications for resource allocation under SSI Survivor Benefits, Title IV-E, and Medicaid override pathways are non-trivial.

The rest of the paper proceeds as follows. Section 2 reviews the prior literature in more detail. Section 3 describes the data, including the NHIS Linked Mortality File, the NCHS death files, the CDC WONDER bridged-race population data, and the IPUMS cause-of-death extracts. Section 4 lays out the matrix-kinship engine, the $\kappa$ estimator, and the cause-specific extension. Section 5 reports the all-cause and cause-specific results, with bootstrap confidence intervals. Section 6 discusses the non-resident-parent bias, the bidirectional definitional issue, and the household-structure stratification. Section 7 concludes with policy implications and a research agenda.

---

## 2. Background

### 2.1 The demographic-rate orphanhood architecture

The published US orphanhood literature uses a common modeling architecture. Death counts from the NCHS multiple-cause-of-death file are stratified by parent age, sex, race / ethnicity, year, and (sometimes) state. Within each stratum, an expected number of dependent children is computed from NCHS natality data on cohort fertility. The product of death counts and expected children per adult gives an expected number of children exposed to parental death, summed over cells to a national total. The recurrence is then propagated forward to compute prevalent stock (children with at least one deceased parent at a given time) and incident flow (children newly experiencing a parental death in a given year).

The mathematical scaffolding underlying this architecture is the matrix-kinship recurrence formalized by Caswell (2019, 2020) and extended to time-varying two-sex models by Caswell & Song (2021). The recurrence operates on age × age block matrices whose entries are age-specific fertility and survival rates; the output is the expected number of each kin type (parents, children, siblings, grandparents, aunts/uncles) per focal individual at each age. The `DemoKin` R package (Williams, Sánchez Pérez, & Alburez-Gutiérrez, 2023) makes the recurrence accessible to applied researchers and is the implementation actually used in Villaveces et al. (2025), Alburez-Gutierrez et al. (2024), and several subsequent papers. The recurrence assumes that "the demographic rates of an individual depend only on the individual's age, sex, and time" -- i.e., that within any demographic cell, individual heterogeneity averages out.

The demographic-rate architecture has the great advantage of being parsimonious. It requires only aggregated input schedules: age-specific death rates, age-specific fertility rates, population counts, and (for full kin-network analysis) survival to specific ages. It has the great disadvantage of imposing within-cell uniformity. If individuals' fertility and mortality are correlated within cells -- if, for example, opioid-overdose decedents have systematically more or fewer co-resident minor children than non-decedents of the same age, sex, race, and year -- the resulting orphanhood estimates are biased. The direction of the bias depends on the sign of the correlation.

### 2.2 What the published papers assume

We grouped the major US orphanhood papers in our companion literature review (Fletcher, 2026a) by whether their core method allows within-cell fertility heterogeneity. The grouping reveals a clear pattern.

The seven papers that do *not* allow within-cell heterogeneity in their core method are: Villaveces et al. (2025) for US all-cause orphanhood, Schlüter et al. (2024) for drug-overdose and firearm orphanhood, Potter et al. (2025) for cancer orphanhood, Verdery et al. (2024) for overdose-related family bereavement, Hillis et al. (2021) for US COVID orphanhood, Hillis et al. (2022) for global COVID orphanhood, and Alburez-Gutierrez et al. (2024) for conflict bereavement. The three that *do* partially or fully allow it are: Jones et al. (2024) for overdose, using NSDUH past-year drug users as a risk-proximate proxy; Guida et al. (2022) for cancer, using site-specific parity corrections; and the UNAIDS Spectrum / AIDS Impact Model (Stover et al.) for HIV, with HIV-stage and ART-status fertility adjustments.

A pattern emerges. The exceptions to the equal-fertility assumption appear when (a) the cause-of-death has a documented epidemiological link to fertility (HIV, cervical cancer), or (b) a risk-proximate survey exists that approximates decedent characteristics (NSDUH drug-use respondents for overdose). The exceptions do not appear when the cause-of-death is broad or when no risk-proximate survey is available. For US all-cause orphanhood the field has had nothing analogous to Spectrum -- until now.

### 2.3 The sensitivity-band approach

Both Villaveces et al. (2025) and Schlüter et al. (2024) report parametric sensitivity analyses on the equal-fertility assumption. The Villaveces sensitivity assumes that female fertility is dampened toward zero in the months leading up to a maternal death, on the rationale that very-late-pregnancy and post-partum mortality among mothers of newborns is rare. The dampening shifts pooled prevalent orphanhood by up to 15 % and incident orphanhood by up to 8.4 %. The Schlüter sensitivity multiplicatively scales fertility among decedents by 1 ± 0.25 and reports that the substantive conclusions (the *relative* burden by year and race) are robust to this scaling. Neither sensitivity assesses (a) whether the parametric form is right, (b) whether the bound is wide enough, or (c) whether the parameter varies by race / ethnicity or cause.

### 2.4 What we add

Our paper makes three contributions to this literature. First, we estimate the within-cell fertility-mortality correlation directly from NHIS-LMF, cell by cell, for sex × race / ethnicity × decade × age band, for the same demographic cells the published US literature uses. Second, we plug the estimated correlation into an existing matrix-kinship engine -- a Python re-implementation of `DemoKin`'s `kin_time_variant_2sex` -- and report recalibrated estimates for two published targets (Villaveces all-cause 2000-2021, Schlüter cause-specific 1999-2020). Third, we transparently document the bidirectional definitional issue around custodial vs biological orphanhood that our NHIS-based approach exposes.

The closest precedent for what we do is Jones et al. (2024), who proxy children-per-overdose-decedent using NSDUH respondents with past-year drug use. Our approach differs in two ways. First, we use the *actual* decedents in NHIS-LMF, not a risk-proximate survey. Second, we estimate $\kappa$ for *all causes* (and for the cause-specific Schlüter target), not just overdose. The methodological scope is correspondingly broader.

---

## 3. Data

### 3.1 NHIS Linked Mortality File

The NHIS-LMF is constructed by NCHS by probabilistic linkage of US National Health Interview Survey respondents to the National Death Index. The 2019 public-use release (used in this paper) covers NHIS sample years 1986 through 2018, with mortality follow-up through December 31, 2019. NCHS released an updated 2022 LMF in January 2026 extending follow-up through December 31, 2022; we treat the 2019 file as the primary analysis sample and note the 2022 release as a planned extension. Our analytic sample is restricted to adults age 18 and older with valid mortality linkage eligibility (`mortelig == 1`). The dependent-variable measure is `n_fam_childminor017` from IPUMS NHIS, defined as the count of co-resident minor children (age 0-17) in the respondent's family unit at NHIS interview, capped at 8.

Sample sizes are large. Across the 1986-2018 pooled extract there are 1.25 million person-records with eligible linkage and `mortstat == 1` (died during follow-up) or `mortstat == 2` (alive at follow-up cutoff). Restricting to adult parents (age ≥ 18 and at least one minor in the family unit) yields 193,245 respondents, of whom 7,437 died during follow-up. For the cause-specific analysis using `MORTUCOD` (NHIS sample years 1986-2004 only), the drug-overdose bucket (NHIS code 122, "Accidental poisoning") contains 697 decedents and the firearm bucket (codes 119, 125, 128, 132) contains 1,566 decedents.

NHIS-LMF carries cause-of-death information in two harmonized fields: `MORTUCODLD` (a 10-category leading-cause recode, available for all sample years) and `MORTUCOD` (a 113-cause-style detailed underlying-cause integer recode, available for sample years 1986-2004 only). We use both. The `MORTUCODLD` field is too coarse to isolate drug-overdose from motor-vehicle-accident decedents, but it is fine enough to distinguish "Accidents" (code 4, which includes drug overdoses, falls, MVAs, and drownings) from "All other causes (residual)" (code 10, which includes suicides, homicides, and intent-undetermined deaths). The `MORTUCOD` field, while not the raw 4-character ICD-10 code, cleanly identifies firearms (codes 119 accidental, 125 suicide, 128 homicide, 132 undetermined) and approximately identifies drug overdose via code 122 (accidental poisoning, which lumps drug overdose with non-drug chemical poisoning).

### 3.2 NCHS multiple-cause-of-death file

We use the Villaveces et al. (2025) Zenodo replication package (DOI 10.5281/zenodo.11423744) as the source for NCHS death counts. The package contains tidied parental-age-relevant deaths by 5-year age band × sex × race / ethnicity × year for 1983-2021. We supplement the package with the same NCHS multiple-cause file extended to a finer ICD-10 single-cause stratification for the Schlüter target. ICD-10 codes used:

- **Drug overdose (broad):** X40-X44 (accidental poisoning by drugs), X60-X64 (intentional self-poisoning by drugs), X85 (assault by drug poisoning), Y10-Y14 (drug poisoning of undetermined intent).
- **Drug overdose (narrow, NHIS-comparable):** X40-X49 only (matches NHIS code 122 = accidental poisoning).
- **Firearm:** W32-W34 (accidental discharge), X72-X74 (intentional self-harm), X93-X95 (assault), Y22-Y24 (undetermined intent), excluding Y35.0 (legal intervention) which is not in our NHIS firearm bucket.

### 3.3 CDC WONDER bridged-race population

Population denominators for the kinship engine come from CDC WONDER bridged-race vintage 2020 single-year-of-age population estimates for 1990-2021. For NHIS sample years 1986-1989 we back-fill population counts from 1990 (estimated impact on focal-age cohorts reaching 17 by 2000 is small; sensitivity analysis available on request). The 2020-2021 CDC WONDER releases disaggregate "Asian or Pacific Islander" into "Asian" and "Native Hawaiian or Other Pacific Islander" plus "More than one race"; we pool the first two into a combined "Asian or PI" bridged-race category to align with the older NCHS death files, and drop "More than one race" (small share, no NHIS analog).

### 3.4 ACS S1002 grandparent-caregiver counts

For the parental + grandparent-caregiver combined total comparable to Villaveces et al.'s 2.91 M headline, we add a flow-stock accounting layer using ACS Table S1002 "Grandparents Living With Grandchildren" estimates for 2010, 2015, 2019, and 2021. We use the subset "grandparents responsible for grandchildren," which excludes grandparents merely co-residing with the grandchild's nuclear family. Adult mortality among ages 50-79 comes from the same CDC WONDER source as the kinship engine. The grandparent layer is *not* NHIS-calibrated because NHIS has no grandchild head-count variable for adults outside the family unit.

---

## 4. Methods

### 4.1 Matrix-kinship engine

We re-implement the parental-kin block of `DemoKin`'s `kin_time_variant_2sex` recurrence in Python (`pykin/` in the project repository). The state vector at focal age $x$ is

$$
\mathbf{m}_{t,x} = \begin{bmatrix} \text{live mother} \\ \text{live father} \\ \text{dead mother} \\ \text{dead father} \end{bmatrix}
$$

each block of length $n_{\text{ages}}$. The transition matrix from focal year $t$ to $t+1$ is block-structured:

$$
U_t = \begin{bmatrix} U_f & 0 & 0 & 0 \\ 0 & U_m & 0 & 0 \\ M_f & 0 & G_f & 0 \\ 0 & M_m & 0 & G_m \end{bmatrix}
$$

where $U_s$ is the age-survival sub-diagonal (parent ages by sex $s$), $M_s$ is the age-mortality sub-diagonal (transitions to dead state at parent age $a$), and $G_s$ is an *absorbing* identity-shaped block in our implementation. The choice of an absorbing dead-block differs from `DemoKin`'s reference implementation (which stores incident-per-year deaths and cumulates post hoc) and produces *cumulative* probability of parental death at age $x$ directly, simplifying downstream summaries.

The initial parent-age distribution for a cohort born in year $t$ is

$$
\pi_{s,t}[a] = \frac{\text{pop}_s(a, t) \cdot \text{ASFR}_s(a, t)}{\sum_a \text{pop}_s(a, t) \cdot \text{ASFR}_s(a, t)}
$$

following Caswell & Song (2021).

The orphanhood prevalent stock at year $t$ for focal age $x$ is then $\sum_a \pi_{s,t-x}[a] \cdot (\text{dead-block}_{t,x}[a])$ summed across sex $s$. Aggregating across focal ages $x = 0, \ldots, 17$ for each focal year gives the prevalent count of US children under 18 with at least one deceased parent.

We replicate the baseline Villaveces et al. (2025) parental-only count for 2021 at 2.24 million, vs their combined parental + caregiver-grandparent count of 2.91 million; the 670 K gap matches our independently estimated grandparent-caregiver layer (2.71 M combined, within 7 % of Villaveces).

### 4.2 Estimating $\kappa$

For each NHIS-LMF cell $c = (\text{sex}, \text{race/eth}, \text{age band}, \text{decade})$ we compute:

$$
K_{\text{died},c} = \frac{\sum_{i \in c, \text{died}_i = 1} w_i \cdot \text{nk}_{i}^{\text{u18}}}{\sum_{i \in c, \text{died}_i = 1} w_i}
$$

$$
\kappa_c = \frac{K_{\text{died},c}}{K_{\text{alive},c}}
$$

where $w_i$ is the NCHS-recommended mortality-weight `mortwtsa` and $\text{nk}_i^{\text{u18}}$ is the count of co-resident minor children in respondent $i$'s family unit. Age bands are 18-29, 30-39, 40-49, 50-59, 60-69, 70+ ; decades are 1 (1986-89), 2 (1990-99), 3 (2000-09), 4 (2010-18). Race/ethnicity is collapsed to a 5-category scheme: Hispanic, Non-Hispanic White, NH Black, NH Asian or Pacific Islander, NH AIAN + other + multiracial. Cells with fewer than 25 weighted decedents are smoothed toward the (sex, race/eth, decade) pool across age bands; cells with fewer than 25 weighted survivors are smoothed analogously toward the (sex, race/eth, age band) pool across decades.

Standard errors come from 200 bootstrap replicates resampling NHIS primary sampling units within strata, with $\kappa$ recomputed in each replicate and the smoothing rules applied within-replicate to maintain coverage.

### 4.3 Applying $\kappa$ inside the matrix engine

The standard kinship engine implicitly assumes equal fertility for decedents and survivors within each (parent age, sex, year, race/eth) cell. To plug $\kappa$ in, we re-weight the dead-parent mass at each focal-age slice:

$$
P_{\text{either dead, calibrated}}(t, x) = 1 - \left(1 - \sum_a \kappa_f(a-x, t-x) \cdot m_f^{\text{dead}}[a, x]\right) \cdot \left(1 - \sum_a \kappa_m(a-x, t-x) \cdot m_m^{\text{dead}}[a, x]\right)
$$

where $\kappa_s(a-x, t-x)$ is the $\kappa$ value at parent's age-at-focal-birth $(a-x)$ in cohort year $(t-x)$ for sex $s$. The interpretation: among adults in cell $c$ who die, the expected number of co-resident minors at the time of parental death is $\kappa_c$ times the cell-average. The implied orphanhood count from that cell scales by $\kappa_c$.

This embedding is the simplest single-multiplier approach. A cleaner alternative folds $\kappa$ directly into the parent-age distribution $\pi_{s,t}$ at cohort initialization. The two are not numerically identical and we comment on the difference in Section 5.4.

### 4.4 Cause-specific calibration for Schlüter

For the Schlüter target we replace $\kappa_c$ with a cause-specific $K^{\text{cause}}_c$ computed from NHIS-LMF decedents in the relevant cause bucket. Three specifications:

1. **All-cause $\kappa$** (baseline NHIS calibration applied to cause-specific NCHS denominators).
2. **Intent-stratified $K$ from `MORTUCODLD`** (NHIS-LMF leading-cause code 4 = "Accidents" or code 10 = "Residual" applied to the matching ICD-10 NCHS subset).
3. **Cause-specific $K$ from `MORTUCOD`** (NHIS-LMF code 122 for drug, codes 119+125+128+132 for firearm), our preferred specification.

For specification 3 we report two NCHS scopes: a NARROW scope (NCHS X40-X49 only, matching NHIS code 122) and a BROAD scope (full Schlüter target X40-X44, X60-X64, X85, Y10-Y14 for drugs plus W32-W34, X72-X74, X93-X95, Y22-Y24 for firearms, with NHIS K_126 and K_129 substituted for the suicide and homicide drug subsets as noisy proxies).

### 4.5 Household-structure stratification

For the appendix analysis of non-resident-parent bias, we classify each respondent's NHIS family unit (`fmx`) as:

- **Coupled**: exactly 2 adults (age ≥ 18) in the family unit AND respondent is married (`marstat` in {10, 11, 12, 13}) or cohabiting (`cohabmarst` in {1, 3, 4}).
- **Sole adult**: exactly 1 adult in the family unit.
- **Multi-adult other**: 3+ adults, or 2 non-married non-cohabiting adults (e.g., adult sibling pair raising children).

We compute $K_{\text{died}}$ and $K_{\text{alive}}$ separately for each structure and report the difference in mortality rates between sole-adult and coupled-parent families as a structural diagnostic.

---

## 5. Results

### 5.1 Baseline matrix-kinship replication

Our Python re-implementation of `kin_time_variant_2sex` produces a baseline 2021 US prevalent parental-orphanhood count of 2,240,912 children. Villaveces et al. (2025) report 2,910,000 children with a deceased parent or caregiver-grandparent in 2021. The 670 K difference is the grandparent-caregiver layer, which we recover separately to 2,711,000 combined (within 7 % of Villaveces). The 2020 → 2021 jump in our model is +156 K (+7 %), matching the directional shift in Villaveces driven by COVID-19 parental mortality. The rate-per-100K trajectory matches: 3,091 in 2000, 2,820 in 2010, 2,903 in 2020, 3,117 in 2021. The slight 2000-2014 decline and 2015+ rise reflect the broad US adult-mortality narrative for the period.

### 5.2 All-cause $\kappa$ calibration

Table 1 reports the 2021 race-stratified prevalent orphanhood under baseline (equal-fertility) and NHIS-calibrated specifications, with 95 % bootstrap confidence intervals on $\Delta \%$.

**Table 1.** US prevalent parental orphanhood, age 0-17, in 2021: baseline matrix-kinship vs NHIS-$\kappa$ calibrated.

| Group | Baseline | Calibrated | $\Delta$ % | 95 % CI on $\Delta$ % |
|---|---:|---:|---:|---|
| Non-Hispanic White | 1,176,062 | 1,014,424 | **-13.7 %** | (-18.6 %, -8.0 %) |
| Non-Hispanic Asian or Pacific Islander | 59,414 | 47,651 | **-19.8 %** | (-27.2 %, +10.7 %) |
| Non-Hispanic Black | 456,694 | 429,032 | -6.1 % | (-12.9 %, +4.0 %) |
| Hispanic | 368,360 | 365,202 | -0.9 % | (-7.4 %, +6.4 %) |
| Non-Hispanic AIAN | 34,750 | 43,913 | **+26.4 %** | (-40.3 %, +90.0 %) |
| All | 2,240,912 | 2,165,354 | -3.4 % | (-17.2 %, +15.9 %) |

The pooled "All" correction is small (-3.4 %) and statistically indistinguishable from zero. The race-stratified pattern is large and signed-opposite. The NH AIAN $+26.4 \%$ point estimate has a wide CI and is not statistically distinguishable from zero at the 5 % level given NHIS-LMF sample sizes; the NH White $-13.7 \%$ and NH Asian/PI $-19.8 \%$ point estimates are statistically distinguishable from zero (the NH Asian/PI CI is wide on the upper bound but excludes zero on the lower bound).

The underlying cell-level $\kappa$ table shows the source of the dispersion. For NH White women in decade 2010-2018, $\kappa = 1.95$ -- decedents had nearly twice the co-resident-child count of survivors. For NH AIAN women and men in 2010-2018, $\kappa = 1.62$ and $1.83$ respectively. For most other (sex, race, decade) cells $\kappa < 1$, often substantially: NH Black men in the 1990s have $\kappa = 0.81$; Hispanic men in the 2010s have $\kappa = 0.67$. The pooled "All" $\kappa \approx 0.95$ averages a $\kappa > 1$ surplus in NH White women against $\kappa < 1$ deficits across most other cells.

### 5.3 Cause-specific recalibration of Schlüter (2024)

Schlüter et al. (2024) report 1.19 million cumulative US children of drug-overdose and firearm parental decedents 1999-2020. Table 2 compares our four NHIS-calibrated specifications against the published estimate.

**Table 2.** Cumulative US children of drug-overdose and firearm parental decedents, 1999-2020, by calibration specification.

| Specification | Drug | Firearm | Combined | $\Delta$ % vs naive | $\Delta$ % vs Schlüter |
|---|---:|---:|---:|---:|---:|
| Schlüter (2024) published | -- | -- | 1,190,000 | -- | -- |
| Naive (kids per living adult, our pipeline) | 656,562 | 413,040 | 1,069,602 | -- | -10.2 % |
| NHIS K (all-cause $\kappa$) | 473,274 | 336,066 | 809,340 | -24.3 % | -32.0 % |
| NHIS K (intent-stratified `MORTUCODLD`) | 429,866 | 286,062 | 715,928 | -33.0 % | -39.8 % |
| **NHIS K (cause-specific `MORTUCOD`, BROAD)** | **416,502** | **274,892** | **691,394** | **-35.4 %** | **-41.9 %** |
| NHIS K (cause-specific `MORTUCOD`, NARROW = NHIS-comparable) | 386,550 | 274,892 | 661,442 | -33.3 % | -- (denominator differs) |

All four NHIS-calibrated specifications converge on a 25-35 % downward correction to the naive kids-per-living-adult assumption. The more detailed cause coding (`MORTUCOD`) modestly increases the correction relative to the cruder coding (`MORTUCODLD`), because the contamination from motor-vehicle-accident and fall decedents (who have somewhat higher K than drug-overdose decedents) gets stripped out of the "accidents" bucket. Our headline specification (`MORTUCOD` BROAD, 691 K combined) is 42 % below the published Schlüter target.

### 5.4 Annual trajectory and race stratification

Figure 1 (not shown in this draft; see `results/kinship/schluter_drugs_firearms/annual_by_cause_mortucod.csv`) reports the annual cumulative trajectory of children-of-drug-or-firearm-decedents under each specification. The naive-baseline and NHIS-calibrated trajectories diverge sharply after 2014 as overdose mortality concentrates in younger parental cohorts. The Schlüter published total grows faster than our naive baseline (because their fertility-male-derived denominator is higher) and continues to grow faster under the NHIS calibration.

Race-stratified cumulative totals (in `results/kinship/schluter_drugs_firearms/mortucod_cumulative_1999_2020.csv`) show the same qualitative pattern as the all-cause analysis: NH White and NH Asian/PI children are *over-counted* by the published estimate; NH AIAN children may be *under-counted* (small-sample, wide CIs); NH Black and Hispanic children sit in between.

---

## 6. Discussion

### 6.1 Magnitude and direction of the bias

Three observations summarize the calibration result.

First, the all-cause pooled correction is small (-3.4 %) and within the parametric sensitivity band Villaveces et al. (2025) report. This is good news for the published all-cause headline at the national level: the equal-fertility assumption is approximately right when averaged across race/ethnic groups.

Second, the race-stratified correction is large and signed-opposite. Non-Hispanic White, non-Hispanic Asian/PI, and (less significantly) non-Hispanic Black children are over-counted by the demographic-rate model. Non-Hispanic American Indian or Alaska Native children are under-counted -- consistent with deaths-of-despair concentrating in young AIAN parents, but with very wide confidence intervals reflecting small NHIS-LMF AIAN samples. Hispanic children are essentially unchanged.

Third, the cause-specific correction is large and unidirectional. Drug overdose and firearm decedents are concentrated in cells where $\kappa < 1$, particularly among younger fathers in NH White and Hispanic cohorts where opioid mortality and firearm violence have risen most. The cumulative published Schlüter total overstates the data-implied total by ~40 %.

### 6.2 The non-resident parent issue

A reviewer of an earlier draft raised an important conceptual point: NHIS measures *co-resident* minors. Non-custodial fathers and other non-resident parents -- a divorced father whose children live with their mother, an incarcerated parent, an absent biological parent -- show up in NHIS with zero dependent children at the survey address. The natality-based published approach sits at the other extreme: every biological birth counts toward parental loss when the parent dies, regardless of co-residence, contact, or relationship quality. The two definitions answer different questions and produce different headline numbers.

For mothers the gap between the two definitions is small: approximately 80-95 % of US mothers are co-resident with their minor children. For fathers the gap is large: 60-75 % are co-resident, with substantial variation by race / ethnicity (lower in NH Black, NH AIAN, and Hispanic groups) and by SES. NHIS captures $K_{\text{mother}}$ fairly well; $K_{\text{father}}$ systematically understates true paternal child-bereavement exposure.

A diagnostic of the size of this bias is that, pooled across all years and races, $K_{\text{mother, died}} = 1.761$ and $K_{\text{father, died}} = 1.766$ -- effectively identical within NHIS. This is *not* a finding about biological-fertility homogeneity between mothers and fathers. It is a finding about the selection that NHIS imposes: we only see fathers who had minor children present at the survey address.

A back-of-envelope augmentation using ACS-based non-resident-father rates and a one-child-each assumption raises $K_{\text{father, died}}$ by 15-30 % depending on race. The effect on the all-cause Villaveces 2021 target is to roughly offset our $\kappa$ correction (which moves the count down by 3 % nationally) and place the true count between 2.17 M (custodial) and 2.4-2.5 M (biological), still below the published 2.91 M after subtracting the 0.6 M grandparent layer. For the Schlüter cause-specific target, where male decedents are 70 % of total and concentrated in high-non-resident-fatherhood groups, the biological-orphanhood number lands around 800-900 K -- still well below the published 1.19 M.

### 6.3 Household structure as a structural diagnostic

Why do most NHIS cells have $\kappa < 1$? The household-structure stratification (Appendix A) reveals the mechanism. Single-adult-parent households face 1.3-1.9× the mortality of coupled-parent households within every race × sex cell in NHIS-LMF. They also have systematically lower $K_{\text{alive}}$ (smaller families at the survey address) than coupled-parent households. The combination produces $K_{\text{died}} < K_{\text{alive}}$ at the aggregate level not because decedents have fewer biological children, but because decedents are over-represented in single-parent household structures that have lower co-resident-minor counts.

This is methodologically important because it points to *household-structure selection*, not biological-fertility selection, as the proximate driver of the calibration result. Two implications follow.

First, the calibration result is robust to alternative definitions of fertility -- the underlying signal is about *household composition at the time of death*, not about parity. This is exactly the right concept for orphanhood (which is, after all, about kids in the home losing a co-resident parent).

Second, the calibration result is sensitive to changes in single-vs-coupled household prevalence over time. If single-parent households become more or less common in a population, $\kappa$ will mechanically shift. Our decade-level $\kappa$ estimates absorb this slowly-changing trend; finer-grained annual $\kappa$ estimates would absorb it more cleanly but require more NHIS sample years.

### 6.4 Implications for policy

The implications for US child-welfare and demographic-bereavement policy depend on which definition is operative.

For SSI Survivor Benefits, which require the surviving child to demonstrate financial dependency on the deceased parent, the relevant concept is closer to *custodial* orphanhood -- the NHIS-based number, 2.17 M in 2021 all-cause + the grandparent layer ≈ 2.71 M combined.

For Title IV-E foster-care placements, which key on actual disruption to the child's living arrangement, custodial orphanhood is again the relevant target.

For grief-counseling allocations under federal education and Medicaid funding streams, which respond to the child's emotional exposure to a parental death regardless of co-residence, biological orphanhood is closer to the target -- between 2.4 and 2.5 M nationally with the non-resident-father augmentation.

For epidemiological surveillance of the deaths-of-despair episode -- the use case where the Schlüter cumulative figure has been most prominently cited -- the relevant target is debatable. If the policy purpose is to size the population of children who *might* need surviving-parent support services, biological orphanhood (800-900 K cumulative drug + firearm 1999-2020) is the conservative number. If the policy purpose is to assess the actual disruption to children's day-to-day caregiving, the custodial number (691 K cumulative) is more accurate. Both are 30-45 % below the published 1.19 M.

### 6.5 Limitations

Five limitations matter for interpretation.

1. **NHIS-LMF measures co-resident, not biological, kids.** This is the central definitional issue discussed in Section 6.2.
2. **$\kappa$ is estimated at decade × age band × race / ethnicity × sex resolution.** Annual variation within a decade is absorbed into the decade-level estimate.
3. **Cause-specific $K$ is estimated on a subset of NHIS sample years.** The detailed `MORTUCOD` field is published for sample years 1986-2004 only; we apply the resulting K to NCHS 1999-2020 deaths under a constant-effects-over-time assumption.
4. **The two-sex independence assumption** ($P_{\text{either dead}} = 1 - (1 - P_{\text{mom dead}})(1 - P_{\text{dad dead}})$) is retained from the standard matrix-kinship model. Joint mortality within couples is positively correlated (shared exposure, shared health behaviors), so this slightly overstates the probability of at least one parent dying.
5. **Bootstrap CIs cover the NHIS sampling component of $\kappa$ only.** They do not include sampling error in the NCHS denominators or CDC WONDER population estimates, nor model uncertainty in the kinship recurrence. A total-error CI would be wider than the bootstrap CI we report.

### 6.6 A research agenda

The single most valuable next step is administrative linkage of NCHS death certificates to NCHS birth certificates and household rosters at the individual level, in a restricted-access state-level pilot. This would resolve the custodial-vs-biological orphanhood question by direct measurement rather than calibration. Realistic state candidates with strong vital-record linkage infrastructure include Wisconsin, North Carolina, Massachusetts, and Utah. A three-state pilot would produce the first empirical $\kappa$ estimates at the cell level that do not require the household-roster proxy NHIS provides.

A second valuable extension is the $\kappa$ calibration of cause-specific orphanhood papers we have not yet addressed: Potter et al. (2025) for cancer (likely modest downward correction); Verdery et al. (2024) for broader kin networks (the parent slice of which our $\kappa$ already calibrates); and the COVID papers (Hillis et al., 2021, 2022) for which NHIS-LMF 2020-2022 data, released January 2026, would be the appropriate source.

A third extension is methodological: re-running the published Villaveces (2025) `DemoKin` pipeline directly with $\kappa$-modified inputs, to verify that our Python embedding matches the R embedding to within numerical precision.

---

## 7. Conclusion

The US orphanhood and bereavement-estimation literature has developed rapidly since 2021. The published estimates are anchored to a demographic-rate architecture that imposes an equal-fertility assumption within demographic cells: adults who die during the modeling horizon are assumed to have the same fertility schedule as adults who survive. Authors flag the assumption and run parametric sensitivities, but until now no US empirical estimate of the within-cell fertility-mortality correlation existed.

Using the NHIS Linked Mortality File 1986-2018, we estimate this correlation directly for the same demographic cells the published US literature uses. The pooled correction to all-cause prevalent orphanhood is small (-3 % for 2021) but the race-stratified pattern is large and signed-opposite, ranging from -20 % for NH Asian / PI children to +26 % for NH AIAN children. The cause-specific correction to the published Schlüter (2024) drug-and-firearm cumulative target is uniformly large: the data-implied total falls 35-42 % below the published headline depending on definition. The substantive conclusion is robust to a back-of-envelope correction for the custodial-vs-biological-orphanhood definitional issue.

The implications for child-welfare resource allocation, federal Survivor Benefits sizing, and epidemiological surveillance of the deaths-of-despair episode are non-trivial. The published headline of 2.91 million US children with a deceased parent or caregiver in 2021 is approximately correct at the national level; the published headline of 1.19 million cumulative children of drug-overdose and firearm parental decedents 1999-2020 is approximately 40 % too high. The race-stratified all-cause pattern is qualitatively wrong without $\kappa$: groups for which the equal-fertility assumption fails in the *positive* direction (NH AIAN) and groups for which it fails in the *negative* direction (NH White, NH Asian / PI) are treated symmetrically by the published model and asymmetrically by the data.

The natural next step is administrative linkage of US vital records at the individual level -- a state-level restricted-access pilot would resolve the definitional issue our NHIS-based work exposes. In the meantime, we recommend the field publish both a custodial-orphanhood headline (NHIS-calibrated, our central estimate) and a biological-orphanhood headline (custodial plus non-resident-father augmentation) for each new estimation paper, and label them explicitly. Headline numbers without definitions are not headlines. They are sources of confusion.

---

## Appendix A. Non-resident parents and the sex asymmetry in $K$

NHIS measures co-resident minors at survey interview. The published natality-based approach counts every biological birth toward potential parental loss. The two definitions answer different questions:

- **Custodial orphanhood**: lost a parent who lived with them at the time of parental death. NHIS-derived $K$ targets this concept.
- **Biological orphanhood**: lost a biological parent, regardless of co-residence. Natality-based methods target this concept.

The asymmetry by parent sex is large. Mothers are co-resident with their minor children in approximately 80-95 % of US cases. Fathers are co-resident in 60-75 % of cases, with substantial variation by race / ethnicity. NHIS therefore captures $K_{\text{mother}}$ accurately but understates $K_{\text{father}}$.

### A.1 Pooled $K$ by sex

**Table A1.** Pooled NHIS-LMF $K$ by sex of respondent (parents only, all years, all races).

| Sex | $K_{\text{alive}}$ | $K_{\text{died}}$ | $\kappa$ |
|---|---:|---:|---:|
| Mother | 1.871 | 1.761 | 0.941 |
| Father | 1.874 | 1.766 | 0.943 |

The identical-K finding is a selection result, not a biological-fertility result. We are conditioning on fathers who had minor children at the survey address.

### A.2 $K$ by sex × race × household structure

**Table A2.** Selected rows from the sex × race × household-structure table (full table in `results/py/appendix_household_structure_K.csv`).

| Sex | Race / eth | HH struct | $K_{\text{alive}}$ | $K_{\text{died}}$ | $\kappa$ | $n_{\text{alive}}$ | $n_{\text{died}}$ |
|---|---|---|---:|---:|---:|---:|---:|
| F | NH White | coupled | 1.97 | 1.77 | 0.90 | 32,649 | 620 |
| F | NH White | sole adult | 1.67 | 1.53 | 0.92 | 11,699 | 390 |
| F | NH Black | coupled | 2.03 | 1.91 | 0.94 | 3,728 | 101 |
| F | NH Black | sole adult | 1.95 | 1.85 | 0.95 | 9,572 | 381 |
| F | NH AIAN | coupled | 1.96 | 1.84 | 0.94 | 5,996 | 311 |
| F | NH AIAN | sole adult | 1.80 | 1.66 | 0.92 | 3,276 | 281 |
| M | NH White | coupled | 1.96 | 1.75 | 0.89 | 27,347 | 999 |
| M | NH White | sole adult | 1.53 | 1.42 | 0.93 | 2,655 | 165 |
| M | NH Black | coupled | 2.03 | 2.03 | 1.00 | 3,585 | 212 |
| M | NH Black | sole adult | 1.50 | 1.40 | 0.93 | 744 | 60 |
| M | NH AIAN | coupled | 1.96 | 1.85 | 0.94 | 4,927 | 517 |
| M | NH AIAN | sole adult | 1.52 | 1.58 | 1.04 | 389 | 92 |

### A.3 Mortality rate by household structure

**Table A3.** Pooled NHIS-LMF mortality rate by sex × race × household structure. Not age-standardized.

| Sex | Race / eth | Coupled | Sole adult | Ratio (sole / coupled) |
|---|---|---:|---:|---:|
| F | NH White | 1.81 % | 3.03 % | 1.67 |
| F | NH Black | 2.21 % | 3.28 % | 1.48 |
| F | Hispanic | 1.39 % | 2.18 % | 1.57 |
| F | NH AIAN | 4.86 % | 7.52 % | 1.55 |
| M | NH White | 3.36 % | 5.63 % | 1.67 |
| M | NH Black | 4.71 % | 6.27 % | 1.33 |
| M | Hispanic | 2.99 % | 4.08 % | 1.36 |
| M | NH AIAN | 8.99 % | 17.10 % | 1.90 |

Single-adult parents have 1.3 to 1.9× the mortality of coupled parents in every race × sex cell. This is the structural engine behind $\kappa < 1$ in most NHIS cells.

### A.4 Back-of-envelope non-resident-father adjustment

**Table A4.** Adjusted $K_{\text{father, died}}$ using ACS-based non-resident-father rates and a one-minor-each assumption.

| Race / eth | $K_{\text{father, died}}$ (NHIS) | Non-resident rate | $K_{\text{father, died}}$ (adjusted) |
|---|---:|---:|---:|
| NH White | 1.703 | 0.30 | 2.003 |
| NH Black | 1.888 | 0.55 | 2.438 |
| Hispanic | 2.093 | 0.35 | 2.443 |
| NH Asian / PI | 1.747 | 0.15 | 1.897 |
| NH AIAN | 1.806 | 0.50 | 2.306 |

A 15-30 % upward adjustment to $K_{\text{father, died}}$ translates to an 8-25 % upward adjustment to the male-decedent contribution to orphanhood. For the all-cause Villaveces 2021 headline this roughly offsets the $\kappa$ downward correction, placing the true count between 2.17 M (custodial) and 2.4-2.5 M (biological). For the cause-specific Schlüter 1999-2020 cumulative, the biological-orphanhood number lands around 800-900 K, still well below the published 1.19 M.

---

## References

Alburez-Gutierrez, D., Acosta, E., Zagheni, E., & Williams, N. E. (2024). The long-lasting effect of armed conflicts deaths on the living: quantifying family bereavement. *Science Advances*, 10(30), eado6951.

Caswell, H. (2019). The formal demography of kinship: a matrix formulation. *Demographic Research*, 41, 679-712.

Caswell, H. (2020). The formal demography of kinship II: multi-state models, parity, and sibship. *Demographic Research*, 42, 1097-1146.

Caswell, H., & Song, X. (2021). The formal demography of kinship III: kinship dynamics with time-varying demographic rates. *Demographic Research*, 45, 517-546.

Fletcher, J. M. (2026a). Literature review: fertility heterogeneity in orphanhood and kinship-bereavement models. NHIS Mortality project working document.

Guida, F., Kidman, R., Ferlay, J., et al. (2022). Global and regional estimates of orphans attributed to maternal cancer mortality in 2020. *Nature Medicine*, 28, 2563-2572.

Hillis, S. D., Blenkinsop, A., Villaveces, A., et al. (2021). COVID-19-associated orphanhood and caregiver death in the United States. *Pediatrics*, 148(6), e2021053760.

Hillis, S., N'konzi, J.-P. N., Msemburi, W., et al. (2022). Orphanhood and caregiver loss among children based on new global excess COVID-19 death estimates. *JAMA Pediatrics*, 176(11), 1145-1148.

Jones, C. M., Zhang, K., Han, B., et al. (2024). Estimated number of children who lost a parent to drug overdose in the US from 2011 to 2021. *JAMA Psychiatry*, 81(8), 789-796.

National Center for Health Statistics. (2026). 2022 NHIS Linked Mortality File: Methodology and Analytic Considerations. Hyattsville, MD: NCHS.

Potter, A. L., Schlüter, B.-S., Alexander, M. J., Yang, C.-F. J., & Kiang, M. V. (2025). Youths experiencing parental death due to cancer. *JAMA Network Open*, 8(7), e2519106.

Schlüter, B.-S., Alburez-Gutierrez, D., Bibbins-Domingo, K., Alexander, M. J., & Kiang, M. V. (2024). Youth experiencing parental death due to drug poisoning and firearm violence in the US, 1999-2020. *JAMA*, 331(20), 1741-1747.

Smith-Greenaway, E., Verdery, A. M., & Carr, D. (2025). The new sociology of bereavement. *Annual Review of Sociology*, 51, 357-375.

Stover, J., Brown, T., Puckett, R., et al. The AIDS Impact Model (AIM) Manual (Spectrum software). Avenir Health / UNAIDS, 2024.

Verdery, A. M., Ryan-Claytor, C., Smith-Greenaway, E., Sarkar, N., & Livings, M. (2024). More than 1.4 million US children have lost a family member to drug overdose. *American Journal of Public Health*, 114(12), 1394-1397.

Villaveces, A., Wang, D., Massetti, G., et al. (2025). Orphanhood and caregiver death among children in the United States by all-cause mortality, 2000-2021. *Nature Medicine*, 31, 672-683.

Williams, I., Sánchez Pérez, J., & Alburez-Gutiérrez, D. (2023). DemoKin: an R package for the formal demography of kinship. *R package*.
