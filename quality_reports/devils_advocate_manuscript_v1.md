# Devil's Advocate: NHIS-Calibrated US Parental Orphanhood (v1)

**Manuscript:** `paper/manuscript/manuscript_v1.md`
**Audience:** intended for top demography / public health journal (Demography, AJPH, JAMA-NetOpen tier).

> "We arrive at the best possible presentation through active dialogue."

The pedagogical philosophy of this skill maps onto a manuscript review as: "we arrive at the best possible argument through challenge." Below: 7 challenges aimed at the structural argument, not just the prose.

---

## Challenges

### Challenge 1 — Ordering: lead with the strongest finding, not the smallest

**Question:** The pooled all-cause result (-3 % national) is the *least* substantively important finding in the paper. Why does the Abstract lead with it?

**Why it matters:** A reader who reaches "modest pooled correction of -3 %" in line two of the Abstract may stop reading. The 42 % Schlüter correction and the +27 % NH AIAN under-count are the headline policy-relevant results. The current ordering buries the lead.

**Suggested resolution:** Restructure the Abstract to lead with the cause-specific Schlüter result (the most novel and most policy-actionable). Then state the all-cause race-stratified dispersion. The "pooled correction is small" comes last as a *calibration check* on the national headline, not as the headline finding itself.

Concretely: rewrite Abstract first 3 sentences as
> "Published estimates of US children orphaned by drug-overdose and firearm parental deaths (Schlüter et al., 2024) rely on a demographic-cell-average dependent-child assumption that has not been empirically tested. Using NHIS-Linked Mortality File data on actual decedents, we estimate that the cumulative count over 1999-2020 is 691,000 children -- 42 % below the published 1,190,000. The correction is robust across four NHIS calibration specifications and to a back-of-envelope augmentation for non-resident parents."

**Slides affected:** Abstract (lines 11-16), §1 Introduction order, §7 Conclusion paragraph 1.

**Severity:** **High** — affects whether the paper gets read past the first paragraph.

---

### Challenge 2 — Prerequisite: a public health audience does not know what "matrix kinship" means

**Question:** §4.1 launches directly into block-structured transition matrices and the dead-block absorbing-state choice. What fraction of the target-journal readership has read Caswell 2019?

**Why it matters:** Demography readers have seen the recurrence; AJPH, JAMA, and policy-focused readers have not. The current §4.1 is unreadable for half the intended audience. Worse, the technical detail (absorbing vs incident dead-block) is methodologically interesting but not load-bearing for the headline result.

**Suggested resolution:** Compress §4.1 to a single paragraph that says "we use the standard time-varying two-sex matrix-kinship recurrence (Caswell & Song 2021) implemented as a Python port of the DemoKin R package, applied to the parental kin block only. Implementation details are in Supplementary Methods." Move the block-matrix equations and absorbing-state discussion to a Methods Appendix. Readers who care can find it; readers who do not will not be stopped.

**Slides affected:** §4.1.

**Severity:** **Medium-High** — gatekeeps half the audience.

---

### Challenge 3 — Gap: where is the back-of-envelope check on the *direction* of the bias?

**Question:** §6.2 argues that the NHIS κ correction (down) and the non-resident-father augmentation (up) "roughly offset." But the manuscript never explicitly tests the *sign* of the residual bias on a held-out, gold-standard comparison.

**Why it matters:** A skeptical reader will ask: "if your κ correction is approximately right, why does Villaveces 2025 land within 8 % of our combined NHIS-calibrated total despite using an *uncorrected* model? Either the non-resident-father augmentation is doing all the work in your favor, or the equal-fertility assumption is approximately right at the national level. You cannot have it both ways."

**Suggested resolution:** Run an explicit benchmarking exercise. Take Villaveces's published 2.91 M as the target, subtract our independently-computed 0.55 M grandparent layer to get 2.36 M parental-only target. Our raw NHIS-κ-calibrated number is 2.17 M (−8 %). Our biological-orphanhood upper bound is 2.4-2.5 M (≈ 0 % vs target). State explicitly: "the data-implied range brackets the Villaveces published parental-only number; the published number is consistent with the *biological* definition of orphanhood, not the custodial definition." This is a much stronger and more honest framing.

**Slides affected:** §6.1 and §6.2.

**Severity:** **High** — strongest available defensive argument; currently underused.

---

### Challenge 4 — Alternative presentation: figures over tables

**Question:** The manuscript currently has zero figures and seven tables. For a methods paper with race-stratified time-varying calibration results, this is exactly backwards.

**Why it matters:** Three things would benefit enormously from figures rather than tables:
- The cumulative cause-specific trajectory 1999-2020 under five specifications (Table 2 + annual data).
- The race-stratified all-cause Δ % over 2000-2021 (Table 1 over time).
- The K_alive vs K_died across age × sex × race (the κ heatmap).

A figure communicates "convergence across four specifications" in a glance. A table requires the reader to do mental math.

**Suggested resolution:** Add three figures:
- **Figure 1:** Annual cumulative drug + firearm orphanhood, 1999-2020, lines for naive / all-cause κ / intent-stratified / MORTUCOD broad / Schlüter published. Single panel.
- **Figure 2:** Race-stratified Δ % over 2000-2021 with bootstrap CI bands. Five panels (one per race / eth).
- **Figure 3:** K_died / K_alive heat map, sex × race / eth × age band × decade. Diverges around 1.0.

Generate these with matplotlib, save to `paper/manuscript/figures/`. The Schlüter and Villaveces papers both have similar figures; matching their visual conventions helps reviewers.

**Slides affected:** §5 throughout.

**Severity:** **Medium** — substantive content is already in the data; figures would just be presentation.

---

### Challenge 5 — Notation conflict: $\kappa$ in §4.2 vs $K$ in Tables and Appendix

**Question:** The manuscript uses $\kappa$ (lowercase Greek kappa) for the ratio $K_{\text{died}} / K_{\text{alive}}$ and $K$ (uppercase Latin K) for the weighted mean of co-resident minors. Tables A1-A4 report $K_{\text{alive}}$, $K_{\text{died}}$, $\kappa$. But §4.2 uses both, and §5 mixes "κ-calibrated" with "K-mortucod" language. Will a reader who sees "K_mortucod = 0.585" in §3.1 know that this is *not* the same as κ_mortucod?

**Why it matters:** Notation conflict is a top-5-journal rejection risk. The Caswell kinship literature uses $\pi$, $U$, $F$ for kinship operators; we are introducing two new symbols ($\kappa$ and $K$) that look similar in print.

**Suggested resolution:** Replace $K$ with $\bar{n}_k$ (mean dependent kids) throughout, and reserve $\kappa$ for the ratio. Or use $D$ for the weighted death count and $K$ for kids-per-decedent, and $\kappa = K_{\text{died}} / K_{\text{alive}}$. Pick one and apply globally.

**Slides affected:** All of §4-§5 and Appendix A.

**Severity:** **Medium** — fixable in revision but the kind of issue a copyeditor will catch.

---

### Challenge 6 — Cognitive load: too many specifications in §5.3

**Question:** Table 2 shows five rows for the Schlüter cumulative target: Schlüter published, naive, all-cause κ, intent-stratified, MORTUCOD BROAD, MORTUCOD NARROW. That is six rows. Most readers cannot hold six specifications in their head.

**Why it matters:** The headline finding -- 691 K vs 1.19 M -- gets diluted by the array of alternative specifications. A reader trying to remember the paper a week later will have lost the message.

**Suggested resolution:** Promote the MORTUCOD BROAD result to the **single** headline. Move the other specifications to a supplementary robustness table. In the main text, lead with one number: "Our preferred specification (MORTUCOD BROAD κ) places the cumulative 1999-2020 children at 691,000, 42 % below the published Schlüter estimate. The alternative κ specifications (all-cause, intent-stratified, MORTUCOD NARROW) range from 661,000 to 809,000 -- all materially below 1.19 M. Robustness details in Supplementary Table S1."

**Slides affected:** §5.3, Abstract.

**Severity:** **Medium** — improves headline retention without sacrificing rigor.

---

### Challenge 7 — Book-vision: does §6 read as a stand-alone policy chapter?

**Question:** §6 (Discussion) and §7 (Conclusion) together run 1,800 words. Could either section stand alone as a section in a methods textbook or a policy report?

**Why it matters:** Methods papers often have weak Discussion sections that re-state the results. The strongest methods papers have Discussions that *teach* the reader something general about the field. Our §6 has the seeds of this (§6.3 on household structure as the structural driver; §6.4 on policy implications by program) but they are buried.

**Suggested resolution:** Promote two passages from §6:
- §6.3 on household-structure selection as the proximate driver of κ < 1 should be a separate sub-section labeled "What κ is actually measuring." This is the *general* methodological lesson of the paper and other applied modelers can apply it.
- §6.4 on custodial-vs-biological orphanhood by policy program should be a separate sub-section labeled "Which definition does the policy purpose require?" Other applied modelers in different policy domains (e.g., Medicaid disability lookback, foster-care entry rates) can directly use this.

These two sub-sections make the paper memorable. Without them, the paper is "calibration of Villaveces and Schlüter." With them, the paper is "methodological framework for definitional choice in survey-linked demographic-rate models." The latter is a much more durable contribution.

**Slides affected:** §6 restructure.

**Severity:** **Medium** — about durability and citation half-life, not about acceptance.

---

## Summary Verdict

**Strengths:** Strong technical execution; substantively important Schlüter recalibration; honest treatment of the custodial-vs-biological definitional issue; clean reconciliation with Villaveces baseline.

**Critical changes (must do before submission):**
- **Reorder the Abstract to lead with the Schlüter 42 % correction**, not the pooled -3 %.
- **Add Figure 1** (annual cumulative trajectory, 1999-2020) at minimum; ideally Figures 2 and 3 as well.
- **Decompose the Schlüter gap** explicitly into κ effect vs definitional gap vs other (per review-paper MC4).

**Suggested improvements (would strengthen the paper):**
- Compress §4.1 matrix-kinship technicality into a paragraph; move details to Supplementary Methods.
- Promote §6.3 on household-structure selection and §6.4 on definitional choice by policy program into the main argument, not just discussion.
- Unify notation ($\bar{n}_k$ for kids-per-decedent, $\kappa$ for the ratio).
- Refresh data to NHIS-LMF 2022 release if feasible (Jan 2026 release extends through 2022).

**Verdict:** The bones of a top-5 paper are here. v2 revision is feasible; v1 as written would draw the major-revision route at most top journals.
