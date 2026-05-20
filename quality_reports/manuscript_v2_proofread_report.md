# Proofreading Report: manuscript_v2.md

**File:** `paper/manuscript/manuscript_v2.md`
**Date:** 2026-05-20
**Reviewer:** proofread skill
**Issues found:** 22 (4 critical numerical, 3 high-priority consistency, 15 minor)

---

## Critical Issues (numerical / factual)

### C1 — Numerical mismatch in our-combined-total computation

- **Location:** Line 305.
- **Current:** "NHIS-calibrated number: **2.17 M in 2021 all-cause** + 0.55 M grandparent layer = 2.71 M combined."
- **Problem:** Mixes our number (2.17 M κ-calibrated parental) with Villaveces's published 0.55 M grandparent layer. Our own grandparent layer is 0.47 M (from §5.1: 2.71 M combined - 2.24 M baseline parental = 0.47 M). The arithmetic also fails: 2.17 + 0.55 = 2.72, not 2.71.
- **Fix:** "NHIS-calibrated number: **2.17 M in 2021 all-cause** + 0.47 M grandparent layer (our independent flow-stock estimate) = 2.64 M combined."

### C2 — Numerical mismatch in Villaveces parental-only reconciliation

- **Location:** Line 295.
- **Current:** "(2.91 M combined minus our 0.55 M grandparent layer = 2.36 M parental-only)"
- **Problem:** The 0.55 M is Villaveces's *published* grandparent layer, not "our" number. Our grandparent layer is 0.47 M (§5.1).
- **Fix:** "(Villaveces's 2.91 M combined minus her 0.55 M caregiver-grandparent layer = 2.36 M parental-only)"

### C3 — Numerical mismatch: "8 % overstatement"

- **Location:** Line 319.
- **Current:** "the published equal-fertility model overstates custodial orphanhood by ~8 % (the $\kappa$ correction)"
- **Problem:** The all-cause pooled κ correction is -3.4 % per Table 1, not -8 %. The 8 % figure appears nowhere else in the manuscript.
- **Fix:** "the published equal-fertility model overstates custodial orphanhood by ~3 % at the pooled US level (the $\kappa$ correction in Table 1)"

### C4 — "Validated to within 1 %" overstates the agreement

- **Location:** Line 127.
- **Current:** "validated against the Villaveces et al. (2025) all-cause parental-only baseline to within 1 % for 2021"
- **Problem:** Our parental-only is 2.24 M; Villaveces's implied parental-only is 2.36 M (= 2.91 - 0.55). That is a 5 % gap, not 1 %. Line 192 itself says "within 7 % of Villaveces" for the combined total.
- **Fix:** "validated against the Villaveces et al. (2025) all-cause parental-only baseline to within 5 % for 2021 (within 7 % for the combined parental + caregiver total)"

---

## High-priority Consistency Issues

### H1 — Notation inconsistency: $K_{\text{alive}}$ vs $\bar{n}_k^{\text{alive}}$

- **Locations:** Lines 32, 364.
- **Problem:** §3.6 establishes $\bar{n}_{k,c}^{\text{alive}}$ as the notation throughout. Line 32 reverts to $K_{\text{alive}}$. Line 364 uses "Identical-K" as a phrase.
- **Fix:** Replace $K_{\text{alive}}$ with $\bar{n}_k^{\text{alive}}$ on line 32. Replace "Identical-K" with "Identical $\bar{n}_k$" on line 364. Note: the variable name "K_alive" was the legacy from v1; v2 should be uniform.

### H2 — Figure numbering mismatch with text reading order

- **Locations:** Lines 196, 213-215 (Figure 2 referenced first), Lines 219-225 (Figure 1 referenced second).
- **Problem:** In reading order, the race-stratified Δ % figure (currently "Figure 2") appears in §5.2 before the cumulative Schlüter trajectory figure (currently "Figure 1") in §5.3. Standard journal convention is to number figures in the order they appear.
- **Fix:** Rename throughout:
  - Old "Figure 2" → new "Figure 1" (race-stratified Δ %)
  - Old "Figure 1" → new "Figure 2" (Schlüter cumulative)
  - Update image-file references in markdown and rename PNG/SVG files accordingly, or just swap the captions / references and leave the file paths in place (cleaner).

### H3 — Stover citation inconsistency

- **Locations:** Line 63 (body, in Table N1), Line 279 (body, §6.1), Line 441 (References).
- **Current:** Body lines 63 cite "(Spectrum, 2014, 2024)"; line 279 cites "(Stover et al.)" without year; references list only Stover et al. (2014).
- **Fix:** Use a single consistent body citation: "Stover et al. (2014, Spectrum)" in line 63, "(Stover et al., 2014)" in line 279. Or add a "Spectrum manual (2024)" citation to the References list if we want to keep the 2024 update referenced.

---

## Minor / Stylistic Issues

### m1 — Grammatically awkward range expression

- **Location:** Line 30.
- **Current:** "ranges from **-20 % for NH Asian / PI children, -14 % for NH White children, and -6 % for NH Black children**, to **-1 % for Hispanic children and +26 % for NH AIAN children**"
- **Problem:** "ranges from X, Y, Z to A, B" is ungrammatical. A range has two endpoints, not five.
- **Fix:** "ranges from **-20 % for NH Asian / PI children** to **+26 % for NH AIAN children**, with intermediate corrections of -14 % (NH White), -6 % (NH Black), and -1 % (Hispanic)."

### m2 — Subject-verb mismatch in lead finding

- **Location:** Line 28.
- **Current:** "Cumulative US children of drug-overdose and firearm parental decedents 1999-2020 are 691,000 ..."
- **Problem:** "Cumulative US children ... are 691,000" reads awkwardly because the predicate is a count.
- **Fix:** "The cumulative count of US children of drug-overdose and firearm parental decedents 1999-2020 is 691,000 ..."

### m3 — Missing comma in citation

- **Location:** Line 48.
- **Current:** "(Fletcher 2026a)"
- **Fix:** "(Fletcher, 2026a)"

### m4 — TYPO: "MEPS-weighted" should be "NHIS-weighted"

- **Location:** Line 263 (Table 3 notes).
- **Current:** "Mortality rates pooled across NHIS sample years 1986-2018, MEPS-weighted."
- **Problem:** MEPS = Medical Expenditure Panel Survey, a different survey. We use NHIS mortality weights (`mortwtsa`).
- **Fix:** "Mortality rates pooled across NHIS sample years 1986-2018, NHIS-mortality-weighted (`mortwtsa`)."

### m5 — Internal meta-commentary should not appear in journal version

- **Location:** Line 333 (end of §6.5 limitations).
- **Current:** "The most important *unstated* limitation in our v1 draft was an inconsistency in how we framed $\kappa$ -- §1 called it a 'fertility-mortality correlation' while §6.3 (v1) demonstrated that it was actually measuring household-composition selection. This version of the paper resolves the inconsistency by anchoring the interpretation on household structure throughout (§5.4 and §6.1)."
- **Problem:** Self-reference to "v1 draft" is process commentary that does not belong in a journal manuscript.
- **Fix:** Delete the entire paragraph.

### m6 — Anthropomorphism in §6.1

- **Location:** Line 277.
- **Current:** "the published demographic-rate orphanhood headlines therefore answer a question they do not realize they are answering"
- **Problem:** Headlines do not "realize" things.
- **Fix:** "the published headlines therefore answer a question that their authors do not foreground"

### m7 — Informal "Pattern:" in §2.2

- **Location:** Line 65.
- **Current:** "Pattern: exceptions appear when (a)"
- **Fix:** "The exceptions appear when (a)..." or "The pattern is clear: exceptions appear when (a)..."

### m8 — Clunky participial in §3.1

- **Location:** Line 87.
- **Current:** "an updated 2022 release was published in January 2026 extending follow-up through end-2022"
- **Fix:** "an updated 2022 release published in January 2026 extends follow-up through end-2022"

### m9 — Imprecise phrasing about decedents in §2.4

- **Location:** Line 79.
- **Current:** "we use the actual decedents in NHIS-LMF"
- **Fix:** "we use actual decedents observed in NHIS-LMF" or "we use decedents directly observed in NHIS-LMF"

### m10 — Awkward phrasing in §5.2 caveat

- **Location:** Line 211.
- **Current:** "NH Black and Hispanic are essentially flat at the point estimates but with wide CIs."
- **Fix:** "NH Black and Hispanic point estimates are near zero with wide CIs."

### m11 — Missing citation for sex-asymmetry rates in §6.2

- **Location:** Line 288.
- **Current:** "Mothers are co-resident with their minor children in approximately 80-95 % of US cases. Fathers are co-resident in 60-75 % of cases"
- **Fix:** Add citation. ACS public-use microdata or CPS pooled tables would be appropriate sources for the rates.

### m12 — Missing citation for deaths-of-despair narrative in §5.2

- **Location:** Line 217.
- **Current:** "tracking the documented rise of deaths of despair in young AIAN cohorts"
- **Fix:** Add Case & Deaton 2015/2020 or NH AIAN-specific overdose / suicide literature citation.

### m13 — "recovers to" reads oddly

- **Location:** Line 192.
- **Current:** "our independent flow-stock accounting layer recovers to 2,711,000 combined"
- **Fix:** "produces a combined total of 2,711,000" or "lands at 2,711,000 combined."

### m14 — "Spectrum" 2024 manual not in references

- **Location:** Line 63, Table N1: "Stover et al. (Spectrum, 2014, 2024)"
- **Fix:** Add a "Spectrum manual" entry to the references list if we want to cite the 2024 version, or drop "2024" from the body citation.

### m15 — Long sentence in §1 ¶6

- **Location:** Line 34.
- **Current:** "Section 6 discusses two implications -- that $\kappa$ is measuring household structure, and that custodial and biological orphanhood are different quantities -- and explains why this matters for policy."
- **Fix:** Split: "Section 6 discusses two implications: $\kappa$ measures household structure (not biological fertility), and custodial vs biological orphanhood are different policy concepts."

---

## Summary

| Category | Count |
|---|:---:|
| Critical (numerical / factual) | 4 |
| High-priority (consistency) | 3 |
| Minor (style, grammar, citation) | 15 |
| **Total** | **22** |

The critical issues (C1-C4) and high-priority issues (H1-H3) should be fixed in the next revision. Most of the minor issues are cosmetic. The Figure renumbering (H2) and the v1-meta-commentary (m5) should be addressed during the JMF voice revision.
