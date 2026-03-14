# Project Memory — Wisconsin Infant Mortality (Attempt 2)

Corrections and learned facts that persist across sessions.
When a mistake is corrected, append a `[LEARN:category]` entry below.

---

<!-- Append new entries below. Most recent at bottom. -->

## Workflow Patterns

[LEARN:workflow] Requirements specification phase catches ambiguity before planning → reduces rework 30-50%. Use spec-then-plan for complex/ambiguous tasks (>1 hour or >3 files).

[LEARN:workflow] Spec-then-plan protocol: AskUserQuestion (3-5 questions) → create `quality_reports/specs/YYYY-MM-DD_description.md` with MUST/SHOULD/MAY requirements → declare clarity status (CLEAR/ASSUMED/BLOCKED) → get approval → then draft plan.

[LEARN:workflow] Context survival before compression: (1) Update MEMORY.md with [LEARN] entries, (2) Ensure session log current (last 10 min), (3) Active plan saved to disk, (4) Open questions documented.

[LEARN:workflow] Plans, specs, and session logs must live on disk (not just in conversation) to survive compression and session boundaries.

## Project-Specific Learnings (from Attempt 1)

[LEARN:data] WISH suppression: "X" in WISH tables = suppressed count (typically 1–4). Impute Black count as Total − White. Document in report and data README.

[LEARN:data] Processed CSVs columns: year, race, births, deaths, rate_per_1000, rate_lo, rate_hi. Geographies: State, Milwaukee, Dane, Rest of Wisconsin (= State − Milwaukee − Dane).

[LEARN:data] Rest of Wisconsin is computed, not a direct WISH query: State − Milwaukee − Dane for births and deaths separately, then rate and CI from those.

[LEARN:figures] Publication palette: White=#2171b5 (blue), Black=#b2182b (dark red). Resolution: 300 DPI. Title suffix: "(95% CI, Poisson-based)". Do not change without reason.

[LEARN:figures] CI method: Poisson-based 95% CI for rate per 1,000. Formula: rate ± 1.96 × (1000 × √D) / B, where D=deaths, B=births.

[LEARN:report] Table 3 is count-based: detectability = deaths averted so post-intervention count falls below lower bound of 95% CI (Poisson). Min averted = ceil(1.96√D). NFP benchmark $3.2M per life (0.31 per $1M).

[LEARN:report] Section 3 "Link to evidence": each bill (AB 1082–1088) has explicit citations and states where direct infant-mortality evidence is absent.

[LEARN:report] Dane Black count CI (1–11): smallest absolute width, largest relative uncertainty (width/mean).

[LEARN:report] Title page: author line is "Jason Fletcher, University of Wisconsin" with "March 2026" on the next line.

[LEARN:report] Report layout: Executive summary → Introduction → 1. Literature Review → 2. Data and Rates → 3. Birth Equity Act → 4. Conclusion → References.

[LEARN:policy] Birth Equity Act: Rep. Shelia Stubbs, seven bills AB 1082–1088 (Cap Times, March 2026). Applies to all residents regardless of race/ethnicity.

[LEARN:policy] Milwaukee has ~55 Black infant deaths/year — the only county-level geography where intervention effects can be evaluated with current data.

## Documentation Standards

[LEARN:documentation] When adding new features, update BOTH README and guide immediately to prevent documentation drift.

[LEARN:documentation] Date fields in frontmatter and README must reflect latest significant changes.

## Design Philosophy

[LEARN:design] This project uses Python (not R). All .claude/ configs adapted for Python: pandas, matplotlib, pdfplumber. R-specific agents/rules have Python equivalents.

[LEARN:design] Quarto → PDF is the primary output format. No Beamer slides (report project, not lecture).

## File Organization

[LEARN:files] Specifications go in `quality_reports/specs/YYYY-MM-DD_description.md`.

[LEARN:files] Python scripts in `scripts/python/`. Figures in `Figures/`. Data in `data/input/` (read-only PDFs) and `data/processed/` (CSVs).

[LEARN:files] Attempt 1 is read-only reference in `reference/`. Never modify `../Attempt 1/`.

## Scope Decisions

[LEARN:scope] No cause-specific analysis (neonatal vs postneonatal, SIDS, injuries). The report notes this as a recommendation for future work, but it is out of scope for this project.
