# Table Review: Wisconsin Achievement Gap Manuscript
**Date:** 2026-04-03  
**Reviewer:** domain-reviewer + review-paper skill framework  
**File:** `manuscript/main.qmd`  
**Tables reviewed:** 14 (tbl-gaps-summary through tbl-crossera)

---

## Summary
- **Overall assessment:** MINOR ISSUES (no results are wrong; presentation bugs affect rendering)
- **Total issues:** 18
- **Blocking issues (prevent clean LaTeX render):** 4
- **Non-blocking (should fix for publication quality):** 14

---

## CRITICAL — LaTeX Rendering Bugs

### Issue C1: `r'\\% ...'` raw-string column headers break LaTeX table rows
- **Location:** `tbl-decomp-full`, `tbl-decomp-subject`, `tbl-wkce-decomp`, `tbl-crossera`
- **Problem:** Python raw strings `r'\\% Between'` emit `\\% Between` into LaTeX source. In LaTeX tabular, `\\` is the row separator — so `\\%` is parsed as "end row, then `%` starts a comment", silently swallowing subsequent columns.
- **Fix:** Change `r'\\% ...'` → `r'\% ...'` (single backslash in raw string = `\%` in LaTeX = percent sign).
- **Severity:** CRITICAL — columns will be missing or table will fail to render correctly.

### Issue C2: Table 3 (`tbl-act-decomp`) note is detached from its float
- **Location:** Lines after `tbl-act-decomp` code cell, raw `{=latex}` block
- **Problem:** The `{=latex}` note block appears at its *text position*, but the table float may appear on a different page. If LaTeX moves the float (e.g., to top of next page), the note appears separated from the table.
- **Fix:** Move note into `pub_table(note=...)` so it is emitted inside the float.
- **Severity:** CRITICAL — detached notes are unacceptable in a publication.

---

## MAJOR — Consistency and Clarity

### Issue M1: `tbl-act-decomp` does not use `pub_table()` helper
- **Location:** `tbl-act-decomp` code cell
- **Problem:** All other tables use `pub_table()`; this one calls `tabulate` directly with no `note=` and uses `\textit{N}` for the N-column instead of `$N$ Dist.` as used elsewhere.
- **Fix:** Refactor to `pub_table()`, change `\textit{N}` → `$N$ Dist.`, move note inside.

### Issue M2: "BW" / "HW" raw codes in Gap column
- **Location:** `tbl-wkce-gaps`, `tbl-wkce-decomp`, `tbl-wkce-gr10`, `tbl-decomp-full`
- **Problem:** The "Gap" column shows raw internal codes "BW" and "HW" which are not self-explanatory in a publication table.
- **Fix:** Map to "Black--White" / "Hispanic--White" before display.

### Issue M3: All tables except `tbl-decomp-full` missing `#| tbl-pos: H`
- **Location:** 13 of 14 tables
- **Problem:** Without placement control, LaTeX floats can be pushed far from their reference point (especially in double-spaced documents), causing the "misplaced" problem reported by the user.
- **Fix:** Add `#| tbl-pos: H` to all tables (`float` package already loaded).

---

## MINOR — Titles and Notes

### Issue m1: `tbl-supp-year` caption contains raw LaTeX (`\\%`)
- Caption: `"District-Level Suppression Rate by Race and Year (Forward Exam, \\%)"` — confusing; the `\\%` should either be spelled out ("Percent Suppressed") or handled cleanly.
- **Fix:** Rename caption to "District-Level Suppression Rates by Race and Year (Forward Exam)"

### Issue m2: `tbl-crossera` `"MMSD vs.\ Peers"` column header
- The `\ ` (non-breaking space) is a LaTeX convention for post-abbreviation spacing; valid but unnecessary in a column header and confusing to read in source.
- **Fix:** Change to `"MMSD vs. Peers"` (plain).

### Issue m3: `tbl-act-decomp` caption uses hyphen in en-dash position
- Caption: "Black-White ACT Composite Score Gap: Within-Between District Decomposition (Grade 11)" — hyphens in compound modifiers are correct, but verify they aren't supposed to be en-dashes.
- **Assessment:** Fine as-is (compound adjective hyphens are correct).

### Issue m4: `tbl-wkce-gaps` and `tbl-wkce-gr10` have duplicate "Gap" and "Gap (pts)" columns
- Having both a "Gap" comparison column and a "Gap (pts)" value column with similar names is slightly confusing.
- **Fix:** Rename the comparison column to "Comparison" to distinguish from the value column.

---

## Positive Findings

1. **All 14 tables have explanatory notes** — self-contained per quality-gates standard.  
2. **Column alignment is correct** throughout (left text, right numbers).  
3. **`booktabs` style** is used consistently (toprule/midrule/bottomrule, no vertical lines).  
4. **Suppression documentation** is thorough and accurate in Appendix A tables.  
5. **T = B + W identity** is explicitly stated in notes for all decomposition tables.  
6. **ACT table** (Table 2) is correctly pivoted to wide format — a substantial improvement over long-format presentation.

---

## Fix Priority (implement in this order)

| # | Severity | Table | Issue |
|---|----------|-------|-------|
| 1 | CRITICAL | tbl-decomp-full, tbl-decomp-subject, tbl-wkce-decomp, tbl-crossera | `r'\\%'` column name bug |
| 2 | CRITICAL | tbl-act-decomp | Detached note; refactor to pub_table() |
| 3 | MAJOR | tbl-wkce-gaps, tbl-wkce-decomp, tbl-wkce-gr10, tbl-decomp-full | Spell out BW/HW |
| 4 | MAJOR | All 13 tables | Add `#| tbl-pos: H` |
| 5 | MINOR | tbl-supp-year | Clean caption |
| 6 | MINOR | tbl-crossera, tbl-wkce-gaps | Column name improvements |
