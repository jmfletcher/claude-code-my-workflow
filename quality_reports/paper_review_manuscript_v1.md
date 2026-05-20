# Manuscript Review: NHIS-Calibrated US Parental Orphanhood (v1)

**Date:** 2026-05-20
**Reviewer:** review-paper skill (self-review)
**File:** `paper/manuscript/manuscript_v1.md` (7,761 words)

## Summary Assessment

**Overall recommendation:** Revise & Resubmit (substantive)

The manuscript reports a methodologically clean and substantively important calibration of US orphanhood-estimation models using NHIS-linked mortality data. The replication-then-calibrate logic is sound, the cell-level $\kappa$ estimates rest on workable NHIS sample sizes for the all-cause analysis, and the cause-specific extension to Schlüter (2024) is a genuine empirical contribution. The strongest finding -- 42 % downward correction to the published Schlüter cumulative -- would be a substantial result if defensible.

Three concerns are major. First, the manuscript is internally inconsistent on what $\kappa$ measures: it is introduced as a "fertility-mortality correlation" but acknowledged in §6.3 to be a household-composition-selection effect. The two interpretations have different policy implications and the paper should commit to one consistently. Second, the back-of-envelope non-resident-father correction is presented as a sensitivity but is too crude to bear the substantive weight assigned to it (ACS rates not conditioned on mortality, "one child each" assumption). Third, the small NHIS sample size in the cause-specific cells (697 drug decedents, 1,566 firearm decedents) requires extensive smoothing that the paper underplays. The reader needs to know how much of the headline 42 % correction would survive a Bayesian or hierarchical-pooling approach with better-quantified uncertainty.

Several minor concerns (referenced below) are easily fixable in revision. The literature positioning is solid, the writing is generally clear, and the technical execution (matrix engine, bootstrap, smoothing) is sound.

## Strengths

1. **Methodological novelty.** First US empirical estimate of within-cell fertility-mortality correlation for orphanhood modeling. Plugs into the existing Caswell / DemoKin recurrence cleanly via a single multiplier.
2. **Substantive importance.** A 35-42 % correction to the published Schlüter (2024) cumulative is large enough to change resource-allocation discussions if defensible.
3. **Honest definitional treatment.** §6.2 and Appendix A address the custodial-vs-biological orphanhood distinction explicitly rather than hiding it. The non-resident-father back-of-envelope is a useful framing device even if the specific numbers need work.
4. **Race-stratified analysis.** The opposite-signed pattern (NH White & NH Asian / PI down; NH AIAN up; Hispanic flat) is well-documented and important for policy.
5. **Transparent replication of Villaveces.** 2.24 M baseline (parental-only) vs 2.91 M published (combined with grandparent layer) is reconciled cleanly to within 7 %.

## Major Concerns

### MC1: Inconsistent framing of $\kappa$

- **Dimension:** Argument structure / writing quality.
- **Issue:** The Introduction frames $\kappa$ as the "within-cell fertility-mortality correlation" (§1, multiple places), implying that the paper measures whether decedents have different *biological* fertility from survivors. But §6.3 demonstrates that the calibration result is structurally driven by household composition: single-adult-parent households have 1.3-1.9× the mortality of coupled-parent households and lower $K_{\text{alive}}$. So $\kappa$ is measuring *household-composition selection on mortality*, not biological-fertility heterogeneity.
- **Suggestion:** Reframe consistently throughout the paper. Either:
  - (a) Drop "fertility" from the framing entirely. Call $\kappa$ the "co-resident-minor correlation" or "dependent-child correlation" and let the household-structure interpretation be primary. The Schlüter cause-specific result is robust to this reframing.
  - (b) Decompose $\kappa$ explicitly into a "household-structure composition" term and a "within-structure fertility" term, and report both. The within-structure $\kappa$ values (Appendix A.2) are uniformly close to 1.0; the aggregate $\kappa < 1$ is driven by composition. This is a sharper, more defensible result.
- **Location:** Title; §1 paragraphs 4-6; §4.2-4.3 mathematical notation; §6.1 conclusion paragraph 2.

### MC2: Non-resident-father correction is too informal for the weight it bears

- **Dimension:** Identification / econometric specification.
- **Issue:** §1 paragraph 8 and §6.2 use the back-of-envelope non-resident-father augmentation to argue that the "true" all-cause count sits between 2.17 M (custodial) and 2.4-2.5 M (biological). The augmentation relies on:
  - ACS-based non-resident-father rates *not* conditioned on the father's eventual mortality status.
  - A flat "one minor child each" assumption.
  - Independence of non-residence from κ.
- **Suggestion:** Either:
  - (a) Demote the back-of-envelope to a transparent sensitivity bound with explicit caveats. Do not claim it "roughly offsets" the κ correction unless the offset is quantified with uncertainty.
  - (b) Strengthen the non-resident-father estimate using NSDUH (which has dependent-child information for substance-using respondents, including those with non-resident kids) or CPS-SCF (which has matched father-child residence at the survey).
  - (c) Run a partial-identification bound: what is the smallest non-resident-father correction that brings the all-cause headline back to Villaveces's 2.91 M? Is it plausible?
- **Location:** §1 paragraph 8; §6.2 paragraphs 2-3; Appendix A.4.

### MC3: Cause-specific cell smoothing receives insufficient discussion

- **Dimension:** Econometric specification.
- **Issue:** §4.2 notes that "cells with fewer than 25 weighted decedents are smoothed toward the (sex, race/eth, decade) pool" but does not report how many cause-specific cells require smoothing or how sensitive the headline is to the threshold. The companion technical writeup acknowledges that *all* drug cells in the `MORTUCOD` analysis are smoothed (697 decedents over 60 cells = ~12 per cell on average) but this is not in the manuscript.
- **Suggestion:** Add a methods sub-section quantifying:
  - Number of cause-specific cells with raw n ≥ 25, between 5 and 25, and < 5.
  - Robustness of the headline cumulative to changing the smoothing threshold (25 → 10, → 50, → no smoothing for cells with any nonzero $n$).
  - A Bayesian / multilevel pooling alternative as a sensitivity (need not be central spec, but the reader should see how much of the 42 % gap survives).
- **Location:** §4.2 methods; §5.3 results table.

### MC4: Missing direct comparison with Schlüter's input-output

- **Dimension:** Identification / literature positioning.
- **Issue:** §5.3 reports our cumulative 691 K vs Schlüter's published 1.19 M and labels the gap as "the calibration effect." But Schlüter's pipeline includes a model for male fertility derived from natality data plus female-fertility extrapolation; our pipeline uses NCHS deaths and the NHIS K directly. The difference between 691 K and 1.19 M is therefore a composite of (a) our κ correction, (b) different male-fertility assumptions, and (c) potentially different cause-of-death definitions. The reader cannot tell which component drives the headline.
- **Suggestion:** Decompose the 1.19 M - 691 K = 499 K gap into three components:
  - (i) Definition (custodial vs biological orphanhood, our §6.2): X K.
  - (ii) κ correction (decedents have lower $K$ than survivors in matched cells): Y K.
  - (iii) Other (male fertility assumptions, age-band aggregation, etc.): Z K.
  - Run our pipeline once with κ = 1 (naive) and compare against Schlüter's published; the gap is component (iii). Then add κ; the new gap is (ii) + (iii). Then add the non-resident-father augmentation; the residual is (i).
- **Location:** §5.3 Table 2 should add a "Schlüter naive (their model with κ = 1)" row.

### MC5: Data vintage and the COVID-19 spike

- **Dimension:** Identification / writing.
- **Issue:** Our NHIS-LMF data ends at sample year 2018 with mortality follow-up through 2019. The Villaveces 2025 target spike year is 2021 (COVID-driven). The cause-specific MORTUCOD ends at NHIS sample year 2004. The manuscript applies our 1986-2018 κ to 2019-2021 deaths and the 1986-2004 cause-specific K to 1999-2020 NCHS deaths under a "constant-effects" assumption that is not directly tested in the data we have.
- **Suggestion:**
  - (a) Acknowledge prominently that the NCHS released a 2022 NHIS-LMF in January 2026 with mortality follow-up through 2022 (currently mentioned only in §3.1 and §6.6 as "future work"). Frame this as the next-step rather than a remediable gap.
  - (b) Test the constant-effects assumption inside the data we *do* have: compare κ in 1990s vs 2010s NHIS sub-samples for cells with adequate sample. Report a stability test in §5.2.
- **Location:** §1 conclusion paragraph; §3.1; §6.5 limitations 2-3.

## Minor Concerns

### mc1: Introduction is overlong

- **Issue:** §1 runs ~2,200 words and previews the entire paper twice. The "Our three main findings, in order of size" list duplicates content from the Abstract.
- **Suggestion:** Cut the Introduction by 40 %. Move the three-finding preview into a single paragraph; tighten the lit-review paragraphs (currently spread across paragraphs 3-5).

### mc2: Figure 1 referenced but not included

- **Issue:** §5.4 references "Figure 1 (not shown in this draft)" -- a publication-quality submission cannot have this.
- **Suggestion:** Either include the figure (annual trajectory under each calibration) or drop §5.4. The annual trajectory is in `results/kinship/schluter_drugs_firearms/annual_by_cause_mortucod.csv` and could be plotted in matplotlib for a clean appendix figure.

### mc3: Bibliography placeholder

- **Issue:** Fletcher (2026a) is listed but is an internal working document, not a publication. The Stover Spectrum reference has no date or DOI.
- **Suggestion:** Either suppress the self-citation (move the lit-review content into §2 directly) or stage it as an online supplement. For Spectrum, cite the published methods paper (Stover et al., AIDS, 2014) rather than the moving manual.

### mc4: Notation in §4 could be cleaner

- **Issue:** §4.2 mixes `nk_under18`, `mortwtsa`, `n_fam_childminor017` (IPUMS variable names) with paper notation $\text{nk}_i^{\text{u18}}$, $w_i$. Pick one convention and use it consistently.
- **Suggestion:** Introduce variable names in the data section (§3), then use math notation throughout §4-5. Move variable-name mappings to a footnote or supplementary table.

### mc5: Limitations section is structurally good but content-light

- **Issue:** §6.5 lists 5 limitations in short paragraphs. The dependent-child variable (`n_fam_childminor017`) is *family-level*, not respondent-level -- if a household has two married adults with three minor children, both adults are coded as 3 minors. The manuscript does not flag this potential double-counting issue.
- **Suggestion:** Add a limitation about family-unit (`fmx`) coding and verify in a footnote that K computed at the *family* level rather than the *respondent* level matches the kinship-engine concept (children per *adult*, not children per *family*). The current K = 1.76 / 1.87 figures look plausible for "children per parent" but could be subtly wrong if double-counting occurs.

### mc6: Discussion paragraph on "deaths-of-despair" lacks citation

- **Issue:** §6.1 paragraph 2 invokes the deaths-of-despair narrative without citing Case & Deaton.
- **Suggestion:** Cite Case & Deaton 2015 / 2020 and possibly Cutler, Deaton, Lleras-Muney (2006) for the cause-of-death decomposition story.

### mc7: Tables lack notes

- **Issue:** Tables 1-2 and A1-A4 have headers but no "Notes:" line describing the unit of observation, weighting, denominator, and exact sample restriction.
- **Suggestion:** Add a standard notes block under each table.

## Referee Objections

### RO1: "Your κ is not measuring what you say it's measuring"

**Why it matters:** If a top-5 referee reads the manuscript with §6.3 in mind, they will conclude that the entire paper is reporting a *household-composition* effect mislabeled as a *fertility* effect. This kind of framing inconsistency can be fatal at top journals because it implies the authors did not understand their own result. The findings are still substantive after reframing, but the rhetorical posture must shift.

**How to address it:** See MC1. Decompose $\kappa$ into household-structure-composition and within-structure components. Lead with the cleaner result.

### RO2: "Your sensitivity analysis is not a sensitivity analysis"

**Why it matters:** The non-resident-father back-of-envelope (§6.2 and Appendix A.4) is the only quantitative argument the manuscript offers against the equal-fertility critique of NHIS itself. A top-5 referee will see that the augmentation rates are not derived from any model, are not conditioned on mortality status, and are applied with a flat "one minor child" multiplier. They will reject the augmentation as a real sensitivity. The manuscript would then be exposed as a one-sided revision: it questions the published literature's assumption but does not robustly defend its own.

**How to address it:** See MC2. Either upgrade the non-resident-father estimate using NSDUH or CPS, or demote it to an explicit upper-bound construction with no claim that it "offsets" the κ correction.

### RO3: "The 42 % gap with Schlüter is mostly definitional"

**Why it matters:** A referee comparing our 691 K to Schlüter's 1.19 M will note that our pipeline operates on NCHS deaths and NHIS K, while Schlüter operates on NCHS deaths and modeled male fertility. The difference is multi-component. We cannot legitimately claim Schlüter "overstates by 42 %" without showing that our pipeline produces a number close to Schlüter's *under κ = 1* (i.e., the same equal-fertility assumption). If our naive-κ-1 pipeline already lands at 1.07 M, the κ-correction contributes only ~380 K of the 500 K gap -- a 32 % effect, not 42 %.

**How to address it:** See MC4. Add a decomposition row to Table 2.

### RO4: "The cause-specific cells are too sparse for cell-level estimation"

**Why it matters:** With 697 NHIS drug decedents over 60 sex × race × age × decade cells (≈ 12 per cell), every cause-specific cell requires smoothing. Without disclosing this, the reader might believe the cell-level $K$ values are estimated from raw data. A referee will ask whether a Bayesian / multilevel approach would produce wider CIs that overlap zero for several race-stratified groups, undermining the headline of "robust 35-42 % correction."

**How to address it:** See MC3. Report the smoothing diagnostics and at least one alternative pooling strategy.

### RO5: "Why aren't you using the 2022 NHIS-LMF?"

**Why it matters:** The 2022 file was released in January 2026; the manuscript is dated May 2026. A referee will see this as a four-month gap and ask why the authors did not refresh. The 2022 release extends mortality follow-up through end-2022, which captures the full COVID-19 spike that drives the Villaveces 2021 calibration target.

**How to address it:** Two options.
- (a) Refresh: re-run the κ estimation on the 2022 file and report the updated numbers. Costs: maybe 1 day of work; benefit: removes the data-vintage criticism entirely.
- (b) Defend: explain why the 1986-2018 file is the right sample for this paper (e.g., MORTUCOD coverage ends at 2004 regardless of the NHIS-LMF vintage; the all-cause analysis is bracketed by Villaveces's modeling horizon ending in 2021; etc.).

## Specific Comments

- **Title:** "Calibrating Demographic Orphanhood Models with Decedent-Level Fertility" -- but as MC1 notes, we are not measuring decedent-level *fertility*. Consider "Decedent-Level Co-Resident Dependents" or "Decedent-Level Household Composition" instead.
- **Abstract first sentence:** "rely on demographic-rate models that multiply parental death counts by an expected number of dependent children" -- tighten. Suggest: "Recent US orphanhood estimates multiply parental death counts by demographic-cell-average dependent children counts derived from natality."
- **§1 paragraph 1, last sentence:** "deaths-of-despair episode" should be linked to a definition or cite Case & Deaton.
- **§1 paragraph 4:** "All of these papers share a common modeling architecture and a common assumption." -- the second "common" is dispensable. "share a common architecture and assumption."
- **§3.1, sample size sentences:** "1.25 million person-records" -- person-years or person-records? Clarify.
- **§4.2 equation block:** $K_{\text{died},c}$ and $K_{\text{alive},c}$ should be defined in a single display with the ratio. Currently two display equations + the ratio inline is awkward.
- **§5.2 sentence on bootstrap CIs:** "the NH AIAN $+26.4 \%$ point estimate has a wide CI and is not statistically distinguishable from zero at the 5 % level given NHIS-LMF sample sizes" -- soft-pedal? The qualitative direction matters even if the level is uncertain. Reword to lead with the directional finding.
- **§6.4 policy implications:** Strong content but reads as a numbered list of programs (SSI, IV-E, grief counseling). Consider re-organizing into 2-3 paragraphs that build a policy argument rather than a list.
- **References:** Fletcher 2026a (self-cite) and the Stover entry need polishing. Williams et al. (2023) for DemoKin -- verify DOI and authorship.

## Summary Statistics

| Dimension | Rating (1-5) |
|---|:---:|
| Argument Structure | 3 |
| Identification | 3 |
| Econometrics | 4 |
| Literature | 4 |
| Writing | 3 |
| Presentation | 2 |
| **Overall** | **3** |

The 3/5 overall reflects: strong technical execution and substantive importance offset by framing inconsistency (MC1), under-developed sensitivity for the non-resident-father critique (MC2), missing decomposition vs Schlüter (MC4), and presentation issues (no Figure 1, data vintage). All five are addressable in revision.
