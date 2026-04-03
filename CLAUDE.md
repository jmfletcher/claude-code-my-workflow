# Wisconsin Schools — Racial Achievement Gap Analysis

## Project identity

**Working title:** Racial achievement gaps in Wisconsin public schools.

**Principal investigator:** Jason Fletcher, University of Wisconsin–Madison.

**Policy context:** The Madison Metropolitan School District (MMSD) is considering redrawing school attendance boundaries. This analysis provides an evidence base for understanding the drivers of race-based differences in test scores — specifically whether gaps are primarily a within-MMSD phenomenon (sorting across schools inside the district) or a cross-district phenomenon — to inform those boundary decisions.

**Repository:** Working research project using the Claude Code academic workflow ([fork lineage](https://github.com/jmfletcher/claude-code-my-workflow/tree/Wisconsin-Schools)).

---

## Research questions

### RQ1 — State-level gaps by race, grade, and subject
How large are racial achievement gaps (Black–White, Hispanic–White, and other minority–White) across Wisconsin public schools? How do gaps vary by grade (3–8 on the Forward Exam) and subject (ELA vs. Math)?

### RQ2 — Within–between decomposition
What share of the statewide racial gap in proficiency is explained by sorting of students *across* schools / districts / counties ("between" component) vs. gaps that exist *within* the same school ("within" component)? Decompose at three levels of aggregation:
- Between/within county
- Between/within district
- Between/within school

### RQ3 — MMSD deep-dive and cross-district comparisons
How large are racial gaps within MMSD, and what drives them? Two key thought experiments:
1. **MMSD minority vs. other districts:** How do Black and Hispanic students in MMSD perform compared to Black and Hispanic students in Milwaukee and other WI districts — not just relative to MMSD white students? This addresses whether MMSD minority students are actually performing well relative to their peers statewide.
2. **MMSD minority vs. non-MMSD white:** Compare racial minority students in MMSD to white students in non-MMSD districts. This addresses the outlier-SES problem: MMSD white students have very high parental education and income, so the MMSD within-district gap overstates "typical" racial gaps.

---

## Data sources

| Source | Description | Access |
|--------|-------------|--------|
| WISEdash Forward Exam | School-level proficiency by race, grades 3–8 | [WISEdash Public Portal](https://wisedash.dpi.wi.gov/Dashboard/portalHome) → Topics → Assessment → Forward Exam |
| DPI Assessment Downloads | Raw CSV files with school IDs, more granular breakdowns | DPI site → Assessment → Forward Exam → Data & Results |
| DPI Enrollment by Race | School-level enrollment counts by race/ethnicity | DPI downloads (merge key: school ID) |
| School characteristics | Urbanicity, FRPL %, district size | DPI or NCES Common Core of Data |

See `DATA.md` for download instructions and file placement. See `.claude/rules/knowledge-base.md` for confirmed variable names and race label strings once data is downloaded.

---

## Deliverables (in priority order)

1. **End-to-end analysis pipeline** — reproducible Python code, documented denominators, versioned outputs
2. **School-level merged dataset** — race-specific proficiency rates per school, with enrollment, suppression flags, and school characteristics
3. **Professional report** (`manuscript/`) — Quarto → PDF; polished tables and publication-quality figures
4. **Slide deck** (`Slides/`) — Quarto RevealJS → PDF; summary of key findings for policy audience

Artifact locations:

| Artifact | Location |
|----------|----------|
| Analysis scripts (Python) | `analysis/` |
| Figures (PDF + PNG) | `output/figures/` |
| Tables (CSV + LaTeX) | `output/tables/` |
| Suppression log | `output/tables/suppression_log.csv` |
| Report source | `manuscript/main.qmd` |
| Slide source | `Slides/main.qmd` |
| Exploratory / scratch | `explorations/` |
| Raw data (not tracked) | `Data/` |

---

## Workflow (non-negotiable)

- **Plan-first** for any non-trivial task (multi-step, multi-file, or ambiguous). Save plans to `quality_reports/plans/YYYY-MM-DD_description.md`; use `quality_reports/specs/` + `templates/requirements-spec.md` when requirements are fuzzy.
- **Contractor mode after approval:** implement → verify → review → fix → score. See `.claude/rules/orchestrator-protocol.md`.
- **Memory:** append `[LEARN:…]` entries to `MEMORY.md` when decisions or corrections should persist.
- **Quality gates:** default **80/100** to commit; 90/100 for manuscript figures and tables. See `.claude/rules/quality-gates.md`.
- **Session logs:** always. Post-plan, incremental updates, and end-of-session summary to `quality_reports/session_logs/`.
- **Check in more frequently** in the first few sessions; taper to standard contractor autonomy as patterns stabilize.

---

## Domain standards

### Data integrity
- **Suppression:** DPI suppresses cells with N < 10 students. Treat suppressed cells as `NaN` — do not impute. Log all suppressed cells to `output/tables/suppression_log.csv`. Report suppression rates when summarizing coverage.
- **Denominators:** Always carry `n_tested` alongside `pct_proficient`. Never plot proficiency rates without annotating or documenting the underlying N. A rate based on 12 students is not comparable to one based on 400.
- **Test type separation:** Do not mix Forward Exam (grades 3–8) with ACT (grade 11) or PreACT (grades 9–10) in any single analysis unless explicitly building a cross-test comparison with documented assumptions.

### Proficiency standards
- DPI changed proficiency cut scores in recent years. Document the year of any standard revision. Time trends that cross a standard-revision year require a caveat or explicit adjustment. Cross-year comparisons default to same-standard years unless stated otherwise.

### MMSD comparisons
- MMSD white students are high-SES outliers statewide (high parental education, high income). Do not use MMSD whites as the comparison group for statewide claims about racial gaps.
- All cross-district comparisons involving MMSD should state explicitly which comparison group is being used and why.
- The two priority comparisons are: (1) MMSD minority vs. same-race students in Milwaukee and other WI districts; (2) MMSD minority vs. non-MMSD white students statewide.
- "Within-MMSD gap" and "MMSD gap relative to state" are distinct quantities — always label which one is being reported.

### Figures
- Publication-ready: white background, minimum 9pt font, consistent font family, labeled axes, legible legends.
- Save every figure as both PDF and PNG (150 DPI minimum).
- Use the project color palette (see `.claude/WORKFLOW_QUICK_REF.md`). Do not use default matplotlib colors in final outputs.
- Suppressed or missing subgroups must be visually distinguished from zero (use a different marker or note in caption).

---

## Pointers

| Resource | Purpose |
|----------|---------|
| `DATA.md` | Data download instructions and file placement |
| `MEMORY.md` | Cross-session learnings and decisions |
| `.claude/rules/knowledge-base.md` | Variable names, race labels, estimand definitions (fill as data arrives) |
| `.claude/WORKFLOW_QUICK_REF.md` | Non-negotiables: paths, figures, colors, reporting |
| `PROJECT_NOTES.md` | Initial research notes (ChatGPT briefing on WISEdash) |
| `Bibliography_base.bib` | Shared citations |
| `.claude/agents/domain-reviewer.md` | Substance review for analysis and report |

---

## Commands (typical)

```bash
# Install dependencies
pip install -r requirements.txt

# Run analysis script
python3 analysis/01_load_and_clean.py

# Render report
quarto render manuscript/main.qmd --to pdf

# Render slides
quarto render Slides/main.qmd --to revealjs
```

Git: conventional commits; do not commit raw data — document paths in `Data/` and ignore via `.gitignore`.
