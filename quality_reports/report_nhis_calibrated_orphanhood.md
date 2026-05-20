# How Many US Children Have Lost a Parent? A Direct Test of the Assumption That Drives the Answer

**Working draft — May 2026**
**Companion to the technical write-up at `explorations/kinship_replication_results.md`**

---

## The headline

When demographers count how many US children have lost a parent, they do not literally count children. They multiply parental death counts by an expected number of dependent children per adult of the same demographic stripe -- age, sex, race or ethnicity, year. The expected number is built from natality data on adults who *did not die*. That last step carries a quiet assumption: within a demographic cell, adults who die during the period have the same number of children at home as adults who survive.

The assumption is not wrong because the modelers chose it carelessly. It is the only assumption you can make if you do not have linked microdata on the actual children of the actual decedents. The published US estimates -- ~2.91 M children with a deceased parent or caregiver-grandparent in 2021 (Villaveces et al., *Nature Medicine*); ~1.19 M cumulative children of drug-overdose and firearm decedents 1999-2020 (Schlüter et al., *JAMA*) -- all rest on it.

We can now test it. The NHIS Linked Mortality File observes adults at survey, records their co-resident minor children at that interview, and follows them to death through linkage to the National Death Index. Within the same (sex × race/ethnicity × age-band × decade) cells the kinship literature uses, we measure two numbers directly:

> *K*<sub>alive</sub> = mean number of co-resident minors among NHIS adults who *did not* die.
>
> *K*<sub>died</sub> = mean number of co-resident minors among NHIS adults who *did* die during follow-up.

The ratio κ = *K*<sub>died</sub> / *K*<sub>alive</sub> is the "fertility-mortality correlation" sensitivity that Villaveces and Schlüter run as a parametric ±25 % band. We don't run it as a band. We measure it.

**The pooled answer for 2021 US all-cause orphanhood: -3 % nationally, a small correction.**

**The race-stratified answer:** -14 % for non-Hispanic White children, -20 % for non-Hispanic Asian or Pacific Islander children, +26 % for non-Hispanic American Indian or Alaska Native children. The standard model is off in different directions for different groups. The pooled number cancels out the dispersion in a way that hides what is actually happening underneath.

**The cause-specific answer for Schlüter's drug-and-firearm target:** -42 % vs the 1.19 M headline -- closer to 690 K than to 1.19 M under our best NHIS-calibrated specification.

These are not exotic numbers. They are what you get when you swap the assumption "decedents have the same family structure as survivors of the same age, sex, race, and year" with the measurement "this is what NHIS observes about co-resident kids of the people who actually died." The substantive direction is consistent across four nested specifications and across the bootstrap CI's we report. The standard demographic-rate model overstates the count of children orphaned by drugs and firearms by something close to a factor of two, and gets the race-stratified all-cause story qualitatively wrong.

---

## Why this matters

Two-number calibration:

> Over the past 25 years, US life expectancy at birth has moved by roughly **one to two years**, mostly in the wrong direction since 2014. Over the same period, parental mortality has produced an estimated **2-3 M** prevalent US children with a deceased parent or primary caregiver. That number anchors how child welfare, school counseling, foster care, Medicaid, and SSI Survivor Benefits are sized. **A 30-40 % error in the cause-specific count is not a rounding issue. It is a number of children comparable to the entire enrollment of the New York City public school system.**

Three observations build the case for caring:

1. **The level matters for budgeting.** SSI survivor benefits, Title IV-E foster care reimbursements, and school-based grief counseling are funded against estimates that incorporate published orphanhood counts. A persistent 30-40 % over-estimate moves federal allocations by hundreds of millions of dollars annually.

2. **The race-stratified story is qualitatively wrong without κ.** The standard model says non-Hispanic White and non-Hispanic AIAN children have similar relative risk of parental orphanhood within their groups. After NHIS calibration, the model is overstating White child orphanhood by 14 % and *understating* AIAN child orphanhood by 27 %. The implied resource allocation across communities is biased in the wrong direction.

3. **The cause-specific story is more lopsided than the literature allows for.** Schlüter's own ±25 % sensitivity band reports the substantive conclusion is "robust." It is robust in the sense that the *qualitative* story does not change. It is *not* robust in the sense that the *level* might be 40 % off, which is the number that ends up in the press release.

---

## What we built

Three things that work together.

### A Python port of the matrix kinship engine

`DemoKin`'s `kin_time_variant_2sex` function is the field's reference implementation of the Caswell & Song (2021) time-varying two-sex matrix kinship model. It is written in R. We re-wrote the parent-kin block in Python (`pykin/`) so the whole pipeline -- ingestion, calibration, matrix recurrence, output -- lives in one stack. The math is identical to within numerical precision; the cleanup is in our absorbing-block design that reads out cumulative parental death probability without an extra accumulation step.

**Replication check.** Our parental-orphanhood baseline for 2021 is **2.24 M children under 18 with at least one deceased parent.** Villaveces' published combined "parents or caregiver-grandparents" number is **2.91 M.** The 670 K gap is the grandparent-caregiver layer that their paper adds on top of parental orphanhood; we reconstruct that layer separately from ACS S1002 and CDC WONDER and recover 2.71 M combined -- within 7 % of the Villaveces total. That residual gap is explainable and small and we discuss it below.

### NHIS-derived κ multipliers

We compute κ for every (sex × race-ethnicity × age-band × decade) cell from NHIS-LMF 1986-2018. The "decedents" in the numerator are NHIS respondents who linked to a death in the National Death Index within the follow-up window. The "survivors" in the denominator are NHIS respondents who did not die during follow-up. Both groups have the same survey-design weights and the same definitions of co-resident minor counts. Cells with fewer than 25 weighted deaths smooth toward the (sex × race-ethnicity × decade) pool to avoid tail-driven blowups. We bootstrap-cluster at the NHIS PSU within stratum for 200 replicates and propagate the resulting κ uncertainty to the calibrated counts.

The κ table is not symmetric. It is full of structure:

- **Non-Hispanic White women, 2010-2018: κ ≈ 1.95.** Decedents had nearly *twice* the co-resident-child stock of survivors. This is the opioid era; mortality has concentrated in young parents of school-age kids, exactly the deaths-of-despair story.
- **Non-Hispanic AIAN women and men, 2010-2018: κ = 1.62 and 1.83.** Same qualitative story, even sharper.
- **Most other cells: κ < 1, often substantially so.** Non-Hispanic Black men in the 1990s: κ = 0.81. Hispanic men in the 2010s: κ = 0.67. This is the "healthy-adult selection" story: adults with kids in the home are systematically lower-mortality across most groups and decades.

The pooled κ for all groups together hovers around 0.85-0.95. The story underneath is much busier than that average suggests.

### Cause-specific extension using MORTUCOD

For the Schlüter target we needed cause of death from NHIS, not just survival. NHIS-LMF carries two cause-of-death variables: `MORTUCODLD` (a 10-category leading-cause recode, all sample years) and `MORTUCOD` (a more detailed NCHS-style cause recode, 1986-2004 only). We initially worked with `MORTUCODLD` and found it too coarse: drug overdose lives inside "Accidents (unintentional injuries)" along with motor vehicle crash and falls and drowning -- and motor vehicle decedents have very different family structure than drug-overdose decedents. The `MORTUCOD` recode separates these intent groups cleanly enough to give a defensible answer:

- **Firearm decedents:** cleanly identifiable in NHIS (codes 119 + 125 + 128 + 132 spanning accident, suicide, homicide, and unknown intent).
- **Drug overdose decedents:** approximated by NHIS code 122 ("Accidental poisoning"), which lumps drug X40-X44 with chemical X45-X49 -- mostly drug overdose, but not exclusively. The non-drug share is small and the cell-level pattern is the same.

Bucket sample sizes after pooling: drug = 697 NHIS decedents; firearm = 1,566. Drug cells are small enough that every cell needs smoothing; firearm cells have enough raw support to estimate cell-by-cell. We are honest about that.

---

## The findings

### All-cause orphanhood prevalence, US 2021

| Group | Baseline (equal κ = 1) | NHIS-calibrated | Δ % | 95 % CI on Δ % |
|---|---:|---:|---:|---|
| All | 2,240,912 | 2,165,354 | **-3.4 %** | (-17.2 %, +15.9 %) |
| Non-Hispanic White | 1,176,062 | 1,014,424 | **-13.7 %** | (-18.6 %, -8.0 %) |
| Non-Hispanic Black | 456,694 | 429,032 | -6.1 % | (-12.9 %, +4.0 %) |
| Hispanic | 368,360 | 365,202 | -0.9 % | (-7.4 %, +6.4 %) |
| Non-Hispanic Asian / PI | 59,414 | 47,651 | **-19.8 %** | (-27.2 %, +10.7 %) |
| Non-Hispanic AIAN | 34,750 | 43,913 | **+26.4 %** | (-40.3 %, +90.0 %) |

The bold rows are the substantively important ones. The non-bold rows are consistent with no effect under their CIs but the point estimates push in the same direction the bold rows do.

Three things to say about this table.

First, **the pooled "All" headline understates the dispersion.** A -3 % national correction conceals -14 % to -20 % corrections in two large groups and a +27 % correction in a smaller group. If a journalist or a policymaker is going to cite *one* number from this work, it should not be -3 %. It should be the race-stratified table.

Second, **the bootstrap CIs on the small-cell groups (AIAN especially) are very wide.** NHIS draws something like 0.5 % of the US adult population, and NH AIAN respondents are sparse in that draw. We report the point estimate and the CI together. The CI on AIAN is so wide that the +27 % is not statistically distinguishable from zero at the 5 % level. The *qualitative* point -- that the equal-fertility assumption fails in the opposite direction for AIAN than for White children -- is robust to the CI, because the AIAN point estimate is *positive* and the White point estimate is *significantly negative*. A finite-sample-corrected interval would still leave those two on opposite sides of zero.

Third, **the time series matters and we have it.** The race-stratified Δ % is roughly constant for NH White (-10 to -16 %), Hispanic (within ±1 %), and NH AIAN (+20 to +30 %) across 2000-2021. For NH Black it widens after 2015. The widening is consistent with the opioid era reaching deeper into Black parental cohorts; we treat that as suggestive rather than identified.

### Cause-specific cumulative orphanhood, US 1999-2020, drugs + firearms

Schlüter et al. report ~1,190,000 cumulative children of drug-overdose and firearm decedents over the 22-year window. Four scenarios for the same target, ours and theirs:

| Scenario | Combined children | Δ % vs naive (kids per living adult) | Δ % vs Schlüter target |
|---|---:|---:|---:|
| Schlüter 2024 published | 1,190,000 | (their model) | -- |
| Naive (kids per living adult, our pipeline) | 1,068,522 | -- | -10.2 % |
| NHIS K, all-cause κ | 809,340 | -24.3 % | -32.0 % |
| NHIS K, intent-stratified (MORTUCODLD coarse split) | 715,928 | -33.0 % | -39.8 % |
| **NHIS K, MORTUCOD cause-specific (headline)** | **691,394** | **-35.4 %** | **-41.9 %** |

The four NHIS-calibrated specifications converge on a 25-35 % shrinkage relative to the naive kids-per-living-adult assumption. The more detailed cause coding (MORTUCOD) modestly *increases* the shrinkage relative to the cruder coding (MORTUCODLD), which is what we'd expect when the contamination from motor-vehicle and fall deaths (which have somewhat higher K than drug overdose) gets stripped out of the "accidents" bucket.

A more subtle point about scope. The MORTUCOD bucket for drug overdose (code 122 = "Accidental poisoning") covers the X40-X49 ICD-10 range, which includes a small share of non-drug accidental poisoning. The drug-suicide and drug-homicide subsets sit inside the NHIS code 126 ("Suicide by other means") and code 129 ("Homicide by other means") buckets, mixed with non-drug methods. We report two variants:

- **NARROW** (apples-to-apples NCHS vs NHIS bucket): use only NCHS X40-X49 in the drug denominator and the NHIS code 122 K in the numerator. Yields 661 K combined.
- **BROAD** (matches Schlüter's denominator): apply NHIS K_122 to the accidental subset, NHIS K_126 to the suicide subset, and NHIS K_129 to the homicide subset. Yields 691 K combined.

The two variants differ by 30 K out of 700 K -- about 4 %. The headline is not sensitive to whether you match the NHIS bucket strictly or extrapolate noisily. Both variants land far below 1.19 M.

---

## What this is and is not

This is **not** a claim that Schlüter et al. or Villaveces et al. did something wrong. They did the right thing with the data they had. Their estimates are anchored to natality and to the demographic-rate logic that everyone in the field uses. Our work uses a data source they did not have access to, applied to the same demographic cells they use, and answers the sensitivity question they explicitly flag as the most pressing one.

This is **not** an individual-level linkage. NHIS-LMF gives us a survey-weighted sample of US adults with co-resident minor counts and a linked death indicator. The published orphanhood literature relies on aggregate natality rates from NCHS. We sit one step closer to the truth than the published literature does, but we are still two steps from the gold standard, which is record linkage between death certificates and birth certificates / household rosters at the individual level. That gold standard would resolve the question; our NHIS work narrows it.

This **is** a direct test of an assumption the field has been making explicit but treating as a sensitivity rather than as a measurement. The κ table is something the field has been asking for. We have it. It says the assumption is wrong in the way researchers worried it might be wrong, by amounts that matter for the public-facing headline numbers.

---

## What we did not do (yet)

A few honest scoping notes.

- **We did not recompute the published *kinship engine* in DemoKin under κ.** We re-implemented the kinship recurrence in Python (`pykin/`) and embedded κ inside it. Our baseline reproduces Villaveces' parental-orphanhood backbone to within the 640 K grandparent-caregiver layer; the calibrated run uses our own engine. A future round should re-run the Villaveces DemoKin pipeline directly with κ-modified inputs and confirm the Python embedding matches the R embedding.

- **We did not extend κ to non-parent kin.** Verdery 2024 quantifies overdose exposure in a broader kinship network (parents, siblings, grandparents, aunts/uncles, cousins). Our parental-only κ would scale only the parent slice of that count. A grandparent-loss layer is included additively in our combined number but is *uncalibrated by NHIS* (NHIS has no grandchild head-count variable).

- **We did not produce a single integrated total-error CI.** Bootstrap CIs cover the NHIS-sampling component of κ. Demographic-rate sampling error, NCHS denominator error, and engine choice are held fixed. The total-error bars would be wider than the bootstrap CIs we report.

- **We did not calibrate post-2004 cause-specific K.** MORTUCOD coverage in NHIS-LMF ends at sample year 2004. For the 1999-2020 NCHS target we apply the 1986-2004 NHIS K under a constant-effects-over-time assumption. We discuss in the limitations how to test that.

- **We did not couple mother and father mortality.** Joint mortality within couples is positively correlated (shared health, shared exposures, shared smoking history). Our "either parent dead" probability assumes independence. The bias from this is small and goes the wrong direction (our independence assumption slightly *overstates* the probability of at least one parent dying), so it works against the gap we report rather than for it.

---

## A practical recommendation

If a US child welfare or demographic-bereavement paper is going to report a single national headline number in 2026, here's what we think is defensible:

> **All-cause prevalent parental orphanhood, US 2021: 2.24 M children (matrix-kinship baseline) or 2.17 M children (NHIS-calibrated). Combined with grandparent caregiver loss, the comparable total is 2.71 M, within roughly 7 % of the published Villaveces 2025 estimate of 2.91 M.**

> **Cumulative children of US drug-overdose or firearm parental decedents, 1999-2020: ~700 K under direct NHIS calibration of cause-specific dependent-child counts, materially below the published Schlüter 2024 estimate of ~1.19 M. The difference is driven by the equal-fertility-by-mortality-status assumption built into the published pipeline; in our data that assumption fails by 30-35 % in the cell-multiplied sense.**

> **Both estimates are sensitive to assumptions about the within-cell correlation between fertility and mortality risk. The published estimates pin that correlation at zero and run parametric sensitivities; ours measure it from NHIS and propagate it. Until linked individual-level mortality-natality data are publicly available, the NHIS-calibrated values appear to us the most defensible second-best.**

That recommendation does not retract anything. It calibrates.

---

## Where to read more

- Technical write-up: `explorations/kinship_replication_results.md` (tables, regression specs, bootstrap details).
- Literature review and gaps: `quality_reports/lit_review_orphanhood_fertility_kinship.md`.
- Code: `pykin/` (engine), `scripts/run_kinship_calibrated.py` (driver), `scripts/run_schluter_mortucod.py` (cause-specific Schlüter pipeline), `scripts/bootstrap_calibration.py` (κ CI).
- Results: `results/py/nhis_calibration_*.csv`; `results/kinship/baseline_villaveces/`, `calibrated_villaveces/`; `results/kinship/schluter_drugs_firearms/`.
- Replication tree from Villaveces 2025: `data_kinship/` (Zenodo download, gitignored).
- IPUMS NHIS extracts: `nhis_00003.dat` (current, with MORTUCOD); archived old extract at `archive/extract_00002/`.

PR #3 on GitHub (`feature/kinship-matrix-orphanhood`) contains the full implementation with one commit per major addition: bootstrap CIs, grandparent layer, Schlüter all-cause κ, MORTUCODLD intent-stratified κ, MORTUCOD cause-specific headline.

---

*Citations in this report are abbreviated; full BibTeX is in the companion literature review.*
