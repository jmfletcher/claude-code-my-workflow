# Wisconsin Schools — Racial Achievement Gap Analysis

## Project identity

**Working title:** Racial achievement gaps in Wisconsin public schools.

**Research question:** How large are racial achievement gaps (Black–White, Hispanic–White) across Wisconsin public schools, and how do they vary by school characteristics (urbanicity, FRPL rate, district size)? Can we construct school-level proficiency rates by race from DPI administrative data and link them to enrollment and school characteristics to explain cross-school variation in gaps?

**Design:** Merge Forward Exam proficiency data (by race/ethnicity, school level) from Wisconsin DPI with enrollment-by-race data and school characteristics. Build school-level racial gap measures. Aggregate to district and county level. Explore predictors of gap size.

**Principal investigator:** Jason Fletcher, University of Wisconsin–Madison.

**Repository:** Working research project using the Claude Code academic workflow ([fork lineage](https://github.com/jmfletcher/claude-code-my-workflow/tree/Wisconsin-Schools)).

---

## Data sources

| Source | Description | Access |
|--------|-------------|--------|
| WISEdash Forward Exam | School-level proficiency by race, grades 3–8 | [WISEdash Public Portal](https://wisedash.dpi.wi.gov/Dashboard/portalHome) → Topics → Assessment → Forward Exam |
| DPI Assessment Downloads | Raw CSV files with school IDs, more granular breakdowns | DPI site → Assessment → Forward Exam → Data & Results |
| DPI Enrollment by Race | School-level enrollment counts by race/ethnicity | DPI downloads (merge key: school ID) |
| School characteristics | Urbanicity, FRPL %, district size | DPI or NCES Common Core of Data |

See `DATA.md` for download instructions and placement.

---

## Deliverables (in priority order)

1. **End-to-end analysis pipeline** — reproducible code, documented denominators, versioned outputs.
2. **School-level dataset** — race-specific proficiency rates by school, merged with characteristics.
3. **Summary tables and figures** — gap distributions, correlates, county/district aggregations.
4. **Manuscript or report** (as scope develops).

Planned locations:

| Artifact | Location |
|----------|----------|
| Analysis scripts (Python) | `analysis/` |
| Figures | `output/figures/` |
| Tables | `output/tables/` |
| Manuscript | `manuscript/` |
| Exploratory / scratch | `explorations/` |
| Raw data (not tracked) | `Data/` |

---

## Workflow (non-negotiable)

- **Plan-first** for any non-trivial task. Save plans to `quality_reports/plans/YYYY-MM-DD_description.md`.
- **Contractor mode after approval:** implement → verify → review → fix → score.
- **Memory:** append `[LEARN:…]` entries to `MEMORY.md` when decisions or corrections should persist.
- **Quality gates:** default **80/100** to commit.

---

## Domain standards

- **Suppression:** Small cells (<10 students) are suppressed in DPI data at school level. Document which schools/subgroups are excluded due to suppression; do not impute.
- **Denominators:** Proficiency rates require both numerator (proficient students) and denominator (tested students). Track both; never use percentages without confirming the underlying N.
- **Standard changes:** DPI changed proficiency cut scores; time trends across years require checking whether standards changed. Document any year where comparisons are unreliable.
- **Test coverage:** Forward Exam (grades 3–8); PreACT (9–10); ACT (11). Do not mix tests unless explicitly modeling cross-test comparisons.
- **Figures:** Publication-ready: consistent fonts, colors, labels, legible legends.

---

## Pointers

| Resource | Purpose |
|----------|---------|
| `DATA.md` | Data download instructions |
| `MEMORY.md` | Cross-session learnings |
| `.claude/rules/` | Workflow rules |
| `PROJECT_NOTES.md` | Initial research notes (ChatGPT briefing) |
| `Bibliography_base.bib` | Shared citations |

---

## Commands (typical)

- **Python (primary):** `python3 analysis/script.py` from repo root; `pip install -r requirements.txt`.
- **Quarto (manuscript):** `quarto render manuscript/main.qmd`.
- **Git:** conventional commits; do not commit raw data — document paths in `Data/` and ignore via `.gitignore`.
