# Bibliography Validation Report

**Date:** March 14, 2026  
**Project:** Wisconsin Infant Mortality (Attempt 2)  
**Files scanned:** `Quarto/report.qmd`, `Quarto/slides.qmd` (not found)  
**Bibliography:** `Bibliography_base.bib`

---

## 1. Summary

| Category | Count |
|----------|-------|
| Bib entries | 12 |
| Unique citations in report.qmd | 11 |
| Missing entries (cited but not in bib) | 0 |
| Unused entries (in bib but not cited) | 1 |
| Quality issues | 3 |

---

## 2. Citation Keys Extracted

### From Bibliography_base.bib (12 keys)

| Key | Type |
|-----|------|
| Altindag2022_denmark | article |
| DCP3_rmnch | incollection |
| CapTimes2026_birth_equity | article |
| KFF2025_disparities | misc |
| Lancet2024_vaccination | article |
| Miller2015_nfp | article |
| NEJM2021_kmc | article |
| Olds2014_nfp_mortality | article |
| Tomlin2021_wisconsin | article |
| WISH_dhs | misc |
| WI_maternal_mortality | misc |
| WI_legislature_birth_equity | misc |

### From Quarto/report.qmd (11 unique bib citations)

| Key | Occurrences |
|-----|-------------|
| WISH_dhs | 2 |
| CapTimes2026_birth_equity | 2 |
| WI_maternal_mortality | 1 |
| Altindag2022_denmark | 4 |
| Lancet2024_vaccination | 1 |
| Miller2015_nfp | 5 |
| Olds2014_nfp_mortality | 3 |
| NEJM2021_kmc | 1 |
| Tomlin2021_wisconsin | 1 |
| KFF2025_disparities | 4 |
| WI_legislature_birth_equity | 1 |

**Note:** `@tbl-effects`, `@tbl-detect-rate`, and `@tbl-detect-count` are Quarto table cross-references, not bibliography citations; they were excluded from this analysis.

### Quarto/slides.qmd

**Status:** File does not exist. No slides file was scanned.

---

## 3. Cross-Reference Results

### Missing entries (CRITICAL)

**None.** All citation keys used in `report.qmd` are present in `Bibliography_base.bib`.

### Unused entries (informational)

| Key | Notes |
|-----|-------|
| DCP3_rmnch | In bibliography but not cited. The report mentions "DCP3 LiST, WHO" and "DCP3/LiST" in the literature review (AB 1082 discussion) but does not use `[@DCP3_rmnch]`. Consider adding a citation where DCP3 evidence is discussed, or remove if not needed. |

### Potential typos

**None.** No similar-but-not-matching keys were found.

---

## 4. Entry Quality

### Required fields check

| Key | author | title | year | journal/booktitle | Notes |
|-----|-------|-------|------|-------------------|-------|
| Altindag2022_denmark | ✓ | ✓ | ✓ | ✓ | OK |
| DCP3_rmnch | ✓ | ✓ | ✓ | ✓ | OK |
| CapTimes2026_birth_equity | ✓ | ✓ | ✓ | ✓ | OK |
| KFF2025_disparities | ✓ | ✓ | ✓ | — | OK (misc) |
| Lancet2024_vaccination | ✓ | ✓ | ✓ | ✓ | OK |
| Miller2015_nfp | ✓ | ✓ | ✓ | ✓ | OK |
| **NEJM2021_kmc** | **✗** | ✓ | ✓ | ✓ | **Missing author** |
| Olds2014_nfp_mortality | ✓ | ✓ | ✓ | ✓ | OK |
| Tomlin2021_wisconsin | ✓ | ✓ | ✓ | ✓ | OK |
| **WISH_dhs** | ✓ | ✓ | **✗** | — | **Missing year** |
| **WI_maternal_mortality** | ✓ | ✓ | **✗** | — | **Missing year** |
| WI_legislature_birth_equity | ✓ | ✓ | ✓ | — | OK (misc) |

### Quality issues (3)

1. **NEJM2021_kmc** — Missing `author` field. The entry has title, journal, volume, number, pages, year, and note (DOI) but no author. For multi-author NEJM articles, add author list or use `author = {{NEJM Study Group}}` or similar.

2. **WISH_dhs** — Missing `year` field. Web/data sources typically have a publication or last-updated year; consider adding for consistency.

3. **WI_maternal_mortality** — Missing `year` field. The title references "2020--2022"; consider adding `year = {2024}` or the appropriate publication year.

### Formatting notes

- All entries use consistent `author = {{...}}` for institutional authors (Cap Times, KFF, Lancet/WHO, Wisconsin DHS, Wisconsin Legislature).
- No malformed characters or obvious encoding issues detected.
- DOI/URL formatting in `note` fields appears correct.

---

## 5. Recommendations

1. **NEJM2021_kmc:** Add an `author` field. For the multi-country KMC trial, the lead authors or study group can be looked up from the DOI (10.1056/NEJMoa2026486).

2. **WISH_dhs:** Add a `year` field (e.g., `year = {2024}` or `year = {2023}`) if a publication/last-updated date is known.

3. **WI_maternal_mortality:** Add `year = {2024}` (or the actual publication year of the 2020--2022 issue brief).

4. **DCP3_rmnch:** Either add `[@DCP3_rmnch]` where DCP3/LiST evidence is discussed (e.g., in the AB 1082 breastfeeding section or the literature review) or document why it is kept as an unused reference.

---

## 6. Validation status

| Check | Result |
|-------|--------|
| All citations have bib entries | ✓ Pass |
| No typos in citation keys | ✓ Pass |
| Unused entries | 1 (informational) |
| Entry quality | 3 issues (non-blocking) |

**Overall:** Bibliography is functional. No critical missing entries. Three quality improvements recommended for completeness.
