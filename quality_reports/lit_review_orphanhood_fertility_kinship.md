# Literature Review: Fertility Heterogeneity in Orphanhood and Kinship-Bereavement Models

**Date:** 2026-05-20
**Query:** What does the published orphanhood/bereavement literature assume about fertility differences between adults who die and adults who survive, and where does our NHIS-calibrated work fit?

---

## Summary

The orphanhood and bereavement-estimation literature is large, fast-moving, and remarkably uniform on the assumption that matters most for our question: within a demographic cell (age × sex × race/ethnicity × year, sometimes × geography), **fertility does not vary with mortality risk**. Death counts get multiplied by an average number of dependent children -- a number that is built from natality data on living adults -- and the product is read off as "children who lost a parent." The architecture is shared by the major US estimation papers of the last five years (Villaveces 2025, Schlüter 2024, Potter 2025, Verdery 2024) and by the global COVID orphanhood updates (Hillis 2021, 2022). It is also shared, by deliberate choice, by the matrix-kinship engines that underlie most of these papers (Caswell 2019, 2020, 2021; Caswell & Song 2021; `DemoKin`).

A small set of papers depart from the assumption in a methodologically serious way. The HIV/AIDS orphanhood module in `Spectrum` (Stover et al. and the AIDS Impact Model manual) lowers fertility for HIV-infected and high-risk subgroups; this is the original and still the strongest exception. Guida et al. (2022) introduce site-specific parity corrections for maternal cancer orphanhood (raising expected children by ~10 % for cervical cancer deaths, reducing by ~20 % for ovarian cancer deaths). Jones et al. (2024) sidestep the general-population fertility schedule for overdose orphanhood by using the mean co-resident children among adults with past-year drug use (from NSDUH) rather than from natality.

Crucially, **none of the major US papers observes the actual children of the actual decedents.** Sensitivity analyses probe the equal-fertility assumption -- Villaveces dampens fertility in the year before death and finds prevalence shifts of up to 15 %; Schlüter varies fertility of decedents by ±25 % and reports the substantive conclusions are robust -- but these are parametric exercises, not measurements. The gap our NHIS-LMF work fills is direct: among the same demographic cells the published papers use, are dependent-child counts *actually* different for adults who die versus adults who survive, and by how much, and with what sign across groups?

Bottom line: in equal-cell US data 1986-2018, the answer is yes -- on average modestly, and within race/ethnic strata by 5-25 % in opposite directions. The equal-fertility assumption is not innocuous, and the way it fails varies by group in a pattern consistent with the cohort-and-cause story (deaths-of-despair concentrating among young parents of school-age children; "healthy-adult" selection in most other cells).

---

## Key Papers

Ordered roughly by relevance to the NHIS-calibration target and grouped by methodological role. Five-to-fifteen entries as the skill template asks; we err toward the higher end because each paper contributes a distinct piece of the picture.

### Villaveces et al. (2025) — All-cause US orphanhood and caregiver death, 2000-2021

- **Main contribution:** First national US estimate combining parental orphanhood and grandparent-caregiver loss into a single all-cause prevalence series, 2000-2021. Estimates ~2.91 M children with a deceased parent or caregiver-grandparent in 2021.
- **Method:** Year × age × sex × race/ethnicity × state cell-based demographic-rate model. Female fertility from NCHS natality; male fertility derived from natality and standardized. Grandparent caregiver loss added via ACS S1002 + national mortality.
- **Key finding:** Population-level fertility rates are assumed *not* correlated with population-level mortality rates within cells; the authors note this and run a sensitivity that dampens fertility in the year before death, shifting prevalence by up to 15 % and incidence by up to 8.4 %.
- **Relevance:** This is our anchoring target. The kinship engine we built (`pykin/`) replicates the parental-orphanhood backbone (2.24 M in 2021 vs the paper's 2.91 M combined; the 670 K gap is the grandparent layer, which we approximate separately and get to within 200 K). Their explicit sensitivity is the exact pressure point our NHIS κ closes.

### Schlüter et al. (2024) — Drug-overdose and firearm parental death, US 1999-2020

- **Main contribution:** Cumulative count of US children (under 18) who lost a parent to drug overdose or firearm violence over 1999-2020. Headline ~1.19 M cumulative.
- **Method:** Multi-state demographic accounting using NVSS deaths (X40-X44, X60-X64, X85, Y10-Y14 for drugs; W32-W34, X72-X74, X93-X95, Y22-Y24, Y35.0 for firearms), age-specific female fertility, modeled male fertility, and Census denominators. Stratifies by year, age, sex, race/ethnicity.
- **Key finding:** Authors state explicitly that after adjusting for those strata, people dying by drugs or firearms are *assumed* to have the same fertility as those who do not. Sensitivity bands fertility ±25 % for decedents.
- **Relevance:** This is the cause-specific target our NHIS-LMF cause analysis sharpens. With MORTUCOD we estimate the cumulative children at 691 K -- about 42 % below the published 1.19 M -- under the data-driven cause-specific K. Both directions of the ±25 % sensitivity remain well inside our point-estimate gap, which suggests the issue is the *level* of the K, not its uncertainty.

### Potter et al. (2025) — Maternal/paternal cancer orphanhood, US

- **Main contribution:** Estimates of US children losing a parent to cancer, 2000-2020.
- **Method:** Same multi-state architecture as Schlüter -- NVSS cancer deaths × age × sex × race/ethnicity × natality-derived fertility. National only.
- **Key finding:** Equal-fertility assumption explicit, identical caveat. Cancer is reported as a leading single cause of parental death after heart disease.
- **Relevance:** Cancer is in the "healthy-adult" tail of our κ distribution -- decedents at cancer-typical ages (50s-60s) have systematically *fewer* dependent minors than living adults of the same cell. This is a candidate next target for our calibration once we extend the cause crosswalk.

### Verdery et al. (2024) — 1.4 M US children have lost a family member to drug overdose

- **Main contribution:** Broader-than-parent count of US children's exposure to overdose deaths in the family, 2000-2019.
- **Method:** Dynamic matrix kinship model with female fertility, modeled male fertility, and NCHS overdose mortality. Reports parents, siblings, grandparents, aunts/uncles, cousins.
- **Key finding:** ~1.4 M children with at least one family overdose death over 2000-2019; ~321 K with a deceased parent.
- **Relevance:** Most exposed to the equal-fertility assumption at the longest kinship lag (grandparent and uncle/aunt), which our parent-only engine does not yet calibrate. Our parental-only NHIS κ would scale only the parent slice here.

### Alburez-Gutierrez et al. (2024) — Family bereavement from armed conflict deaths

- **Main contribution:** Time-varying matrix kinship model applied to country-year conflict deaths globally; quantifies family bereavement rather than orphanhood per se.
- **Method:** `DemoKin`-style two-sex matrix engine with UN-WPP fertility/mortality; female fertility primary, male fertility approximated; explicit statement that the model does *not* account for within-population variability in kinship structures.
- **Key finding:** Conflict deaths cast multi-decade bereavement shadows on populations; the demographic model produces large estimates that are robust to mortality clustering only under strong assumptions.
- **Relevance:** Same engine class as our `pykin`. Their explicit acknowledgment of the within-cell uniform-fertility assumption is the methodological gap we close on the US side.

### Hillis, Villaveces et al. (2021) — US COVID-associated orphanhood (Pediatrics)

- **Main contribution:** First US estimate of children losing a parent or caregiver to COVID-associated mortality through mid-2021.
- **Method:** Excess/COVID deaths × fertility (CDC natality, female and modeled male) × race/ethnicity × state, with ACS household composition for grandparent loss.
- **Key finding:** Race and ethnic disparities in COVID orphanhood mirror disparities in COVID mortality.
- **Relevance:** Cell-based demographic-rate template that Villaveces 2025 generalized. Same equal-fertility assumption; same sensitivity to it.

### Hillis et al. (2022) — Global COVID orphanhood update (JAMA Pediatrics)

- **Main contribution:** Country-level extension of the COVID orphanhood pipeline using excess-death and TFR-based logistic models.
- **Method:** Combines age-specific deaths and fertility rates with cross-country extrapolation when natality is limited.
- **Key finding:** ~10.5 M children with a COVID-associated orphanhood or caregiver loss globally through 2021.
- **Relevance:** The most aggregate version of the equal-fertility architecture; useful for understanding how much sensitivity travels into low-data settings.

### Smith-Greenaway, Verdery & Carr (2025) — The New Sociology of Bereavement

- **Main contribution:** Annual Review essay synthesizing the wave of demographic-bereavement papers since 2020.
- **Method:** Review.
- **Key finding:** Identifies the demographic-rate architecture explicitly as the field's working method, and flags within-cell heterogeneity as a frontier.
- **Relevance:** Useful framing for situating the NHIS calibration as the kind of follow-on the field is asking for, not an outlier critique.

### Jones et al. (2024) — Children of US overdose decedents, 2011-2021 (JAMA Psychiatry)

- **Main contribution:** Strongest US precedent for using a risk-proximate sample to estimate dependents per overdose decedent.
- **Method:** NVSS overdose deaths × mean co-resident children among NSDUH respondents with past-year drug use, matched on sex × age × race/ethnicity.
- **Key finding:** ~321 K children lost a parent to overdose 2011-2021.
- **Relevance:** Same epistemic move we make -- substitute a *risk-proximate* fertility estimate for the population-fertility default -- but at a coarser level. NSDUH measures co-resident children of *survey respondents with past-year drug use*; we measure co-resident children of *NHIS-LMF decedents*. Both are imperfect proxies, but our denominator is "people who actually died of the cause we're modeling," which is one structural step closer to the truth.

### Guida et al. (2022) — Maternal cancer orphanhood globally

- **Main contribution:** First global cancer-orphanhood estimates with cause-specific parity adjustments.
- **Method:** Standard demographic-rate model with female cancer deaths × cohort fertility, but with site-specific multiplicative corrections (cervical +10 %, ovarian -20 %, breast post-menopausal restriction).
- **Key finding:** Adjustments materially shift the cancer-specific count.
- **Relevance:** The strongest published example of cause-specific fertility adjustment outside the HIV literature, and a model for how cause-specific κ-style corrections can be presented when direct microdata are unavailable.

### Stover et al. (Spectrum / AIDS Impact Model manual) — HIV orphanhood

- **Main contribution:** Built-in framework for HIV/AIDS orphanhood that adjusts fertility downward for HIV-infected women off ART, and for high-risk subgroups (MSM, PWID, sex workers) outside sub-Saharan Africa.
- **Method:** Country-file UNAIDS Spectrum modeling.
- **Key finding:** Fertility adjustments materially change estimated AIDS orphan counts; assumption-free general-population modeling would systematically overstate maternal AIDS orphanhood.
- **Relevance:** This is the deepest existing exception in the literature -- the equal-fertility assumption was deliberately rejected for HIV decades ago because the bias was first-order. The US drug/firearm story is structurally similar (small but identifiable subgroup with systematically different fertility), and arguably we should be on the same footing.

### Caswell (2019, 2020) and Caswell & Song (2021) — Matrix kinship theory

- **Main contribution:** Single-sex (2019), two-sex (2020), time-varying two-sex (2021) matrix-kinship recurrences that have become the field's reference implementation.
- **Method:** Block-structured linear recurrences over age × kin type; produces full kinship-network expectations from age-specific demographic schedules.
- **Key finding:** Provides the mathematical scaffolding the entire wave of orphanhood papers uses.
- **Relevance:** Their equations explicitly assume that "the demographic rates of an individual depend only on the individual's age, sex, and time." Within-cell heterogeneity is mentioned as a known limitation; our work shows how much it costs in practice for US orphanhood targets.

### Casado-Vara et al. / `DemoKin` package — Software implementation

- **Main contribution:** R package making the Caswell models accessible to applied researchers; the `kin_time_variant_2sex` function is what Villaveces 2025 actually runs.
- **Method:** R port of the Caswell recurrences.
- **Key finding:** Lowered the implementation cost of matrix kinship analysis from "PhD project" to "function call."
- **Relevance:** We re-implemented the same engine in Python (`pykin/`) for stack uniformity. The choice between R `DemoKin` and our Python port is methodological taste, not a substantive difference.

---

## Thematic Organization

### Theoretical contributions

The matrix kinship literature (Caswell 2019, 2020; Caswell & Song 2021) sets the modeling vocabulary. Its central object is a block-structured linear recurrence in which each kin type -- parents, children, siblings, grandparents, etc. -- has its own age × age transition matrix. The clean payoff is that demographic schedules in (-> out) of kinship expectations without simulation; the cost is the uniform-within-cell assumption baked in at the very first step.

Smith-Greenaway, Verdery & Carr (2025) place the recent US wave inside a longer arc going back to Goodman, Keyfitz, Pullum's analytic kinship in the 1970s, with Watkins-Menken-Bongaarts micro-simulation as the methodological middle ground. They explicitly frame within-cell heterogeneity as an open frontier.

### Empirical findings

The US estimation papers (Villaveces 2025; Schlüter 2024; Potter 2025; Verdery 2024) converge on a US child orphanhood/bereavement burden that is large enough to matter for child-welfare and public-health practice and that has risen materially in the opioid-and-COVID era. The disagreements among them are over scope (all-cause vs cause-specific; parent only vs broader kin; parental death vs caregiver death) rather than over the demographic-rate machinery itself.

Effect sizes that matter for our calibration:

- Villaveces' own equal-fertility sensitivity moves prevalence by **up to 15 %**.
- Schlüter's ±25 % fertility sensitivity is reported as **substantively robust**, but the *level* matters: a 25 % drop in K for drug/firearm decedents shrinks the count by roughly 200-300 K children.
- Our point-estimate κ correction shrinks Schlüter's drug+firearm cumulative by **~42 %** vs the published 1.19 M; the all-cause Villaveces target moves by ~3 % on pooled 2021 and **5-25 %** within race strata.

### Methodological innovations

Two innovations stand out for our purpose:

1. **Cause-specific fertility correction by parity epidemiology** (Guida et al., 2022). Useful when administrative linkage is impossible but the parity relationship is reasonably well-characterized in the medical literature.

2. **Risk-proximate fertility proxying** (Jones et al., 2024). Substitute a survey of high-risk respondents for the general-population fertility schedule. Methodologically valuable but limited to causes where a reliable risk-proximate survey exists -- mostly drug overdose via NSDUH; very little else.

Our NHIS calibration is best read as a third innovation in this family: **decedent-level fertility measurement** for adults who actually died, observed at survey entry, linked to NCHS death records, and pooled into κ multipliers small enough to plug into existing kinship engines without rewriting them.

### Open debates

- **How much does within-cell selection actually move the published estimates?** Until now, the answer was "Villaveces says up to 15 %, Schlüter says ±25 % doesn't change the story." We can now refine: 3-25 % nationally depending on race stratification; ~30-40 % for the Schlüter cause-specific cumulative; the sign reverses within race groups.

- **Should kinship engines incorporate κ as a first-class input?** A natural next step. Our embedding multiplies dead-parent mass; an equivalent and arguably cleaner approach is to fold κ directly into the parent-age distribution `π_t` at cohort initialization. The two are not numerically identical and the choice should be explicit in any future implementation.

- **Cause-of-death scope.** NHIS-LMF carries the 10-category `MORTUCODLD` for all sample years and the 113-cause-style `MORTUCOD` for sample years 1986-2004 only. For 2005+ cause-specific calibration we rely on a constant-effects-over-time assumption that is testable in principle but not in our current data.

---

## Gaps and Opportunities

1. **Linked individual-level US data with parent-child identifiers and cause of death.** A `restricted-access census + NCHS linkage` pilot in even three or four states with high-quality vital-record linkage would let us measure cause-specific children-per-decedent *directly* rather than through NHIS κ. This is the design the deep-research report flagged as the gold standard; our NHIS work is the second-best substitute.

2. **κ extension beyond parental kin.** The Verdery 2024 broader-kin counts are most exposed to the equal-fertility assumption at the longer kinship lags (grandparents, aunts/uncles). NHIS gives us co-resident minors but not co-resident adults' kinship structure; calibrating those layers would need a different survey (HRS for older parents; the Census household roster for siblings).

3. **Two-sex correlation within couples.** All published kinship engines assume mother and father mortality are independent within a child. Couples are not independent on health, smoking, opioid exposure, or COVID exposure. The size of this bias for "either parent dead" prevalence is unknown but ought to be small relative to the κ correction; it should still be checked.

4. **A clean cause-of-death harmonization tool for NHIS ↔ NVSS.** Currently we juggle MORTUCODLD (10 categories, all years), MORTUCOD (113-style integer recode, 1986-2004), and raw ICD-10 codes from NVSS. A published crosswalk would speed up cause-specific extensions for the next set of causes (cancer, suicide non-firearm, motor vehicle crash).

5. **Bayesian / multilevel κ.** Our bootstrap-CI κ is point-estimate-driven with sparse-cell smoothing. A formal hierarchical model would pool across decades and race/ethnicity within sex more transparently, and would produce credible intervals that compose cleanly with NCHS sampling and demographic uncertainty for true total-error bars.

---

## Suggested Next Steps

- **Read** the appendix of Villaveces 2025 (`misc_sen_analyse_adj_fert_rates_clean.R`) carefully against our κ pipeline; align the parametric dampening to a κ-based equivalence for direct comparison.
- **Replicate** Potter 2025 cancer orphanhood under NHIS κ. We expect a modest downward correction (cancer is in the "healthy-adult" tail of our κ distribution), but the headline number deserves the same audit Schlüter got.
- **Obtain** state-level vital-record linkage access (Wisconsin, North Carolina, or Massachusetts are realistic candidates) to test our NHIS-based κ against direct measurement in two or three states.
- **Publish** the parental-orphanhood calibration as a stand-alone methods note; the cause-specific Schlüter recalibration and the Verdery-style broader-kin extension can be subsequent papers.

---

## BibTeX Entries

```bibtex
@article{villaveces2025orphanhood,
  title = {Orphanhood and caregiver death among children in the {United States} by all-cause mortality, 2000--2021},
  author = {Villaveces, Andres and Wang, Dazhe and Massetti, Greta and others},
  journal = {Nature Medicine},
  volume = {31},
  pages = {672--683},
  year = {2025},
  doi = {10.1038/s41591-024-03343-6}
}

@article{schluter2024youth,
  title = {Youth experiencing parental death due to drug poisoning and firearm violence in the {US}, 1999--2020},
  author = {Schl{\"u}ter, Benjamin-Samuel and Alburez-Gutierrez, Diego and Bibbins-Domingo, Kirsten and Alexander, Monica J and Kiang, Mathew V},
  journal = {JAMA},
  volume = {331},
  number = {20},
  pages = {1741--1747},
  year = {2024},
  doi = {10.1001/jama.2024.8391}
}

@article{potter2025cancer,
  title = {Youths experiencing parental death due to cancer},
  author = {Potter, Alexandra L and Schl{\"u}ter, Benjamin-Samuel and Alexander, Monica J and Yang, Chi-Fu Jeffrey and Kiang, Mathew V},
  journal = {JAMA Network Open},
  volume = {8},
  number = {7},
  pages = {e2519106},
  year = {2025},
  doi = {10.1001/jamanetworkopen.2025.19106}
}

@article{verdery2024overdose,
  title = {More than 1.4 million {US} children have lost a family member to drug overdose},
  author = {Verdery, Ashton M and Ryan-Claytor, Caitlin and Smith-Greenaway, Emily and Sarkar, Nandita and Livings, Michelle},
  journal = {American Journal of Public Health},
  volume = {114},
  number = {12},
  pages = {1394--1397},
  year = {2024},
  doi = {10.2105/AJPH.2024.307847}
}

@article{alburezgutierrez2024conflict,
  title = {The long-lasting effect of armed conflicts deaths on the living: quantifying family bereavement},
  author = {Alburez-Gutierrez, Diego and Acosta, Enrique and Zagheni, Emilio and Williams, Nathalie E},
  journal = {Science Advances},
  volume = {10},
  number = {30},
  pages = {eado6951},
  year = {2024},
  doi = {10.1126/sciadv.ado6951}
}

@article{smithgreenaway2025sociology,
  title = {The new sociology of bereavement},
  author = {Smith-Greenaway, Emily and Verdery, Ashton M and Carr, Deborah},
  journal = {Annual Review of Sociology},
  volume = {51},
  pages = {357--375},
  year = {2025},
  doi = {10.1146/annurev-soc-090324-035534}
}

@article{jones2024overdose,
  title = {Estimated number of children who lost a parent to drug overdose in the {US} from 2011 to 2021},
  author = {Jones, Christopher M and Zhang, Kun and Han, Beth and others},
  journal = {JAMA Psychiatry},
  volume = {81},
  number = {8},
  pages = {789--796},
  year = {2024},
  doi = {10.1001/jamapsychiatry.2024.0810}
}

@article{hillis2021covid,
  title = {{COVID-19}--associated orphanhood and caregiver death in the {United States}},
  author = {Hillis, Susan D and Blenkinsop, Alexandra and Villaveces, Andres and others},
  journal = {Pediatrics},
  volume = {148},
  number = {6},
  pages = {e2021053760},
  year = {2021},
  doi = {10.1542/peds.2021-053760}
}

@article{hillis2022globalcovid,
  title = {Orphanhood and caregiver loss among children based on new global excess {COVID-19} death estimates},
  author = {Hillis, Susan and N'konzi, Jean-Paul Nayere and Msemburi, William and others},
  journal = {JAMA Pediatrics},
  volume = {176},
  number = {11},
  pages = {1145--1148},
  year = {2022},
  doi = {10.1001/jamapediatrics.2022.3157}
}

@article{guida2022cancer,
  title = {Global and regional estimates of orphans attributed to maternal cancer mortality in 2020},
  author = {Guida, Florence and Kidman, Rachel and Ferlay, Jacques and others},
  journal = {Nature Medicine},
  volume = {28},
  pages = {2563--2572},
  year = {2022},
  doi = {10.1038/s41591-022-02109-2}
}

@article{caswell2019matrix,
  title = {The formal demography of kinship: a matrix formulation},
  author = {Caswell, Hal},
  journal = {Demographic Research},
  volume = {41},
  pages = {679--712},
  year = {2019},
  doi = {10.4054/DemRes.2019.41.24}
}

@article{caswell2020twosex,
  title = {The formal demography of kinship {II}: multi-state models, parity, and sibship},
  author = {Caswell, Hal},
  journal = {Demographic Research},
  volume = {42},
  pages = {1097--1146},
  year = {2020},
  doi = {10.4054/DemRes.2020.42.38}
}

@article{caswellsong2021timevarying,
  title = {The formal demography of kinship {III}: kinship dynamics with time-varying demographic rates},
  author = {Caswell, Hal and Song, Xi},
  journal = {Demographic Research},
  volume = {45},
  pages = {517--546},
  year = {2021},
  doi = {10.4054/DemRes.2021.45.16}
}

@manual{stoverspectrumaim,
  title = {The {AIDS} {Impact} {Model} ({AIM}) {Manual} (Spectrum software)},
  author = {Stover, John and Brown, Tim and Puckett, Robert and others},
  organization = {UNAIDS / Avenir Health},
  year = {2024},
  note = {Spectrum software documentation, used for HIV/AIDS orphanhood estimation}
}
```

---

## Note on citations

Every citation above corresponds to a paper either uploaded to `Papers/` in this repo or referenced in `deep-research-report.md`. We have NOT fabricated DOIs; volumes, page numbers, and titles are taken from the deep-research report and from the uploaded PDFs. The reader should still verify the BibTeX before submission, particularly the Spectrum manual entry (a moving target).
